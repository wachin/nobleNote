# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A model that shows a list of files (the search results for notes)."""

import html as _html
import re as _re
import threading
from pathlib import Path

from PyQt6.QtCore import QFileInfo, QMimeData, QModelIndex, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QApplication, QFileIconProvider

USER_ROLE_PATH = Qt.ItemDataRole.UserRole + 1

_HTML_TAG_REGEX = _re.compile(r"<[^>]*>")
_WHITE_SPACE_PRE_WRAP = "p, li { white-space: pre-wrap; }"


def _file_content_contains(html_file_path: str, content: str) -> bool:
    """True if the file (read as html) contains the given text."""
    try:
        text = Path(html_file_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    index = text.find(_WHITE_SPACE_PRE_WRAP)
    if index != -1:
        text = text[:index] + text[index + len(_WHITE_SPACE_PRE_WRAP):]
    stripped = _HTML_TAG_REGEX.sub("", text)
    needle = _html.escape(content, quote=False)
    return needle.lower() in stripped.lower()


def _file_filter(file_name: str, content: str, html_file_path: str) -> bool:
    """Functor equivalent of FindFileModel::FileContains."""
    if file_name and content:
        return (QFileInfo(html_file_path).baseName().lower().find(file_name.lower()) != -1
                or _file_content_contains(html_file_path, content))
    if content:
        return _file_content_contains(html_file_path, content)
    return QFileInfo(html_file_path).baseName().lower().find(file_name.lower()) != -1


class FindFileModel(QStandardItemModel):
    """Shows a list of files that match a search query."""

    _resultsReady = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._resultsReady.connect(self._find_in_files_finished)
        self._cancel_requested = False
        self._worker = None

    # --- generic helpers -------------------------------------------------
    def fileName(self, index: QModelIndex) -> str:
        item = self.itemFromIndex(index)
        if item is None:
            return ""
        return QFileInfo(item.data(USER_ROLE_PATH)).fileName()

    def filePath(self, index: QModelIndex) -> str:
        item = self.itemFromIndex(index)
        if item is None:
            return ""
        return QFileInfo(item.data(USER_ROLE_PATH)).filePath()

    def size(self, index: QModelIndex) -> int:
        item = self.itemFromIndex(index)
        if item is None:
            return 0
        return QFileInfo(item.data(USER_ROLE_PATH)).size()

    def fileInfo(self, index: QModelIndex) -> QFileInfo:
        item = self.itemFromIndex(index)
        if item is None:
            return QFileInfo()
        return QFileInfo(item.data(USER_ROLE_PATH))

    def appendFile(self, file_path: str):
        info = QFileInfo(file_path)
        if not info.path() or info.path() == ".":
            return
        file_path_trunc = info.dir().dirName() + " / " + info.fileName()
        file_item = QStandardItem(file_path_trunc)
        file_item.setIcon(QFileIconProvider().icon(info))
        file_item.setData(file_path, USER_ROLE_PATH)
        file_item.setEditable(False)
        self.appendRow(file_item)

    def remove(self, index: QModelIndex) -> bool:
        item = self.itemFromIndex(index)
        if item is None:
            return False
        file_path = item.data(USER_ROLE_PATH)
        try:
            Path(file_path).unlink()
            removed = True
        except OSError:
            removed = False
        if removed:
            self.removeRow(index.row(), index.parent())
        return removed
    def findInFiles(self, fileName: str, content: str, path: str, waitCursor: bool):
        """Search recursively.  May be called multiple times while the user
        is typing a search word."""
        if not path or (not fileName and not content):
            return

        self._cancel_requested = True
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=0.1)
        self._cancel_requested = False

        if waitCursor:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        def worker():
            found = []
            try:
                for file_path in Path(path).rglob("*"):
                    if self._cancel_requested:
                        break
                    if file_path.is_file():
                        if _file_filter(fileName, content, str(file_path)):
                            found.append(str(file_path))
            except OSError:
                pass
            self._resultsReady.emit(found)

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _find_in_files_finished(self, results: list):
        self.clear()
        for file_name in results:
            self.appendFile(file_name)
        QApplication.restoreOverrideCursor()

    # --- drag and drop ---------------------------------------------------
    def mimeTypes(self) -> list:
        return ["text/uri-list"]

    def mimeData(self, indexes) -> QMimeData:
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(self.filePath(i)) for i in indexes]
        mime_data.setUrls(urls)
        return mime_data

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """Rename the underlying file (enables QAbstractItemView::edit)."""
        if role != Qt.ItemDataRole.EditRole:
            return False
        try:
            old = Path(self.filePath(index))
            new = old.parent / Path(str(value)).name
            old.rename(new)
            f = True
        except OSError:
            f = False
        if index.isValid():
            new_path = (self.fileInfo(index).path()
                        + "/" + QFileInfo(str(value)).fileName())
            self.setData(index, new_path, USER_ROLE_PATH)
        return f

    # --- search ----------------------------------------------------------
    @staticmethod
    def find0(search_name: str, search_text: str, path: str) -> list:
        """searchName and searchText can be empty strings."""
        result = []
        if not path or (not search_name and not search_text):
            return result
        root = Path(path)
        for file in root.rglob("*"):
            if file.is_file():
                if _file_filter(search_name, search_text, str(file)):
                    result.append(str(file))
        return result