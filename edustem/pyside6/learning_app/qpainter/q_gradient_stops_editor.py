"""L'éditeur des points d'arrêt du constructeur de dégradés (notion 2.4) : `QGradientStopsEditor`.

Contrôle composé, propre à la notion 2.4 : une rangée par point d'arrêt,
avec sa couleur et sa position. Son code n'est jamais montré. La notion
présente son API visible : `stops()`, qui rend les points au format de
`QGradient.setStops()`, et le signal `stopsChanged`. Texte d'interface en
français, sans `tr()` (skill `interactive-walkthrough-app`, §10).
"""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

# A gradient stop, as `QGradient.setStops()` takes it: a position from 0 to 1, and a color.
GradientStop = tuple[float, QColor]


class QGradientStopsEditor(QWidget):
    """Éditeur des points d'arrêt d'un dégradé : une rangée par point, sa couleur et sa position.

    Points d'arrêt:
        `stops()` rend les points triés par position, au format de
        `QGradient.setStops()` : des paires (position de 0 à 1, `QColor`).
        `setStops()` les remplace. Il y en a toujours entre
        `MinimumStopCount` et `MaximumStopCount` ; `stopCount()` les compte.

    Rangées:
        Chaque rangée montre un bouton de couleur, qui ouvre le choix d'une
        couleur, alpha compris, puis un sélecteur de position de 0 à 100 %,
        puis un bouton « Retirer ». Les rangées gardent leur ordre de
        création, même quand une position en dépasse une autre : seul
        `stops()` trie. Toutes les rangées sont construites une fois, puis
        affichées ou cachées : l'éditeur ne crée aucun widget après sa
        construction.

    Ajout et retrait:
        `addStop()` ajoute un point au milieu du plus grand écart entre deux
        points voisins, avec la couleur du dégradé à cet endroit (moyenne
        des deux voisins, en RGB) : le dégradé ne change pas d'aspect.
        `removeStop()` retire le point d'une rangée. Les boutons se
        désactivent aux deux limites.

    Signaux:
        stopsChanged(): Émis après chaque changement des points, par
            l'utilisateur ou par le code.

    Slots:
        setStops(list), addStop(), removeStop(int), setStopColor(int, QColor),
        setStopPosition(int, float).
    """

    stopsChanged = Signal()

    MinimumStopCount = 2
    MaximumStopCount = 8

    def __init__(self, stops: Sequence[GradientStop] | None = None, parent: QWidget | None = None) -> None:
        """Initialise l'éditeur.

        Args:
            stops: Les points de départ, au format de `stops()`. None : du
                noir au blanc.
            parent: Widget parent, ou None.

        Raises:
            ValueError: Trop peu ou trop de points, ou une position hors de
                0 à 1.
        """
        super().__init__(parent)
        self._stops: list[GradientStop] = []
        self._rows: list[QGradientStopsEditor._StopRow] = [
            self._StopRow(index, self) for index in range(self.MaximumStopCount)
        ]

        self._addButton: QPushButton = QPushButton("Ajouter un point d'arrêt")
        self._addButton.clicked.connect(self.addStop)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        for row in self._rows:
            layout.addWidget(row.widget)
        layout.addWidget(self._addButton, 0, Qt.AlignmentFlag.AlignLeft)

        self.setStops(stops if stops is not None else [(0.0, QColor("black")), (1.0, QColor("white"))])

    # ====== API : points d'arrêt ======

    def stops(self) -> list[GradientStop]:
        """Les points d'arrêt triés par position : des paires (position de 0 à 1, `QColor`)."""
        return sorted(((position, QColor(color)) for position, color in self._stops), key=lambda stop: stop[0])

    def stopCount(self) -> int:
        """Le nombre de points d'arrêt."""
        return len(self._stops)

    @Slot(list)
    def setStops(self, stops: Sequence[GradientStop]) -> None:
        """Remplace tous les points d'arrêt, dans l'ordre donné.

        Raises:
            ValueError: Trop peu ou trop de points, ou une position hors de
                0 à 1.
        """
        if not self.MinimumStopCount <= len(stops) <= self.MaximumStopCount:
            raise ValueError(f"a gradient needs {self.MinimumStopCount} to {self.MaximumStopCount} stops, "
                             f"got {len(stops)}")
        for position, _color in stops:
            if not 0.0 <= position <= 1.0:
                raise ValueError(f"stop position {position} is outside [0, 1]")
        self._stops = [(float(position), QColor(color)) for position, color in stops]
        self._refreshRows()
        self.stopsChanged.emit()

    @Slot()
    def addStop(self) -> None:
        """Ajoute un point au milieu du plus grand écart, sans changer l'aspect du dégradé.

        Ne fait rien si l'éditeur a déjà `MaximumStopCount` points.
        """
        if len(self._stops) >= self.MaximumStopCount:
            return
        ordered = self.stops()
        gaps = [(ordered[index + 1][0] - ordered[index][0], index) for index in range(len(ordered) - 1)]
        _gap, index = max(gaps)
        (before, beforeColor), (after, afterColor) = ordered[index], ordered[index + 1]
        color = QColor(*(round((first + second) / 2)
                         for first, second in zip(beforeColor.getRgb(), afterColor.getRgb())))
        self._stops.append(((before + after) / 2, color))
        self._refreshRows()
        self.stopsChanged.emit()

    @Slot(int)
    def removeStop(self, index: int) -> None:
        """Retire le point d'une rangée (dans l'ordre des rangées).

        Ne fait rien s'il ne reste que `MinimumStopCount` points.

        Raises:
            IndexError: Aucune rangée de ce rang.
        """
        if not 0 <= index < len(self._stops):
            raise IndexError(f"no stop at row {index}")
        if len(self._stops) <= self.MinimumStopCount:
            return
        del self._stops[index]
        self._refreshRows()
        self.stopsChanged.emit()

    @Slot(int, QColor)
    def setStopColor(self, index: int, color: QColor) -> None:
        """Change la couleur du point d'une rangée.

        Raises:
            IndexError: Aucune rangée de ce rang.
        """
        position, _color = self._stopAt(index)
        self._stops[index] = (position, QColor(color))
        self._refreshRows()
        self.stopsChanged.emit()

    @Slot(int, float)
    def setStopPosition(self, index: int, position: float) -> None:
        """Change la position du point d'une rangée, bornée à 0 à 1.

        Raises:
            IndexError: Aucune rangée de ce rang.
        """
        _position, color = self._stopAt(index)
        self._stops[index] = (min(max(position, 0.0), 1.0), color)
        self._refreshRows()
        self.stopsChanged.emit()

    # ====== Private ======

    class _StopRow:
        """Les widgets d'une rangée de l'éditeur : couleur, position, retrait."""

        def __init__(self, index: int, editor: QGradientStopsEditor) -> None:
            self.widget: QWidget = QWidget()
            self.colorButton: QPushButton = QPushButton()
            self.colorButton.setToolTip("Choisir la couleur de ce point d'arrêt")
            self.colorButton.setFixedWidth(110)
            self.colorButton.clicked.connect(lambda: editor._chooseStopColor(index))
            self.positionSlider: QSlider = QSlider(Qt.Orientation.Horizontal)
            self.positionSlider.setRange(0, 100)
            self.positionSlider.setToolTip("Position de ce point d'arrêt, de 0 % (début) à 100 % (fin)")
            self.positionSlider.valueChanged.connect(lambda percent: editor._followPositionSlider(index, percent))
            self.positionLabel: QLabel = QLabel()
            self.positionLabel.setMinimumWidth(self.positionLabel.fontMetrics().horizontalAdvance("100 %"))
            self.positionLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.removeButton: QPushButton = QPushButton("Retirer")
            self.removeButton.setToolTip("Retirer ce point d'arrêt")
            self.removeButton.clicked.connect(lambda: editor.removeStop(index))

            layout = QHBoxLayout(self.widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.colorButton)
            layout.addWidget(self.positionSlider, 1)
            layout.addWidget(self.positionLabel)
            layout.addWidget(self.removeButton)

        def show(self, position: float, color: QColor, canRemove: bool) -> None:
            """Affiche un point : sa couleur sur le bouton, sa position sur le sélecteur."""
            # Explicit text color, black or white by the lightness of the swatch: always readable.
            textColor = "#000000" if color.lightness() > 140 or color.alpha() < 110 else "#ffffff"
            self.colorButton.setText(color.name(QColor.NameFormat.HexArgb if color.alpha() < 255
                                                else QColor.NameFormat.HexRgb))
            red, green, blue, alpha = color.getRgb()
            self.colorButton.setStyleSheet(f"background-color: rgba({red}, {green}, {blue}, {alpha}); "
                                           f"color: {textColor}; border: 1px solid #7f8c8d; padding: 3px;")
            self.positionSlider.blockSignals(True)
            self.positionSlider.setValue(round(position * 100))
            self.positionSlider.blockSignals(False)
            self.positionLabel.setText(f"{round(position * 100)} %")
            self.removeButton.setEnabled(canRemove)

    def _stopAt(self, index: int) -> GradientStop:
        if not 0 <= index < len(self._stops):
            raise IndexError(f"no stop at row {index}")
        return self._stops[index]

    def _refreshRows(self) -> None:
        """Montre une rangée par point, à jour, et cache les autres ; signaux des sélecteurs bloqués."""
        canRemove = len(self._stops) > self.MinimumStopCount
        for index, row in enumerate(self._rows):
            visible = index < len(self._stops)
            row.widget.setVisible(visible)
            if visible:
                position, color = self._stops[index]
                row.show(position, color, canRemove)
        self._addButton.setEnabled(len(self._stops) < self.MaximumStopCount)

    def _followPositionSlider(self, index: int, percent: int) -> None:
        position, color = self._stops[index]
        if round(position * 100) != percent:
            self.setStopPosition(index, percent / 100)

    def _chooseStopColor(self, index: int) -> None:
        _position, color = self._stops[index]
        chosen = QColorDialog.getColor(color, self, "Couleur du point d'arrêt",
                                       QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if chosen.isValid():
            self.setStopColor(index, chosen)

