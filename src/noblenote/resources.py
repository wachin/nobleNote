# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Resource helper: loads the svg icons used by nobleNote.

In the C++ version the icons were compiled into the binary through a Qt
resource file.
In this Python port we ship the very same svg files as package data
(see the icons/ directory next to this module).

Most of the icons are drawn with dark grey strokes (#535353, #000000), which
makes them invisible on a dark color scheme.  Those monochrome icons are
re-rendered with the palette's text color, keeping the original grey levels as
opacity.  Colored icons (the logo, the eraser, the folder glyphs, ...) are
returned untouched, and nothing changes on light color schemes.

A few icons have a redrawn version for dark color schemes (flat light glyphs).
They live in the dark/ subdirectory under the same file name; on a dark scheme
they take precedence and their flat color is replaced with the palette text
color, so they keep following the color scheme (and qt6ct) as well.
"""

import re
from pathlib import Path

from PyQt6.QtCore import (
    QByteArray, QEvent, QObject, QRectF, Qt, QTimer, pyqtSignal,
)
from PyQt6.QtGui import QColor, QIcon, QImage, QPainter, QPalette, QPixmap
from PyQt6.QtWidgets import QApplication

try:  # PyQt6.QtSvg is a separate module (python3-pyqt6.qtsvg on Debian)
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:  # pragma: no cover - fall back to the plain svg icon
    QSvgRenderer = None

ICON_DIR = Path(__file__).resolve().parent / "icons"

# Icons redrawn for dark color schemes, picked by file name when one exists.
DARK_ICON_DIR = ICON_DIR / "dark"

# aliases used by the original Qt resource file
_ALIASES = {
    "nobleNote": "noblenote.svg",
    "closeB": "fileclose.svg",
    "hyperlink": "emblem-web.svg",
    "newFolder": "foldernew.svg",
    "newNote": "filenew.svg",
    "deleteFolder": "folderremove.svg",
    "deleteNote": "fileremove.svg",
    "renameFolder": "folderrename.svg",
    "renameNote": "filerename.svg",
    "file": "file.svg",
    "cut_file": "cut_file.svg",
    "folder": "folder.svg",
    "bulletpoints": "bulletpoints.svg",
    "trash": "trash.svg",
    "preferences": "preferences.svg",
    "bold": "format-text-bold.svg",
    "italic": "format-text-italic.svg",
    "strikedout": "format-text-strikethrough.svg",
    "underlined": "format-text-underline.svg",
    "clearFormatting": "clear_formatting.svg",
}

_ICON_SIZES = (16, 22, 24, 32, 48)
_HEX_COLOR = re.compile(r"#([0-9a-fA-F]{6})\b")

# key: (path, foreground color) -> QIcon
_icon_cache = {}


def icon_path(name: str) -> str:
    """Return the absolute path of the icon with the given alias (or name)."""
    return str(_variant_path(name))


def _hex_luminance(hex_color: str) -> float:
    """Perceived brightness of a #rrggbb color, in the 0..1 range."""
    value = hex_color.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return 0.299 * r + 0.587 * g + 0.114 * b


def _is_monochrome(svg: str) -> bool:
    """True when every color of the svg is a grey (no hue, no saturation)."""
    for hex_color in _HEX_COLOR.findall(svg):
        red, green, blue = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        if max(red, green, blue) - min(red, green, blue) > 24:
            return False
    return True


def _text_color() -> QColor:
    """Text color of the current palette, or an invalid color if unavailable."""
    app = QApplication.instance()
    if app is None:
        return QColor()
    return app.palette().color(QPalette.ColorRole.WindowText)


def _is_dark_scheme() -> bool:
    """True when the application uses a dark color scheme (light text)."""
    color = _text_color()
    return color.isValid() and _hex_luminance(color.name()) >= 0.5


def _variant_path(name: str) -> Path:
    """The svg of this alias for the current color scheme.

    On a dark scheme a redrawn icon in dark/ wins over the default one; icons
    that only exist in one version are shared by both schemes.
    """
    filename = _ALIASES.get(name, name)
    if _is_dark_scheme():
        redrawn = DARK_ICON_DIR / filename
        if redrawn.exists():
            return redrawn
    return ICON_DIR / filename


def _render(renderer, size: int) -> QImage:
    """Render the svg at the given size on a transparent image."""
    rendered = QImage(size, size, QImage.Format.Format_ARGB32)
    rendered.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rendered)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return rendered


def _render_svg(svg: str):
    """A multi size QIcon for the given svg markup, or None if unusable."""
    if QSvgRenderer is None:
        return None
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    if not renderer.isValid():
        return None
    qicon = QIcon()
    for size in _ICON_SIZES:
        qicon.addPixmap(QPixmap.fromImage(_render(renderer, size)))
    return qicon


def _retint_redrawn(path: Path, color: QColor):
    """Paint a flat redrawn dark glyph in the palette text color.

    The redrawn icons are light glyphs (#e6e6e6); the grey to opacity mapping
    above would turn them into ghosts, so their flat color is replaced instead.
    """
    try:
        svg = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not _is_monochrome(svg):
        return None
    return _render_svg(_HEX_COLOR.sub(color.name(), svg))

def _adapt_to_palette(path: Path, qicon: QIcon) -> QIcon:
    """Re-render a monochrome dark svg with the palette text color."""
    color = _text_color()
    if not color.isValid() or _hex_luminance(color.name()) < 0.5:
        return qicon  # light color scheme: the original dark icons are fine
    if QSvgRenderer is None:
        return qicon
    try:
        svg = path.read_text(encoding="utf-8")
    except OSError:
        return qicon
    if not _is_monochrome(svg):
        return qicon

    key = (str(path), color.name())
    if key in _icon_cache:
        return _icon_cache[key]

    renderer = QSvgRenderer(str(path))
    if not renderer.isValid():
        return qicon

    adapted = QIcon()
    for size in _ICON_SIZES:
        rendered = _render(renderer, size)

        # the grey level of every pixel becomes its opacity in the text color
        tinted = QImage(size, size, QImage.Format.Format_ARGB32)
        tinted.fill(Qt.GlobalColor.transparent)
        for y in range(size):
            for x in range(size):
                pixel = rendered.pixelColor(x, y)
                if pixel.alpha() == 0:
                    continue
                luminance = (0.299 * pixel.red() + 0.587 * pixel.green()
                             + 0.114 * pixel.blue()) / 255.0
                alpha = round(pixel.alpha() * (1.0 - luminance))
                if alpha:
                    tinted.setPixelColor(x, y, QColor(color.red(), color.green(),
                                                      color.blue(), alpha))
        adapted.addPixmap(QPixmap.fromImage(tinted))

    _icon_cache[key] = adapted
    return adapted


def clear_icon_cache():
    """Drop the recolored icons (the color scheme changed)."""
    _icon_cache.clear()


class _PaletteWatcher(QObject):
    """Emits paletteChanged after the application color scheme changed.

    PyQt6/Qt6 has no QApplication.paletteChanged signal, so the change is
    taken from the application palette change events, which is what a theme
    switch (qt6ct, the desktop color scheme, ...) delivers to the widgets.
    """

    paletteChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._text_color = _text_color().name()
        self._pending = False

    def eventFilter(self, obj, event) -> bool:
        if event.type() in (QEvent.Type.ApplicationPaletteChange,
                            QEvent.Type.PaletteChange):
            # a theme switch sends many events, look at the palette once
            if not self._pending:
                self._pending = True
                QTimer.singleShot(0, self._check)
        return False

    def _check(self):
        self._pending = False
        color = _text_color().name()
        if not _text_color().isValid() or color == self._text_color:
            return
        self._text_color = color
        clear_icon_cache()
        self.paletteChanged.emit()


_watcher = None


def palette_watcher():
    """The object whose paletteChanged signal fires on a color scheme change.

    Install the application event filter on first use.  Returns None when
    there is no QApplication yet (icons then cannot be recolored anyway).
    """
    global _watcher
    app = QApplication.instance()
    if app is None:
        return None
    if _watcher is None:
        _watcher = _PaletteWatcher()
        app.installEventFilter(_watcher)
    return _watcher


def icon(name: str) -> QIcon:
    """Return the QIcon for the given resource alias."""
    path = _variant_path(name)
    if not path.exists():
        # fall back to the theme icon when the svg is not present
        return QIcon.fromTheme(name)
    if path.parent == DARK_ICON_DIR:
        color = _text_color()
        key = (str(path), color.name())
        if key not in _icon_cache:
            _icon_cache[key] = (_retint_redrawn(path, color)
                                or _adapt_to_palette(path, QIcon(str(path))))
        return _icon_cache[key]
    return _adapt_to_palette(path, QIcon(str(path)))
