# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Overridden QFileSystemModel that circumvents a bug in the base class which
causes the flags() method to never return Qt.ItemIsEditable, so rename/edit
operations always fail."""

from PyQt6.QtCore import (QFileInfo, QMimeData, QModelIndex,
                          QUrl, Qt, QDir, pyqtSignal)
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QMessageBox


class FileSystemModel(QFileSystemModel):
    droppedAFile = pyqtSignal()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction,
                     row: int, column: int, parent: QModelIndex) -> bool:
        from PyQt6.QtCore import QSettings

        # is drop into "empty space"
        is_root_folder = self.index(QSettings().value("root_path").toString()) == parent

        # row == -1 && column == -1 dropped directly on item or on "empty space"
        if (row == -1 and column == -1) and not is_root_folder:
            files = [u.toLocalFile() for u in data.urls() if u.toLocalFile()]
            if not files:  # no local files
                return False

            if self.index(QFileInfo(files[0]).absolutePath()) == parent:
                return False  # dropped in the same folder they are in

            root_path = QSettings().value("root_path").toString()
            dirs = QDir(root_path).entryInfoList([QDir.Filter.Dirs,
                                                  QDir.Filter.NoDotAndDotDot],
                                                 QDir.SortFlag.Name)
            # search for the right dir
            parent_path = ""
            for file in dirs:
                if self.index(file.absoluteFilePath()) == parent:
                    parent_path = file.absoluteFilePath()

            first_info = QFileInfo(files[0])
            # check if the parent directory of the dragged file is one of the
            # notebook directories
            if first_info.absolutePath() in [d.absoluteFilePath() for d in dirs]:
                action = Qt.DropAction.MoveAction

            # remove all file titles that don't exist in the target folder,
            # because they will be successfully dropped
            remaining = []
            for file in files:
                path = (parent_path + QDir.separator()
                        + QFileInfo(file).fileName())
                if QFileInfo(path).exists():
                    remaining.append(file)

            dropped = super().dropMimeData(data, action, row, column, parent)

            if not dropped:
                if remaining:
                    existing_files = "\n".join(remaining) + "\n"
                    title = "Files could not be dropped"
                    text = ("The files could not be dropped because files of the "
                            "same names are already existing in this notebook:\n\n"
                            + QDir.toNativeSeparators(existing_files))
                    if len(remaining) == 1:
                        title = "File could not be dropped"
                        text = ("The file could not be dropped because a file with "
                                "the same name already exists in this notebook:\n\n"
                                + QDir.toNativeSeparators(existing_files))
                    QMessageBox.warning(None, title, text)
                return False
            else:
                self.droppedAFile.emit()
                return True  # files successfully dropped