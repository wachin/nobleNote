# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Resource helper: loads the svg icons used by nobleNote.

In the C++ version the icons are compiled into the binary via nobleNote.qrc.
In this Python port we ship the very same svg files as package data
(see the icons/ directory next to this module).

Most of the icons are drawn with dark grey strokes (#535353, #000000), which
makes them invisible on a dark color scheme.  Those monochrome icons are
re-rendered with the palette's text color, keeping the original grey levels as
opacity.  Colored icons (the logo, the eraser, the folder glyphs, ...) are
returned untouched, and nothing changes on light color schemes.
"""

import re
from pathlib import Path

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QImage, QPainter, QPalette, QPixmap
from PyQt6.QtWidgets import QApplication

try:  # PyQt6.QtSvg is a separate module (python3-pyqt6.qtsvg on Debian)
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:  # pragma: no cover - fall back to the plain svg icon
    QSvgRenderer = None

ICON_DIR = Path(__file__).resolve().parent / "icons"

# aliases as defined in nobleNote.qrc
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
    return str(ICON_DIR / _ALIASES.get(name, name))


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
        rendered = QImage(size, size, QImage.Format.Format_ARGB32)
        rendered.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rendered)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()

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


def icon(name: str) -> QIcon:
    """Return the QIcon for the given resource alias."""
    path = ICON_DIR / _ALIASES.get(name, name)
    if path.exists():
        qicon = QIcon(str(path))
        return _adapt_to_palette(path, qicon)
    # fall back to the theme icon when the svg is not present
    return QIcon.fromTheme(name)
