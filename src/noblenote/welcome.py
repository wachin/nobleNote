# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""The Welcome dialog shown when the notes root directory is invalid."""

from PyQt6.QtCore import QDir, QSettings
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog

from .lineedit import LineEdit
from .ui.ui_welcome import Ui_Welcome


class Welcome(QDialog, Ui_Welcome):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        app = QApplication.instance()
        self.is_portable = bool(QSettings().value("isPortable", False))
        if self.is_portable:
            default_path = QDir.toNativeSeparators(
                app.applicationDirPath() + "/" + app.applicationName())
        else:
            default_path = QDir.toNativeSeparators(
                QDir.homePath() + "/" + app.applicationName())
        self.default_path = default_path

        self.path = LineEdit(self)
        self.path.setText(default_path)
        self.gridLayout.addWidget(self.path, 3, 0, 1, 1)

        self.browse.clicked.connect(self.open_dir)
        self.accepted.connect(self.set_root_dir)

    def open_dir(self):
        app = QApplication.instance()
        if self.is_portable:
            standard_path = app.applicationDirPath()
        else:
            standard_path = QDir.homePath()
        directory = QFileDialog.getExistingDirectory(
            self, "Choose a directory", standard_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks)
        if directory:
            self.path.setText(directory)
        else:
            self.path.setText(self.default_path)

    def set_root_dir(self):
        if self.path.text() == "":
            QSettings().setValue("root_path", self.default_path)
        else:
            QSettings().setValue("root_path", self.path.text())

    def get_instance(self, root_path_is_set: bool, root_path_exists: bool,
                     root_path_is_writable: bool):
        if self.is_portable:
            if not root_path_is_set:
                self.welcomeText.setText(
                    "Welcome to nobleNote!\nThis is the first time that "
                    "nobleNote has been started.\nThis is the portable edition "
                    "of nobleNote.\nYou are encouraged to use the default path, "
                    "but you can also choose any other directory.")
            elif root_path_is_set and not root_path_exists:
                self.welcomeText.setText(
                    "Welcome to nobleNote!\nThe set path for the notes does not "
                    "exist.\nMaybe it has been moved or renamed.\nYou can choose "
                    "a new directory where the notes are or where they will be "
                    "saved in.")
            elif root_path_exists and not root_path_is_writable:
                self.welcomeText.setText(
                    "Welcome to nobleNote!\nThe path where the notes are located "
                    "is not writable.\nMaybe your drive is running in read only "
                    "mode.")
        else:
            if not root_path_is_set:
                self.welcomeText.setText(
                    "Welcome to nobleNote!\nThis is the first time that "
                    "nobleNote has been started.\nYou can choose a directory "
                    "where the notes will be saved in.")
            elif root_path_is_set and not root_path_exists:
                self.welcomeText.setText(
                    "Welcome to nobleNote!\nThe set path for the notes does not "
                    "exist.\nMaybe it has been moved or renamed.\nYou can choose "
                    "a new directory where the notes are or where they will be "
                    "saved in.")
            elif root_path_exists and not root_path_is_writable:
                self.welcomeText.setText(
                    "Welcome to nobleNote!\nThe path where the notes are located "
                    "is not writable.\nYou can choose a new directory where the "
                    "notes will be saved in. Otherwise changes might not be saved.")