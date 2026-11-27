# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""The window that lists the persistent history of a note.

Every recorded change can be read, copied and inserted back into the note, and
the note can be restored to the closest saved point in the past.
"""

from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox,
                             QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                             QPlainTextEdit, QPushButton, QTableView,
                             QVBoxLayout)

from .undohistory import (ENTRY_DELETE, ENTRY_INSERT, ENTRY_OPEN,
                          ENTRY_REDO, ENTRY_RELOAD, ENTRY_REPLACE,
                          ENTRY_RESTORE, ENTRY_UNDO, HistoryEntry, UndoHistory,
                          one_line)


def entry_text(entry: HistoryEntry) -> str:
    """The most interesting text of a change (what was removed, else added)."""
    return entry.removed or entry.added


class _HistoryModel(QAbstractTableModel):
    def __init__(self, window: "HistoryWindow"):
        super().__init__(window)
        self._window = window
        self.entries: list[HistoryEntry] = []

    def set_entries(self, entries: list[HistoryEntry]):
        self.beginResetModel()
        self.entries = entries
        self.endResetModel()

    def entry_at(self, row: int) -> HistoryEntry | None:
        if 0 <= row < len(self.entries):
            return self.entries[row]
        return None

    # ------------------------------------------------------------------
    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.entries)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else 3

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return (self._window.tr("Date and time"),
                    self._window.tr("Action"),
                    self._window.tr("Text"))[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        entry = self.entry_at(index.row())
        if entry is None:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if index.column() == 1:
                return self._window.kind_label(entry.kind)
            return one_line(entry_text(entry))
        if role == Qt.ItemDataRole.ToolTipRole:
            lines = [entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                     self._window.kind_label(entry.kind)]
            if entry.removed:
                lines += ["", self._window.tr("Removed text:"), entry.removed]
            if entry.added:
                lines += ["", self._window.tr("Added text:"), entry.added]
            return "\n".join(lines)
        return None


class HistoryWindow(QDialog):
    """Lists the history of one note and recovers text from it."""

    insertRequested = pyqtSignal(str)
    restoreRequested = pyqtSignal(str)

    def __init__(self, history: UndoHistory, note_title: str, parent=None):
        super().__init__(parent)
        self.history_ = history
        self.note_title_ = note_title
        self.setWindowTitle(self.tr("Change history") + " — " + note_title)
        self.resize(900, 620)
        self.setModal(False)

        self._all_entries: list[HistoryEntry] = []

        layout = QVBoxLayout(self)

        explanation = QLabel(self.tr(
            "Every change of this note is kept here, also after closing "
            "nobleNote. Select a change to read, copy or insert the deleted "
            "text, or to restore the note to a saved point."), self)
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText(
            self.tr("Search in the deleted or written text"))
        self.search_edit.setClearButtonEnabled(True)
        layout.addWidget(self.search_edit)

        self.model = _HistoryModel(self)
        self.table = QTableView(self)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 170)
        self.table.setColumnWidth(1, 150)
        layout.addWidget(self.table, 1)

        self.detail = QPlainTextEdit(self)
        self.detail.setReadOnly(True)
        self.detail.setMinimumHeight(130)
        layout.addWidget(self.detail)

        buttons = QHBoxLayout()
        self.copy_button = QPushButton(self.tr("Copy deleted text"), self)
        self.insert_button = QPushButton(
            self.tr("Insert in the note"), self)
        self.restore_button = QPushButton(
            self.tr("Restore the note to this moment"), self)
        self.refresh_button = QPushButton(self.tr("Refresh"), self)
        buttons.addWidget(self.copy_button)
        buttons.addWidget(self.insert_button)
        buttons.addWidget(self.restore_button)
        buttons.addStretch(1)
        buttons.addWidget(self.refresh_button)
        layout.addLayout(buttons)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close, parent=self)
        layout.addWidget(self.button_box)

        self.search_edit.textChanged.connect(self._fill_table)
        self.table.selectionModel().selectionChanged.connect(
            self._selection_changed)
        self.copy_button.clicked.connect(self._copy_text)
        self.insert_button.clicked.connect(self._insert_text)
        self.restore_button.clicked.connect(self._restore_note)
        self.refresh_button.clicked.connect(self.refresh)
        self.button_box.rejected.connect(self.close)

        self._selection_changed()
        self.refresh()

    # ------------------------------------------------------------------
    def kind_label(self, kind: str) -> str:
        labels = {
            ENTRY_OPEN: self.tr("Note opened"),
            ENTRY_RELOAD: self.tr("Note reloaded"),
            ENTRY_INSERT: self.tr("Text typed"),
            ENTRY_DELETE: self.tr("Text deleted"),
            ENTRY_REPLACE: self.tr("Text replaced"),
            ENTRY_UNDO: self.tr("Undo"),
            ENTRY_REDO: self.tr("Redo"),
            ENTRY_RESTORE: self.tr("Note restored"),
        }
        return labels.get(kind, kind)

    def refresh(self):
        self.setWindowTitle(self.tr("Change history") + " — "
                            + self.note_title_)
        self._all_entries = self.history_.entries()
        self._fill_table()

    def _fill_table(self):
        needle = self.search_edit.text().strip().casefold()
        if needle:
            entries = [
                entry for entry in self._all_entries
                if needle in entry.removed.casefold()
                or needle in entry.added.casefold()
                or needle in self.kind_label(entry.kind).casefold()
                or needle in entry.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S").casefold()]
        else:
            entries = list(self._all_entries)
        self.model.set_entries(entries)
        if entries:
            self.table.selectRow(0)
        else:
            self.detail.clear()
            self._selection_changed()

    def _selected_entry(self) -> HistoryEntry | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.entry_at(indexes[0].row())

    def _selection_changed(self, *args):
        entry = self._selected_entry()
        if entry is None:
            self.detail.clear()
            self.copy_button.setEnabled(False)
            self.insert_button.setEnabled(False)
            self.restore_button.setEnabled(False)
            return
        lines = [
            self.tr("Action: ") + self.kind_label(entry.kind),
            self.tr("Date and time: ") + entry.timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"),
        ]
        if entry.removed:
            lines += ["", self.tr("Removed text:"), entry.removed]
        if entry.added:
            lines += ["", self.tr("Added text:"), entry.added]
        if not entry.removed and not entry.added:
            lines += ["", self.tr("This entry has no text of its own.")]
        self.detail.setPlainText("\n".join(lines))
        self.copy_button.setEnabled(bool(entry.removed))
        self.insert_button.setEnabled(bool(entry_text(entry)))
        self.restore_button.setEnabled(True)

    # ------------------------------------------------------------------
    def _copy_text(self):
        entry = self._selected_entry()
        if entry is None:
            return
        text = entry.removed or entry.added
        if text:
            QGuiApplication.clipboard().setText(text)

    def _insert_text(self):
        entry = self._selected_entry()
        if entry is None:
            return
        text = entry_text(entry)
        if text:
            self.insertRequested.emit(text)

    def _restore_note(self):
        entry = self._selected_entry()
        if entry is None:
            return
        checkpoint = self.history_.checkpoint(entry.id)
        if checkpoint is None:
            QMessageBox.information(
                self, self.tr("Restore the note"),
                self.tr("There is no saved restoration point before this "
                        "change. Open the note and make a change first."))
            return
        html, timestamp = checkpoint
        answer = QMessageBox.question(
            self, self.tr("Restore the note"),
            self.tr("The note will go back to its state at %1. Later changes "
                    "are not deleted from the history: you can read them "
                    "here again. Do you want to continue?")
            .replace("%1", timestamp.strftime("%Y-%m-%d %H:%M:%S")),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.restoreRequested.emit(html)
        self.refresh()
