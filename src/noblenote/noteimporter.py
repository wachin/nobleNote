# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Imports tomboy/gnote xml notes into the html format used by nobleNote."""

import threading
from pathlib import Path

from PyQt6.QtCore import QFileInfo, QObject, QSettings
from PyQt6.QtWidgets import QFileDialog, QProgressDialog, QWidget

from .htmlnotewriter import HtmlNoteWriter
from .progressreceiver import ProgressReceiver


class NoteImporter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        parent_widget = self.parent() if hasattr(self.parent(), "isWidgetType") else None
        if parent_widget is not None and isinstance(parent_widget, QWidget):
            self.parent_widget = parent_widget
        else:
            self.parent_widget = None
        self.import_files = []
        self.file_dialog = None
        self.dialog = None
        self.progress_receiver = None

    def importDialog(self):
        if self.file_dialog is not None:
            return

        self.import_files.clear()

        self.file_dialog = QFileDialog(
            self.parent_widget,
            self.tr("Select one or more tomboy or gnote notes"),
            str(QSettings().value("import_path", "")),
            self.tr("Notes") + " (*.note)")
        self.file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
        self.file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        self.file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        self.file_dialog.setOption(QFileDialog.Option.ReadOnly)
        self.file_dialog.show()
        self.file_dialog.accepted.connect(self.import_xml_notes)
        self.file_dialog.rejected.connect(self.file_dialog.deleteLater)

    def import_xml_notes(self):
        self.import_files = list(self.file_dialog.selectedFiles())
        if not self.import_files:
            return

        QSettings().setValue("import_path",
                             QFileInfo(self.import_files[-1]).absolutePath())

        self.dialog = QProgressDialog(self.parent_widget)
        self.dialog.setLabelText(self.tr("Importing notes..."))
        self.dialog.setRange(0, len(self.import_files))

        self.progress_receiver = ProgressReceiver(self.parent_widget)
        self.progress_receiver.valueChanged.connect(self.dialog.setValue)
        root_path = str(QSettings().value("root_path", ""))

        def worker():
            for file in self.import_files:
                HtmlNoteWriter.write_xml_2_html(file, root_path)
                self.progress_receiver.post_progress_event()

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()
        self.dialog.show()

        def wait_for_finish():
            self._thread.join()
            self.dialog.reject()
            self.dialog.deleteLater()
            self.file_dialog.deleteLater()
            self.file_dialog = None

        threading.Thread(target=wait_for_finish, daemon=True).start()