# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Resource helper: loads the svg icons used by nobleNote.

In the C++ version the icons are compiled into the binary via nobleNote.qrc.
In this Python port we ship the very same svg files as package data
(see the icons/ directory next to this module).
"""

from pathlib import Path

from PyQt6.QtGui import QIcon

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


def icon_path(name: str) -> str:
    """Return the absolute path of the icon with the given alias (or name)."""
    return str(ICON_DIR / _ALIASES.get(name, name))


def icon(name: str) -> QIcon:
    """Return the QIcon for the given resource alias."""
    path = ICON_DIR / _ALIASES.get(name, name)
    if path.exists():
        return QIcon(str(path))
    # fall back to the theme icon when the svg is not present
    return QIcon.fromTheme(name)