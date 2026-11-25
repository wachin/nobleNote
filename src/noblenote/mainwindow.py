# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""The main window of the note taking application."""

import os
import shutil
import sys
import weakref
from pathlib import Path

from PyQt6.QtCore import (QDir, QFileInfo, QFileSystemWatcher, QModelIndex,
                          QPoint, QSettings, QStandardPaths, Qt,
                          QItemSelectionModel)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QFileDialog,
                             QInputDialog, QListView,
                             QMainWindow, QMenu, QMessageBox, QScroller,
                             QSplitter, QSystemTrayIcon, QTextEdit)

from .backup import Backup
from .fileiconprovider import FileIconProvider
from .filesystemmodel import FileSystemModel
from .findfilemodel import FindFileModel
from .findfilesystemmodel import FindFileSystemModel
from .htmlnotereader import HtmlNoteReader
from .lineedit import LineEdit
from .note import Note
from .noteimporter import NoteImporter
from .preferences import Preferences
from .resources import icon
from .systemtraycreator import SystemTrayCreator
from .textsearchtoolbar import TextSearchToolbar
from .ui.ui_mainwindow import Ui_MainWindow
from .version import APP_VERSION

# For the C++ version this was compiled in conditionally:
# #define NO_SYSTEM_TRAY_ICON
USE_SYSTEM_TRAY = True


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self._make_actions(self)
        self.setupUi(self)

        self.file_watcher = QFileSystemWatcher(self)
        self.create_and_update_recent()

        # tray icon
        self.minimize_restore_action = QAction(self.tr("&Restore"), self)
        self.action_quit_systray_menu = QAction(self.tr("&Quit"), self)

        self.t_icon = None
        self.i_menu = None
        self.icon_creator = None
        if USE_SYSTEM_TRAY:
            self.t_icon = QSystemTrayIcon(self)
            self.t_icon.setIcon(icon("nobleNote"))
            self.t_icon.show()

            self.i_menu = QMenu(self)
            # the context menu needs at least one action else right click
            # will not work
            self.i_menu.addAction(self.minimize_restore_action)
            self.i_menu.addAction(self.action_quit_systray_menu)
            self.t_icon.setContextMenu(self.i_menu)

            self.icon_creator = SystemTrayCreator(self)

            if QSettings().value("open_notes_from_tray", False):
                self.icon_creator.noteClicked.connect(self.open_one_note)
                self.i_menu.aboutToShow.connect(self._populate_tray_menu_from_notes)

        # toolbar
        self.tool_bar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.tool_bar.addAction(self.actionNew_folder)
        self.tool_bar.addAction(self.actionRename_folder)
        self.tool_bar.addAction(self.actionDelete_folder)
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.actionNew_note)
        self.tool_bar.addAction(self.actionRename_note)
        self.tool_bar.addAction(self.actionDelete_note)
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.actionHistory)
        self.tool_bar.addAction(self.actionTrash)
        self.tool_bar.addAction(self.actionConfigure)
        toolbar_visible = bool(QSettings().value("mainwindow_toolbar_visible", True))
        self.actionShowToolbar.setChecked(toolbar_visible)
        self.tool_bar.setVisible(toolbar_visible)
# ------------------------------------------------------------------
        # search line edits
        self.search_text = LineEdit(self)
        self.search_text.setPlaceholderText(self.tr("Type to search for notes"))
        self.gridLayout.addWidget(self.search_text, 2, 0)

        self.splitter = QSplitter(self.centralwidget)
        self.gridLayout.addWidget(self.splitter, 3, 0)

        # icon providers
        self.folder_icon_provider = FileIconProvider()
        self.note_icon_provider = FileIconProvider()

        self.folder_model = FindFileSystemModel(self)
        self.folder_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.folder_fs_model = FileSystemModel(self)
        self.folder_fs_model.setFilter(QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot)
        self.folder_fs_model.setReadOnly(False)
        self.folder_fs_model.setIconProvider(self.folder_icon_provider)
        self.folder_model.setSourceModel(self.folder_fs_model)

        self.note_fs_model = FileSystemModel(self)
        self.note_fs_model.setFilter(QDir.Filter.Files)
        self.note_fs_model.setReadOnly(False)
        self.note_fs_model.setIconProvider(self.note_icon_provider)

        self.find_note_model = FindFileModel(self)

        self.note_model = FindFileSystemModel(self)
        self.note_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.note_model.setSourceModel(self.note_fs_model)

        self.folder_view = QListView(self.splitter)
        self.note_view = QListView(self.splitter)

        self.folder_view.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.note_view.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel)

        for list_view in (self.folder_view, self.note_view):
            list_view.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu)
            list_view.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
            list_view.viewport().setAcceptDrops(True)
            list_view.setDropIndicatorShown(True)
            list_view.setDefaultDropAction(Qt.DropAction.CopyAction)
            list_view.setSelectionBehavior(
                QAbstractItemView.SelectionBehavior.SelectRows)

        self.note_view.setDragEnabled(True)
        self.folder_view.setDragEnabled(False)

        if bool(QSettings().value("kinetic_scrolling", False)):
            QScroller.grabGesture(self.folder_view.viewport(),
                                  QScroller.GestureType.LeftMouseButtonGesture)
            QScroller.grabGesture(self.note_view.viewport(),
                                  QScroller.GestureType.LeftMouseButtonGesture)

        self.folder_view.setModel(self.folder_model)
        self.note_view.setModel(self.note_model)
        self.folder_view.setEditTriggers(
            QAbstractItemView.EditTrigger.EditKeyPressed)
        self.note_view.setEditTriggers(
            QAbstractItemView.EditTrigger.EditKeyPressed)
        self.note_view.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)

        self.note_importer = NoteImporter(self)

        self.make_standard_paths()

        self.actionRename_note.setIconVisibleInMenu(False)

        # open notes collection (weak references)
        self.open_notes = []
        self.shortcut_note_list = []
        self.to_be_renamed_notebook = ""

        self._connect_signals()

        self.write_backup_dir_path()
# ------------------------------------------------------------------
    def _connect_signals(self):
        self.folder_view.activated.connect(self.folder_activated_index)
        self.folder_view.clicked.connect(self.folder_activated_index)
        self.folder_view.selectionModel().selectionChanged.connect(
            self.folder_activated_selection)
        self.folder_view.itemDelegate().closeEditor.connect(
            self.folder_rename_finished)
        self.folder_view.customContextMenuRequested.connect(
            self.show_context_menu_folder)
        self.search_text.textChanged.connect(self.find)

        self.note_fs_model.fileRenamed.connect(self.note_rename_finished)
        self.file_watcher.fileChanged.connect(self.create_and_update_recent)

        self.note_view.activated.connect(self.open_note)
        self.note_view.customContextMenuRequested.connect(
            self.show_context_menu_note)
        self.note_view.selectionModel().selectionChanged.connect(
            self.note_activated_selection)
        self.note_view.activated.connect(self.note_activated_index)
        self.note_view.clicked.connect(self.note_activated_index)
        self.note_view.selectionModel().selectionChanged.connect(
            self.enable_note_menu)

        if USE_SYSTEM_TRAY:
            self.t_icon.activated.connect(self.icon_activated)
            self.minimize_restore_action.triggered.connect(self.tray_actions)

        self.actionImport.triggered.connect(self.note_importer.importDialog)
        self.actionQuitFileMenu.triggered.connect(self.quit)
        self.actionTrash.triggered.connect(self.show_backup_window)
        if USE_SYSTEM_TRAY:
            self.action_quit_systray_menu.triggered.connect(self.quit)
        self.actionNew_folder.triggered.connect(self.new_folder)
        self.actionRename_folder.triggered.connect(self.rename_folder)
        self.actionDelete_folder.triggered.connect(self.remove_folder)
        self.actionNew_note.triggered.connect(self.new_note)
        self.actionRename_note.triggered.connect(self.rename_note)
        self.actionDelete_note.triggered.connect(self.remove_note)
        self.action_Cut.triggered.connect(self.get_cut_files)
        self.action_Paste.triggered.connect(self.paste_files)
        self.actionShowToolbar.toggled.connect(self.tool_bar.setVisible)
        self.tool_bar.visibilityChanged.connect(self.actionShowToolbar.setChecked)

        self.actionConfigure.triggered.connect(self.show_preferences)
        self.actionAbout.triggered.connect(self.about)
        self.search_text.sendCleared.connect(self.select_folder)

        # moving a note with drag and drop removes it from the recent files
        self.folder_fs_model.droppedAFile.connect(
            self.create_and_update_recent)
        self.folder_fs_model.droppedAFile.connect(
            lambda: self.find(False) if self.search_text.text() else None)

    # ------------------------------------------------------------------
    # notes collection helpers (replacement for QPointer<QWidget> list)
    def _add_open_note(self, note):
        self.open_notes.append(weakref.ref(note))
        note.destroyed.connect(lambda: self._prune_open_notes())

    def _prune_open_notes(self):
        self.open_notes = [ref for ref in self.open_notes if ref() is not None]

    def _notes(self):
        """Yield the still-alive Note widgets, pruning the dead references."""
        alive = []
        for ref in self.open_notes:
            widget = ref()
            if widget is not None:
                alive.append(ref)
                yield widget
        self.open_notes = alive

    def select_folder(self):
        if not self.folder_view.selectionModel().selectedIndexes():
            return
        self.folder_activated_index(
            self.folder_view.selectionModel().selectedIndexes()[0])

    def write_backup_dir_path(self):
        """Generates a backup path according to OS and portability."""
        if not bool(QSettings().value("isPortable", False)):  # not portable
            suffix = str(QSettings().value("root_path", ""))
            suffix = suffix.replace("/", "_")
            locations = QStandardPaths.standardLocations(
                QStandardPaths.StandardLocation.AppLocalDataLocation)
            backup_path = locations[0] if locations else ""
            # reduce an extraordinarily long path, replaces
            # .../nobleNote/nobleNote/... with .../nobleNote/...
            double_ns = "/nobleNote/nobleNote"
            single_ns = "/nobleNote"
            backup_path = QDir.toNativeSeparators(backup_path)
            if double_ns in backup_path.replace("\\", "/"):
                backup_path = backup_path.replace(double_ns, single_ns)
        else:  # portable
            backup_path = QApplication.instance().applicationDirPath()

        QSettings().setValue("backup_dir_path",
                             backup_path + "/" + "backups" + suffix)

    def change_root_index(self):
        for note in list(self._notes()):
            note.close()
        self.open_notes.clear()
        self.write_backup_dir_path()
        self.make_standard_paths()

    def make_standard_paths(self):
        root_path = str(QSettings().value("root_path", ""))
        if not Path(root_path).exists():
            Path(root_path).mkdir(parents=True, exist_ok=True)

        backup_path = str(QSettings().value("backup_dir_path", ""))
        if not Path(backup_path).exists():
            Path(backup_path).mkdir(parents=True, exist_ok=True)

        self.folder_view.setRootIndex(self.folder_model.setRootPath(root_path))

        # make sure there is at least one folder
        dir_list = QDir(root_path).entryList(QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot)
        if not dir_list:
            default_dir_name = self.tr("default")
            QDir(root_path).mkdir(default_dir_name)
            self.note_view.setRootIndex(
                self.note_model.setRootPath(root_path + "/" + default_dir_name))
        else:
            self.note_view.setRootIndex(
                self.note_model.setRootPath(root_path + "/" + dir_list[0]))

        # select the first folder
        if dir_list:
            self.folder_view.selectionModel().select(
                self.folder_model.index(root_path + "/" + dir_list[0]),
                QItemSelectionModel.SelectionFlag.Select)

    def enable_note_menu(self, selected, deselected):
        self.actionRename_note.setDisabled(not selected.indexes())
        self.actionDelete_note.setDisabled(not selected.indexes())

    def show_preferences(self):
        if getattr(self, "_pref", None) is None or self._pref is None:
            self._pref = Preferences(self)
            self._pref.pathChanged.connect(self.change_root_index)
            self._pref.kineticScrollingEnabledChanged.connect(
                self.set_kinetic_scrolling_enabled)
            self._pref.recentCountChanged.connect(self.create_and_update_recent)
            self._pref.accepted.connect(self.settings_accepted)
        self._pref.show()

    def settings_accepted(self):
        if not USE_SYSTEM_TRAY:
            return
        self.icon_creator.disconnect()
        if QSettings().value("open_notes_from_tray", False):
            self.icon_creator.noteClicked.connect(self.open_one_note)
            try:
                self.i_menu.aboutToShow.disconnect()
            except TypeError:
                pass
            self.i_menu.aboutToShow.connect(self._populate_tray_menu_from_notes)
        else:
            self.i_menu.clear()
            try:
                self.i_menu.aboutToShow.disconnect()
            except TypeError:
                pass
            self.i_menu.addAction(self.minimize_restore_action)
            self.i_menu.addAction(self.action_quit_systray_menu)

    def folder_rename_finished(self, editor, hint):
        selected = self.folder_view.selectionModel().selectedRows()
        if not selected:
            return
        new_notebook_name = str(
            selected[0].data(Qt.ItemDataRole.DisplayRole) or "")
        recent = self._recent_list()
        for i in range(len(recent)):
            file_name = QFileInfo(recent[i]).fileName()
            stripped_path = recent[i]
            stripped_path = stripped_path[:-(len(file_name)
                                           + len(self.to_be_renamed_notebook) + 1)]
            if self.to_be_renamed_notebook not in stripped_path:
                recent[i] = stripped_path + new_notebook_name + "/" + file_name
        QSettings().setValue("Recent_notes", recent)

        # map EndEditHint enum to a Python int comparison
        from PyQt6.QtWidgets import QAbstractItemDelegate
        if not selected[0].isValid() or hint is None:
            return
        try:
            is_revert = (hint == QAbstractItemDelegate.EndEditHint.RevertModelCache)
        except (AttributeError, TypeError):
            is_revert = False
        if not is_revert:  # canceled editing
            curr_folder_path = self.folder_model.filePath(
                self.folder_view.selectionModel().selectedRows()[0])
            self.folder_model.sort(0)
            self.folder_view.setCurrentIndex(
                self.folder_model.index(curr_folder_path))

            # set current folder
            self.note_model.setSourceModel(self.note_fs_model)
            self.note_view.setRootIndex(
                self.note_model.setRootPath(curr_folder_path))

        self.folder_view.scrollTo(
            self.folder_view.selectionModel().selectedRows()[0])

    def closeEvent(self, event):
        if bool(QSettings().value("dont_quit_on_close", False)):
            self.hide()
        else:
            QSettings().setValue("mainwindow_size", self.saveGeometry())
            QSettings().setValue("splitter", self.splitter.saveState())

            # close any open note windows (normally not children of this)
            for note in list(self._notes()):
                note.close()
                # close() runs the closeEvent which removes the note from the
                # open notes list, so re-add it here
                if note.note_descriptor():
                    Note.add_to_open_note_list(note.note_descriptor().file_path())
            QApplication.setQuitOnLastWindowClosed(True)

        super().closeEvent(event)

    def quit(self):
        QSettings().setValue("mainwindow_size", self.saveGeometry())
        QSettings().setValue("mainwindow_toolbar_visible",
                             self.actionShowToolbar.isChecked())
        QApplication.setQuitOnLastWindowClosed(True)
        QApplication.closeAllWindows()
        QApplication.quit()

    def note_is_open(self, path: str) -> bool:
        win = self.note_window(path)
        if win is not None:
            win.activateWindow()  # highlight the note window
            return True
        return False

    def note_window(self, file_path: str):
        uuid_ = HtmlNoteReader.uuid(file_path)
        for note in self._notes():
            if (note.note_descriptor() is not None
                    and note.note_descriptor().uuid() == uuid_
                    and uuid_ is not None):
                return note
            if uuid_ is None:
                if QFileInfo(note.note_descriptor().file_path()) == QFileInfo(file_path):
                    return note
        return None

    def open_note(self, index):
        self.open_all_notes()

    def open_all_notes(self):
        indexes = self.note_view.selectionModel().selectedRows()
        for ind in indexes:
            if not ind.isValid():
                ind = self.note_view.currentIndex()
            note_path = self.note_model.filePath(ind)
            if not QFileInfo(note_path).exists():
                QMessageBox.warning(self, self.tr("Note does not exist"),
                                    self.tr("The selected note cannot be opened "
                                            "because it has been moved or "
                                            "renamed!"))
                return
            self.open_one_note(note_path)

    def open_one_note(self, path: str):
        if self.note_is_open(path):
            return

        note = Note(path)
        self._add_open_note(note)
        note.setObjectName(path)
        Note.add_to_open_note_list(path)
        if bool(QSettings().value("kinetic_scrolling", False)):
            QScroller.grabGesture(note.text_edit().viewport(),
                                  QScroller.GestureType.LeftMouseButtonGesture)
        # only show the searchBar if the note contains the search text
        if self.note_model.sourceModel() is self.find_note_model:
            note.set_search_bar_text(self.search_text.text())
        note.show_after_loaded()

        recent_note_list = self._recent_list()
        if path in recent_note_list:
            recent_note_list.remove(path)
        recent_note_list.insert(0, path)
        while (len(recent_note_list)
               > int(QSettings().value("Number_of_recent_Notes", 5))):
            recent_note_list.pop()
        QSettings().setValue("Recent_notes", recent_note_list)
    def new_folder(self):
        path = self.folder_model.rootPath() + "/" + self.tr("new notebook")
        counter = 0
        while Path(path).exists():
            counter += 1
            path = self.folder_model.rootPath() + "/" + \
                self.tr("new notebook (%1)").replace("%1", str(counter))
        idx = self.folder_model.mkdir(self.folder_view.rootIndex(),
                                      QDir(path).dirName())
        if idx.isValid():
            self.folder_view.setCurrentIndex(idx)
            self.folder_view.edit(idx)  # 'open' for rename
        self.folder_model.sort(0)
        if self.folder_view.selectionModel().selectedRows():
            self.folder_view.scrollTo(
                self.folder_view.selectionModel().selectedRows()[0])

    def new_note(self):
        file_path = self.note_model.rootPath() + "/" + self.tr("new note")
        counter = 0
        while Path(file_path).exists():
            counter += 1
            file_path = self.note_model.rootPath() + "/" + \
                self.tr("new note (%1)").replace("%1", str(counter))
        try:
            Path(file_path).touch()
        except OSError:
            return
        idx = self.note_model.index(file_path)
        if idx.isValid():
            self.note_view.setCurrentIndex(idx)
            self.note_view.edit(idx)  # 'open' for rename
        self.note_view.model().sort(0)
        if self.note_view.selectionModel().selectedRows():
            self.note_view.scrollTo(
                self.note_view.selectionModel().selectedRows()[0])

    def rename_folder(self):
        if self.folder_view.selectionModel().selectedRows():
            self.folder_view.edit(
                self.folder_view.selectionModel().selectedRows()[0])
            self.to_be_renamed_notebook = str(
                self.folder_view.selectionModel().selectedRows()[0].data(
                    Qt.ItemDataRole.DisplayRole) or "")

    def rename_note(self):
        if self.note_view.selectionModel().selectedRows():
            self.note_view.edit(self.note_view.selectionModel().selectedRows()[0])

    def remove_folder(self):
        if not self.folder_view.selectionModel().selectedRows():
            return

        root_path = str(QSettings().value("root_path", ""))
        dir_list = QDir(root_path).entryList(QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot)

        # keep at least one folder
        if len(dir_list) == 1:
            QMessageBox.information(
                self, self.tr("Notebook could not be deleted"),
                self.tr("The notebook could not be deleted because one "
                        "notebook must remain"))
            return

        idx = self.folder_view.selectionModel().selectedRows()[0]

        # remove empty folders without prompt else show a yes/abort message box
        if not self.folder_model.rmdir(idx):  # folder not empty
            answer = QMessageBox.warning(
                self, self.tr("Delete Notebook"),
                self.tr('Are you sure you want to delete the notebook "%1" '
                        'and move all containing notes to the trash?')
                .replace("%1", self.folder_model.fileName(idx)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Abort)
            if answer != QMessageBox.StandardButton.Yes:
                return

            # list all files
            path = self.folder_model.filePath(idx)
            file_list = QDir(path).entryList(QDir.Filter.NoDotAndDotDot | QDir.Filter.Dirs | QDir.Filter.Files)

            indexes = []
            for file_name in file_list:
                indexes.append(self.folder_model.index(path + "/" + file_name))

            self.folder_model.copyNotesToBackupDir(indexes)
            self.folder_model.removeList(indexes)

            # try to remove the (now empty?) folder again
            if not self.folder_model.rmdir(idx):
                QMessageBox.warning(
                    self, self.tr("Notebook could not be deleted"),
                    self.tr("The notebook could not be deleted because one or "
                            "more notes inside the notebook could not be "
                            "deleted."))
                return

    def set_kinetic_scrolling_enabled(self, enabled: bool):
        widgets = [self.note_view, self.folder_view]
        for note in self._notes():
            if hasattr(note, "text_edit"):
                widgets.append(note.text_edit())

        for widget in widgets:
            if widget is None:
                continue
            if enabled:
                QScroller.grabGesture(
                    widget.viewport(),
                    QScroller.GestureType.LeftMouseButtonGesture)
            else:
                QScroller.ungrabGesture(widget.viewport())

    def show_context_menu_folder(self, pos: QPoint):
        global_pos = self.folder_view.mapToGlobal(pos)
        menu = QMenu(self)
        if not self.folder_view.indexAt(pos).isValid():
            menu.addAction(self.actionNew_folder)
        if self.folder_view.indexAt(pos).isValid():
            menu.addAction(self.actionRename_folder)
            menu.addAction(self.actionDelete_folder)
            if self.shortcut_note_list:
                menu.addSeparator()
                menu.addAction(self.action_Paste)
        menu.exec(global_pos)

    def show_context_menu_note(self, pos: QPoint):
        global_pos = self.note_view.mapToGlobal(pos)
        menu = QMenu(self)

        if (not self.note_view.indexAt(pos).isValid()
                and not (self.note_model.sourceModel() is self.find_note_model)):
            menu.addAction(self.actionNew_note)
            menu.addSeparator()
            menu.addAction(self.action_Paste)
        if self.note_view.indexAt(pos).isValid():
            if self.note_view.selectionModel().selectedRows().count() == 1:
                menu.addAction(self.actionRename_note)
            else:
                open_all = QAction(self.tr("&Open notes"), menu)
                open_all.triggered.connect(self.open_all_notes)
                menu.addAction(open_all)
            menu.addAction(self.actionDelete_note)

            # show source code menu entry
            if (bool(QSettings().value("show_source", False))
                    and len(self.note_view.selectionModel().selectedRows()) == 1):
                show_source = QAction(self.tr("Show &Source"), menu)
                show_source.triggered.connect(self.open_note_source)
                menu.addAction(show_source)
            menu.addSeparator()
            menu.addAction(self.action_Cut)
        menu.exec(global_pos)

    def get_cut_files(self):
        self.shortcut_note_list.clear()

        if self.note_view.hasFocus():
            selected = self.note_view.selectionModel().selectedRows()
            for idx in selected:
                self.shortcut_note_list.append(self.note_model.filePath(idx))

        if self.shortcut_note_list:
            self.action_Paste.setEnabled(True)

        self.note_icon_provider = FileIconProvider()
        self.note_icon_provider.set_cut_files(self.shortcut_note_list)
        self.note_fs_model.setIconProvider(self.note_icon_provider)

        for idx in self.note_view.selectionModel().selectedRows():
            self.note_view.update(idx)

    def paste_files(self):
        if not self.shortcut_note_list:
            return

        copy_error_files = ""
        selected_rows = self.folder_view.selectionModel().selectedRows()
        if not selected_rows:
            return
        target_dir = self.folder_model.filePath(selected_rows[0])
        for note_path in self.shortcut_note_list:
            old_path = Path(note_path)
            new_path = Path(target_dir) / old_path.name
            try:
                shutil.copyfile(str(old_path), str(new_path))
                old_path.unlink(missing_ok=True)  # cut semantics
            except OSError:
                copy_error_files += '"%s"\n' % note_path

        if copy_error_files:
            QMessageBox.critical(
                self, self.tr("Copy error"),
                self.tr("Notes of the same names already exist in this "
                        "notebook:\n\n%1")
                .replace("%1", QDir.toNativeSeparators(copy_error_files)))
        self.shortcut_note_list.clear()
        self.action_Paste.setDisabled(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            if self.note_view.hasFocus():
                self.remove_note()
            if self.folder_view.hasFocus():
                self.remove_folder()

        if event.matches(QKeySequence.StandardKey.Cut):
            self.get_cut_files()
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste_files()
        if event.key() == Qt.Key.Key_Escape:
            self.shortcut_note_list.clear()
            self.note_icon_provider = FileIconProvider()
            self.note_fs_model.setIconProvider(self.note_icon_provider)

            rows = set()
            i = 0
            while self.note_view.indexAt(QPoint(0, i)).isValid():
                rows.add(self.note_view.indexAt(QPoint(0, i)))
                i += 1
            for index in rows:
                self.note_view.update(index)

        super().keyPressEvent(event)

    def about(self):
        version = APP_VERSION
        app_name = QApplication.instance().applicationName() or "nobleNote"
        html = self.tr("<h1>{0} version {1}</h1>"
                       "<p><b>{0}</b> is a note taking application</p>"
                       "<p>Copyright © 2020 Christian Metscher</p>"
                       "<p>This is the PyQt6 port of nobleNote.</p>"
                       "<p>THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT "
                       "WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING "
                       "BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
                       "FITNESS FOR A PARTICULAR PURPOSE AND "
                       "NONINFRINGEMENT.</p>"
                       "<p>PyQt6</p>").format(app_name, version)
        QMessageBox.about(self, self.tr("About ") + app_name, html)

    def remove_note(self):
        if not self.note_view.selectionModel().selectedRows():
            return

        names = ""
        file_names = self.note_model.fileNames(
            self.note_view.selectionModel().selectedRows())
        for name in file_names:
            names += '"%s"\n' % name

        num_notes = len(self.note_view.selectionModel().selectedRows())
        selected = self.note_view.selectionModel().selectedRows()

        if self.note_model.allSizeZero(selected):
            # zero size files do not go to the trash
            title = self.tr("Deleting notes")
            text = self.tr("Are you sure you want to permanently delete the "
                           "selected notes?")
        elif num_notes > 1:
            title = self.tr("Delete Multiple Notes")
            text = (self.tr("Are you sure you want to move these %1 notes to "
                            "the trash?\n\n%2")
                    .replace("%1", str(num_notes)).replace("%2", names))
        else:
            title = self.tr("Delete Note")
            text = self.tr("Are you sure you want to move the note %1 to the "
                           "trash?").replace("%1", names)

        if QMessageBox.warning(self, title, text,
                               QMessageBox.StandardButton.Yes
                               | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return

        selected_rows = self.note_view.selectionModel().selectedRows()
        # try to copy the files to be removed into the backup folder
        self.note_model.copyNotesToBackupDir(selected_rows)
        self.note_model.removeList(selected_rows)
        self.create_and_update_recent()

    def create_and_update_recent(self):
        self.menu_Open_recent.clear()
        recent_file_paths = self._recent_list()

        # remove all nonexisting note paths
        cleaned = []
        for path in recent_file_paths:
            if Path(path).exists():
                cleaned.append(path)
        recent_file_paths = cleaned

        # remove note paths that exceed the count from the preferences
        while (len(recent_file_paths)
               > int(QSettings().value("Number_of_recent_Notes", 5))):
            recent_file_paths.pop()
        QSettings().setValue("Recent_notes", recent_file_paths)

        self.file_watcher.addPaths(recent_file_paths)

        self.menu_Open_recent.setDisabled(not recent_file_paths)

        for path in recent_file_paths:
            recent_action = QAction(self.menu_Open_recent)
            recent_action.setText(QFileInfo(path).fileName())
            recent_action.setData(path)
            recent_action.triggered.connect(self.open_recent)
            self.menu_Open_recent.addAction(recent_action)

    def open_recent(self):
        action = self.sender()
        if action is None:
            return
        path = action.data()
        if not path:
            return
        if self.note_is_open(path):
            return
        self.open_one_note(path)

    def open_note_source(self):
        ind = self.note_view.currentIndex()
        file_path = self.note_model.filePath(ind)
        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return

        source_window = QMainWindow()
        source_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        text_edit = QTextEdit(source_window)
        text_edit.setReadOnly(True)
        text_edit.setPlainText(content)
        source_window.setCentralWidget(text_edit)

        if bool(QSettings().value("kinetic_scrolling", False)):
            QScroller.grabGesture(text_edit.viewport(),
                                  QScroller.GestureType.LeftMouseButtonGesture)

        search_bar = TextSearchToolbar(text_edit, source_window)
        source_window.addToolBar(search_bar)
        source_window.resize(Note.editor_size())

        self._add_open_note(source_window)
        source_window.show()

    def _recent_list(self) -> list:
        recent = QSettings().value("Recent_notes", [])
        if isinstance(recent, str):
            return [recent]
        return [str(r) for r in (recent or [])]

    def note_rename_finished(self, path: str, old_name: str, new_name: str):
        file_path = self.note_model.filePath(self.note_view.currentIndex())
        win = self.note_window(path + "/" + old_name)
        if win is not None:
            win.setWindowTitle(QFileInfo(path + "/" + new_name).baseName())

        self.note_view.model().sort(0)
        self.note_view.setCurrentIndex(self.note_model.index(file_path))
        if self.note_view.selectionModel().selectedRows():
            self.note_view.scrollTo(
                self.note_view.selectionModel().selectedRows()[0])

        old_path = path + "/" + old_name
        new_path = path + "/" + new_name
        recent = self._recent_list()
        for i in range(len(recent)):
            if os.path.normpath(recent[i]) == os.path.normpath(old_path):
                recent[i] = new_path
        QSettings().setValue("Recent_notes", recent)

    def folder_activated_index(self, selected):
        # clear the search line edit
        self.search_text.clear()

        self.actionNew_note.setEnabled(True)
        self.actionRename_note.setDisabled(True)
        self.actionDelete_note.setDisabled(True)

        self.note_model.setSourceModel(self.note_fs_model)
        self.note_view.setRootIndex(
            self.note_model.setRootPath(self.folder_model.filePath(selected)))

        self.note_view.viewport().setAcceptDrops(True)

    def folder_activated_selection(self, selected, deselected):
        if not selected.indexes():
            return
        self.folder_activated_index(selected.indexes()[0])

    def note_activated_index(self, selected):
        self.actionRename_note.setEnabled(True)
        self.actionDelete_note.setEnabled(True)

    def note_activated_selection(self, selected, deselected):
        if not selected.indexes():
            return
        self.note_activated_index(selected.indexes()[0])

    # ------------------------------------------------------------------
    def icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.tray_actions()

    def tray_actions(self):
        if self.isMinimized() or self.isHidden():
            self.showNormal()
        else:
            self.hide()

    def showEvent(self, event):
        self.minimize_restore_action.setText(self.tr("&Minimize"))
        if QSettings().contains("mainwindow_size"):
            data = QSettings().value("mainwindow_size", b"")
            if isinstance(data, (bytes, bytearray)):
                from PyQt6.QtCore import QByteArray
                data = QByteArray(data)
            self.restoreGeometry(data)
        if QSettings().contains("splitter"):
            data = QSettings().value("splitter", b"")
            if isinstance(data, (bytes, bytearray)):
                from PyQt6.QtCore import QByteArray
                data = QByteArray(data)
            self.splitter.restoreState(data)

        self.show_open_notes()
        super().showEvent(event)

    def show_open_notes(self):
        if not QSettings().contains("open_notes"):
            return
        notes = QSettings().value("open_notes", [])
        if isinstance(notes, str):
            notes = [notes]
        else:
            notes = list(notes or [])
        for path in notes:
            if not self.note_is_open(path) and Path(path).exists():
                note = Note(path)
                self._add_open_note(note)
                note.setObjectName(path)
                note.show_after_loaded()

    def hideEvent(self, event):
        self.minimize_restore_action.setText(self.tr("&Restore"))
        super().hideEvent(event)

    def show_backup_window(self):
        if getattr(self, "_backup", None) is None or self._backup is None:
            self._backup = Backup(self)

    def find(self, wait_cursor_enabled=True):
        # disable the note toolbar buttons because the current notes are not
        # longer visible with the findNoteModel
        self.note_view.viewport().setAcceptDrops(False)
        self.note_model.setSourceModel(self.find_note_model)
        self.note_model.clear()  # clear old search results
        self.note_model.findInFiles(self.search_text.text(),
                                    self.search_text.text(),
                                    self.folder_model.rootPath(),
                                    wait_cursor_enabled)
        self.actionNew_note.setDisabled(True)

    def _populate_tray_menu_from_notes(self):
        self.icon_creator.populate_menu(self.i_menu)
        self.i_menu.addSeparator()
        self.i_menu.addAction(self.minimize_restore_action)
        self.i_menu.addAction(self.action_quit_systray_menu)