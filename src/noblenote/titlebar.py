# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A frameless window title bar that also hosts the formatting toolbar.

The native title bar is dropped so that the text formatting actions can live
in the same row as the note title, keeping everything as compact as possible.
"""

from PyQt6.QtCore import QEvent, QObject, QSize, Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QStyle,
                             QToolButton, QWidget)

from .resources import icon, palette_watcher

TITLE_BAR_HEIGHT = 28
_GRIP_SIZE = 5

# (edges, cursor) for the eight invisible grips around the window border
_GRIPS = (
    (Qt.Edge.TopEdge | Qt.Edge.LeftEdge, Qt.CursorShape.SizeFDiagCursor),
    (Qt.Edge.TopEdge, Qt.CursorShape.SizeVerCursor),
    (Qt.Edge.TopEdge | Qt.Edge.RightEdge, Qt.CursorShape.SizeBDiagCursor),
    (Qt.Edge.LeftEdge, Qt.CursorShape.SizeHorCursor),
    (Qt.Edge.RightEdge, Qt.CursorShape.SizeHorCursor),
    (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge, Qt.CursorShape.SizeBDiagCursor),
    (Qt.Edge.BottomEdge, Qt.CursorShape.SizeVerCursor),
    (Qt.Edge.BottomEdge | Qt.Edge.RightEdge, Qt.CursorShape.SizeFDiagCursor),
)


class _ResizeGrip(QWidget):
    """An invisible strip on the window border that starts a system resize."""

    def __init__(self, window: QWidget, edges, cursor):
        super().__init__(window)
        self.edges_ = edges
        self.setCursor(cursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemResize(self.edges_)
                event.accept()
                return
        super().mousePressEvent(event)


class WindowResizeGrips(QObject):
    """Keeps the resize grips of a frameless window in place."""

    def __init__(self, window: QWidget):
        super().__init__(window)
        self.window_ = window
        self.grips_ = [_ResizeGrip(window, edges, cursor)
                       for edges, cursor in _GRIPS]
        window.installEventFilter(self)
        self.reposition()

    def eventFilter(self, obj, event):
        if obj is self.window_ and event.type() in (QEvent.Type.Resize,
                                                    QEvent.Type.Show,
                                                    QEvent.Type.WindowStateChange):
            self.reposition()
        return False

    def reposition(self):
        width = self.window_.width()
        height = self.window_.height()
        size = _GRIP_SIZE
        rects = (
            (0, 0, size, size),
            (size, 0, width - 2 * size, size),
            (width - size, 0, size, size),
            (0, size, size, height - 2 * size),
            (width - size, size, size, height - 2 * size),
            (0, height - size, size, size),
            (size, height - size, width - 2 * size, size),
            (width - size, height - size, size, size),
        )
        visible = not (self.window_.isMaximized()
                       or self.window_.isFullScreen())
        for grip, (x, y, w, h) in zip(self.grips_, rects):
            grip.setGeometry(x, y, max(w, 0), max(h, 0))
            grip.setVisible(visible)
            if visible:
                grip.raise_()


class NoteTitleBar(QWidget):
    """Custom title bar: app icon, note title, formatting toolbar, buttons."""

    def __init__(self, window: QWidget, toolbar: QWidget, parent=None):
        super().__init__(parent)
        self.window_ = window
        self.setObjectName("TitleBar")
        self.setFixedHeight(TITLE_BAR_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Preferred,
                           QSizePolicy.Policy.Fixed)
        self._title = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(2)

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(QSize(16, 16))
        layout.addWidget(self.icon_label)

        self.title_label = QLabel(self)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored,
                                       QSizePolicy.Policy.Preferred)
        self.title_label.setMinimumWidth(1)
        layout.addWidget(self.title_label, 1)

        # the formatting toolbar lives inside the title bar
        self.toolbar = toolbar
        self.toolbar.setSizePolicy(QSizePolicy.Policy.Maximum,
                                   QSizePolicy.Policy.Fixed)
        layout.addWidget(self.toolbar)

        self.minimize_button = self._window_button(
            QStyle.StandardPixmap.SP_TitleBarMinButton,
            window.showMinimized, self.tr("Minimize"))
        self.maximize_button = self._window_button(
            QStyle.StandardPixmap.SP_TitleBarMaxButton,
            self.toggle_maximized, self.tr("Maximize"))
        self.close_button = self._window_button(
            QStyle.StandardPixmap.SP_TitleBarCloseButton,
            window.close, self.tr("Close"))
        for button in (self.minimize_button, self.maximize_button,
                       self.close_button):
            layout.addWidget(button)

        window.installEventFilter(self)
        self.refresh()

        watcher = palette_watcher()
        if watcher is not None:
            watcher.paletteChanged.connect(self.refresh)

    # ------------------------------------------------------------------
    def _window_button(self, standard_pixmap, slot, tooltip) -> QToolButton:
        button = QToolButton(self)
        button.setAutoRaise(True)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setToolTip(tooltip)
        button.setIconSize(QSize(16, 16))
        button.setFixedSize(QSize(24, TITLE_BAR_HEIGHT - 4))
        button.setProperty("standardPixmap", int(standard_pixmap))
        button.clicked.connect(slot)
        return button

    def _standard_icon(self, button: QToolButton):
        pixmap = QStyle.StandardPixmap(button.property("standardPixmap"))
        if (pixmap == QStyle.StandardPixmap.SP_TitleBarMaxButton
                and self.window_.isMaximized()):
            pixmap = QStyle.StandardPixmap.SP_TitleBarNormalButton
        return self.style().standardIcon(pixmap)

    def refresh(self):
        """Re-create the icons after the application palette changed."""
        self.icon_label.setPixmap(icon("nobleNote").pixmap(16, 16))
        for button in (self.minimize_button, self.maximize_button,
                       self.close_button):
            button.setIcon(self._standard_icon(button))
        self._update_title()

    # ------------------------------------------------------------------
    def set_title(self, title: str):
        self._title = title or ""
        self._update_title()

    def _update_title(self):
        available = self.title_label.width()
        if available <= 0:
            self.title_label.setText("")
            return
        metrics = QFontMetrics(self.title_label.font())
        self.title_label.setText(metrics.elidedText(
            self._title, Qt.TextElideMode.ElideRight, available))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_title()

    def eventFilter(self, obj, event):
        if obj is self.window_ and event.type() == QEvent.Type.WindowStateChange:
            self.maximize_button.setIcon(self._standard_icon(self.maximize_button))
        return False

    # ------------------------------------------------------------------
    def toggle_maximized(self):
        if self.window_.isMaximized():
            self.window_.showNormal()
        else:
            self.window_.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window_.windowHandle()
            if handle is not None:
                handle.startSystemMove()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximized()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
