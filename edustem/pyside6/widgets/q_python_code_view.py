"""Coloration syntaxique Python et zone d'affichage de code, partagées par
toutes les applications PySide6 du projet.

Ce module vit une seule fois ici, sous `edustem/pyside6`, contrairement à
`q_step_walkthrough.py` qui, lui, est recopié tel quel dans chaque projet
d'apprentissage interactif (voir le SKILL "interactive-walkthrough-app").
Chaque `q_step_walkthrough.py` importe `QPythonCodeView` d'ici plutôt que de
redéfinir son propre surligneur.
"""

from __future__ import annotations

import re
from typing import override

from PySide6.QtCore import QRect, QSize, Qt, Slot
from PySide6.QtGui import (
    QColor, QFont, QPainter, QPaintEvent, QResizeEvent, QSyntaxHighlighter, QTextCharFormat, QTextDocument,
)
from PySide6.QtWidgets import QPlainTextEdit, QWidget


class QPythonSyntaxHighlighter(QSyntaxHighlighter):
    """Coloration syntaxique Python minimale : mots-clés, chaînes, commentaires,
    nombres, décorateurs, noms après `def`/`class`, `self`. Pas un vrai
    analyseur, mais suffisant pour un court extrait pédagogique.
    """

    # Block state used to track an unclosed triple-quoted string across lines.
    _Normal, _InTripleString = 0, 1
    _TripleQuote = re.compile(r'"""')

    # Python keywords and built-in functions recognized for syntax highlighting.
    _Keywords: tuple[str, ...] = (
        "def", "class", "return", "if", "elif", "else", "for", "while", "import", "from", "as",
        "with", "in", "not", "and", "or", "is", "None", "True", "False", "pass", "break", "continue",
        "lambda", "try", "except", "finally", "raise", "yield", "global", "nonlocal", "assert", "del",
    )
    _Builtins: tuple[str, ...] = (
        "print", "len", "range", "str", "int", "float", "list", "dict", "set", "tuple", "round",
    )

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        def formatFor(color: str, *, bold: bool = False, italic: bool = False) -> QTextCharFormat:
            format_ = QTextCharFormat()
            format_.setForeground(QColor(color))
            format_.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
            format_.setFontItalic(italic)
            return format_

        self._keywordFormat: QTextCharFormat = formatFor("#569cd6")
        self._builtinFormat: QTextCharFormat = formatFor("#4ec9b0")
        self._selfFormat: QTextCharFormat = formatFor("#9cdcfe", italic=True)
        self._stringFormat: QTextCharFormat = formatFor("#ce9178")
        self._commentFormat: QTextCharFormat = formatFor("#6a9955", italic=True)
        self._numberFormat: QTextCharFormat = formatFor("#b5cea8")
        self._decoratorFormat: QTextCharFormat = formatFor("#dcdcaa")
        self._definitionNameFormat: QTextCharFormat = formatFor("#dcdcaa", bold=True)

        self._keywordPattern: re.Pattern[str] = re.compile(r"\b(" + "|".join(self._Keywords) + r")\b")
        self._builtinPattern: re.Pattern[str] = re.compile(r"\b(" + "|".join(self._Builtins) + r")\b")
        self._selfPattern: re.Pattern[str] = re.compile(r"\bself\b")
        self._numberPattern: re.Pattern[str] = re.compile(r"\b\d+\.?\d*\b")
        self._decoratorPattern: re.Pattern[str] = re.compile(r"@\w+")
        self._definitionPattern: re.Pattern[str] = re.compile(r"\b(?:def|class)\s+(\w+)")
        self._singleLineStringPattern: re.Pattern[str] = re.compile(
            r"(\"[^\"\\]*(?:\\.[^\"\\]*)*\"|'[^'\\]*(?:\\.[^'\\]*)*')"
        )

    @override
    def highlightBlock(self, text: str) -> None:  # noqa: D102 (Qt override)
        for pattern, format_ in (
            (self._numberPattern, self._numberFormat),
            (self._builtinPattern, self._builtinFormat),
            (self._keywordPattern, self._keywordFormat),
            (self._selfPattern, self._selfFormat),
            (self._decoratorPattern, self._decoratorFormat),
        ):
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format_)

        for match in self._definitionPattern.finditer(text):
            self.setFormat(match.start(1), match.end(1) - match.start(1), self._definitionNameFormat)

        # Strings are colored after keywords/numbers/etc.: their format overwrites, across their
        # whole span, any false positive found inside (e.g. "self" within a string). The same
        # spans are reused below for the comment: they let a `#` inside a string be skipped
        # instead of mistakenly starting a real comment.
        stringSpans = [match.span() for match in self._singleLineStringPattern.finditer(text)]
        for start, end in stringSpans:
            self.setFormat(start, end - start, self._stringFormat)

        commentStart = self._findCommentStart(text, stringSpans)
        if commentStart >= 0:
            self.setFormat(commentStart, len(text) - commentStart, self._commentFormat)

        self._highlightTripleQuotedStrings(text)

    @staticmethod
    def _findCommentStart(text: str, stringSpans: list[tuple[int, int]]) -> int:
        """Position du premier `#` qui amorce un vrai commentaire, ou -1.

        Un `#` situé à l'intérieur d'une chaîne (ex. un code couleur CSS
        `"#2b2b2b"`) n'amorce pas un commentaire : il est ignoré au profit du
        `#` suivant, s'il y en a un.
        """
        index = text.find("#")
        while index >= 0:
            if not any(start <= index < end for start, end in stringSpans):
                return index
            index = text.find("#", index + 1)
        return -1

    def _highlightTripleQuotedStrings(self, text: str) -> None:
        startIndex = 0
        if self.previousBlockState() != self._InTripleString:
            match = self._TripleQuote.search(text)
            startIndex = match.start() if match else -1
        while startIndex >= 0:
            match = self._TripleQuote.search(text, startIndex + 3)
            if match:
                endIndex = match.end()
                self.setFormat(startIndex, endIndex - startIndex, self._stringFormat)
                self.setCurrentBlockState(self._Normal)
                nextMatch = self._TripleQuote.search(text, endIndex)
                startIndex = nextMatch.start() if nextMatch else -1
            else:
                self.setFormat(startIndex, len(text) - startIndex, self._stringFormat)
                self.setCurrentBlockState(self._InTripleString)
                startIndex = -1


class QPythonCodeView(QPlainTextEdit):
    """Zone d'affichage de code Python en lecture seule : coloration
    syntaxique et numéros de ligne, calquée sur l'exemple "Code Editor" de
    la documentation Qt (gouttière peinte par un widget compagnon
    `_QLineNumberArea`, synchronisée au défilement et au nombre de lignes).
    """

    def __init__(self, *, showLineNumbers: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setFont(QFont("Consolas", 10))
        # A visible border: with a dark theme, the window background is as dark as the code (#1e1e1e)
        # and a borderless view would vanish into it.
        self.setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; "
                           "border: 1px solid #5c6773; border-radius: 4px; }")
        self._highlighter: QPythonSyntaxHighlighter = QPythonSyntaxHighlighter(self.document())

        self._lineNumberArea: _QLineNumberArea = _QLineNumberArea(self)
        self._lineNumberArea.setVisible(showLineNumbers)
        self.blockCountChanged.connect(self._updateLineNumberAreaWidth)
        self.updateRequest.connect(self._updateLineNumberArea)
        self._updateLineNumberAreaWidth(0)

    def _lineNumberAreaWidth(self) -> int:
        # isHidden(), pas isVisible() : isVisible() reste False tant que la vue elle-même n'a
        # jamais été affichée, ce qui annulait la marge jusqu'au premier affichage.
        if self._lineNumberArea.isHidden():
            return 0
        digitCount = len(str(max(1, self.blockCount())))
        return 8 + self.fontMetrics().horizontalAdvance("9") * digitCount

    @Slot(int)
    def _updateLineNumberAreaWidth(self, _newBlockCount: int) -> None:
        self.setViewportMargins(self._lineNumberAreaWidth(), 0, 0, 0)

    @Slot(QRect, int)
    def _updateLineNumberArea(self, rect: QRect, dy: int) -> None:
        if dy:
            self._lineNumberArea.scroll(0, dy)
        else:
            self._lineNumberArea.update(0, rect.y(), self._lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._updateLineNumberAreaWidth(0)

    def _paintLineNumberArea(self, event: QPaintEvent) -> None:
        painter = QPainter(self._lineNumberArea)
        painter.fillRect(event.rect(), QColor("#1e1e1e"))
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        areaWidth = self._lineNumberArea.width()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#6e7681"))
                painter.drawText(0, top, areaWidth - 4, self.fontMetrics().height(),
                                  Qt.AlignmentFlag.AlignRight, str(blockNumber + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            blockNumber += 1

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: D102 (Qt override)
        super().resizeEvent(event)
        rect = self.contentsRect()
        self._lineNumberArea.setGeometry(QRect(rect.left(), rect.top(), self._lineNumberAreaWidth(), rect.height()))


class _QLineNumberArea(QWidget):
    """Gouttière de numéros de ligne accolée à un `QPythonCodeView`. Ne peint
    rien elle-même : délègue à `_paintLineNumberArea` du widget qu'elle
    accompagne, seul à connaître la position réelle des blocs de texte.
    """

    def __init__(self, codeView: QPythonCodeView) -> None:
        super().__init__(codeView)
        self._codeView: QPythonCodeView = codeView

    @override
    def sizeHint(self) -> QSize:  # noqa: D102 (Qt override)
        return QSize(self._codeView._lineNumberAreaWidth(), 0)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: D102 (Qt override)
        self._codeView._paintLineNumberArea(event)
