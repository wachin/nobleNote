# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""MainWindow form (equivalent of ui/mainwindow.ui)."""

from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (QGridLayout, QMainWindow, QMenu, QMenuBar,
                             QStatusBar, QToolBar, QWidget)

from ..resources import icon
from PyQt6.QtCore import QCoreApplication

_translate = QCoreApplication.translate


class Ui_MainWindow:
    def setupUi(self, main_window: QMainWindow):
        main_window.setWindowTitle(_translate("MainWindow", "nobleNote"))
        main_window.setWindowIcon(icon("nobleNote"))
        main_window.setToolButtonStyle(__import__("PyQt6.QtCore", fromlist=["Qt"])
                                       .Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        # ------------------------------------------------ central widget
        self.centralwidget = QWidget(main_window)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        main_window.setCentralWidget(self.centralwidget)

        main_window.statusbar = QStatusBar(main_window)
        main_window.setStatusBar(main_window.statusbar)

        # ------------------------------------------------ menu bar
        self.menubar = QMenuBar(main_window)
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setTitle(_translate("MainWindow", "&File"))
        self.menu_Open_recent = QMenu(self.menuFile)
        self.menu_Open_recent.setTitle(_translate("MainWindow", "Open recent"))
        self.menu_Edit = QMenu(self.menubar)
        self.menu_Edit.setTitle(_translate("MainWindow", "&Edit"))
        self.menu_View = QMenu(self.menubar)
        self.menu_View.setTitle(_translate("MainWindow", "&View"))
        self.menu_Settings = QMenu(self.menubar)
        self.menu_Settings.setTitle(_translate("MainWindow", "&Settings"))
        self.menu_Help = QMenu(self.menubar)
        self.menu_Help.setTitle(_translate("MainWindow", "&Help"))

        self.menuFile.addAction(self.menu_Open_recent.menuAction())
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionImport)
        self.menuFile.addAction(self.actionTrash)
        self.menuFile.addAction(self.actionQuitFileMenu)

        self.menu_Edit.addAction(self.actionNew_folder)
        self.menu_Edit.addAction(self.actionRename_folder)
        self.menu_Edit.addAction(self.actionDelete_folder)
        self.menu_Edit.addSeparator()
        self.menu_Edit.addAction(self.actionNew_note)
        self.menu_Edit.addAction(self.actionRename_note)
        self.menu_Edit.addAction(self.actionDelete_note)
        self.menu_Edit.addSeparator()
        self.menu_Edit.addAction(self.action_Cut)
        self.menu_Edit.addAction(self.action_Paste)

        self.menu_View.addAction(self.actionShowToolbar)
        self.menu_View.addAction(self.actionHistory)

        self.menu_Settings.addAction(self.actionConfigure)
        self.menu_Help.addAction(self.actionAbout)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menu_Edit.menuAction())
        self.menubar.addAction(self.menu_View.menuAction())
        self.menubar.addAction(self.menu_Settings.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())
        main_window.setMenuBar(self.menubar)

        # ------------------------------------------------ toolbar
        self.tool_bar = QToolBar("tool_bar", main_window)
        self.tool_bar.setObjectName("tool_bar")
        main_window.addToolBar(self.tool_bar)

    def retranslateUi(self, main_window: QMainWindow):
        pass

    def _make_actions(self, main_window: QMainWindow):
        # actions must exist before setupUi() adds them to the menus
        self.actionQuitFileMenu = QAction(main_window)
        self.actionQuitFileMenu.setText(_translate("MainWindow", "&Quit"))
        self.actionQuitFileMenu.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+Q")))

        self.actionImport = QAction(main_window)
        self.actionImport.setText(_translate("MainWindow", "&Import"))

        self.actionConfigure = QAction(icon("preferences"), _translate("MainWindow", "&Configure..."), main_window)
        self.actionConfigure.setShortcut(QKeySequence("Ctrl+."))

        self.actionTrash = QAction(icon("trash"), _translate("MainWindow", "&Trash"), main_window)
        self.actionTrash.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+Shift+T")))

        self.actionAbout = QAction(_translate("MainWindow", "&About"), main_window)

        self.actionShowToolbar = QAction(main_window)
        self.actionShowToolbar.setText(_translate("MainWindow", "&Show toolbar"))
        self.actionShowToolbar.setCheckable(True)

        self.actionHistory = QAction(main_window)
        self.actionHistory.setText(_translate("MainWindow", "&History"))
        self.actionHistory.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+Shift+H")))
        self.actionHistory.setVisible(False)

        self.actionNew_folder = QAction(icon("newFolder"), _translate("MainWindow", "&New notebook"), main_window)
        self.actionNew_folder.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+N")))

        self.actionRename_folder = QAction(icon("renameFolder"), _translate("MainWindow", "&Rename notebook"), main_window)
        self.actionRename_folder.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+R")))

        self.actionDelete_folder = QAction(icon("deleteFolder"), _translate("MainWindow", "&Delete notebook"), main_window)
        self.actionDelete_folder.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+D")))

        self.actionNew_note = QAction(icon("newNote"), _translate("MainWindow", "&New note"), main_window)
        self.actionNew_note.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+Shift+N")))

        self.actionRename_note = QAction(icon("renameNote"), _translate("MainWindow", "&Rename note"), main_window)
        self.actionRename_note.setEnabled(False)
        self.actionRename_note.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+Shift+R")))
        self.actionRename_note.setText(_translate("MainWindow", "&Rename note"))

        self.actionDelete_note = QAction(icon("deleteNote"), _translate("MainWindow", "&Delete note"), main_window)
        self.actionDelete_note.setEnabled(False)
        self.actionDelete_note.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+Shift+D")))

        self.action_Cut = QAction(_translate("MainWindow", "&Cut"), main_window)
        self.action_Cut.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+X")))

        self.action_Paste = QAction(_translate("MainWindow", "&Paste"), main_window)
        self.action_Paste.setEnabled(False)
        self.action_Paste.setShortcut(QKeySequence(_translate("MainWindow", "Ctrl+V")))

        self.actionA = QAction(_translate("MainWindow", "a"), main_window)