# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""The Preferences dialog."""

from PyQt6.QtCore import QDir, QFileInfo, QSettings, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox

from .note import Note
from .ui.ui_preferences import Ui_Preferences


class Preferences(QDialog, Ui_Preferences):
    pathChanged = pyqtSignal()
    kineticScrollingEnabledChanged = pyqtSignal(bool)
    recentCountChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.retranslateUi(self)

        self.settings = QSettings(self)
        self.root_path = ""
        self.original_root_path = ""

        for size in QFontDatabase.standardSizes():
            self.fontSizeComboBox.addItem(str(size))

        self.openNotesFromTray.setChecked(
            bool(self.settings.value("open_notes_from_tray", False)))
        self.dontQuit.setChecked(
            bool(self.settings.value("dont_quit_on_close", False)))
        self.showSource.setChecked(
            bool(self.settings.value("show_source", False)))
        self.kineticScrolling.setChecked(
            bool(self.settings.value("kinetic_scrolling", False)))
        self.silentStart.setChecked(
            bool(self.settings.value("Hide_main_at_startup", False)))
        size = Note.editor_size()
        self.sizeSpinHeight.setValue(size.height())
        self.sizeSpinWidth.setValue(size.width())

        self.buttonBox.accepted.connect(self.save_settings)
        self.browseButton.clicked.connect(self.set_new_paths)
        self.kineticScrolling.toggled.connect(self.kineticScrollingEnabledChanged)
        self.fontSizeComboBox.currentTextChanged.connect(self.set_font_size)

    def set_font_size(self, size: str):
        font = QFont()
        try:
            point_size = float(size)
        except ValueError:
            return
        font.setPointSizeF(point_size)
        font.setFamily(self.fontComboBox.currentFont().family())
        self.fontComboBox.setFont(font)

    def showEvent(self, event):
        self.rootPathLabel.setText(QDir.toNativeSeparators(
            str(self.settings.value("root_path", ""))))
        self.backupPathLabel.setText(QDir.toNativeSeparators(
            str(self.settings.value("backup_dir_path", ""))))
        self.root_path = str(self.settings.value("root_path", ""))
        self.original_root_path = self.root_path

        font = QFont()
        font.setFamily(str(self.settings.value("note_editor_font", "DejaVu Sans")))
        font.setPointSize(int(self.settings.value("note_editor_font_size", 10)))
        self.fontComboBox.setFont(font)
        self.fontSizeComboBox.setCurrentIndex(
            self.fontSizeComboBox.findText(
                str(int(self.settings.value("note_editor_font_size", 10)))))
        self.recentSpin.setValue(int(self.settings.value("Number_of_recent_Notes", 5)))
        super().showEvent(event)

    def save_settings(self):
        if not self.settings.isWritable():
            QMessageBox.warning(self, self.tr("Warning"),
                                self.tr("Could not write settings!"))

        if self.root_path != self.original_root_path:
            answer = QMessageBox.question(
                self, self.tr("Keep old trash folder?"),
                self.tr("Do you want to keep the old trash folder associated "
                        "with the path %1? (You will be able to see the old "
                        "files in the trash again if you change back to the "
                        "previous directory.)")
                .replace("%1", QDir.toNativeSeparators(
                    str(self.settings.value("backup_dir_path", "")))),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer == QMessageBox.StandardButton.No:
                backup_dir = str(self.settings.value("backup_dir_path", ""))
                if backup_dir:
                    from pathlib import Path
                    try:
                        for backup in Path(backup_dir).glob("*"):
                            if backup.is_file():
                                backup.unlink(missing_ok=True)
                        Path(backup_dir).rmdir()
                    except OSError:
                        QMessageBox.warning(
                            self, self.tr("Couldn't delete trash folder"),
                            self.tr("Could not delete the trash folder!"))
            self.settings.setValue("root_path", self.root_path)
            self.pathChanged.emit()

        self.settings.setValue("dont_quit_on_close", self.dontQuit.isChecked())
        self.settings.setValue("open_notes_from_tray",
                               self.openNotesFromTray.isChecked())
        self.settings.setValue("note_editor_default_size",
                               QSize(self.sizeSpinWidth.value(),
                                     self.sizeSpinHeight.value()))
        self.settings.setValue("show_source", self.showSource.isChecked())
        self.settings.setValue("Hide_main_at_startup", self.silentStart.isChecked())
        self.settings.setValue("kinetic_scrolling",
                               self.kineticScrolling.isChecked())
        self.settings.setValue("note_editor_font",
                               self.fontComboBox.currentFont().family())
        self.settings.setValue("note_editor_font_size",
                               self.fontComboBox.font().pointSize())
        self.settings.setValue("Number_of_recent_Notes",
                               self.recentSpin.value())

        self.recentCountChanged.emit()
        self.accept()

    def open_dir(self) -> str:
        path = QFileDialog.getExistingDirectory(
            self, self.tr("Open Directory"), self.root_path,
            QFileDialog.Option.ShowDirsOnly
            | QFileDialog.Option.DontResolveSymlinks)
        info = QFileInfo(path)
        if not info.isWritable() and path:
            QMessageBox.warning(self, self.tr("No Write Access"),
                                self.tr('The path "%1" is not writable!')
                                .replace("%1", QDir.toNativeSeparators(info.filePath())))
            return ""
        return path

    def set_new_paths(self):
        new_path = self.open_dir()
        if new_path:
            self.root_path = new_path
            self.rootPathLabel.setText(self.root_path)
            self.backupPathLabel.setText(
                self.tr("(Will be updated after pressing OK.)"))