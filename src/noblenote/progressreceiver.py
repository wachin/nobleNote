# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Used to report progress from worker threads.

In the C++ version the worker threads post QEvent objects to themselves and
the value is emitted from the event() override.  PyQt signals are already
queued/thread-safe, so the helper is simplified:  post_progress_event() just
increments the counter and emits valueChanged on the GUI thread.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class ProgressReceiver(QObject):
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.interval_ = 20
        self.value_ = 0

    def set_interval(self, interval: int):
        self.interval_ = interval

    def interval(self) -> int:
        return self.interval_

    def set_value(self, value: int):
        self.value_ = value

    def value(self) -> int:
        return self.value_

    def post_progress_event(self):
        self.value_ += 1
        self.valueChanged.emit(self.value_)