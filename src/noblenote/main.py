#!/usr/bin/env python3
# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Equivalent of src/main.cpp - application entry point."""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import QDir, QFileInfo, QLibraryInfo, QLocale, QSettings
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox, QStyleFactory

from .mainwindow import MainWindow
from .welcome import Welcome


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("nobleNote")
    app.setOrganizationName("nobleNote")

    if sys.platform.startswith("win"):
        app.setStyle(QStyleFactory.create("Fusion"))

    # Qt translations (optional)
    from PyQt6.QtCore import QTranslator

    qt_translator = QTranslator()
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if qt_translator.load("qt_" + QLocale.system().name(), translations_path):
        app.installTranslator(qt_translator)

    # nobleNote translations (the .qm files shipped in translations/)
    noblenote_translator = QTranslator()
    noblenote_path = str(Path(__file__).resolve().parent / "translations")
    if noblenote_translator.load(QLocale.system(), "noblenote", "_",
                                 noblenote_path):
        app.installTranslator(noblenote_translator)

    app.setQuitOnLastWindowClosed(False)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)

    # portable version: store the settings next to the executable
    app_dir = QDir.toNativeSeparators(app.applicationDirPath())
    settings_file_path = app_dir + "/" + app.applicationName() + "/" + \
                         QFileInfo(QSettings().fileName()).fileName()
    settings_file = QFileInfo(settings_file_path)
    if settings_file.exists():
        parent = settings_file.dir()
        parent.cdUp()  # cdUp because the folder is created by QSettings later
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                          parent.absolutePath())
        QSettings().setValue("isPortable", True)
    else:
        QSettings().setValue("isPortable", False)

    if not QSettings().isWritable():
        QMessageBox.critical(None, "Settings not writable",
                             "%s settings not writable!" % app.applicationName())

    if not Path(str(QSettings().value("import_path", ""))).exists():
        QSettings().setValue("import_path", QDir.homePath())

    root_path_is_set = QSettings().contains("root_path")
    root_path_value = str(QSettings().value("root_path", ""))
    root_path_exists = Path(root_path_value).exists()
    root_path_is_writable = os.access(root_path_value, os.W_OK)

    if not root_path_exists or not root_path_is_writable:
        # the welcome dialog writes the root path
        welcome = Welcome()
        welcome.get_instance(root_path_is_set, root_path_exists,
                             root_path_is_writable)
        if welcome.exec() == QDialog.DialogCode.Rejected:
            return 0  # leave main if the user rejects the welcome dialog
    elif not root_path_is_set:
        QSettings().setValue("root_path",
                             QDir.toNativeSeparators(
                                 app.applicationDirPath() + "/"
                                 + app.applicationName()))

    window = MainWindow()
    if bool(QSettings().value("Hide_main_at_startup", False)):
        window.show_open_notes()
    else:
        window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())