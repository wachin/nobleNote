# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Persistent per-note undo history.

Qt keeps the undo stack of a note in memory only: it is lost when the note is
reloaded or when nobleNote is closed.  This module records every text change in
a small SQLite database inside the configuration directory, so deleted words
can still be found and recovered much later from the history window.

Changes are stored as the removed and the added text of every edit, grouped a
little while typing, and the full document is snapshotted from time to time
(and always after an undo or a redo) so the note can be restored to a point in
the past.
"""

from __future__ import annotations

import sqlite3
import time
import zlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QSettings, QTimer
from PyQt6.QtGui import QTextDocument

# entries of the same kind closer than this are written as one entry
BUFFER_SECONDS = 1.5
# a snapshot of the whole note is kept at least this often...
SNAPSHOT_EVERY_ENTRIES = 10
SNAPSHOT_SECONDS = 60.0

ENTRY_OPEN = "open"
ENTRY_RELOAD = "reload"
ENTRY_INSERT = "insert"
ENTRY_DELETE = "delete"
ENTRY_REPLACE = "replace"
ENTRY_UNDO = "undo"
ENTRY_REDO = "redo"
ENTRY_RESTORE = "restore"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    note_id INTEGER NOT NULL,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    removed TEXT NOT NULL DEFAULT '',
    added TEXT NOT NULL DEFAULT '',
    snapshot BLOB
);
CREATE INDEX IF NOT EXISTS entries_note_id ON entries(note_id, id);
"""


@dataclass
class HistoryEntry:
    """One recorded change of a note."""

    id: int
    timestamp: datetime
    kind: str
    removed: str
    added: str


def one_line(text: str, limit: int = 120) -> str:
    """The beginning of a text on a single line, for lists and banners."""
    collapsed = " ".join(text.split())
    if len(collapsed) > limit:
        collapsed = collapsed[:limit - 1] + "\u2026"
    return collapsed


def history_database_path() -> Path:
    """The database lives next to the settings file, also in portable mode."""
    file_name = QSettings().fileName()
    if file_name:
        base = Path(file_name).parent
    else:
        base = Path.home() / ".config" / "nobleNote"
    return base / "history" / "undo-history.sqlite3"


class HistoryDatabase:
    """A tiny SQLite store for the history of every note."""

    def __init__(self, path: Path):
        self.connection: Optional[sqlite3.Connection] = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(str(path), timeout=5)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.executescript(_SCHEMA)
            self.connection.commit()
        except (OSError, sqlite3.Error):
            if self.connection is not None:
                self.connection.close()
            self.connection = None

    # ------------------------------------------------------------------
    def note_id(self, key: str, path: str = "") -> Optional[int]:
        if self.connection is None:
            return None
        now = datetime.now().isoformat(timespec="seconds")
        try:
            with self.connection:
                row = self.connection.execute(
                    "SELECT id FROM notes WHERE key = ?", (key,)).fetchone()
                if row is not None:
                    self.connection.execute(
                        "UPDATE notes SET path = ?, updated_at = ? WHERE id = ?",
                        (path, now, row[0]))
                    return int(row[0])
                cursor = self.connection.execute(
                    "INSERT INTO notes (key, path, updated_at) VALUES (?, ?, ?)",
                    (key, path, now))
                return int(cursor.lastrowid)
        except sqlite3.Error:
            return None

    def add_entry(self, note_id: Optional[int], kind: str, removed: str,
                  added: str,
                  timestamp: Optional[datetime] = None) -> Optional[int]:
        if self.connection is None or note_id is None:
            return None
        timestamp = timestamp or datetime.now()
        try:
            with self.connection:
                cursor = self.connection.execute(
                    "INSERT INTO entries (note_id, ts, kind, removed, added)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (note_id, timestamp.isoformat(timespec="seconds"), kind,
                     removed, added))
                return int(cursor.lastrowid)
        except sqlite3.Error:
            return None

    def set_snapshot(self, entry_id: Optional[int], html: str) -> None:
        if self.connection is None or entry_id is None:
            return
        try:
            with self.connection:
                self.connection.execute(
                    "UPDATE entries SET snapshot = ? WHERE id = ?",
                    (zlib.compress(html.encode("utf-8")), entry_id))
        except sqlite3.Error:
            pass

    def entries(self, note_id: Optional[int],
                limit: Optional[int] = None) -> list[HistoryEntry]:
        if self.connection is None or note_id is None:
            return []
        query = ("SELECT id, ts, kind, removed, added FROM entries"
                 " WHERE note_id = ? ORDER BY id DESC")
        parameters: tuple = (note_id,)
        if limit is not None:
            query += " LIMIT ?"
            parameters += (limit,)
        try:
            rows = self.connection.execute(query, parameters).fetchall()
        except sqlite3.Error:
            return []
        entries = []
        for row in rows:
            try:
                timestamp = datetime.fromisoformat(row[1])
            except ValueError:
                timestamp = datetime.now()
            entries.append(HistoryEntry(
                id=int(row[0]), timestamp=timestamp, kind=str(row[2]),
                removed=str(row[3] or ""), added=str(row[4] or "")))
        return entries

    def checkpoint(self, note_id: Optional[int],
                   entry_id: int) -> Optional[tuple[str, datetime]]:
        """The newest snapshot at or before entry_id, with its timestamp."""
        if self.connection is None or note_id is None:
            return None
        try:
            row = self.connection.execute(
                "SELECT snapshot, ts FROM entries WHERE note_id = ? AND id <= ?"
                " AND snapshot IS NOT NULL ORDER BY id DESC LIMIT 1",
                (note_id, entry_id)).fetchone()
        except sqlite3.Error:
            return None
        if row is None:
            return None
        try:
            html = zlib.decompress(row[0]).decode("utf-8")
        except (zlib.error, UnicodeDecodeError):
            return None
        try:
            timestamp = datetime.fromisoformat(row[1])
        except ValueError:
            timestamp = datetime.now()
        return html, timestamp


_database: Optional[HistoryDatabase] = None


def history_database() -> HistoryDatabase:
    """The shared history database of the application."""
    global _database
    if _database is None:
        _database = HistoryDatabase(history_database_path())
    return _database


# ----------------------------------------------------------------------
def _common_prefix(first: str, second: str) -> int:
    """Length of the common prefix, compared in slices (fast for long text)."""
    low, high = 0, min(len(first), len(second))
    while low < high:
        middle = (low + high + 1) // 2
        if first[:middle] == second[:middle]:
            low = middle
        else:
            high = middle - 1
    return low


def _common_suffix(first: str, second: str, prefix: int) -> int:
    """Length of the common suffix that does not overlap the prefix."""
    low, high = 0, min(len(first), len(second)) - prefix
    while low < high:
        middle = (low + high + 1) // 2
        if first[len(first) - middle:] == second[len(second) - middle:]:
            low = middle
        else:
            high = middle - 1
    return low


def change_parts(old_text: str, new_text: str) -> tuple[int, str, str]:
    """The position, removed text and added text between two document states."""
    prefix = _common_prefix(old_text, new_text)
    suffix = _common_suffix(old_text, new_text, prefix)
    removed = old_text[prefix:len(old_text) - suffix]
    added = new_text[prefix:len(new_text) - suffix]
    return prefix, removed, added


class UndoHistory(QObject):
    """Records every change of a note in the history database."""

    def __init__(self, document: QTextDocument, key: str, path: str = "",
                 parent=None):
        super().__init__(parent)
        self.document_ = document
        self.database_ = history_database()
        self.note_id_ = self.database_.note_id(key, path)
        self._shadow = document.toPlainText()
        self._pending: Optional[dict] = None
        self._forced_kind: Optional[str] = None
        self._suppressed = False
        self._changes_since_snapshot = 0
        self._last_snapshot = time.monotonic()
        self.last_written: Optional[HistoryEntry] = None

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(int(BUFFER_SECONDS * 1000))
        self._timer.timeout.connect(self.flush)

        # contentsChanged is emitted for every edit (contentsChange is not
        # delivered in every Qt build); the text difference is computed here
        document.contentsChanged.connect(self._on_contents_change)
        self.reset_baseline(ENTRY_OPEN)

    # ------------------------------------------------------------------
    def entries(self, limit: Optional[int] = None) -> list[HistoryEntry]:
        return self.database_.entries(self.note_id_, limit)

    def checkpoint(self, entry_id: int) -> Optional[tuple[str, datetime]]:
        return self.database_.checkpoint(self.note_id_, entry_id)

    # ------------------------------------------------------------------
    def _on_contents_change(self):
        new_text = self.document_.toPlainText()
        old_text = self._shadow
        if new_text == old_text:
            return
        self._shadow = new_text
        if self._suppressed:
            return

        prefix, removed_text, added_text = change_parts(old_text, new_text)
        forced = self._forced_kind
        self._forced_kind = None

        if forced is not None:
            self.flush()
            self._write(forced, prefix, removed_text, added_text)
            return

        if removed_text and added_text:
            kind = ENTRY_REPLACE
        elif removed_text:
            kind = ENTRY_DELETE
        else:
            kind = ENTRY_INSERT
        self._buffer(kind, prefix, removed_text, added_text)

    def _buffer(self, kind: str, position: int, removed: str, added: str):
        now = time.monotonic()
        pending = self._pending
        if (pending is not None and pending["kind"] == kind
                and now - pending["last"] <= BUFFER_SECONDS):
            if kind == ENTRY_INSERT and position == (pending["position"]
                                                     + len(pending["added"])):
                pending["added"] += added
                pending["last"] = now
                self._timer.start()
                return
            if kind == ENTRY_DELETE:
                if position + len(removed) == pending["position"]:
                    pending["removed"] = removed + pending["removed"]
                    pending["position"] = position
                    pending["last"] = now
                    self._timer.start()
                    return
                if position == pending["position"]:
                    pending["removed"] += removed
                    pending["last"] = now
                    self._timer.start()
                    return
            if kind == ENTRY_REPLACE and position == pending["position"]:
                pending["removed"] += removed
                pending["added"] += added
                pending["last"] = now
                self._timer.start()
                return
        self.flush()
        self._pending = {"kind": kind, "position": position, "removed": removed,
                         "added": added, "last": now}
        self._timer.start()

    def flush(self):
        """Write the buffered change, if any."""
        self._timer.stop()
        pending = self._pending
        self._pending = None
        if pending is None:
            return
        self._write(pending["kind"], pending["position"], pending["removed"],
                    pending["added"])

    def _write(self, kind: str, position: int, removed: str, added: str):
        timestamp = datetime.now()
        entry_id = self.database_.add_entry(
            self.note_id_, kind, removed, added, timestamp)
        self._changes_since_snapshot += 1
        snapshot_now = (
            kind in (ENTRY_UNDO, ENTRY_REDO, ENTRY_RESTORE)
            or self._changes_since_snapshot >= SNAPSHOT_EVERY_ENTRIES
            or time.monotonic() - self._last_snapshot >= SNAPSHOT_SECONDS)
        if snapshot_now:
            self.database_.set_snapshot(entry_id, self.document_.toHtml())
            self._changes_since_snapshot = 0
            self._last_snapshot = time.monotonic()
        self.last_written = HistoryEntry(
            id=entry_id if entry_id is not None else -1,
            timestamp=timestamp, kind=kind, removed=removed, added=added)

    # ------------------------------------------------------------------
    def mark_next(self, kind: str):
        """The next document change is the result of this action (undo/redo)."""
        self.flush()
        self._forced_kind = kind

    def clear_mark(self):
        self._forced_kind = None

    def reset_baseline(self, kind: str = ENTRY_RELOAD):
        """Start from the current document (after opening or reloading it)."""
        self.flush()
        self._suppressed = False
        self._forced_kind = None
        self._shadow = self.document_.toPlainText()
        timestamp = datetime.now()
        entry_id = self.database_.add_entry(
            self.note_id_, kind, "", "", timestamp)
        self.database_.set_snapshot(entry_id, self.document_.toHtml())
        self._changes_since_snapshot = 0
        self._last_snapshot = time.monotonic()
        self.last_written = HistoryEntry(
            id=entry_id if entry_id is not None else -1, timestamp=timestamp,
            kind=kind, removed="", added="")

    # ------------------------------------------------------------------
    def suspend(self):
        """Ignore the changes until the document has been reloaded."""
        self.flush()
        self._suppressed = True

    def begin_external_change(self) -> str:
        """Suppress recording while the note is replaced programmatically."""
        self.flush()
        self._suppressed = True
        return self.document_.toPlainText()

    def end_external_change(self, previous_text: str,
                            kind: str = ENTRY_RESTORE):
        self._shadow = self.document_.toPlainText()
        self._suppressed = False
        self._forced_kind = None
        position, removed, added = change_parts(previous_text, self._shadow)
        self._write(kind, position, removed, added)
