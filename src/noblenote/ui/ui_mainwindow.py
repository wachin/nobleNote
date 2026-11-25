# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""MainWindow form (equivalent of ui/mainwindow.ui)."""

from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (QGridLayout, QMainWindow, QMenu, QMenuBar,
                             QStatusBar, QToolBar, QWidget)

from ..resources import icon


class Ui_MainWindow:
    def setupUi(self, main_window: QMainWindow):
        main_window.setWindowTitle("nobleNote")
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
        self.menuFile.setTitle("&File")
        self.menu_Open_recent = QMenu(self.menuFile)
        self.menu_Open_recent.setTitle("Open recent")
        self.menu_Edit = QMenu(self.menubar)
        self.menu_Edit.setTitle("&Edit")
        self.menu_View = QMenu(self.menubar)
        self.menu_View.setTitle("&View")
        self.menu_Settings = QMenu(self.menubar)
        self.menu_Settings.setTitle("&Settings")
        self.menu_Help = QMenu(self.menubar)
        self.menu_Help.setTitle("&Help")

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
        self.actionQuitFileMenu.setText("&Quit")
        self.actionQuitFileMenu.setShortcut(QKeySequence("Ctrl+Q"))

        self.actionImport = QAction(main_window)
        self.actionImport.setText("&Import")

        self.actionConfigure = QAction(icon("preferences"), "&Configure...", main_window)
        self.actionConfigure.setShortcut(QKeySequence("Ctrl+."))

        self.actionTrash = QAction(icon("trash"), "&Trash", main_window)
        self.actionTrash.setShortcut(QKeySequence("Ctrl+Shift+T"))

        self.actionAbout = QAction("&About", main_window)

        self.actionShowToolbar = QAction(main_window)
        self.actionShowToolbar.setText("&Show toolbar")
        self.actionShowToolbar.setCheckable(True)

        self.actionHistory = QAction(main_window)
        self.actionHistory.setText("&History")
        self.actionHistory.setShortcut(QKeySequence("Ctrl+Shift+H"))
        self.actionHistory.setVisible(False)

        self.actionNew_folder = QAction(icon("newFolder"), "&New notebook", main_window)
        self.actionNew_folder.setShortcut(QKeySequence("Ctrl+N"))

        self.actionRename_folder = QAction(icon("renameFolder"), "&Rename notebook", main_window)
        self.actionRename_folder.setShortcut(QKeySequence("Ctrl+R"))

        self.actionDelete_folder = QAction(icon("deleteFolder"), "&Delete notebook", main_window)
        self.actionDelete_folder.setShortcut(QKeySequence("Ctrl+D"))

        self.actionNew_note = QAction(icon("newNote"), "&New note", main_window)
        self.actionNew_note.setShortcut(QKeySequence("Ctrl+Shift+N"))

        self.actionRename_note = QAction(icon("renameNote"), "&Rename note", main_window)
        self.actionRename_note.setEnabled(False)
        self.actionRename_note.setShortcut(QKeySequence("Ctrl+Shift+R"))
        self.actionRename_note.setText("&Rename note")

        self.actionDelete_note = QAction(icon("deleteNote"), "&Delete note", main_window)
        self.actionDelete_note.setEnabled(False)
        self.actionDelete_note.setShortcut(QKeySequence("Ctrl+Shift+D"))

        self.action_Cut = QAction("&Cut", main_window)
        self.action_Cut.setShortcut(QKeySequence("Ctrl+X"))

        self.action_Paste = QAction("&Paste", main_window)
        self.action_Paste.setEnabled(False)
        self.action_Paste.setShortcut(QKeySequence("Ctrl+V"))

        self.actionA = QAction("a", main_window)