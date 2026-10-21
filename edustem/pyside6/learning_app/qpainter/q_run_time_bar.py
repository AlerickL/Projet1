"""Barre du temps de calcul : la part d'une limite de temps prise par la dernière exécution.

Plomberie de l'atelier de dessin (notion 5.2) : la ligne sous le canevas,
décrite en mots à l'étape « Les garde-fous ». Elle n'apparaît jamais dans le
code affiché.
"""

from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget


class QRunTimeBar(QWidget):
    """Le temps de calcul de la dernière exécution, sur une limite : en texte, puis en barre colorée.

    Texte:
        « Temps de calcul : 0,42 s sur 1 s » : le temps à deux décimales, avec
        la virgule décimale, et la limite.

    Barre:
        Sa longueur est la part de la limite prise par le temps de calcul,
        plafonnée à la barre pleine. Sa couleur dépend de cette part :
        `NormalColor` sous `WarningShare`, `WarningColor` sous
        `CriticalShare`, puis `CriticalColor`. Le texte est à côté de la
        barre, jamais dedans : le texte d'une `QProgressBar` ne change pas de
        couleur au passage du remplissage, et se lirait mal sur un
        remplissage foncé en thème clair. Une feuille de style colore la
        barre, car les styles natifs de Windows ignorent sa palette ; son
        cadre et son fond suivent le thème (`palette(mid)`, `palette(base)`).

    Slots:
        setRunTime(float), setLimit(float).
    """

    WarningShare = 0.6
    CriticalShare = 0.85
    NormalColor = QColor("#2e7d32")
    WarningColor = QColor("#c86400")
    CriticalColor = QColor("#c62828")

    def __init__(self, limit: float, parent: QWidget | None = None) -> None:
        """Initialise la barre à un temps de calcul nul.

        Args:
            limit: La limite de temps, en secondes, strictement positive.
            parent: Widget parent, ou None.

        Raises:
            ValueError: `limit` n'est pas strictement positive.
        """
        super().__init__(parent)
        self.__limit: float = _checkedLimit(limit)
        self.__runTime: float = 0.0
        self.__label: QLabel = QLabel()
        self.__bar: QProgressBar = QProgressBar()
        self.__bar.setRange(0, self._BarSteps)
        self.__bar.setTextVisible(False)
        self.__bar.setFixedHeight(10)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__label)
        layout.addWidget(self.__bar, 1)
        self.__refresh()

    # ====== API: run time ======

    def runTime(self) -> float:
        """Le temps de calcul affiché, en secondes."""
        return self.__runTime

    @Slot(float)
    def setRunTime(self, seconds: float) -> None:
        """Affiche un nouveau temps de calcul, en secondes ; un temps négatif compte pour 0."""
        self.__runTime = max(0.0, seconds)
        self.__refresh()

    def limit(self) -> float:
        """La limite de temps, en secondes."""
        return self.__limit

    @Slot(float)
    def setLimit(self, limit: float) -> None:
        """Change la limite de temps, en secondes, strictement positive.

        Raises:
            ValueError: `limit` n'est pas strictement positive.
        """
        self.__limit = _checkedLimit(limit)
        self.__refresh()

    # ====== API: what is shown ======

    def share(self) -> float:
        """La part de la limite prise par le temps de calcul, 1 à la limite ; peut dépasser 1."""
        return self.__runTime / self.__limit

    def color(self) -> QColor:
        """La couleur de la barre, selon `share()`."""
        if self.share() >= self.CriticalShare:
            return QColor(self.CriticalColor)
        if self.share() >= self.WarningShare:
            return QColor(self.WarningColor)
        return QColor(self.NormalColor)

    def text(self) -> str:
        """Le texte affiché à gauche de la barre."""
        return self.__label.text()

    # ====== Private ======

    _BarSteps = 1000
    _StyleSheet = (
        "QProgressBar {{ border: 1px solid palette(mid); border-radius: 3px; background-color: palette(base); }}"
        " QProgressBar::chunk {{ background-color: {color}; }}"
    )

    def __refresh(self) -> None:
        self.__label.setText(
            f"Temps de calcul : {self.__runTime:.2f} s sur {self.__limit:g} s".replace(".", ","))
        self.__bar.setValue(round(min(self.share(), 1.0) * self._BarSteps))
        self.__bar.setStyleSheet(self._StyleSheet.format(color=self.color().name()))


def _checkedLimit(limit: float) -> float:
    if not limit > 0:
        raise ValueError(f"the time limit must be strictly positive, got {limit}")
    return limit
