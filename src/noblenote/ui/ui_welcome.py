# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Welcome dialog form (equivalent of ui/welcome.ui)."""

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QGridLayout, QLabel,
                             QPushButton, QSizePolicy, QSpacerItem, QWidget)

_translate = QCoreApplication.translate


class Ui_Welcome:
    def setupUi(self, welcome_dialog: QDialog):
        welcome_dialog.resize(421, 220)
        welcome_dialog.setWindowTitle(_translate("Welcome", "Welcome to nobleNote"))

        self.gridLayout = QGridLayout(welcome_dialog)
        self.gridLayout.setObjectName("gridLayout")

        self.horizontalSpacer_2 = QSpacerItem(40, 20,
                                              QSizePolicy.Policy.Expanding,
                                              QSizePolicy.Policy.Minimum)
        self.gridLayout.addItem(self.horizontalSpacer_2, 2, 0)

        self.welcomeText = QLabel(welcome_dialog)
        self.welcomeText.setText("Welcome to nobleNote!\n"
                                 "This is the first time that nobleNote has been "
                                 "started.\nYou can choose a directory where the "
                                 "notes will be saved in.")
        self.welcomeText.setWordWrap(True)
        self.welcomeText.setObjectName("welcomeText")
        self.gridLayout.addWidget(self.welcomeText, 1, 0, 1, 2)

        self.browse = QPushButton(welcome_dialog)
        self.browse.setText(_translate("Welcome", "&Browse"))
        self.browse.setObjectName("browse")
        self.gridLayout.addWidget(self.browse, 3, 1)

        self.buttonBox = QDialogButtonBox(welcome_dialog)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel
                                         | QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 2)

        self.verticalSpacer_2 = QSpacerItem(20, 40,
                                            QSizePolicy.Policy.Minimum,
                                            QSizePolicy.Policy.Expanding)
        self.gridLayout.addItem(self.verticalSpacer_2, 0, 0)

        self.verticalSpacer = QSpacerItem(20, 40,
                                          QSizePolicy.Policy.Minimum,
                                          QSizePolicy.Policy.Expanding)
        self.gridLayout.addItem(self.verticalSpacer, 4, 1)

        self.buttonBox.accepted.connect(welcome_dialog.accept)
        self.buttonBox.rejected.connect(welcome_dialog.reject)

    def retranslateUi(self, welcome_dialog: QDialog):
        pass