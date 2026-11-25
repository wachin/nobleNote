# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""AbstractNoteReader - interface for the note reader classes."""

from abc import ABC, abstractmethod
from typing import Optional


class AbstractNoteReader(ABC):
    """Interface for note reader classes.

    read() must be called before the accessor methods may be used.
    """

    @abstractmethod
    def read(self):
        """Read the contents of the document."""

    @abstractmethod
    def uuid(self):
        """The uuid that has been extracted during read()."""

    @abstractmethod
    def title(self) -> str:
        ...

    @abstractmethod
    def last_change(self):
        ...

    @abstractmethod
    def create_date(self):
        ...