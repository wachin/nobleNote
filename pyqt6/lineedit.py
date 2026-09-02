# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A QLineEdit with a clear (close) button."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLineEdit, QStyle, QToolButton

from .resources import icon


class LineEdit(QLineEdit):
    sendCleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clear_button = QToolButton(self)
        self.clear_button.setIcon(icon("closeB"))
        self.clear_button.setCursor(Qt.CursorShape.ArrowCursor)
        self.clear_button.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self.clear_button.hide()
        self.clear_button.clicked.connect(self.clear)
        self.clear_button.clicked.connect(self.sendCleared)
        self.textChanged.connect(self.update_close_button)
        frame_width = self.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
        self.setStyleSheet("QLineEdit { padding-right: %dpx; }"
                           % (self.clear_button.sizeHint().width() + frame_width + 1))
        msz = self.minimumSizeHint()
        self.setMinimumSize(max(msz.width(),
                                self.clear_button.sizeHint().height() + frame_width * 2 + 2),
                            max(msz.height(),
                                self.clear_button.sizeHint().height() + frame_width * 2 + 2))

    def resizeEvent(self, event):
        sz = self.clear_button.sizeHint()
        frame_width = self.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
        self.clear_button.move(self.rect().right() - frame_width - sz.width(),
                               (self.rect().bottom() + 1 - sz.height()) // 2)
        super().resizeEvent(event)

    def update_close_button(self, text: str):
        self.clear_button.setVisible(bool(text))