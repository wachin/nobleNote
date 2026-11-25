# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""The Note widget displays the content of a note file."""

from PyQt6.QtCore import QByteArray, QSettings, QSize, Qt
from PyQt6.QtGui import QAction, QFont, QKeySequence
from PyQt6.QtWidgets import QMainWindow

from .notedescriptor import NoteDescriptor
from .textbrowser import TextBrowser
from .textdocument import TextDocument
from .textformattingtoolbar import TextFormattingToolbar
from .textsearchtoolbar import TextSearchToolbar
from .ui.ui_note import Ui_Note


class Note(QMainWindow, Ui_Note):
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.show_after_loading_ = False
        self.text_browser = TextBrowser(self)
        self.text_document = TextDocument(self)
        self.text_browser.setDocument(self.text_document)
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

        self.toolbar = TextFormattingToolbar(self.text_browser, self)
        self.toolbar.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.addToolBar(self.toolbar)
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)

        font = QFont()
        font.setFamily(str(QSettings().value("note_editor_font", "DejaVu Sans")))
        font.setPointSize(int(QSettings().value("note_editor_font_size", 10)))
        self.text_document.setDefaultFont(font)
        self.toolbar.set_font(font)

        # must be constructed after the TextDocument
        self.note_descriptor_ = NoteDescriptor(file_path, self.text_browser,
                                               self.text_document, self)
        self.text_browser.setReadOnly(self.note_descriptor_.read_only())
        self.text_browser.setTextInteractionFlags(
            self.text_browser.textInteractionFlags()
            | Qt.TextInteractionFlag.LinksAccessibleByMouse)

        self.gridLayout.addWidget(self.text_browser, 0, 0, 1, 1)
        self.text_browser.setFocus()

        self.search_bar = TextSearchToolbar(self.text_browser, self)
        self.search_bar.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.addToolBar(self.search_bar)

        self.note_descriptor_.close.connect(self.close)
        self.text_browser.signalFocusInEvent.connect(
            self.note_descriptor_.state_change)
        self.note_descriptor_.loadFinished.connect(
            self.load_size_and_show, Qt.ConnectionType.QueuedConnection)

    # ------------------------------------------------------------------
    def note_descriptor(self) -> NoteDescriptor:
        return self.note_descriptor_

    def text_edit(self):
        return self.text_browser

    def highlight_text(self, the_str: str):
        self.search_bar.highlight_text(the_str)

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
        if self.search_bar.isVisible() or self.toolbar.isVisible():
            self.show_hide_toolbars.setText("Hide Toolbars")
        else:
            self.show_hide_toolbars.setText("Show Toolbars")

        menu = self.text_browser.createStandardContextMenu()
        menu.addAction(self.show_hide_toolbars)
        menu.exec(self.text_browser.mapToGlobal(point))

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