# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Preferences dialog form (equivalent of ui/preferences.ui)."""

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox,
                             QFontComboBox, QGridLayout, QLabel, QLineEdit,
                             QPushButton, QSizePolicy, QSpacerItem,
                             QSpinBox, QComboBox)

translate = QCoreApplication.translate


class Ui_Preferences:
    def setupUi(self, pref_dialog: QDialog):
        pref_dialog.resize(446, 605)
        pref_dialog.setWindowTitle(translate("Preferences", "Preferences"))

        self.gridLayout = QGridLayout(pref_dialog)
        self.gridLayout.setObjectName("gridLayout")

        # row 0
        self.rootLabel = QLabel(pref_dialog)
        font = self.rootLabel.font()
        font.setBold(True)
        self.rootLabel.setFont(font)
        self.rootLabel.setText(translate("Preferences", "Root directory:"))
        self.gridLayout.addWidget(self.rootLabel, 0, 1)

        # row 1
        self.rootPathLabel = QLineEdit(pref_dialog)
        self.rootPathLabel.setText("root folder")
        self.rootPathLabel.setReadOnly(True)
        self.gridLayout.addWidget(self.rootPathLabel, 1, 1)
        self.browseButton = QPushButton(pref_dialog)
        self.browseButton.setText(translate("Preferences", "&Browse ..."))
        self.gridLayout.addWidget(self.browseButton, 1, 2)

        # row 2
        self.gridLayout.addItem(QSpacerItem(20, 10,
                                            QSizePolicy.Policy.Minimum,
                                            QSizePolicy.Policy.Fixed), 2, 1)

        # row 3
        self.backupLabel = QLabel(pref_dialog)
        font = self.backupLabel.font()
        font.setBold(True)
        self.backupLabel.setFont(font)
        self.backupLabel.setText(translate("Preferences", "Backup directory:"))
        self.gridLayout.addWidget(self.backupLabel, 3, 1)

        # row 4
        self.backupPathLabel = QLineEdit(pref_dialog)
        self.backupPathLabel.setText("backup folder")
        self.gridLayout.addWidget(self.backupPathLabel, 4, 1, 1, 2)

        # row 5
        self.gridLayout.addItem(QSpacerItem(20, 10,
                                            QSizePolicy.Policy.Minimum,
                                            QSizePolicy.Policy.Fixed), 5, 1)

        # row 6
        self.label_6 = QLabel(pref_dialog)
        self.label_6.setText(translate("Preferences", "Number of recently opened notes"))
        self.gridLayout.addWidget(self.label_6, 6, 1)
        self.recentSpin = QSpinBox(pref_dialog)
        self.recentSpin.setMaximum(15)
        self.recentSpin.setValue(5)
        self.gridLayout.addWidget(self.recentSpin, 6, 2)

        # row 7
        self.dontQuit = QCheckBox(pref_dialog)
        self.dontQuit.setText(translate("Preferences", "&Close to tray"))
# row 11
        self.kineticScrolling = QCheckBox(pref_dialog)
        self.kineticScrolling.setText(translate("Preferences", "&Touch screen scrolling"))
        self.kineticScrolling.setToolTip("Enables drag to scroll")
        self.gridLayout.addWidget(self.kineticScrolling, 11, 1)

        # row 12
        self.gridLayout.addItem(QSpacerItem(20, 10,
                                            QSizePolicy.Policy.Minimum,
                                            QSizePolicy.Policy.Fixed), 12, 1)

        # row 13
        self.label_2 = QLabel(pref_dialog)
        font = self.label_2.font()
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setText(translate("Preferences", "Note editor default size:"))
        self.gridLayout.addWidget(self.label_2, 13, 1)

        # row 14
        self.label_3 = QLabel(pref_dialog)
        self.label_3.setText(translate("Preferences", "Width:"))
        self.gridLayout.addWidget(self.label_3, 14, 1)
        self.sizeSpinWidth = QSpinBox(pref_dialog)
        self.sizeSpinWidth.setMaximum(65536)
        self.sizeSpinWidth.setSingleStep(5)
        self.sizeSpinWidth.setValue(335)
        self.gridLayout.addWidget(self.sizeSpinWidth, 14, 2)

        # row 15
        self.label_4 = QLabel(pref_dialog)
        self.label_4.setText(translate("Preferences", "Height:"))
        self.gridLayout.addWidget(self.label_4, 15, 1)
        self.sizeSpinHeight = QSpinBox(pref_dialog)
        self.sizeSpinHeight.setMaximum(65536)
        self.sizeSpinHeight.setSingleStep(5)
        self.sizeSpinHeight.setValue(250)
        self.gridLayout.addWidget(self.sizeSpinHeight, 15, 2)

        # row 16
        self.gridLayout.addItem(QSpacerItem(20, 10,
                                            QSizePolicy.Policy.Minimum,
                                            QSizePolicy.Policy.Fixed), 16, 1)

        # row 17
        self.label_5 = QLabel(pref_dialog)
        font = self.label_5.font()
        font.setBold(True)
        self.label_5.setFont(font)
        self.label_5.setText(translate("Preferences", "Note editor default font:"))
        self.gridLayout.addWidget(self.label_5, 17, 1)

        # row 18
        self.fontComboBox = QFontComboBox(pref_dialog)
        self.gridLayout.addWidget(self.fontComboBox, 18, 1)
        self.fontSizeComboBox = QComboBox(pref_dialog)
        self.fontSizeComboBox.setSizePolicy(QSizePolicy.Policy.Minimum,
                                            QSizePolicy.Policy.Fixed)
        self.gridLayout.addWidget(self.fontSizeComboBox, 18, 2)

        # row 19
        self.spellCheckBox = QCheckBox(pref_dialog)
        self.spellCheckBox.setText(translate(
            "Preferences", "Check spelling while typing"))
        self.spellCheckBox.setToolTip(translate(
            "Preferences", "Underline misspelled words with Hunspell"))
        self.gridLayout.addWidget(self.spellCheckBox, 19, 1, 1, 2)

        # row 20
        self.spellLanguageLabel = QLabel(pref_dialog)
        self.spellLanguageLabel.setText(translate(
            "Preferences", "Dictionary:"))
        self.gridLayout.addWidget(self.spellLanguageLabel, 20, 1)
        self.spellLanguageComboBox = QComboBox(pref_dialog)
        self.gridLayout.addWidget(self.spellLanguageComboBox, 20, 2)

        # row 21
        self.buttonBox = QDialogButtonBox(pref_dialog)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel
                                         | QDialogButtonBox.StandardButton.Ok)
        self.gridLayout.addWidget(self.buttonBox, 21, 2)

        self.buttonBox.accepted.connect(pref_dialog.accept)
        self.buttonBox.rejected.connect(pref_dialog.reject)

    def retranslateUi(self, pref_dialog: QDialog):
        pass
        self.gridLayout.addWidget(self.dontQuit, 7, 1, 1, 2)

        # row 8
        self.openNotesFromTray = QCheckBox(pref_dialog)
        self.openNotesFromTray.setText(translate("Preferences", "&Open notes from tray"))
        self.openNotesFromTray.setToolTip(translate(
            "Preferences",
            "<html><head/><body><p>Notes can be opened from the tray icon "
            "when the application is minimized to the system tray</p>"
            "</body></html>"))
        self.gridLayout.addWidget(self.openNotesFromTray, 8, 1, 1, 2)

        # row 9
        self.silentStart = QCheckBox(pref_dialog)
        self.silentStart.setText(translate("Preferences", "&Hide main window at startup"))
        self.silentStart.setToolTip(translate(
            "Preferences",
            "Do not show the main interface and notes on startup.\n"
            "(Minimized to tray icon)"))
        self.gridLayout.addWidget(self.silentStart, 9, 1)

        # row 10
        self.showSource = QCheckBox(pref_dialog)
        self.showSource.setText(translate("Preferences", "&Show \"Show Source\" menu entry"))
        self.gridLayout.addWidget(self.showSource, 10, 1)