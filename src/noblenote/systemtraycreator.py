# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Builds the "open notes from the tray icon" menu."""

from PyQt6.QtCore import QDir, QFileInfo, QObject, QSettings, pyqtSignal
from PyQt6.QtWidgets import QMenu


class SystemTrayCreator(QObject):
    noteClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def populate_menu(self, menu: QMenu):
        menu.clear()

        root_path = str(QSettings().value("root_path", ""))
        dirs = QDir(root_path).entryInfoList(
            QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot
            | QDir.Filter.NoSymLinks,
            QDir.SortFlag.Name | QDir.SortFlag.IgnoreCase)

        for notebook in dirs:
            notebook_menu = menu.addMenu(QDir(notebook.filePath()).dirName())
            entries = QDir(notebook.filePath()).entryInfoList(
                QDir.Filter.Files,
                QDir.SortFlag.Name | QDir.SortFlag.IgnoreCase)
            for note_info in entries:
                action = notebook_menu.addAction(note_info.fileName())
                action.triggered.connect(
                    lambda checked=False, path=note_info.filePath():
                        self.noteClicked.emit(path))