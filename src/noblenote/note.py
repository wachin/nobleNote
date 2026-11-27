# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""The Note widget displays the content of a note file."""

from pathlib import Path

from PyQt6.QtCore import QByteArray, QCoreApplication, QSettings, QSize, Qt
from PyQt6.QtGui import QAction, QFont, QKeySequence
from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow

from .historywindow import HistoryWindow
from .notedescriptor import NoteDescriptor
from .resources import icon, palette_watcher
from .spellchecker import SpellCheck
from .textbrowser import TextBrowser
from .textdocument import TextDocument
from .textformattingtoolbar import TextFormattingToolbar
from .textsearchtoolbar import TextSearchToolbar
from .titlebar import NoteTitleBar, WindowResizeGrips
from .ui.ui_note import Ui_Note
from .undobanner import UndoBanner
from .undohistory import (ENTRY_REDO, ENTRY_RESTORE, ENTRY_UNDO, UndoHistory,
                          one_line)

class Note(QMainWindow, Ui_Note):
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # no native title bar: the formatting toolbar lives in ours
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        self.show_after_loading_ = False
        self.text_browser = TextBrowser(self)
        self.text_document = TextDocument(self)
        self.text_browser.setDocument(self.text_document)
        self.spell_check = SpellCheck(self.text_browser, self)
        self.text_browser.undoRequested.connect(self.undo)
        self.text_browser.redoRequested.connect(self.redo)
        self.text_browser.ensureCursorVisible()
        # tab size 4 (android compatibility)
        self.text_browser.setTabStopDistance(
            self.fontMetrics().boundingRect(" ").width() * 4)

        self.show_hide_toolbars = QAction(self)
        self.show_hide_toolbars.setShortcut(QKeySequence("Ctrl+T"))
        self.show_hide_toolbars.triggered.connect(self.show_or_hide_toolbars)

        self.text_browser.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.text_browser.customContextMenuRequested.connect(
            self.show_context_menu)

        # undo/redo: the window shortcuts show the big reminder and feed the
        # persistent history of the note
        self.undo_action = QAction(icon("undo"), self.tr("&Undo"), self)
        self.undo_action.setShortcuts([QKeySequence.StandardKey.Undo])
        self.undo_action.setToolTip(self.tr("Undo (Ctrl+Z)"))
        self.undo_action.triggered.connect(self.undo)
        self.redo_action = QAction(icon("redo"), self.tr("&Redo"), self)
        self.redo_action.setShortcuts([QKeySequence.StandardKey.Redo,
                                       QKeySequence("Ctrl+Y")])
        self.redo_action.setToolTip(
            self.tr("Redo (Ctrl+Shift+Z or Ctrl+Y)"))
        self.redo_action.triggered.connect(self.redo)
        self.history_action = QAction(self.tr("Change &history…"), self)
        self.history_action.setShortcut(QKeySequence("Ctrl+Shift+H"))
        self.history_action.triggered.connect(self.show_history_window)
        for action in (self.undo_action, self.redo_action,
                       self.history_action):
            self.addAction(action)

        self._history = None
        self._history_window = None

        self.toolbar = TextFormattingToolbar(self.text_browser, self)
        self.toolbar.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.toolbar.add_history_actions(self.undo_action, self.redo_action)
        self.toolbar.preferencesRequested.connect(self.show_preferences)
        self._pref_connected_ = False

        self.title_bar = NoteTitleBar(self, self.toolbar, self)
        self.setMenuWidget(self.title_bar)
        self.windowTitleChanged.connect(self.title_bar.set_title)
        self.title_bar.set_title(self.windowTitle())
        self.resize_grips = WindowResizeGrips(self)

        self.apply_default_font()

        # must be constructed after the TextDocument
        self.note_descriptor_ = NoteDescriptor(file_path, self.text_browser,
                                               self.text_document, self)
        self.text_browser.setReadOnly(self.note_descriptor_.read_only())
        self.text_browser.setTextInteractionFlags(
            self.text_browser.textInteractionFlags()
            | Qt.TextInteractionFlag.LinksAccessibleByMouse)

        self.gridLayout.addWidget(self.text_browser, 0, 0, 1, 1)
        self.banner = UndoBanner(self.centralwidget)
        self.text_browser.setFocus()

        self.search_bar = TextSearchToolbar(self.text_browser, self)
        self.search_bar.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.addToolBar(self.search_bar)

        self.note_descriptor_.aboutToLoad.connect(self._suspend_history)
        self.note_descriptor_.close.connect(self.close)
        self.text_browser.signalFocusInEvent.connect(
            self.note_descriptor_.state_change)
        self.note_descriptor_.loadFinished.connect(
            self.load_size_and_show, Qt.ConnectionType.QueuedConnection)

        watcher = palette_watcher()
        if watcher is not None:
            watcher.paletteChanged.connect(self.refresh_history_icons)

    # ------------------------------------------------------------------
    def note_descriptor(self) -> NoteDescriptor:
        return self.note_descriptor_

    def text_edit(self):
        return self.text_browser

    def highlight_text(self, the_str: str):
        self.search_bar.highlight_text(the_str)

    def apply_default_font(self):
        """Use the note editor font chosen in the preferences."""
        font = QFont()
        font.setFamily(str(QSettings().value("note_editor_font", "DejaVu Sans")))
        font.setPointSize(int(QSettings().value("note_editor_font_size", 10)))
        self.text_document.setDefaultFont(font)

    def apply_spell_check_settings(self):
        """Use the spell checking settings chosen in the preferences."""
        self.spell_check.apply_settings()

    def refresh_history_icons(self):
        """Re-create the undo/redo icons after the palette changed."""
        self.undo_action.setIcon(icon("undo"))
        self.redo_action.setIcon(icon("redo"))

    # ------------------------------------------------------------------
    def _suspend_history(self):
        """Do not record the programmatic reload of the note."""
        if self._history is not None:
            self._history.suspend()

    def _init_history(self):
        """Start recording the persistent history once the note is loaded."""
        if self._history is None:
            uuid_ = self.note_descriptor_.uuid()
            path = self.note_descriptor_.file_path()
            if uuid_:
                key = "uuid:" + str(uuid_)
            else:
                key = "path:" + str(Path(path).resolve())
            self._history = UndoHistory(self.text_document, key, path, self)
        else:
            self._history.reset_baseline()

    def _show_history_banner(self, title: str, detail: str = "",
                             hint: str = ""):
        self.banner.show_message(title, detail, hint)

    def undo(self):
        if self.note_descriptor_.read_only():
            self._show_history_banner(self.tr("The note is read-only"))
            return
        if not self.text_document.isUndoAvailable():
            self._show_history_banner(
                self.tr("Nothing to undo"), "",
                self.tr("Redo with Ctrl+Shift+Z (or Ctrl+Y)"))
            return
        if self._history is not None:
            self._history.mark_next(ENTRY_UNDO)
        self.text_browser.undo()
        if self._history is not None:
            self._history.clear_mark()
            self._history.flush()
        self._show_history_action_banner("undo")

    def redo(self):
        if self.note_descriptor_.read_only():
            self._show_history_banner(self.tr("The note is read-only"))
            return
        if not self.text_document.isRedoAvailable():
            self._show_history_banner(
                self.tr("Nothing to redo"), "", self.tr("Undo with Ctrl+Z"))
            return
        if self._history is not None:
            self._history.mark_next(ENTRY_REDO)
        self.text_browser.redo()
        if self._history is not None:
            self._history.clear_mark()
            self._history.flush()
        self._show_history_action_banner("redo")

    def _show_history_action_banner(self, kind: str):
        entry = self._history.last_written if self._history else None
        if kind == "undo":
            title = self.tr("Undone")
            hint = self.tr("Redo with Ctrl+Shift+Z (or Ctrl+Y)")
        else:
            title = self.tr("Redone")
            hint = self.tr("Undo with Ctrl+Z")
        detail = ""
        if entry is not None:
            snippet = one_line(entry.removed or entry.added, 80)
            if snippet:
                if kind == "undo" and entry.added:
                    detail = self.tr("Restored: «%1»").replace("%1", snippet)
                elif kind == "redo" and entry.added:
                    detail = self.tr("Written: «%1»").replace("%1", snippet)
                else:
                    detail = self.tr("Removed: «%1»").replace("%1", snippet)
        self._show_history_banner(title, detail, hint)

    def show_history_window(self):
        """Open the window with the whole change history of this note."""
        if self._history is None:
            self._show_history_banner(self.tr("The history is not ready"))
            return
        if self._history_window is None:
            self._history_window = HistoryWindow(
                self._history, self.windowTitle(), self)
            self._history_window.insertRequested.connect(
                self.insert_history_text)
            self._history_window.restoreRequested.connect(
                self.restore_history_snapshot)
        self._history_window.note_title_ = self.windowTitle()
        self._history_window.refresh()
        self._history_window.show()
        self._history_window.raise_()
        self._history_window.activateWindow()

    def insert_history_text(self, text: str):
        if self.note_descriptor_.read_only():
            self._show_history_banner(self.tr("The note is read-only"))
            return
        cursor = self.text_browser.textCursor()
        cursor.insertText(text)
        self.text_browser.setTextCursor(cursor)
        self.text_browser.setFocus()

    def restore_history_snapshot(self, html: str):
        if self.note_descriptor_.read_only():
            self._show_history_banner(self.tr("The note is read-only"))
            return
        previous = self._history.begin_external_change()
        self.text_browser.setHtml(html)
        self._history.end_external_change(previous, ENTRY_RESTORE)
        self.text_document.setModified(True)
        self._show_history_banner(
            self.tr("Note restored"),
            self.tr("The later changes are still in the history."),
            self.tr("History: Ctrl+Shift+H"))

    @staticmethod
    def _main_window():
        """The main window, if the application has one."""
        app = QApplication.instance()
        if app is None:
            return None
        for widget in app.topLevelWidgets():
            if hasattr(widget, "note_view") and hasattr(widget, "show_preferences"):
                return widget
        return None

    def show_preferences(self):
        """Open the program preferences (font family and size live there)."""
        main_window = self._main_window()
        if main_window is not None:
            main_window.show_preferences()
            preference_dialog = getattr(main_window, "_pref", None)
            if preference_dialog is not None and not self._pref_connected_:
                preference_dialog.accepted.connect(self.apply_default_font)
                self._pref_connected_ = True
            return
        # a note window without a main window (e.g. opened from the tray)
        from .preferences import Preferences
        dialog = Preferences(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_default_font()

    # ------------------------------------------------------------------
    def _uuid_key(self) -> str:
        uuid_ = self.note_descriptor_.uuid()
        return "{" + str(uuid_) + "}" if uuid_ else "{}"

    def load_size_and_show(self):
        size_key = "Notes/" + self._uuid_key() + "_size"
        size = QSettings().value(size_key, Note.editor_size())
        try:
            self.resize(QSize(int(size.width()), int(size.height())))
        except Exception:
            pass
        if self.show_after_loading_:
            self.show()
        self.restore_window_state()
        self._init_history()
        if self.search_bar.text():
            self.search_bar.search_line().setFocus()
            self.search_bar.select_next_expression()
            self.search_bar.show()
        else:
            self.search_bar.hide()

    @staticmethod
    def add_to_open_note_list(path: str):
        saved = QSettings().value("open_notes", [])
        if isinstance(saved, str):
            saved = [saved]
        else:
            saved = list(saved or [])
        saved.append(path)
        QSettings().setValue("open_notes", saved)

    @staticmethod
    def editor_size() -> QSize:
        return QSettings().value("note_editor_default_size", QSize(650, 400))

    def save_window_state(self, variant_list):
        uuid_key = variant_list[4]
        QSettings().setValue("Notes/" + uuid_key + "_size", variant_list[0])
        QSettings().setValue("Note_window_and_toolbar/state", variant_list[1])
        QSettings().setValue("Notes/" + uuid_key + "_window_position",
                             variant_list[2])
        QSettings().setValue("Notes/" + uuid_key + "_cursor_position",
                             variant_list[3])
        saved_open_note_list = QSettings().value("open_notes", [])
        if isinstance(saved_open_note_list, str):
            saved_open_note_list = [saved_open_note_list]
        else:
            saved_open_note_list = list(saved_open_note_list or [])
        if variant_list[5] in saved_open_note_list:
            saved_open_note_list.remove(variant_list[5])
        QSettings().setValue("open_notes", saved_open_note_list)

    def restore_window_state(self):
        state = QSettings().value("Note_window_and_toolbar/state", QByteArray())
        if isinstance(state, (bytes, bytearray)):
            state = QByteArray(state)
        self.restoreState(state)

        pos_key = "Notes/" + self._uuid_key() + "_window_position"
        if QSettings().contains(pos_key):
            geometry_data = QSettings().value(pos_key, QByteArray())
            if isinstance(geometry_data, (bytes, bytearray)):
                geometry_data = QByteArray(geometry_data)
            self.restoreGeometry(geometry_data)
        else:  # center in desktop if there's no saved position
            self.move(self.screen().availableGeometry().center()
                      - self.rect().center())

    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.text_browser.setTextInteractionFlags(
                Qt.TextInteractionFlag.LinksAccessibleByMouse
                | Qt.TextInteractionFlag.LinksAccessibleByKeyboard)
            self.text_browser.setReadOnly(self.note_descriptor_.read_only())

        if (event.modifiers() == Qt.KeyboardModifier.ControlModifier
                and event.key() == Qt.Key.Key_F):
            if self.text_browser.textCursor().hasSelection():
                self.search_bar.set_text(
                    self.text_browser.textCursor().selectedText())
            if not self.search_bar.isVisible():
                self.search_bar.setVisible(True)
                self.search_bar.search_line().setFocus()

        if (event.modifiers() == Qt.KeyboardModifier.ControlModifier
                and event.key() == Qt.Key.Key_T):
            self.show_or_hide_toolbars()

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.text_browser.setReadOnly(self.note_descriptor_.read_only())
        self.text_browser.setTextInteractionFlags(
            self.text_browser.textInteractionFlags()
            | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        super().keyReleaseEvent(event)

    # ------------------------------------------------------------------
    def set_search_bar_text(self, the_str: str):
        self.search_bar.set_text(the_str)
        self.search_bar.select_next_expression()
        self.search_bar.setVisible(True)

    def show_context_menu(self, point):
        menu = self._create_context_menu()
        menu.exec(self.text_browser.mapToGlobal(point))

    def _create_context_menu(self):
        if self.search_bar.isVisible() or self.toolbar.isVisible():
            self.show_hide_toolbars.setText(self.tr("Hide Toolbars"))
        else:
            self.show_hide_toolbars.setText(self.tr("Show Toolbars"))

        menu = self.text_browser.createStandardContextMenu()
        # the built-in undo/redo entries have no reminder and no history:
        # replace them with the actions of the note window
        # the context is assembled at runtime so that these Qt-internal
        # strings do not end up in the nobleNote translation files
        text_context = "QText" + "Control"
        builtin_texts = {
            QCoreApplication.translate(text_context, "&Undo").replace("&", ""),
            QCoreApplication.translate(text_context, "&Redo").replace("&", ""),
            "Undo", "Redo",
        }
        for action in list(menu.actions()):
            if action.text().replace("&", "") in builtin_texts:
                menu.removeAction(action)
        first = menu.actions()[0] if menu.actions() else None
        if first is not None:
            menu.insertAction(first, self.redo_action)
            menu.insertAction(self.redo_action, self.undo_action)
            if not first.isSeparator():
                menu.insertSeparator(first)
        else:
            menu.addAction(self.undo_action)
            menu.addAction(self.redo_action)
            menu.addSeparator()
        self.spell_check.populate_menu(menu,
                                       self.text_browser.cursorRect().center())
        menu.addSeparator()
        menu.addAction(self.show_hide_toolbars)
        menu.addAction(self.history_action)
        return menu

    def show_or_hide_toolbars(self):
        if self.search_bar.isVisible() or self.toolbar.isVisible():
            if self.search_bar.isVisible():
                self.search_bar.setVisible(False)
            if self.toolbar.isVisible():
                self.toolbar.setVisible(False)
        else:
            self.search_bar.setVisible(True)
            self.toolbar.setVisible(True)

    def show_after_loaded(self):
        self.show_after_loading_ = True

    def closeEvent(self, event):
        if self._history is not None:
            self._history.flush()
        if self._history_window is not None:
            self._history_window.close()
        self.note_descriptor_.state_change()
        # collect everything that requires the gui thread
        variant_list = [self.size(),
                        self.saveState(),
                        self.saveGeometry(),
                        self.text_browser.textCursor().position(),
                        self._uuid_key(),
                        self.note_descriptor().file_path()]
        self.save_window_state(variant_list)
        super().closeEvent(event)