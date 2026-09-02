# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""A toolbar with buttons to format the text of a QTextEdit."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (QAction, QBrush, QColor, QFont, QFontDatabase,
                         QFontInfo, QIcon, QKeySequence, QPixmap, QTextCharFormat,
                         QTextCursor, QTextListFormat)
from PyQt6.QtWidgets import (QColorDialog, QComboBox, QFontComboBox,
                             QInputDialog, QLineEdit, QToolBar, QTextEdit)

from .resources import icon


class TextFormattingToolbar(QToolBar):
    def __init__(self, text_edit: QTextEdit, parent=None):
        super().__init__(parent)
        self.text_edit_ = text_edit
        self.setWindowTitle("Format actions")
        self.setObjectName("Formattoolbar")

        # Bold
        self.action_text_bold = QAction(icon("bold"), "&Bold", self)
        self.action_text_bold.setShortcut(QKeySequence("Ctrl+B"))
        bold = QFont()
        bold.setBold(True)
        self.action_text_bold.setFont(bold)
        self.action_text_bold.triggered.connect(self.bold_text)
        self.addAction(self.action_text_bold)
        self.action_text_bold.setCheckable(True)

        # Italic
        self.action_text_italic = QAction(icon("italic"), "&Italic", self)
        self.action_text_italic.setShortcut(QKeySequence("Ctrl+I"))
        italic = QFont()
        italic.setItalic(True)
        self.action_text_italic.setFont(italic)
        self.action_text_italic.triggered.connect(self.italic_text)
        self.addAction(self.action_text_italic)
        self.action_text_italic.setCheckable(True)

        # Underline
        self.action_text_underline = QAction(icon("underlined"), "&Underline", self)
        self.action_text_underline.setShortcut(QKeySequence("Ctrl+U"))
        underline = QFont()
        underline.setUnderline(True)
        self.action_text_underline.setFont(underline)
        self.action_text_underline.triggered.connect(self.underlined_text)
        self.addAction(self.action_text_underline)
        self.action_text_underline.setCheckable(True)

        # Strike out
        self.action_text_strike_out = QAction(icon("strikedout"), "&Strike Out", self)
        self.action_text_strike_out.setShortcut(QKeySequence("Ctrl+S"))
        strike_out = QFont()
        strike_out.setStrikeOut(True)
        self.action_text_strike_out.setFont(strike_out)
        self.action_text_strike_out.triggered.connect(self.striked_out_text)
        self.addAction(self.action_text_strike_out)
        self.action_text_strike_out.setCheckable(True)

        # Hyperlink
        self.action_insert_hyperlink = QAction(icon("hyperlink"), "&Hyperlink", self)
        self.action_insert_hyperlink.setShortcut(QKeySequence("Ctrl+K"))
        self.action_insert_hyperlink.triggered.connect(self.insert_hyperlink)
        self.addAction(self.action_insert_hyperlink)

        # Clear formatting
        self.action_clear_formatting = QAction(icon("clearFormatting"), "&Clear formatting", self)
        self.action_clear_formatting.setShortcut(QKeySequence("Ctrl+Space"))
        self.action_clear_formatting.triggered.connect(self.clear_char_format)
        self.addAction(self.action_clear_formatting)

        # Bullet points
        self.action_bullet_point = QAction(icon("bulletpoints"), "Bullet point", self)
        self.action_bullet_point.setShortcut(QKeySequence("Ctrl+Shift+L"))
        self.action_bullet_point.setCheckable(True)
        self.action_bullet_point.triggered.connect(self.insert_bullet_points)
        self.addAction(self.action_bullet_point)

        # Text color
        text_pix = QPixmap(16, 16)
        text_pix.fill(self.text_edit_.palette().windowText().color())
        self.action_text_color = QAction(QIcon(text_pix), "&Text color...", self)
        self.action_text_color.triggered.connect(self.colored_text)
        self.addAction(self.action_text_color)

        # Background color
        b_pix = QPixmap(16, 16)
        b_pix.fill(self.text_edit_.palette().base().color())
        self.action_text_bcolor = QAction(QIcon(b_pix), "&Background color...", self)
        self.action_text_bcolor.triggered.connect(self.marked_text)
        self.addAction(self.action_text_bcolor)

        # Font selection
        self.font_combo_box = QFontComboBox(self)
        self.font_combo_box.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.addWidget(self.font_combo_box)
        self.font_combo_box.currentTextChanged.connect(self.font_of_text)

        # Font size selection
        self.font_size_combo_box = QComboBox(self)
        self.font_size_combo_box.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        for size in QFontDatabase.standardSizes():
            self.font_size_combo_box.addItem(str(size))
        self.addWidget(self.font_size_combo_box)
        self.font_size_combo_box.currentTextChanged.connect(self.point_size_of_text)

        self.text_edit_.currentCharFormatChanged.connect(self.get_font_and_point_size_of_text)
        self.text_edit_.cursorPositionChanged.connect(self.update_bullet_point_toolbar_button)

    # ------------------------------------------------------------------
    def merge_format_on_word_or_selection(self, fmt: QTextCharFormat):
        cursor = self.text_edit_.textCursor()
        if not cursor.selectedText():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        self.text_edit_.mergeCurrentCharFormat(fmt)
        cursor.mergeCharFormat(fmt)

    def clear_char_format(self):
        cursor = self.text_edit_.textCursor()
        if not cursor.selectedText():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.setCharFormat(QTextCharFormat())
        self.text_edit_.setCurrentCharFormat(QTextCharFormat())

    def get_font_and_point_size_of_text(self, fmt: QTextCharFormat):
        f = fmt.font()
        self.font_combo_box.setCurrentIndex(
            self.font_combo_box.findText(QFontInfo(f).family()))
        self.font_size_combo_box.setCurrentIndex(
            self.font_size_combo_box.findText(str(f.pointSize())))
        self.action_text_bold.setChecked(f.bold())
        self.action_text_italic.setChecked(f.italic())
        self.action_text_underline.setChecked(f.underline())
        self.action_text_strike_out.setChecked(f.strikeOut())
        text_pix = QPixmap(16, 16)
        if fmt.foreground().style() == Qt.BrushStyle.NoBrush:
            text_pix.fill(self.text_edit_.palette().windowText().color())
        else:
            text_pix.fill(fmt.foreground().color())
        self.action_text_color.setIcon(QIcon(text_pix))
        b_pix = QPixmap(16, 16)
        if fmt.background().style() == Qt.BrushStyle.NoBrush:
            b_pix.fill(self.text_edit_.palette().base().color())
        else:
            b_pix.fill(fmt.background().color())
        self.action_text_bcolor.setIcon(QIcon(b_pix))

    def update_bullet_point_toolbar_button(self):
        cursor = self.text_edit_.textCursor()
        current_list = cursor.currentList()
    def bold_text(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold
                          if self.action_text_bold.isChecked() else QFont.Weight.Normal)
        self.merge_format_on_word_or_selection(fmt)

    def italic_text(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.action_text_italic.isChecked())
        self.merge_format_on_word_or_selection(fmt)

    def underlined_text(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.action_text_underline.isChecked())
        self.merge_format_on_word_or_selection(fmt)

    def colored_text(self):
        col = QColorDialog.getColor(self.text_edit_.textColor(), self)
        if not col.isValid():
            return
        fmt = QTextCharFormat()
        fmt.setForeground(QBrush(col, Qt.BrushStyle.SolidPattern))
        self.merge_format_on_word_or_selection(fmt)
        pix = QPixmap(16, 16)
        pix.fill(col)
        self.action_text_color.setIcon(QIcon(pix))

    def marked_text(self):
        col = QColorDialog.getColor(self.text_edit_.textBackgroundColor(), self)
        if not col.isValid():
            return
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(col, Qt.BrushStyle.SolidPattern))
        self.merge_format_on_word_or_selection(fmt)
        pix = QPixmap(16, 16)
        pix.fill(col)
        self.action_text_bcolor.setIcon(QIcon(pix))

    def insert_hyperlink(self):
        cursor = self.text_edit_.textCursor()
        selected_text = cursor.selectedText()
        link, ok = QInputDialog.getText(self.text_edit_, "Insert hyperlink",
                                        "Addr&ess:", QLineEdit.EchoMode.Normal,
                                        selected_text)
        if not ok:
            return
        if not selected_text:
            selected_text = link
        fmt = cursor.charFormat()
        if "@" in link:
            cursor.insertHtml('<a href="mailto:%s">%s</a>' % (link, selected_text))
        else:
            cursor.insertHtml('<a href="%s">%s</a>' % (link, selected_text))
        cursor.insertText(" ", fmt)

    def font_of_text(self, f: str):
        fmt = QTextCharFormat()
        fmt.setFontFamilies([f])
        self.merge_format_on_word_or_selection(fmt)

    def point_size_of_text(self, p: str):
        try:
            point_size = float(p)
        except ValueError:
            return
        if point_size > 0:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(point_size)
            self.merge_format_on_word_or_selection(fmt)

    def set_font(self, font: QFont):
        self.font_combo_box.setCurrentFont(font)
        self.font_size_combo_box.setCurrentIndex(
            self.font_size_combo_box.findText(str(font.pointSize())))
    def striked_out_text(self):
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(self.action_text_strike_out.isChecked())
        self.merge_format_on_word_or_selection(fmt)

    def insert_bullet_points(self):
        cursor = self.text_edit_.textCursor()
        current_list = cursor.currentList()
        if (current_list is not None
                and current_list.format().style() == QTextListFormat.Style.ListDisc):
            current_block = cursor.block()
            current_list.remove(current_block)
            block_format = cursor.blockFormat()
            block_format.setIndent(0)
            cursor.setBlockFormat(block_format)
        elif current_list is None or (current_list is not None
                and current_list.format().style() != QTextListFormat.Style.ListDisc):
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.Style.ListDisc)
            cursor.createList(list_format)
        if (current_list is not None
                and current_list.format().style() == QTextListFormat.Style.ListDisc):
            self.action_bullet_point.setChecked(True)
        elif current_list is None or (current_list is not None
                and current_list.format().style() != QTextListFormat.Style.ListDisc):
            self.action_bullet_point.setChecked(False)
