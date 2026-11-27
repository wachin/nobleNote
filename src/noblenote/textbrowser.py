# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A text edit with custom focus and paste handling."""

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import (QDesktopServices, QKeySequence, QTextCharFormat,
                         QTextDocumentFragment)
from PyQt6.QtWidgets import QTextBrowser


class TextBrowser(QTextBrowser):
    signalFocusInEvent = pyqtSignal()
    signalFocusOutEvent = pyqtSignal()
    undoRequested = pyqtSignal()
    redoRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        self.setOpenLinks(False)  # all links are opened in the web browser
        self.anchorClicked.connect(self.open_link_in_browser)

    def keyPressEvent(self, event):
        # QTextEdit handles Ctrl+Z itself, which would bypass the reminder and
        # the history of the note window: report it instead.
        if event.matches(QKeySequence.StandardKey.Undo):
            self.undoRequested.emit()
            event.accept()
            return
        if (event.matches(QKeySequence.StandardKey.Redo)
                or (event.key() == Qt.Key.Key_Y
                    and event.modifiers() == Qt.KeyboardModifier.ControlModifier)):
            self.redoRequested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        self.signalFocusInEvent.emit()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.signalFocusOutEvent.emit()
        super().focusOutEvent(event)

    def open_link_in_browser(self, link: QUrl):
        QDesktopServices.openUrl(link)

    def insertFromMimeData(self, source):
        """Insert rich text (e.g. pasted web content) as a fragment."""
        cursor_format = self.textCursor().charFormat()
        if source.hasHtml():
            fragment = QTextDocumentFragment.fromHtml(source.html(),
                                                      self.document())
            self.textCursor().insertFragment(fragment)
            self.ensureCursorVisible()
            self.textCursor().insertText(" ", cursor_format)
        else:
            super().insertFromMimeData(source)

    def slot_set_read_only(self, ro: bool):
        self.setReadOnly(ro)