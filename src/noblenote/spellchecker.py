# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Spell checking of the note editor with Hunspell.

Misspelled words are marked with the platform's red wavy underline and can be
corrected from the context menu; "Add to dictionary" keeps the word in
QSettings, so it is no longer underlined in any note.

Hunspell is used through the optional `hunspell` python bindings (Debian:
python3-hunspell) together with the dictionaries installed on the system
(/usr/share/hunspell, DICPATH, ...).  When the module or a dictionary is
missing nothing is underlined and the editor keeps working as before.
"""

import os
import re
from pathlib import Path

from PyQt6.QtCore import QLocale, QObject, QSettings, QTimer
from PyQt6.QtGui import QAction, QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QTextEdit

from . import resources

try:  # optional dependency: spell checking works without it
    import hunspell as _hunspell
except ImportError:  # pragma: no cover - depends on the system
    _hunspell = None

#: Places with *.aff/*.dic dictionaries, in search order (DICPATH wins).
_DICTIONARY_DIRS = (
    os.environ.get("DICPATH", ""),
    "/usr/share/hunspell",
    "/usr/share/myspell",
    "/usr/share/myspell/dicts",
    "/usr/local/share/hunspell",
    os.path.expanduser("~/.local/share/hunspell"),
    os.path.expanduser("~/.hunspell"),
    "/Library/Spelling",
    os.path.expanduser("~/Library/Spelling"),
)

#: links and e-mail addresses are never spell checked
_IGNORED_RE = re.compile(r"(?:[A-Za-z][A-Za-z0-9+.-]*://|www\.)\S+|\S+@\S+\.\S+")

#: words: letters (accents included) with inner apostrophes or hyphens
_WORD_RE = re.compile(r"[^\W\d_]+(?:['\u2019-][^\W\d_]+)*")

_MAX_SELECTIONS = 5000
_MAX_WORD_LENGTH = 45

#: loaded dictionaries are shared by every note window
_dictionaries = {}


def dictionary_dirs():
    """Every directory that may contain hunspell dictionaries."""
    dirs = []
    for entry in _DICTIONARY_DIRS:
        for directory in str(entry).split(os.pathsep):
            if directory and directory not in dirs:
                dirs.append(directory)
    return dirs


def available_dictionaries() -> dict:
    """Map a language name ("es_EC") to its (dictionary, affix) paths."""
    found = {}
    for directory in dictionary_dirs():
        path = Path(directory)
        if not path.is_dir():
            continue
        for affix in path.glob("*.aff"):
            dictionary = affix.with_suffix(".dic")
            if dictionary.is_file():
                found.setdefault(affix.stem, (str(dictionary), str(affix)))
    return dict(sorted(found.items()))


def spell_checking_available() -> bool:
    """True when the bindings and at least one dictionary are installed."""
    return _hunspell is not None and bool(available_dictionaries())


def _match_language(name: str, available: dict) -> str:
    """The dictionary key that best matches a language name, or ''."""
    name = (name or "").replace("-", "_").lower()
    if not name or not available:
        return ""
    for key in available:
        if key.lower() == name:
            return key
    base = name.split("_")[0]
    for key in available:
        if key.lower().split("_")[0] == base:
            return key
    return ""


def default_language(available: dict) -> str:
    """The dictionary chosen in the preferences or the system language."""
    if not available:
        return ""
    requested = str(QSettings().value("spell_check_language", "") or "")
    language = (_match_language(requested, available)
                or _match_language(QLocale.system().name(), available))
    if language:
        return language
    return "en_US" if "en_US" in available else next(iter(available))


def _user_words() -> set:
    saved = QSettings().value("spell_check_user_words", [])
    if isinstance(saved, str):
        saved = [saved]
    return {str(word) for word in (saved or []) if str(word).strip()}


def _save_user_words(words):
    QSettings().setValue("spell_check_user_words", sorted(words))


def _underline_format() -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
    fmt.setUnderlineColor(QColor("#ff8a80" if resources._is_dark_scheme()
                                 else "#d32f2f"))
    return fmt


class HunspellChecker:
    """A thin wrapper around a hunspell dictionary."""

    def __init__(self, language: str = ""):
        self.dictionary = None
        self.language = ""
        self.user_words = _user_words()
        self.load(language)

    def load(self, language: str = ""):
        available = available_dictionaries()
        if _hunspell is None or not available:
            self.dictionary = None
            self.language = ""
            return
        language = (_match_language(language, available)
                    or default_language(available))
        paths = available[language]
        if paths not in _dictionaries:
            try:
                _dictionaries[paths] = _hunspell.HunSpell(*paths)
            except Exception:  # broken dictionary: no spell checking
                self.dictionary = None
                self.language = ""
                return
        self.dictionary = _dictionaries[paths]
        self.language = language
        for word in self.user_words:
            self.dictionary.add(word)

    def available(self) -> bool:
        return self.dictionary is not None

    def check(self, word: str) -> bool:
        if self.dictionary is None:
            return True
        return bool(self.dictionary.spell(word))

    def suggest(self, word: str, limit: int = 8) -> list:
        if self.dictionary is None:
            return []
        return list(self.dictionary.suggest(word))[:limit]

    def add(self, word: str):
        word = word.strip()
        if not word:
            return
        self.user_words.add(word)
        if self.dictionary is not None:
            self.dictionary.add(word)
        _save_user_words(self.user_words)


class SpellCheck(QObject):
    """Underlines the misspelled words of a QTextEdit and offers corrections."""

    def __init__(self, text_edit: QTextEdit, parent=None):
        super().__init__(parent or text_edit)
        self.text_edit_ = text_edit
        self.checker = HunspellChecker()
        self.enabled_ = False
        self.format_ = _underline_format()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(350)
        self.timer.timeout.connect(self.update)
        text_edit.textChanged.connect(self._text_changed)
        watcher = resources.palette_watcher()
        if watcher is not None:
            watcher.paletteChanged.connect(self._palette_changed)
        self.apply_settings()

    # -- configuration -------------------------------------------------
    def apply_settings(self):
        """Re-read enabled state, language and dictionary from QSettings."""
        self.checker = HunspellChecker(
            str(QSettings().value("spell_check_language", "") or ""))
        self.enabled_ = bool(
            QSettings().value("spell_check_enabled", True)
            and self.checker.available())
        self.format_ = _underline_format()
        self.timer.stop()
        if self.enabled_:
            self.update()
        else:
            self.text_edit_.setExtraSelections([])

    def _text_changed(self):
        if self.enabled_:
            self.timer.start()

    def _palette_changed(self):
        """Follow a color scheme change with the underline color."""
        self.format_ = _underline_format()
        self.update()

    # -- underlining ---------------------------------------------------
    def update(self):
        """Recompute the underlines of the whole document."""
        if not self.enabled_:
            return
        document = self.text_edit_.document()
        selections = []
        block = document.begin()
        while block.isValid() and len(selections) < _MAX_SELECTIONS:
            text = block.text()
            ignored = [(match.start(), match.end())
                       for match in _IGNORED_RE.finditer(text)]
            for match in _WORD_RE.finditer(text):
                if not self._is_misspelled(match.group(), match.start(),
                                           ignored):
                    continue
                cursor = QTextCursor(document)
                cursor.setPosition(block.position() + match.start())
                cursor.setPosition(block.position() + match.end(),
                                   QTextCursor.MoveMode.KeepAnchor)
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = self.format_
                selections.append(selection)
            block = block.next()
        self.text_edit_.setExtraSelections(selections)

    def _is_misspelled(self, word: str, start: int, ignored) -> bool:
        if len(word) < 2 or len(word) > _MAX_WORD_LENGTH:
            return False
        if any(char.isdigit() for char in word):
            return False
        if any(char.isupper() for char in word[1:]):
            return False  # PyQt, iPhone, McDonald: not dictionary words
        for begin, end in ignored:
            if begin <= start < end:
                return False
        return not self.checker.check(word)

    # -- context menu --------------------------------------------------
    def misspelled_cursor(self, position):
        """A cursor selecting the misspelled word at a viewport position."""
        if not self.enabled_:
            return None
        cursor = self.text_edit_.cursorForPosition(position)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()
        if not word or not _WORD_RE.fullmatch(word):
            return None
        if not self._is_misspelled(word, 0, []):
            return None
        return cursor

    def populate_menu(self, menu, position) -> bool:
        """Add the suggestions and "Add to dictionary" to a context menu."""
        cursor = self.misspelled_cursor(position)
        if cursor is None:
            return False
        word = cursor.selectedText()
        actions = []
        for suggestion in self.checker.suggest(word):
            action = QAction(suggestion, menu)
            action.triggered.connect(
                lambda _checked=False, target=QTextCursor(cursor),
                text=suggestion: self._replace(target, text))
            actions.append(action)
        if actions:
            separator = QAction(menu)
            separator.setSeparator(True)
            actions.append(separator)
        add_action = QAction(self.tr("Add to dictionary"), menu)
        add_action.triggered.connect(
            lambda _checked=False, text=word: self.add_to_dictionary(text))
        actions.append(add_action)

        first = menu.actions()[0] if menu.actions() else None
        if first is None:
            menu.addActions(actions)
        else:
            menu.insertActions(first, actions)
        return True

    def _replace(self, cursor, word: str):
        if not cursor.hasSelection():
            return
        cursor.insertText(word)
        self.update()

    def add_to_dictionary(self, word: str):
        self.checker.add(word)
        self.update()
