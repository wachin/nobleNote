# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A class writing formatted text in html files (htmlnotewriter)."""

import re
from pathlib import Path

from PyQt6.QtCore import QDate, QDateTime, QDir, QSettings, QFileInfo
from PyQt6.QtGui import QTextDocument

from . import htmlnotereader
from .datetimeutil import DateTime, quid_str, create_quid, is_null


class HtmlNoteWriter:
    def __init__(self, file_path: str):
        self.file_path_ = file_path
        self.document_ = None        # QTextDocument
        self.title_ = ""
        self.uuid_ = None            # uuid.UUID or None
        self.last_change_ = QDateTime()
        self.last_metadata_change_ = QDateTime()
        self.create_date_ = QDateTime()

    def set_document(self, document: QTextDocument):
        self.document_ = document

    def document(self) -> QTextDocument:
        return self.document_

    def set_title(self, title: str):
        self.title_ = title

    def title(self) -> str:
        return self.title_

    def set_uuid(self, uuid_):
        self.uuid_ = uuid_

    def uuid(self):
        return self.uuid_

    def set_last_change(self, dt: QDateTime):
        self.last_change_ = dt

    def last_change(self) -> QDateTime:
        return self.last_change_

    def set_last_metadata_change(self, dt: QDateTime):
        self.last_metadata_change_ = dt

    def last_metadata_change(self) -> QDateTime:
        return self.last_metadata_change_

    def set_create_date(self, dt: QDateTime):
        self.create_date_ = dt

    def create_date(self) -> QDateTime:
        return self.create_date_

    def write(self):
        if self.document_ is None:
            raise RuntimeError("HtmlNoteWriter.write failed : no QTextDocument set")

        self.document_.setMetaInformation(
            QTextDocument.MetaInformation.DocumentTitle, self.title_)
        html = self.document_.toHtml()

        # remove { } braces
        uuid_str = quid_str(self.uuid_).strip("{}")

        # insert meta elements (the C++ version reuses lastChange_ for the
        # create-date, so this is reproduced faithfully)
        last_change = self.last_change_ if not self.last_change_.isNull() \
            else QDateTime.currentDateTime()

        html = self._insert_meta_element(html, "create-date",
                                         DateTime.to_iso8601(last_change))
        html = self._insert_meta_element(html, "last-change-date",
                                         DateTime.to_iso8601(last_change))
        html = self._insert_meta_element(html, "uuid", uuid_str)

        # set html5 utf-8 tag
        meta_line = '<meta charset="UTF-8"/>'
        head_idx = html.find("<head>")
        if head_idx != -1:
            html = html[:head_idx + len("<head>")] + meta_line + html[head_idx + len("<head>"):]

        try:
            with open(self.file_path_, "w", encoding="utf-8") as f:
                f.write(html)
        except OSError:
            pass

    def _insert_meta_element(self, html: str, name: str, content: str) -> str:
        meta_line = '<meta name="%s" content="%s"/>' % (name, content)
        head_idx = html.find("<head>")
        if head_idx != -1:
            html = html[:head_idx + len("<head>")] + meta_line + html[head_idx + len("<head>"):]
        return html

    @staticmethod
    def write_xml_2_html(xml_file_path: str, output_path: str):
        if not xml_file_path or not output_path:
            return

        from .xmlnotereader import XmlNoteReader

        document = QTextDocument()
        reader = XmlNoteReader(xml_file_path, document)
        reader.read()

        folder = ""
        tag = reader.tag()
        illegal = re.compile(r"[\\^/?<>:*|\"]|^(com\d|lpt\d|con|nul|prn)$",
                             re.IGNORECASE)
        if tag:
            tag = tag.replace("system:notebook:", "")
            tag = tag.replace("system:template", "")
            tag = illegal.sub("", tag)
            if tag.startswith("."):
                tag = tag[1:]
            folder = tag
        if not folder:
            folder = "default"

        title = reader.title()
        title = illegal.sub("", title)
        if not title:
            title = "untitled note"

        Path(output_path).mkdir(parents=True, exist_ok=True)
        file_path = str(Path(output_path) / folder / title)

        # avoid overwriting existing files
        counter = 0
        orig_path = file_path
        while Path(file_path).exists():
            counter += 1
            file_path = "%s (%d)" % (orig_path, counter)

        writer = HtmlNoteWriter(file_path)
        writer.document_ = document
        writer.set_title(title)
        writer.set_last_change(reader.last_change())
        writer.set_last_metadata_change(reader.last_metadata_change())
        writer.set_create_date(reader.create_date())
        writer.set_uuid(reader.uuid())
        writer.write()

        backup_dir = QSettings().value("backup_dir_path", "").toString() or ""
        if backup_dir:
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
            uuid_str = quid_str(reader.uuid()).strip("{}")
            try:
                import shutil
                shutil.copyfile(file_path, str(Path(backup_dir) / uuid_str))
            except OSError:
                pass