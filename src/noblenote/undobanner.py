# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A big, transient reminder shown over the note editor.

It is used when the note is undone or redone: it tells what happened and,
very prominently, which shortcut redoes or undoes it.
"""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QTimer, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QLabel,
                             QVBoxLayout, QWidget)

_VISIBLE_MS = 3000


class UndoBanner(QFrame):
    """A large rounded message centered at the top of the editor."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("UndoBanner")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(4)

        self.title_label = QLabel(self)
        self.title_label.setObjectName("UndoBannerTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setTextFormat(Qt.TextFormat.PlainText)
        self.detail_label = QLabel(self)
        self.detail_label.setObjectName("UndoBannerDetail")
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setWordWrap(True)
        self.detail_label.setTextFormat(Qt.TextFormat.PlainText)
        self.hint_label = QLabel(self)
        self.hint_label.setObjectName("UndoBannerHint")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setWordWrap(True)
        self.hint_label.setTextFormat(Qt.TextFormat.PlainText)

        layout.addWidget(self.title_label)
        layout.addWidget(self.detail_label)
        layout.addWidget(self.hint_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

        self.setStyleSheet(
            "#UndoBanner {"
            "  background-color: palette(base);"
            "  border: 3px solid palette(highlight);"
            "  border-radius: 14px;"
            "}"
            "#UndoBannerTitle {"
            "  color: palette(text);"
            "  font-size: 26px;"
            "  font-weight: bold;"
            "}"
            "#UndoBannerDetail {"
            "  color: palette(text);"
            "  font-size: 16px;"
            "}"
            "#UndoBannerHint {"
            "  color: palette(text);"
            "  font-size: 15px;"
            "  font-weight: bold;"
            "}")

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

        parent.installEventFilter(self)
        self.relocate()

    # ------------------------------------------------------------------
    def show_message(self, title: str, detail: str, hint: str):
        self.title_label.setText(title)
        self.detail_label.setText(detail)
        self.detail_label.setVisible(bool(detail))
        self.hint_label.setText(hint)
        self.hint_label.setVisible(bool(hint))
        self._resize_to_parent()
        self.show()
        self.raise_()
        self._timer.start(_VISIBLE_MS)

    def _resize_to_parent(self):
        parent = self.parentWidget()
        if parent is None:
            return
        available = max(parent.width() - 48, 240)
        self.setMaximumWidth(available)
        self.adjustSize()
        # long details get a wide box, short messages a compact one
        width = max(min(self.sizeHint().width(), available),
                    min(460, available))
        self.setFixedWidth(width)
        self.adjustSize()
        self.relocate()

    def relocate(self):
        parent = self.parentWidget()
        if parent is None:
            return
        x = max((parent.width() - self.width()) // 2, 0)
        self.move(x, 16)

    def eventFilter(self, obj, event):
        if obj is self.parentWidget() and event.type() == QEvent.Type.Resize:
            self.relocate()
        return False
