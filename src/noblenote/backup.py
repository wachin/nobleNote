# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""The Backup class asynchronously reads note backup files from the file system
and shows a Trash window where trashed notes can be inspected and restored."""

import threading
from pathlib import Path

from PyQt6.QtCore import QDir, QFileInfo, QObject, QSettings, Qt
from PyQt6.QtWidgets import QProgressDialog

from .htmlnotereader import HtmlNoteReader
from .progressreceiver import ProgressReceiver
from .trash import Trash


class Backup(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_ = parent
        self.note_files = []
        self.backup_files = []
        self.backup_data_hash = {}
        self.progress_receiver1 = None
        self.progress_dialog1 = None
        self.progress_receiver2 = None
        self.progress_dialog2 = None
        self.trash = None
        self.get_notes()  # creates the tree children for the orphan backups

    def get_notes(self):
        root_path = str(QSettings().value("root_path", ""))
        if root_path:
            root = Path(root_path)
            for path in root.rglob("*"):
                if path.is_file():
                    self.note_files.append(str(path))

        self.progress_receiver1 = ProgressReceiver(self)
        self.progress_dialog1 = QProgressDialog(self.parent_)
        self.progress_dialog1.setLabelText("Indexing notes...")

        self.progress_receiver1.valueChanged.connect(self.progress_dialog1.setValue)

        def uuid_worker():
            for file in self.note_files:
                HtmlNoteReader.uuid(file)
                self.progress_receiver1.post_progress_event()

        self._thread1 = threading.Thread(target=uuid_worker, daemon=True)
        self._thread1.start()
        self.progress_dialog1.show()

        # the rest is done after the uuid indexing thread has finished
        def wait_for_finish():
            self._thread1.join()
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.setup_backups)

        threading.Thread(target=wait_for_finish, daemon=True).start()

    def setup_backups(self):
        # collect the uuids of the notes that were indexed in get_notes()
        note_uuid_list = [str(HtmlNoteReader.uuid(f)) for f in self.note_files]

        backup_dir = str(QSettings().value("backup_dir_path", ""))
        backup_files = []
        if backup_dir:
            backup_dir_path = Path(backup_dir)
            for info in sorted(backup_dir_path.glob("*"), key=lambda p: p.name):
                if info.is_file():
                    backup_files.append(QFileInfo(str(info)))

        # remove the backups that belong to an existing note
        for uuid_str in note_uuid_list:
            uuid_str = uuid_str.strip("{}")
            for info in list(backup_files):
                if info.fileName() == uuid_str:
                    backup_files.remove(info)

        if not backup_files:
            self.show_trash()
            return

        self.progress_receiver2 = ProgressReceiver(self)
        self.progress_dialog2 = QProgressDialog(self.parent_)
        self.progress_dialog2.setLabelText("Indexing trash...")
        self.progress_dialog2.setRange(0, len(backup_files))
        self.progress_receiver2.valueChanged.connect(self.progress_dialog2.setValue)

        self.progress_dialog1.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.progress_dialog2.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        def read_backups():
            for info in backup_files:
                reader = HtmlNoteReader(info.absoluteFilePath())
                reader.read()
                title = reader.title()
                if not title:
                    title = "deleted note"
                data = [title, info.absoluteFilePath(), reader.html()]
                self.backup_data_hash[info.absoluteFilePath()] = data
                self.progress_receiver2.post_progress_event()

        self._thread2 = threading.Thread(target=read_backups, daemon=True)
        self._thread2.start()
        self.progress_dialog2.show()

        def wait_for_trash():
            self._thread2.join()
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.show_trash)

        threading.Thread(target=wait_for_trash, daemon=True).start()

    def show_trash(self):
        self.trash = Trash(self.backup_data_hash, self.parent_)
        self.trash.destroyed.connect(self.deleteLater)
        # reparent so that these windows don't linger around after closing
        self.progress_dialog1.setParent(self.trash)
        self.progress_dialog2.setParent(self.trash)
        self.trash.show()