# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A class writing formatted text in xml files.
The format is similar to the xml format used by tomboy/gnote."""

from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape

from PyQt6.QtCore import QDateTime
from PyQt6.QtGui import QFont, QTextCharFormat, QTextCursor, QTextDocument

from .datetimeutil import DateTime, quid_str, create_quid


class XmlNoteWriter:
    def __init__(self, file_path: str = ""):
        self.file_path_ = file_path
        self.frame_ = None
        self.uuid_ = None
        self.last_change_ = QDateTime()
        self.last_metadata_change_ = QDateTime()
        self.create_date_ = QDateTime()

    def set_device(self, file_path):
        self.file_path_ = file_path

    def device(self):
        return self.file_path_ or None

    def set_frame(self, frame):
        self.frame_ = frame

    def frame(self):
        return self.frame_

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

    def set_uuid(self, uuid_):
        self.uuid_ = uuid_

    def uuid(self):
        return self.uuid_

    def _date_string(self, dt: QDateTime) -> str:
        if dt.isNull():
            dt = QDateTime.currentDateTime()
        return DateTime.to_iso8601(dt)

    def write(self):
        if self.frame_ is None or not self.file_path_:
            return

        uuid_str = quid_str(self.uuid_).strip("{}")
        if not uuid_str:
            uuid_str = quid_str(create_quid()).strip("{}")

        title = self.frame_.document().metaInformation(
            QTextDocument.MetaInformation.DocumentTitle) or ""

        chunks = []
        chunks.append('<?xml version="1.0" encoding="utf-8"?>')
        chunks.append('<note version="0.3" xmlns:link="http://example.com">')
        chunks.append("  <id>urn:uuid:%s</id>" % uuid_str)
        chunks.append("  <title>%s</title>" % _xml_escape(title))
        chunks.append('  <text xml:space="preserve">')
        chunks.append('    <note-content version="0.1">')

        block = self.frame_.document().firstBlock()
        while block.isValid():
            block_text = block.text()
            for fr in block.textFormats():
                fmt = fr.format
                text = block_text[fr.start:fr.start + fr.length]
                text = text.replace("\u2029", "\n").replace("\u2028", "\n")
                tags = []
                if fmt.fontItalic():
                    tags.append("italic")
                if fmt.fontStrikeOut():
                    tags.append("strikethrough")
                if fmt.fontWeight() > QFont.Weight.Normal:
                    tags.append("bold")
                if fmt.underlineStyle() != QTextCharFormat.UnderlineStyle.NoUnderline:
                    tags.append("underline")

                for tag in tags:
                    chunks.append("      <%s>" % tag)
                chunks.append("      %s" % _xml_escape(text))
                for tag in reversed(tags):
                    chunks.append("      </%s>" % tag)

            # newline between blocks
            chunks.append("      \n")
            block = block.next()

        chunks.append("    </note-content>")
        chunks.append("  </text>")
        chunks.append("  <last-change-date>%s</last-change-date>"
                      % self._date_string(self.last_change_))
        chunks.append("  <last-metadata-change>%s</last-metadata-change>"
                      % self._date_string(self.last_metadata_change_))
        chunks.append("  <create-date>%s</create-date>"
                      % self._date_string(self.create_date_))
        chunks.append("  <tags>")
        chunks.append("    <tag>system:notebook:%s</tag>" % "nobleNote")
        chunks.append("  </tags>")
        chunks.append("</note>")

        try:
            Path(self.file_path_).write_text("\n".join(chunks) + "\n",
                                              encoding="utf-8")
        except OSError:
            pass