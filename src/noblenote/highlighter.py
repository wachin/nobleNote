# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Highlights words when the find-in-text function is activated."""

from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expression = ""
        self.case_sensitive = False
        self.keyword_format = QTextCharFormat()

    def highlightBlock(self, text: str):
        if not self.expression:
            return
        flag = (QRegularExpression.PatternOption.NoPatternOption
                if self.case_sensitive
                else QRegularExpression.PatternOption.CaseInsensitiveOption)
        pattern = QRegularExpression(self.expression, flag)
        self.keyword_format.setBackground(Qt.GlobalColor.yellow)
        it = pattern.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(), match.capturedLength(),
                           self.keyword_format)