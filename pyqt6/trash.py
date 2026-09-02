# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A Trash window where trashed notes can be inspected and restored.
Created by the Backup class."""

from pathlib import Path

from PyQt6.QtCore import Qt, QSettings, QFileInfo  # noqa: F401
from PyQt6.QtWidgets import QDialog, QMessageBox, QTreeWidgetItem

from .ui.ui_trash import Ui_Trash


class Trash(QDialog, Ui_Trash):
    def __init__(self, backup_data_hash, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        for key, values in backup_data_hash.items():
            item = QTreeWidgetItem(self.treeWidget)
            item.setText(0, values[0])  # title
            # title, path and content
            item.setData(0, Qt.ItemDataRole.UserRole, list(values))

        self.treeWidget.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        self.treeWidget.itemSelectionChanged.connect(self.show_preview)
        self.deleteButton.clicked.connect(self.delete_backup)
        self.restoreButton.clicked.connect(self.restore_backup)

    def restore_backup(self):
        if not self.treeWidget.selectedItems():
            return

        root_path = str(QSettings().value("root_path", ""))
        directory = root_path + "/restored notes"
        if not Path(directory).exists():
            Path(directory).mkdir(parents=True, exist_ok=True)

        for item in self.treeWidget.selectedItems():
            data_list = list(item.data(0, Qt.ItemDataRole.UserRole))
            title = data_list.pop(0)
            backup_file = data_list[0]
            if not Path(backup_file).exists():
                return
            file_path = directory + "/" + title
            i = 0
            while Path(file_path).exists():
                i += 1
                file_path = "%s(%d)" % (directory + "/" + title + " (", i) + ")"
            try:
                import shutil
                shutil.copyfile(backup_file, file_path)
            except OSError:
                pass
            del item  # remove from the tree

    def delete_backup(self):
        if not self.treeWidget.selectedItems():
            return

        files = []
        item_list = list(self.treeWidget.selectedItems())
        for item in item_list:
            data_list = list(item.data(0, Qt.ItemDataRole.UserRole))
            data_list.pop(0)  # removing title from the list
            files.append(data_list[0])

        answer = QMessageBox.warning(
            self, "Deleting notes",
            "Are you sure you want to permanently delete the selected notes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Abort)
        if answer != QMessageBox.StandardButton.Yes:
            return

        backup_dir = str(QSettings().value("backup_dir_path", ""))
        for file in files:
            if Path(file).exists():
                Path(file).unlink(missing_ok=True)
            uuid_str = file.replace(backup_dir + "/", "")
            QSettings().remove("Notes/" + uuid_str + "_size")
            QSettings().remove("Notes/" + uuid_str + "_cursor_position")
            QSettings().remove("Notes/" + uuid_str + "_window_position")

        for item in item_list:
            del item

    def show_preview(self):
        if self.treeWidget.currentItem() is None:  # prevents program crash
            self.textEdit.clear()
            return

        if not self.treeWidget.currentItem().isSelected():
            if self.treeWidget.selectedItems().count() != 1:
                self.textEdit.clear()
            else:
                data = list(self.treeWidget.selectedItems()[0].data(
                    0, Qt.ItemDataRole.UserRole))
                self.textEdit.setText(data[-1])
        else:
            data = list(self.treeWidget.currentItem().data(
                0, Qt.ItemDataRole.UserRole))
            self.textEdit.setText(data[-1])