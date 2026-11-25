# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Abstraction layer to the underlying note file on the filesystem.
Manages automatic saving and reloading of the note files."""

import threading
from pathlib import Path

from PyQt6.QtCore import QDateTime, QDir, QFileInfo, QObject, QSettings, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox, QTextBrowser

from .datetimeutil import create_quid, is_null
from .htmlnotereader import HtmlNoteReader
from .htmlnotewriter import HtmlNoteWriter
from .textdocument import TextDocument
from .xmlnotereader import XmlNoteReader


class NoteDescriptor(QObject):
    loadFinished = pyqtSignal(object)     # HtmlNoteReader, emitted after async load
    close = pyqtSignal()

    _lock_count = 0

    class Lock:
        """Re-entrance protection for stateChange()."""

        def __init__(self):
            NoteDescriptor._lock_count += 1

        def __del__(self):
            if NoteDescriptor._lock_count > 0:
                NoteDescriptor._lock_count -= 1

        @staticmethod
        def is_locked():
            return NoteDescriptor._lock_count > 0

    def __init__(self, file_path: str, text_browser: QTextBrowser,
                 document: TextDocument, note_widget=None):
        super().__init__(note_widget)
        self.initial_lock = NoteDescriptor.Lock()  # blocks stateChange while loading

        self.note_widget_ = note_widget
        self.document_ = document
        self.text_browser_ = text_browser
        self.file_path_ = file_path
        self.read_only_ = False
        self.uuid_ = None
        self.last_change_ = QDateTime()
        self.title_ = ""
        self.create_date_ = QDateTime()

        QTimer.singleShot(0, self.load)  # load after gui events have been processed
        self.document_.delayedModificationChanged.connect(self.state_change)
        # signal across threads, used to load the html asynchronously
        self.loadFinished.connect(self.on_html_load_finished,
                                  Qt.ConnectionType.QueuedConnection)

    def file_path(self) -> str:
        return self.file_path_

    def read_only(self) -> bool:
        return self.read_only_

    def uuid(self):
        return self.uuid_

    # ------------------------------------------------------------------
    def state_change(self):
        """1. checks if the file exists and if its uuid is still the same
           2. rare case: check for modification inside the autosave-interval
           3. reload if modified"""
        if NoteDescriptor.Lock.is_locked() or self.read_only_:
            return

        lock = NoteDescriptor.Lock()

        # 1. a filePath_ that still exists and a uuid that has changed means
        #    the file has been replaced by another file of the same name
        if Path(self.file_path_).exists():
            uuid_ = HtmlNoteReader.uuid(self.file_path_)
            if uuid_ is not None and self.uuid_ != uuid_:
                self.find_or_recreate()
        else:  # file does not longer exist
            self.find_or_recreate()

        # 2. rare: reload a note if it has been modified before the autosave
        #    has been triggered
        if (self.last_change_.toSecsSinceEpoch()
                < QFileInfo(self.file_path_).lastModified().toSecsSinceEpoch()):
            if self.document_.isModified():
                app_name = QApplication.instance().applicationName()
                answer = QMessageBox.warning(
                    self.note_widget_, self.tr("Note modified"),
                    self.tr("This note has been modified by another instance "
                            "of %1. Should the note be saved under a different "
                            "name? Else the note will be reloaded.")
                    .replace("%1", app_name),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if answer == QMessageBox.StandardButton.Yes:
                    self.uuid_ = create_quid()
                    self.title_ = QFileInfo(self.file_path_).baseName()
                    self.create_date_ = QDateTime.currentDateTime()
                    self.save(self.file_path_, self.uuid_, False)
                else:  # not modified, silently reload
                    self.load()
            return

        # 3. reload if modified
        if self.document_.isModified():
            self.save(self.file_path_, self.uuid_, True)
            self.document_.setModified(False)
            return

    def find_or_recreate(self):
        # search the moved or renamed file by its uuid
        root_path = QSettings().value("root_path", "").toString() or ""
        new_file_path = HtmlNoteReader.find_uuid(self.uuid_, root_path)

        if not new_file_path:
            answer = QMessageBox.warning(
                self.note_widget_, self.tr("Note does not exist"),
                self.tr("This note does not longer exist. Do you want to keep "
                        "the editor open?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer == QMessageBox.StandardButton.Yes:
                self.title_ = QFileInfo(self.file_path_).baseName()
                if self.note_widget_:
                    self.note_widget_.setWindowTitle(self.title_)
                self.save(self.file_path_, self.uuid_, False)  # old path / new uuid
            else:
                self.close.emit()
            return

        self.file_path_ = new_file_path
        self.title_ = QFileInfo(self.file_path_).baseName()
        if self.note_widget_:
            self.note_widget_.setWindowTitle(self.title_)

    def unlock_state_change(self):
        self.initial_lock = None
    def save(self, file_path: str, uuid_, overwrite_existing: bool):
        if not overwrite_existing:
            # avoid overwriting an existing file
            counter = 0
            orig_path = self.file_path_
            while Path(self.file_path_).exists():
                counter += 1
                self.file_path_ = "%s (%d)" % (orig_path, counter)

        Path(QFileInfo(file_path).absolutePath()).mkdir(parents=True, exist_ok=True)
        backup_dir = QSettings().value("backup_dir_path", "").toString() or ""
        if backup_dir:
            Path(backup_dir).mkdir(parents=True, exist_ok=True)

        self.write(file_path, uuid_)  # write note
        uuid_str = str(uuid_) if uuid_ is not None else ""
        if uuid_str and backup_dir:
            self.write_backup(backup_dir + QDir.separator() + uuid_str, uuid_)

        if self.note_widget_:
            self.note_widget_.setWindowTitle(self.title_)

    def write(self, file_path: str, uuid_):
        writer = HtmlNoteWriter(file_path)
        writer.set_document(self.document_)
        writer.set_uuid(uuid_)
        self.last_change_ = QDateTime.currentDateTime()
        writer.set_last_change(self.last_change_)
        writer.set_create_date(self.create_date_)
        writer.set_title(self.title_)
        writer.write()

    def write_backup(self, backup_file_path: str, uuid_):
        writer = HtmlNoteWriter(backup_file_path)
        writer.set_document(self.document_)
        writer.set_uuid(uuid_)
        writer.set_last_change(self.last_change_)
        writer.set_create_date(self.create_date_)
        writer.set_title(self.title_)
        writer.write()

    def load(self):
        # check if the file is a tomboy note
        if XmlNoteReader.might_be_xml_note(self.file_path_):
            reader = XmlNoteReader(self.file_path_, self.document_)
            reader.read()  # can only be run in the gui thread
            self.on_load_finished(reader, True)
        else:
            reader = HtmlNoteReader(self.file_path_)

            # run read concurrently (the document is set in the gui thread)
            def worker():
                reader.read()
                self.loadFinished.emit(reader)

            threading.Thread(target=worker, daemon=True).start()

        self.title_ = QFileInfo(self.file_path_).baseName()

    def on_html_load_finished(self, reader):
        # the text document must be manipulated on the gui thread
        self.document_.setHtml(reader.html())
        self.on_load_finished(reader)

    def on_load_finished(self, reader, is_xml_note=False):
        if self.note_widget_:
            self.note_widget_.setWindowTitle(self.title_)

        self.create_date_ = reader.create_date()
        last_mod = QFileInfo(self.file_path_).lastModified()
        self.last_change_ = last_mod if last_mod.isValid() else QDateTime.currentDateTime()
        self.uuid_ = reader.uuid()  # can be None

        pos_key = ("Notes/" + ("{" + str(self.uuid_) + "}" if self.uuid_ else "{}")
                   + "_cursor_position")
        cursor = self.text_browser_.textCursor() if self.text_browser_ else None
        if cursor is not None:
            try:
                pos = int(QSettings().value(pos_key, 0))
            except (TypeError, ValueError):
                pos = 0
            cursor.setPosition(pos)
            self.text_browser_.setTextCursor(cursor)

        # incomplete note, overwrite with html format
        if is_xml_note or is_null(self.uuid_):
            if is_null(self.uuid_):
                self.uuid_ = create_quid()
            self.save(self.file_path_, self.uuid_, True)

        self.document_.setModified(False)  # avoid delayedModificationChanged

        QTimer.singleShot(0, self.unlock_state_change)  # enable stateChange afterwards