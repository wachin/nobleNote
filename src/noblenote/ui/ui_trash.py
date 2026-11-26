# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Trash dialog form (equivalent of ui/trash.ui)."""

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox,
                             QFrame, QGridLayout, QLabel, QPushButton,
                             QTextEdit, QTreeWidget)

translate = QCoreApplication.translate


class Ui_Trash:
    def setupUi(self, trash_dialog: QDialog):
        trash_dialog.resize(468, 355)
        trash_dialog.setWindowTitle(translate("Trash", "Trash"))

        self.gridLayout = QGridLayout(trash_dialog)
        self.gridLayout.setObjectName("gridLayout")

        self.buttonBox = QDialogButtonBox(trash_dialog)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 2)

        self.restoreButton = QPushButton(trash_dialog)
        self.restoreButton.setText(translate("Trash", "&Restore"))
        self.restoreButton.setObjectName("restoreButton")
        self.gridLayout.addWidget(self.restoreButton, 1, 0)

        self.deleteButton = QPushButton(trash_dialog)
        self.deleteButton.setText(translate("Trash", "&Delete"))
        self.deleteButton.setObjectName("deleteButton")
        self.gridLayout.addWidget(self.deleteButton, 1, 1)

        self.frame = QFrame(trash_dialog)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")

        self.textEdit = QTextEdit(self.frame)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")
        self.gridLayout_2.addWidget(self.textEdit, 1, 1)

        self.label = QLabel(self.frame)
        self.label.setText(translate("Trash", "Select the notes you want to delete or restore"))
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0)

        self.label_2 = QLabel(self.frame)
        self.label_2.setText(translate("Trash", "Preview"))
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 0, 1)

        self.treeWidget = QTreeWidget(self.frame)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeWidget.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.setHeaderLabels([translate("Trash", "Deleted notes")])
        self.treeWidget.setObjectName("treeWidget")
        self.gridLayout_2.addWidget(self.treeWidget, 1, 0)

        self.gridLayout.addWidget(self.frame, 0, 0, 1, 3)

        self.buttonBox.rejected.connect(trash_dialog.reject)

    def retranslateUi(self, trash_dialog: QDialog):
        pass