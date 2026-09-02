# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Helpers used by the components of the application."""

import re
import uuid as _uuid
from typing import Optional

from PyQt6.QtCore import QDateTime, Qt


# ---------------------------------------------------------------------------
# UUID helpers
#
# In the C++ source QUuid::toString() produces a string like
# "{xxxxxxxx-xxxx-...}".  Those strings (including the braces) are used as
# keys inside QSettings and inside the note files meta tags, so we reproduce
# the exact same format for full compatibility with existing installations.
# ---------------------------------------------------------------------------


def parse_quid(value: Optional[str]) -> Optional[_uuid.UUID]:
    """Parse a QUuid string (with or without braces) into a uuid.UUID.

    Returns None for an invalid or empty/null uuid.
    """
    if not value:
        return None
    s = value.strip()
    if s.startswith("{"):
        s = s[1:]
    if s.endswith("}"):
        s = s[:-1]
    try:
        return _uuid.UUID(s)
    except ValueError:
        return None


def quid_str(uuid_: Optional[_uuid.UUID]) -> str:
    """Format a uuid.UUID like QUuid::toString() would (with braces)."""
    if uuid_ is None:
        return "{}"
    return "{" + str(uuid_) + "}"


def create_quid() -> _uuid.UUID:
    """Equivalent of QUuid::createUuid()."""
    return _uuid.uuid4()


def is_null(uuid_: Optional[_uuid.UUID]) -> bool:
    """Equivalent of QUuid::isNull()."""
    return uuid_ is None


# ---------------------------------------------------------------------------
# Qt::mightBeRichText / Qt::convertFromPlainText equivalents
# ---------------------------------------------------------------------------


def might_be_rich_text(text: str) -> bool:
    """Heuristic equivalent of Qt::mightBeRichText() (Qt6 removed it)."""
    if not "+" in text and ("<" in text or "&lt;" in text) and ">" in text:
        return True
    # look for any html/rich text tag
    return re.search(r"<[a-zA-Z/!][^>]*>", text) is not None


def convert_from_plain_text(text: str) -> str:
    """Equivalent of Qt::convertFromPlainText() without the empty-line
    paragraph handling that the C++ helper performs internally."""
    escaped = text.replace("&", "&amp;")
    escaped = escaped.replace(">", "&gt;")
    escaped = escaped.replace("<", "&lt;")
    # newlines become <br />
    escaped = escaped.replace("\r\n", "<br />")
    escaped = escaped.replace("\n", "<br />")
    escaped = escaped.replace("\r", "<br />")
    return escaped


# ---------------------------------------------------------------------------
# DateTime helper (equivalent of the C++ class DateTime)
# ---------------------------------------------------------------------------


class DateTime:
    """Date formatting helper class."""

    @staticmethod
    def get_time_zone_offset(dt: QDateTime) -> str:
        offset = dt.offsetFromUtc() // 3600
        if offset > 0:
            return "+%02d:00" % offset
        return "%02d:00" % offset

    @staticmethod
    def to_iso8601(dt: QDateTime) -> str:
        base = dt.toString(Qt.DateFormat.ISODate)
        msec = dt.toString("zzz")
        return base + "." + msec + "0000" + DateTime.get_time_zone_offset(dt)