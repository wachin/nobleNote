# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Re-emits the modificationChanged signal of a QTextDocument after a delay
if the modified property is still set. Does not modify the modified property.
"""

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QTextDocument


class TextDocument(QTextDocument):
    delayedModificationChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.delay_ = 2000
        self.timer.setInterval(self.delay_)
        self.timer.setSingleShot(True)
        self.modificationChanged.connect(self.start_stop_timer)
        self.timer.timeout.connect(self.send_delayed_modification_changed)

    def setDelay(self, delay: int):
        self.delay_ = delay

    def delay(self) -> int:
        return self.delay_

    def start_stop_timer(self, modified: bool):
        if modified:
            self.timer.start()
        else:
            self.timer.stop()

    def send_delayed_modification_changed(self):
        if self.isModified():
            self.delayedModificationChanged.emit()