# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A class reading formatted text in xml files.

The format is similar to the xml format used by tomboy/gnote.
Reading requires a QTextDocument.
"""

import uuid as _uuid
from typing import Optional

from PyQt6.QtCore import (
    QIODevice,
    QDateTime,
    QDirIterator,
    QFile,
    QFileInfo,
    QXmlStreamReader,
    Qt,
)
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor, QTextDocument
from PyQt6.QtWidgets import QApplication

from .abstractnotereader import AbstractNoteReader
from .datetimeutil import parse_quid


class XmlNoteReader(AbstractNoteReader):
    """Reads formatted text in xml files.

    The format is similar to the xml format used by tomboy/gnote.
    """

    def __init__(self, file_path: str, doc: Optional[QTextDocument]):
        super().__init__()
        self._parser = QXmlStreamReader()
        self.file_path_ = file_path
        self.document_ = doc
        self.title_ = ""
        self.uuid_: Optional[_uuid.UUID] = None
        self.last_change_ = QDateTime()
        self.last_metadata_change_ = QDateTime()
        self.create_date_ = QDateTime()
        self.tag_ = ""

    # ------------------------------------------------------------------
    # accessors
    # ------------------------------------------------------------------
    def set_device(self, device: QIODevice):
        self._parser.setDevice(device)

    def device(self) -> Optional[QIODevice]:
        return self._parser.device()

    def set_document(self, document: QTextDocument):
        self.document_ = document

    def document(self) -> Optional[QTextDocument]:
        return self.document_

    def uuid(self, file_path=None) -> Optional[_uuid.UUID]:
        """Instance call: the uuid that has been extracted during read().

        Class-level call (C++ overload): XmlNoteReader.uuid(filePath)
        reads the uuid from a file.
        """
        if file_path is not None:
            return XmlNoteReader._uuid_from_file(file_path)
        if isinstance(self, XmlNoteReader):
            return self.uuid_
        return XmlNoteReader._uuid_from_file(self)

    def title(self) -> str:
        return self.title_

    def last_change(self) -> QDateTime:
        return self.last_change_

    def last_metadata_change(self) -> QDateTime:
        return self.last_metadata_change_

    def create_date(self) -> QDateTime:
        return self.create_date_

    def tag(self) -> str:
        """The notebook tag, e.g. system:notebook:MyNotebook."""
        return self.tag_

    # ------------------------------------------------------------------
    # reading
    # ------------------------------------------------------------------
    def read(self):
        file = QFile(self.file_path_)
        if not file.open(QIODevice.OpenModeFlag.ReadOnly):
            return
        self._parser.setDevice(file)
        self._parse_xml()

        # if uuid wasn't inside the xml text try to get it out of the filename
        if self.uuid_ is None:
            self.uuid_ = parse_quid(QFileInfo(self.file_path_).baseName())

        # remove the title inside the document and the empty 2nd line, because
        # the title is already in the window title
        if self.document_ is not None:
            cursor = QTextCursor(self.document_)  # point to start of the document
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            title_line = cursor.selectedText()
            if title_line.strip() == self.title_.strip():
                cursor.deleteChar()
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock,
                                QTextCursor.MoveMode.KeepAnchor, 2)
            empty_line = cursor.selectedText()
            if not empty_line.strip():
                cursor.deleteChar()

        file.close()

    def _parse_xml(self):
        """Read the content's of a QIODevice and write the formatted text into
        the QTextDocument."""
        if self._parser.device() is None:
            return

        # skip everything until <note-content>
        while not self._parser.atEnd():
            self._parser.readNext()

            name = self._parser.name()
            if name == "note-content":
                if self.document_ is None:  # no document to write the content into
                    self._parser.skipCurrentElement()
                else:
                    self._read_content()
            elif name in ("id", "uuid"):  # only "id" is written
                id_str = self._parser.readElementText()
                self.uuid_ = self._parse_uuid(id_str)
            elif name == "title":
                self.title_ = self._parser.readElementText()
            elif name == "last-change-date":
                self.last_change_ = QDateTime.fromString(
                    self._parser.readElementText(), Qt.DateFormat.ISODate)
            elif name == "last-metadata-change":
                self.last_metadata_change_ = QDateTime.fromString(
                    self._parser.readElementText(), Qt.DateFormat.ISODate)
            elif name == "create-date":
                self.create_date_ = QDateTime.fromString(
                    self._parser.readElementText(), Qt.DateFormat.ISODate)
            elif name == "tag":
                self.tag_ = self._parser.readElementText()

            if self._parser.hasError():
                return

    def _read_content(self):
        """Read contents of <note-content> tag and insert the formatted text
        into the document."""
        cursor = QTextCursor(self.document_.rootFrame())
        fmt = QTextCharFormat()

        if QApplication.instance() is not None:
            font = QApplication.font()
        else:  # may happen in unit tests without a running application
            font = QFont()
        base_point_size = font.pointSizeF()
        if base_point_size <= 0:
            base_point_size = 12.0
        base_family = font.family()

        while not self._parser.atEnd():
            token = self._parser.readNext()

            if token == QXmlStreamReader.TokenType.Characters:
                # read the text between the formatting elements
                cursor.insertText(self._parser.text(), fmt)
            elif token == QXmlStreamReader.TokenType.StartElement:
                # read elements <bold> <italic> and set the formatting
                name = self._parser.name()
                qual = self._parser.qualifiedName()
                if name == "bold":
                    fmt.setFontWeight(QFont.Weight.Bold)
                if name == "italic":
                    fmt.setFontItalic(True)
                if name == "underline":
                    fmt.setUnderlineStyle(
                        QTextCharFormat.UnderlineStyle.SingleUnderline)
                if name in ("strikethrough", "strikeout"):
                    # only strikethrough is written, but strikeout is also
                    # allowed for reading
                    fmt.setFontStrikeOut(True)
                if name == "highlight":
                    fmt.setBackground(QColor(255, 255, 0))
                if qual == "size:small":  # mutually exclusive options
                    fmt.setFontPointSize(base_point_size * 0.8)
                elif qual == "size:large":
                    fmt.setFontPointSize(base_point_size * 1.4)
                elif qual == "size:huge":
                    fmt.setFontPointSize(base_point_size * 1.6)
                if name == "monospace":
                    fmt.setFontFamilies(["Monospace"])
                # <link:url> is ignored, links are kept as plain text
            elif token == QXmlStreamReader.TokenType.EndElement:
                # unset formatting
                name = self._parser.name()
                qual = self._parser.qualifiedName()
                if name == "note-content":  # end of note content, exit here
                    return
                if name == "bold":
                    fmt.setFontWeight(QFont.Weight.Normal)
                if name == "italic":
                    fmt.setFontItalic(False)
                if name == "underline":
                    fmt.setUnderlineStyle(
                        QTextCharFormat.UnderlineStyle.NoUnderline)
                if name in ("strikethrough", "strikeout"):
                    fmt.setFontStrikeOut(False)
                if name == "highlight":
                    fmt.clearBackground()
                if qual in ("size:small", "size:large", "size:huge"):
                    fmt.setFontPointSize(base_point_size)
                if name == "monospace":
                    fmt.setFontFamilies([base_family])
                # ignore id

            if self._parser.hasError():
                return

    # ------------------------------------------------------------------
    # static helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_uuid(id_str: str) -> Optional[_uuid.UUID]:
        if id_str is None:
            return None
        # try to parse the rightmost 32 digits and four hyphens
        u = parse_quid(id_str[-(32 + 4):])
        if u is None:  # if parsing fails, try more complex parsing
            if id_str.startswith("urn:uuid:"):  # check the urn:uuid: prefix
                # 32 digits and four hyphens
                start = len("urn:uuid:")
                u = parse_quid(id_str[start:start + 32 + 4])
            else:  # try to parse the whole string (simplified() equivalent)
                u = parse_quid(" ".join(id_str.split()))
        return u

    @staticmethod
    def _uuid_from_file(file_path: str) -> Optional[_uuid.UUID]:
        """Reads a uuid from a file.

        If the uuid could not be found, a null uuid (None) is returned.
        """
        file = QFile(file_path)
        if not file.open(QIODevice.OpenModeFlag.ReadOnly):
            return None
        reader = QXmlStreamReader(file)
        while not reader.atEnd():
            if (reader.readNextStartElement()
                    and reader.name() in ("id", "uuid")):
                id_str = reader.readElementText()
                file.close()
                return XmlNoteReader._parse_uuid(id_str)
            if reader.hasError():
                file.close()
                return None
        file.close()
        # if uuid wasn't inside the xml text try to get it out of the filename
        return parse_quid(QFileInfo(file_path).baseName())

    @staticmethod
    def find_uuid(uuid_: Optional[_uuid.UUID], path: str) -> str:
        """Searches all directories under the given path recursively for a
        file with the given uuid.

        Returns the first file that contains the given uuid or an empty
        string if the uuid could not be found or if the given uuid is null.
        """
        if uuid_ is None:
            return ""

        it = QDirIterator(path, flags=QDirIterator.IteratorFlag.Subdirectories)
        while it.hasNext():
            file_path = it.next()
            if uuid_ == XmlNoteReader.uuid(file_path):
                return file_path
        return ""

    @staticmethod
    def might_be_xml_note(file_path: str) -> bool:
        """Heuristic that checks for a <note ...> xml element."""
        file = QFile(file_path)
        if not file.open(QIODevice.OpenModeFlag.ReadOnly):
            return False
        reader = QXmlStreamReader(file)
        while not reader.atEnd():
            reader.readNext()
            if reader.isStartElement():
                name = reader.name()
                if name == "note":
                    file.close()
                    return True
                if name in ("html", "head"):  # detect html
                    file.close()
                    return False
            if reader.hasError():  # this should detect plain text
                file.close()
                return False
        file.close()
        return False
