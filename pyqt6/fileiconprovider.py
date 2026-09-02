# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Icon provider for the note and folder lists."""

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtCore import QFileInfo

from .resources import icon


class FileIconProvider(QFileIconProvider):
    def __init__(self):
        super().__init__()
        self.cut_files = []

    def icon(self, info: QFileInfo) -> QIcon:
        if info.isDir():
            return icon("folder")
        if info.isFile():
            if info.absoluteFilePath() in self.cut_files:
                return icon("cut_file")
            return icon("file")
        return super().icon(info)

    def set_cut_files(self, files):
        self.cut_files = list(files)