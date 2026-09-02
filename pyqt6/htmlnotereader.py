# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A class reading formatted html text and plain text (htmlnotereader)."""

import uuid as _uuid
from typing import Optional
from pathlib import Path

from PyQt6.QtCore import QDateTime, QFileInfo, Qt
from PyQt6.QtGui import QTextDocument

from .abstractnotereader import AbstractNoteReader
from .datetimeutil import might_be_rich_text, convert_from_plain_text, parse_quid

_UTF8 = "utf-8"


class HtmlNoteReader(AbstractNoteReader):
    def __init__(self, file_path: str):
        self.file_path_ = file_path
        self.title_ = ""
        self.uuid_ = None          # uuid.UUID or None (null uuid)
        self.last_change_ = QDateTime()
        self.last_metadata_change_ = QDateTime()
        self.create_date_ = QDateTime()
        self.html_ = ""

    def read(self):
        self._read(self.file_path_)

    def uuid(self, file_path=None) -> Optional[_uuid.UUID]:
        """Instance call: the uuid that has been extracted during read().

        Class-level call (C++ overload): HtmlNoteReader.uuid(filePath)
        reads the uuid from a file and returns None if it could not be
        found.
        """
        if file_path is not None:
            return HtmlNoteReader._uuid_from_file(file_path)
        if isinstance(self, HtmlNoteReader):
            return self.uuid_
        return HtmlNoteReader._uuid_from_file(self)

    def title(self) -> str:
        return self.title_

    def last_change(self) -> QDateTime:
        return self.last_change_

    def last_metadata_change(self) -> QDateTime:
        return self.last_metadata_change_

    def create_date(self) -> QDateTime:
        return self.create_date_

    def html(self) -> str:
        """Returns the html contents of the file."""
        return self.html_

    # @staticmethod alias used by the C++ version as titleFromHtml
    @staticmethod
    def title_from_html(file_path: str) -> str:
        try:
            content = Path(file_path).read_text(encoding=_UTF8, errors="replace")
        except OSError:
            return ""
        document = QTextDocument()
        document.setHtml(content)
        return document.metaInformation(QTextDocument.MetaInformation.DocumentTitle)

    def _read(self, file_path: str):
        try:
            html = Path(file_path).read_text(encoding=_UTF8, errors="replace")
        except OSError:
            return

        if html and not might_be_rich_text(html):
            html = convert_from_plain_text(html)

        self.uuid_ = HtmlNoteReader.uuid_from_html(html)
        last_str = HtmlNoteReader.meta_content(html, "last-change-date")
        create_str = HtmlNoteReader.meta_content(html, "create-date")
        if last_str:
            self.last_change_ = QDateTime.fromString(last_str, Qt.DateFormat.ISODate)
        if create_str:
            self.create_date_ = QDateTime.fromString(create_str, Qt.DateFormat.ISODate)

        title_start = html.find("<title>")
        title_end = html.find("</title>")
        if title_start != -1 and title_end != -1 and title_start < title_end:
            start = title_start + len("<title>")
            self.title_ = html[start:title_end]

        self.html_ = html

    @staticmethod
    def _uuid_from_file(file_path: str) -> Optional[_uuid.UUID]:
        """Read the uuid from a file. Returns None if it could not be found."""
        try:
            content = Path(file_path).read_text(encoding=_UTF8, errors="replace")
        except OSError:
            return None
        if not might_be_rich_text(content):
            return None
        return HtmlNoteReader.uuid_from_html(content)

    @staticmethod
    def find_uuid(uuid_: _uuid.UUID, path: str) -> str:
        """Recursively search directory 'path' for a file containing the given
        uuid. Returns the first match or an empty string."""
        if uuid_ is None:
            return ""
        root = Path(path)
        if not root.is_dir():
            return ""
        for file_path in root.rglob("*"):
            if file_path.is_file():
                if uuid_ == HtmlNoteReader.uuid(str(file_path)):
                    return str(file_path)
        return ""

    @staticmethod
    def uuid_from_html(html: str) -> Optional[_uuid.UUID]:
        return parse_quid(HtmlNoteReader.meta_content(html, "uuid").strip())

    @staticmethod
    def meta_content(html: str, name: str) -> str:
        """Return the text of the content attribute in a
        <meta name="foo" content="bar" /> element for the given name."""
        if not html:
            return ""

        # find meta elements and read the requested name
        end_idx = 0
        iterations = 0
        while iterations < 10000:
            meta_idx = html.find("<meta", end_idx + 1)
            if meta_idx == -1:
                break
            end_idx = html.find(">", meta_idx + 1)
            meta_line = html[meta_idx:end_idx + 1]
            if name in meta_line:
                idx = meta_line.rfind('"')
                before_idx = meta_line.rfind('"', 0, idx - 1 if idx > 0 else 0)
                if idx != -1 or before_idx != -1:
                    # return the content between the quotes
                    return meta_line[before_idx + 1:idx]
            iterations += 1
        return ""