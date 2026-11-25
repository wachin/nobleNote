# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A search toolbar for a QTextEdit with find next/previous."""

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QKeySequence, QTextCursor, QTextDocument
from PyQt6.QtWidgets import (QCheckBox, QLineEdit, QTextEdit, QToolBar,
                             QToolButton)

from .highlighter import Highlighter
from .lineedit import LineEdit


class TextSearchToolbar(QToolBar):
    def __init__(self, text_edit: QTextEdit, parent=None):
        super().__init__(parent)
        self.text_edit_ = text_edit
        self.highlighter = None
        self.setWindowTitle("Search bar")
        self.setObjectName("Searchtoolbar")

        self.typing_timer = QTimer(self)
        self.typing_timer.setSingleShot(True)
        count = self.text_edit_.document().characterCount()
        self.typing_timer.setInterval(300 if count > 5000 else 0)
        self.typing_timer.timeout.connect(self.select_next_expression)

        self.close_search = QToolButton(self)
        self.close_search.setText("\u274c")
        self.close_search.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        self.addWidget(self.close_search)

        self.search_line_ = LineEdit(self)
        self.search_line_.setPlaceholderText("Enter search argument")
        self.addWidget(self.search_line_)

        self.find_previous = QToolButton(self)
        self.find_previous.setText("Find &previous")
        self.addWidget(self.find_previous)

        self.find_next = QToolButton(self)
        self.find_next.setText("Find &next")
        self.addWidget(self.find_next)

        self.case_sensitive_box = QCheckBox(self)
        self.case_sensitive_box.setText("&Case sensitive")
        self.addWidget(self.case_sensitive_box)

        self.close_search.clicked.connect(self.hide)
        self.search_line_.textChanged.connect(self.typing_timer.start)
        self.find_next.clicked.connect(self.select_next_expression)
        self.find_previous.clicked.connect(self.select_previous_expression)
        self.search_line_.returnPressed.connect(self.select_next_expression)

    def search_line(self) -> QLineEdit:
        return self.search_line_

    def text(self) -> str:
        return self.search_line_.text()

    def set_text(self, text: str):
        self.search_line_.setText(text)
        self.highlight_text(self.text_edit_.textCursor().selectedText())

    def select_next_expression(self):
        flag = QTextDocument.FindFlag.FindCaseSensitively \
            if self.case_sensitive_box.isChecked() else QTextDocument.FindFlag(0)
        if not self.text_edit_.find(self.search_line_.text(), flag):
            self.text_edit_.moveCursor(QTextCursor.MoveOperation.Start,
                                       QTextCursor.MoveMode.MoveAnchor)
            self.text_edit_.find(self.search_line_.text(), flag)
        self.highlight_text(self.search_line_.text())

    def select_previous_expression(self):
        flag = QTextDocument.FindFlag.FindCaseSensitively
        if self.case_sensitive_box.isChecked():
            flag |= QTextDocument.FindFlag.FindBackward
        else:
            flag = QTextDocument.FindFlag.FindBackward
        if not self.text_edit_.find(self.search_line_.text(), flag):
            self.text_edit_.moveCursor(QTextCursor.MoveOperation.End,
                                       QTextCursor.MoveMode.MoveAnchor)
            self.text_edit_.find(self.search_line_.text(), flag)
        self.highlight_text(self.search_line_.text())

    def highlight_text(self, string: str):
        # a new highlighter takes ownership of the document highlight state
        self.highlighter = Highlighter(self.text_edit_.document())
        self.highlighter.expression = string
        self.highlighter.case_sensitive = self.case_sensitive_box.isChecked()

        def cleanup():
            try:
                self.highlighter.setParent(None)
                self.highlighter.deleteLater()
                self.highlighter = None
            except RuntimeError:
                pass

        self.close_search.clicked.connect(cleanup)
        self.close_search.clicked.connect(self.text_edit_.setFocus)
        self.close_search.clicked.connect(self.search_line_.clear)
        self.text_edit_.ensureCursorVisible()