# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Note window form (equivalent of ui/note.ui)."""

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import QGridLayout, QMainWindow, QWidget

from ..resources import icon

_translate = QCoreApplication.translate


class Ui_Note:
    def setupUi(self, note_window: QMainWindow):
        note_window.setWindowTitle(_translate("Note", "Note-Editor"))
        note_window.setWindowIcon(icon("nobleNote"))

        self.centralwidget = QWidget(note_window)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        note_window.setCentralWidget(self.centralwidget)

    def retranslateUi(self, note_window: QMainWindow):
        pass