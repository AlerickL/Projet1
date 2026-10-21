"""Étiquette de lecture : une valeur lue par le code affiché, sous la zone de contenu.

Outil d'observation partagé par toutes les applications de `learning_app`.
Le code affiché d'une notion n'en emploie qu'une méthode, celle de `QLabel` :
`setText(texte)`. Sa création reste cachée.
"""

from __future__ import annotations

from typing import override

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QLabel, QWidget


class QReadoutLabel(QLabel):
    """Étiquette de lecture, en police à chasse fixe, cachée tant qu'elle est vide.

    Texte:
        Toujours du texte brut, jamais interprété comme du HTML : une valeur
        lue comme `QSize(30, 20)` ou `a < b` s'affiche telle quelle. Les
        sauts de ligne sont conservés, et le texte peut être sélectionné à
        la souris pour être copié. Une ligne plus longue que la largeur
        disponible continue à la ligne suivante, entre deux mots : la
        lecture n'élargit jamais la page, quel que soit son texte (un long
        message d'erreur, un `print()`).

    Visibilité:
        `setText()` affiche l'étiquette dès que le texte n'est pas vide, et
        la cache quand il l'est. `clear()` la vide et la cache : c'est la
        remise à zéro avant le rejeu. La police à chasse fixe garde les
        chiffres alignés d'une ligne à l'autre.

    Slots:
        setText(str), clear().
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise une étiquette vide, donc cachée.

        Args:
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setWordWrap(True)
        self.setVisible(False)

    # ====== API: text ======

    @override
    @Slot(str)
    def setText(self, text: str) -> None:
        """Affiche `text`, ou cache l'étiquette si `text` est vide."""
        super().setText(text)
        self.setVisible(bool(text))

    @override
    @Slot()
    def clear(self) -> None:
        """Vide l'étiquette et la cache."""
        self.setText("")
