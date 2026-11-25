# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Proxy model for both QFileSystemModel and FindFileModel that allows access
to methods that exist in both classes.  Call setSourceModel with an instance
of one of these models.  Important: always use mapToSource and mapFromSource
for QModelIndexes."""

from PyQt6.QtCore import (QDir, QFileInfo, QModelIndex,
                          QSortFilterProxyModel, QSettings)
from PyQt6.QtGui import QFileSystemModel

from .findfilemodel import FindFileModel
from .htmlnotereader import HtmlNoteReader


class FindFileSystemModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _fsm(self):
        src = self.sourceModel()
        return src if isinstance(src, QFileSystemModel) else None

    def _ffm(self):
        src = self.sourceModel()
        return src if isinstance(src, FindFileModel) else None

    def fileName(self, index: QModelIndex) -> str:
        fsm = self._fsm()
        if fsm is not None:
            return fsm.fileName(self.mapToSource(index))
        ffm = self._ffm()
        if ffm is not None:
            return ffm.fileName(self.mapToSource(index))
        return ""

    def fileNames(self, indices) -> list:
        names = {}
        for idx in indices:
            fsm = self._fsm()
            if fsm is not None:
                names[idx] = fsm.fileName(self.mapToSource(idx))
            else:
                ffm = self._ffm()
                if ffm is not None:
                    names[idx] = ffm.fileName(self.mapToSource(idx))
        return list(names.values())

    def filePath(self, index: QModelIndex) -> str:
        fsm = self._fsm()
        if fsm is not None:
            return fsm.filePath(self.mapToSource(index))
        ffm = self._ffm()
        if ffm is not None:
            return ffm.filePath(self.mapToSource(index))
        return ""

    def allSizeZero(self, indices) -> bool:
        for idx in indices:
            size = 0
            fsm = self._fsm()
            if fsm is not None:
                # QFileInfo wrapper required because QFileSystemModel::size
                # only updates after app restart
                size = QFileInfo(fsm.filePath(self.mapToSource(idx))).size()
            else:
                ffm = self._ffm()
                if ffm is not None:
                    size = ffm.size(self.mapToSource(idx))
            if size > 0:
                return False
        return True

    def rmdir(self, index: QModelIndex) -> bool:
        fsm = self._fsm()
        if fsm is not None:
            return fsm.rmdir(self.mapToSource(index))
        return False

    def mkdir(self, parent: QModelIndex, name: str) -> QModelIndex:
        fsm = self._fsm()
        if fsm is not None:
            return self.mapFromSource(fsm.mkdir(self.mapToSource(parent), name))
        return QModelIndex()

    def remove(self, index: QModelIndex) -> bool:
        fsm = self._fsm()
        if fsm is not None:
            return fsm.remove(self.mapToSource(index))
        ffm = self._ffm()
        if ffm is not None:
            return ffm.remove(self.mapToSource(index))
        return False

    def removeList(self, indexes) -> bool:
        successful = True
        for idx in indexes:
            if not self.remove(idx):
                successful = False
        return successful

    def fileInfo(self, index: QModelIndex) -> QFileInfo:
        fsm = self._fsm()
        if fsm is not None:
            return fsm.fileInfo(self.mapToSource(index))
        ffm = self._ffm()
        if ffm is not None:
            return ffm.fileInfo(self.mapToSource(index))
        return QFileInfo()

    def appendFile(self, file_path: str):
        ffm = self._ffm()
        if ffm is not None:
            ffm.appendFile(file_path)

    def setRootPath(self, new_path: str) -> QModelIndex:
        fsm = self._fsm()
        if fsm is not None:
            return self.mapFromSource(fsm.setRootPath(new_path))
        return QModelIndex()

    def rootPath(self) -> str:
        fsm = self._fsm()
        if fsm is not None:
            return fsm.rootPath()
        return ""

    def clear(self):
        ffm = self._ffm()
        if ffm is not None:
            ffm.clear()

    def findInFiles(self, fileName: str, content: str, path: str, waitCursor: bool):
        ffm = self._ffm()
        if ffm is not None:
            ffm.findInFiles(fileName, content, path, waitCursor)

    def index(self, a, b=None, c=None):
        # If the first argument is a string, treat it as a path-based index
        if isinstance(a, str):
            path = a
            column = b if isinstance(b, int) else 0
            fsm = self._fsm()
            if fsm is not None:
                return self.mapFromSource(fsm.index(path, column))
            return QModelIndex()
        else:
            # Otherwise, treat it as the standard index (row, column, parent)
            return super().index(a, b, c)

    def copyNotesToBackupDir(self, indexes):
        """Read the uuid from each note and copy the note to the backup dir
        with the uuid as its name."""
        import shutil
        backup_dir = str(QSettings().value("backup_dir_path", "") or "")
        for index in indexes:
            file_path = self.filePath(index)
            uuid_ = HtmlNoteReader.uuid(file_path)
            if uuid_ is not None:
                try:
                    shutil.copyfile(file_path, backup_dir + QDir.separator()
                                    + str(uuid_))
                except OSError:
                    pass