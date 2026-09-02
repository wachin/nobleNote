# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.

from pathlib import Path

VERSION_FILE = Path(__file__).resolve().parent.parent / "version.txt"


def version_string() -> str:
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.readline().strip()
    except OSError:
        return "unknown"


APP_VERSION = version_string()