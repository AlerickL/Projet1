"""L'éditeur de code de l'atelier de dessin (notion 5.2) : `QDrawingCodeEditor`.

Un `QPythonCodeView` (coloration et numéros de ligne) rendu modifiable, avec
le strict minimum d'un éditeur Python. Outil d'observation de l'atelier :
son code n'est jamais montré. La notion 5.2 présente son API visible :
`setPlainText()` et `toPlainText()` (API de Qt), le signal `textChanged`
(API de Qt) et `setErrorLine()`. Texte d'interface en français, sans `tr()`
(skill `interactive-walkthrough-app`, §10).
"""

from __future__ import annotations

from typing import override

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QKeyEvent, QTextCursor, QTextFormat
from PySide6.QtWidgets import QTextEdit, QWidget

from ...widgets.q_python_code_view import QPythonCodeView


class QDrawingCodeEditor(QPythonCodeView):
    """Éditeur de code Python minimal, pour de courts programmes de dessin.

    Saisie:
        Tab insère quatre espaces, ou indente les lignes sélectionnées ;
        Maj+Tab les désindente. Entrée garde l'indentation de la ligne, et
        l'augmente après un `:`.

    Fragments:
        `insertSnippet()` insère un fragment sous la ligne courante, à son
        indentation (une ligne vide est remplacée).

    Erreur:
        `setErrorLine()` surligne une ligne en rouge ; `errorLine()` la lit.
        Une ligne qui n'existe pas dans le texte (zéro, négative, ou au-delà
        de la dernière) retire le surlignage, comme `None`. Toute
        modification du texte retire le surlignage.

    Slots:
        setErrorLine(object), insertSnippet(str).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setReadOnly(False)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * len(self._Indent))
        self._errorLine: int | None = None
        self.textChanged.connect(self._clearErrorLine)

    # ====== API : erreur ======

    def errorLine(self) -> int | None:
        """La ligne surlignée en rouge, numérotée à partir de 1, ou `None`."""
        return self._errorLine

    @Slot(object)
    def setErrorLine(self, line: int | None) -> None:
        """Surligne une ligne en rouge, numérotée à partir de 1, ou retire le surlignage (`None`)."""
        block = self.document().findBlockByNumber(line - 1) if line is not None and line >= 1 else None
        self._errorLine = line if block is not None and block.isValid() else None
        selections: list[QTextEdit.ExtraSelection] = []
        if block is not None and self._errorLine is not None:
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#5a1e1e"))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = QTextCursor(block)
            selections.append(selection)
        self.setExtraSelections(selections)

    # ====== API : fragments ======

    @Slot(str)
    def insertSnippet(self, snippet: str) -> None:
        """Insère un fragment sous la ligne courante, à son indentation, et y place le curseur.

        Si la ligne courante est vide, le fragment la remplace. Après une
        ligne qui se termine par `:`, le fragment est indenté d'un cran de
        plus.
        """
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        lineText = cursor.block().text()
        indent = lineText[: len(lineText) - len(lineText.lstrip())]
        if lineText.strip():
            if lineText.rstrip().endswith(":"):
                indent += self._Indent
            cursor.insertText("\n" + indent)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(indent)
        cursor.insertText(("\n" + indent).join(snippet.strip("\n").splitlines()))
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self.setFocus()

    # ====== Événements ======

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: D102 (Qt override)
        key = event.key()
        if key == Qt.Key.Key_Tab and not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if self.textCursor().hasSelection():
                self._shiftSelectedLines(indent=True)
            else:
                self.insertPlainText(self._Indent)
            return
        if key == Qt.Key.Key_Backtab:
            self._shiftSelectedLines(indent=False)
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            lineText = self.textCursor().block().text()
            indent = lineText[: len(lineText) - len(lineText.lstrip())]
            if lineText[: self.textCursor().positionInBlock()].rstrip().endswith(":"):
                indent += self._Indent
            self.insertPlainText("\n" + indent)
            return
        super().keyPressEvent(event)

    # ====== Privé ======

    _Indent = "    "

    def _shiftSelectedLines(self, *, indent: bool) -> None:
        cursor = self.textCursor()
        document = self.document()
        first = document.findBlock(cursor.selectionStart())
        last = document.findBlock(cursor.selectionEnd())
        if cursor.hasSelection() and cursor.selectionEnd() == last.position() and last != first:
            last = last.previous()  # a selection ending at the very start of a line excludes that line
        cursor.beginEditBlock()
        block = first
        while block.isValid():
            lineCursor = QTextCursor(block)
            if indent:
                lineCursor.insertText(self._Indent)
            else:
                text = block.text()
                removed = len(text) - len(text.lstrip(" "))
                for _ in range(min(removed, len(self._Indent))):
                    lineCursor.deleteChar()
            if block == last:
                break
            block = block.next()
        cursor.endEditBlock()

    @Slot()
    def _clearErrorLine(self) -> None:
        if self._errorLine is not None:
            self.setErrorLine(None)
