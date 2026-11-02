"""Panneau des contrôles des étapes « À vous » d'une notion.

Plomberie partagée par toutes les applications de `learning_app` : jamais
affiché dans le code montré à l'étudiant, et cité seulement pour
`setCaption()`, présenté par la notion qui l'emploie. Il crée et dispose les
contrôles (sélecteur numérique, liste déroulante, case à cocher, bouton,
groupe de boutons radio), les garde cachés jusqu'à leur révélation, et les
remet à zéro avant chaque rejeu. Le code affiché de la notion ne voit que
les contrôles Qt rendus par les méthodes `add…()` : il les connecte et les
lit lui-même.

Texte d'interface en français, sans `tr()` (exception déclarée dans le skill
`interactive-walkthrough-app`, §10).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from PySide6.QtCore import SIGNAL, QMetaMethod, QObject, QSignalBlocker, Qt, Slot
from PySide6.QtWidgets import (
    QAbstractButton, QButtonGroup, QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QSlider, QWidget,
)


class QControlPanel(QWidget):
    """Panneau qui crée, révèle et remet à zéro les contrôles d'une notion.

    Création:
        `addSlider()`, `addComboBox()`, `addCheckBox()`, `addButton()` et
        `addRadioGroup()` ajoutent chacun une rangée au panneau, dans
        l'ordre d'appel, et rendent le contrôle Qt créé. Ils sont appelés
        une seule fois, à la construction de la notion. La valeur de départ
        passée à la création est mémorisée : c'est celle que rétablit
        `resetControls()`. `controls()` rend les contrôles créés.

    Sélecteur numérique:
        Le `QSlider` porte des entiers. Une étiquette, à sa droite, affiche
        la valeur divisée par `divisor`, avec la virgule décimale et le
        suffixe donné (« 2,5 px »). `valueText()` rend ce texte.

    Libellés:
        `setCaption()` change le libellé d'une rangée, par exemple quand un
        même sélecteur change de sens. `caption()` le rend.

    Révélation:
        Le panneau et toutes ses rangées sont cachés au départ et après
        chaque `resetControls()`. `reveal()` affiche le panneau et les
        rangées des contrôles donnés, ou toutes ses rangées sans argument.

    Remise à zéro:
        `resetControls()` cache tout, rétablit les libellés, les bornes et
        les valeurs de départ signaux bloqués, puis retire toutes les connexions faites sur les signaux
        propres des contrôles (`valueChanged`, `clicked`, `idToggled`…).
        L'étape « À vous » qui les connecte peut donc être rejouée sans que
        les connexions s'accumulent. Toute connexion faite hors du panneau,
        même dans le code caché de la notion, est retirée aussi.

    Slots:
        reveal(*controls), resetControls(), setCaption(QObject, str).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise un panneau vide et caché.

        Args:
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self._layout: QFormLayout = QFormLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._rows: list[QControlPanel._Row] = []
        self.setVisible(False)

    # ====== API: creation ======

    def addSlider(self, caption: str, minimum: int, maximum: int, value: int, divisor: int = 1,
                  suffix: str = "") -> QSlider:
        """Ajoute un sélecteur numérique horizontal, avec l'étiquette de sa valeur.

        Args:
            caption: Libellé de la rangée, sans deux-points (« Épaisseur »).
            minimum, maximum: Bornes entières du sélecteur.
            value: Valeur de départ, entre les bornes.
            divisor: Diviseur de la valeur affichée : 10 affiche 25 comme
                « 2,5 ». Une puissance de 10 donne autant de décimales que
                de zéros ; tout autre diviseur, deux décimales.
            suffix: Unité écrite après la valeur affichée (« px », « % »,
                « ° »), précédée d'une espace, sauf le degré.

        Returns:
            Le sélecteur créé, caché jusqu'à `reveal()`.

        Raises:
            ValueError: Bornes inversées, valeur hors bornes ou diviseur
                non positif.
        """
        if minimum > maximum:
            raise ValueError(f"minimum {minimum} is greater than maximum {maximum}")
        if not minimum <= value <= maximum:
            raise ValueError(f"value {value} is outside [{minimum}, {maximum}]")
        if divisor <= 0:
            raise ValueError(f"divisor must be positive, got {divisor}")

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        valueLabel = QLabel()
        valueLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row = QControlPanel._Row(slider, value, valueLabel=valueLabel, divisor=divisor, suffix=suffix)
        # Wide enough for both bounds: the label never moves the slider while it is dragged.
        metrics = valueLabel.fontMetrics()
        valueLabel.setMinimumWidth(max(metrics.horizontalAdvance(row.format(bound)) for bound in (minimum, maximum)))
        self.__connectValueLabel(row)
        row.refreshValueLabel()

        field = QWidget()
        fieldLayout = QHBoxLayout(field)
        fieldLayout.setContentsMargins(0, 0, 0, 0)
        fieldLayout.addWidget(slider, 1)
        fieldLayout.addWidget(valueLabel)
        self.__addRow(row, caption, field)
        return slider

    def addComboBox(self, caption: str, choices: Sequence[tuple[str, object]], currentIndex: int = 0) -> QComboBox:
        """Ajoute une liste déroulante ; chaque choix porte une valeur, lue par `currentData()`.

        Args:
            caption: Libellé de la rangée, sans deux-points.
            choices: Couples (texte affiché, valeur portée), dans l'ordre.
            currentIndex: Index du choix de départ.

        Returns:
            La liste déroulante créée, cachée jusqu'à `reveal()`.

        Raises:
            ValueError: Aucun choix, ou index de départ hors de la liste.
        """
        if not choices:
            raise ValueError("a combo box needs at least one choice")
        if not 0 <= currentIndex < len(choices):
            raise ValueError(f"currentIndex {currentIndex} is outside the {len(choices)} choices")
        comboBox = QComboBox()
        for text, data in choices:
            comboBox.addItem(text, data)
        comboBox.setCurrentIndex(currentIndex)
        self.__addRow(QControlPanel._Row(comboBox, currentIndex), caption, comboBox)
        return comboBox

    def addCheckBox(self, text: str, checked: bool = False) -> QCheckBox:
        """Ajoute une case à cocher, sur toute la largeur du panneau.

        Args:
            text: Texte de la case.
            checked: État de départ.

        Returns:
            La case créée, cachée jusqu'à `reveal()`.
        """
        checkBox = QCheckBox(text)
        checkBox.setChecked(checked)
        self.__addRow(QControlPanel._Row(checkBox, checked), "", checkBox)
        return checkBox

    def addButton(self, text: str) -> QPushButton:
        """Ajoute un bouton, sur toute la largeur du panneau.

        Args:
            text: Texte du bouton.

        Returns:
            Le bouton créé, caché jusqu'à `reveal()`.
        """
        button = QPushButton(text)
        self.__addRow(QControlPanel._Row(button, None), "", button)
        return button

    def addRadioGroup(self, caption: str, choices: Sequence[str], checked: int = 0) -> QButtonGroup:
        """Ajoute un groupe de boutons radio exclusifs, côte à côte.

        Le bouton de rang `i` reçoit l'identifiant `i` : `checkedId()` et le
        signal `idToggled` le rendent.

        Args:
            caption: Libellé de la rangée, sans deux-points.
            choices: Texte de chaque bouton, dans l'ordre.
            checked: Rang du bouton coché au départ.

        Returns:
            Le groupe créé (enfant Qt du panneau) ; ses boutons sont cachés
            jusqu'à `reveal()`.

        Raises:
            ValueError: Aucun choix, ou rang de départ hors de la liste.
        """
        if not choices:
            raise ValueError("a radio group needs at least one choice")
        if not 0 <= checked < len(choices):
            raise ValueError(f"checked {checked} is outside the {len(choices)} choices")
        group = QButtonGroup(self)
        field = QWidget()
        fieldLayout = QHBoxLayout(field)
        fieldLayout.setContentsMargins(0, 0, 0, 0)
        for identifier, text in enumerate(choices):
            button = QRadioButton(text)
            group.addButton(button, identifier)
            fieldLayout.addWidget(button)
        fieldLayout.addStretch(1)
        group.button(checked).setChecked(True)
        self.__addRow(QControlPanel._Row(group, checked), caption, field)
        return group

    def controls(self) -> list[QObject]:
        """Les contrôles créés, dans l'ordre des rangées (un `QButtonGroup` pour un groupe radio)."""
        return [row.control for row in self._rows]

    def valueText(self, slider: QSlider) -> str:
        """Le texte affiché à droite d'un sélecteur numérique du panneau (« 2,5 px »).

        Raises:
            ValueError: `slider` n'est pas un sélecteur de ce panneau.
        """
        row = self.__rowOf(slider)
        if row.valueLabel is None:
            raise ValueError("this control is not a slider")
        return row.valueLabel.text()

    # ====== API: captions ======

    def caption(self, control: QObject) -> str:
        """Le libellé de la rangée d'un contrôle, sans deux-points ; vide sans libellé.

        Raises:
            ValueError: Le contrôle n'appartient pas à ce panneau.
        """
        return self.__rowOf(control).caption

    @Slot(QObject, str)
    def setCaption(self, control: QObject, caption: str) -> None:
        """Change le libellé de la rangée d'un contrôle, créée avec un libellé.

        Raises:
            ValueError: Le contrôle n'appartient pas à ce panneau, ou sa
                rangée a été créée sans libellé.
        """
        row = self.__rowOf(control)
        label = self._layout.labelForField(row.field)
        if not isinstance(label, QLabel):
            raise ValueError("this control was created without a caption")
        row.caption = caption
        label.setText(f"{caption} :")

    @Slot(QSlider, int)
    def setDivisor(self, slider: QSlider, divisor: int) -> None:
        """Change le diviseur de la valeur affichée d'un sélecteur (voir `addSlider()`).

        `resetControls()` rétablit le diviseur de départ.

        Raises:
            ValueError: Le sélecteur n'appartient pas à ce panneau, ou le
                diviseur n'est pas positif.
        """
        if divisor <= 0:
            raise ValueError(f"divisor must be positive, got {divisor}")
        row = self.__rowOf(slider)
        row.divisor = divisor
        # Never narrower than before: the label must not move the slider when the divisor changes back.
        metrics = row.valueLabel.fontMetrics()
        needed = max(metrics.horizontalAdvance(row.format(bound)) for bound in (slider.minimum(), slider.maximum()))
        row.valueLabel.setMinimumWidth(max(row.valueLabel.minimumWidth(), needed))
        row.refreshValueLabel()

    # ====== API: visibility ======

    @Slot()
    def reveal(self, *controls: QObject) -> None:
        """Affiche le panneau et les rangées des contrôles donnés ; toutes les rangées sans argument.

        Raises:
            ValueError: Un contrôle n'appartient pas à ce panneau.
        """
        rows = [self.__rowOf(control) for control in controls] if controls else self._rows
        for row in rows:
            self._layout.setRowVisible(row.field, True)
        self.setVisible(True)

    @Slot()
    def resetControls(self) -> None:
        """Cache tout, rétablit les valeurs de départ et retire les connexions des contrôles."""
        self.setVisible(False)
        for row in self._rows:
            self._layout.setRowVisible(row.field, False)
            if row.caption != row.startCaption:
                self.setCaption(row.control, row.startCaption)
            row.restoreStartValue()
            for sender in row.senders():
                _disconnectOwnSignals(sender)
            if row.valueLabel is not None:
                self.__connectValueLabel(row)
                row.refreshValueLabel()

    # ====== Private ======

    class _Row:
        """Une rangée : le contrôle, son champ dans le layout et sa valeur de départ."""

        def __init__(self, control: QObject, startValue: object, *, valueLabel: QLabel | None = None,
                     divisor: int = 1, suffix: str = "") -> None:
            self.control: QObject = control
            self.startValue: object = startValue
            self.caption: str = ""
            self.startCaption: str = ""
            self.startRange: tuple[int, int] | None = None
            if isinstance(control, QSlider):
                self.startRange = (control.minimum(), control.maximum())
            self.valueLabel: QLabel | None = valueLabel
            self.divisor: int = divisor
            self.startDivisor: int = divisor
            self.suffix: str = suffix
            self.field: QWidget = QWidget()

        def format(self, value: int) -> str:
            """La valeur d'un sélecteur telle qu'affichée : divisée, virgule décimale, suffixe."""
            return _formatNumber(value, self.divisor) + _spacedSuffix(self.suffix)

        def refreshValueLabel(self) -> None:
            if self.valueLabel is not None and isinstance(self.control, QSlider):
                self.valueLabel.setText(self.format(self.control.value()))

        def senders(self) -> list[QObject]:
            """Les objets dont les signaux sont connectés par la notion : le contrôle, et les boutons d'un groupe."""
            if isinstance(self.control, QButtonGroup):
                return [self.control, *self.control.buttons()]
            return [self.control]

        def restoreStartValue(self) -> None:
            blockers = [QSignalBlocker(sender) for sender in self.senders()]
            control = self.control
            if isinstance(control, QSlider):
                self.divisor = self.startDivisor
                control.setRange(*self.startRange)
                control.setValue(self.startValue)
            elif isinstance(control, QComboBox):
                control.setCurrentIndex(self.startValue)
            elif isinstance(control, QButtonGroup):
                control.button(self.startValue).setChecked(True)
            elif isinstance(control, QAbstractButton) and self.startValue is not None:
                control.setChecked(self.startValue)
            for blocker in blockers:
                blocker.unblock()

    def __addRow(self, row: QControlPanel._Row, caption: str, field: QWidget) -> None:
        row.field = field
        row.caption = row.startCaption = caption
        if caption:
            self._layout.addRow(f"{caption} :", field)
        else:
            self._layout.addRow(field)
        self._layout.setRowVisible(field, False)
        self._rows.append(row)

    def __rowOf(self, control: QObject) -> QControlPanel._Row:
        for row in self._rows:
            if row.control is control:
                return row
        raise ValueError("this control does not belong to the panel")

    def __connectValueLabel(self, row: QControlPanel._Row) -> None:
        assert isinstance(row.control, QSlider)
        row.control.valueChanged.connect(lambda _value: row.refreshValueLabel())


# ====== Private ======

def _formatNumber(value: int, divisor: int) -> str:
    """Un entier divisé par `divisor`, en texte français (virgule décimale)."""
    if divisor == 1:
        return str(value)
    exponent = math.log10(divisor)
    decimals = round(exponent) if exponent == round(exponent) else 2
    return f"{value / divisor:.{decimals}f}".replace(".", ",")


def _spacedSuffix(suffix: str) -> str:
    """Le suffixe d'une valeur, précédé d'une espace, sauf le degré (« 3 px », « 50 % », mais « 30° »)."""
    return suffix if not suffix or suffix.startswith("°") else f" {suffix}"


def _disconnectOwnSignals(sender: QObject) -> None:
    """Retire toutes les connexions des signaux déclarés par la classe du contrôle, au-delà de `QWidget` ou `QObject`.

    Les contrôles de Qt n'ont aucune connexion interne sur ces signaux : la
    déconnexion ne retire que celles du panneau et de la notion.
    """
    base = QWidget.staticMetaObject if isinstance(sender, QWidget) else QObject.staticMetaObject
    metaObject = sender.metaObject()
    for index in range(base.methodCount(), metaObject.methodCount()):
        method = metaObject.method(index)
        if method.methodType() != QMetaMethod.MethodType.Signal:
            continue
        signature = SIGNAL(bytes(method.methodSignature()).decode())
        if sender.receivers(signature) > 0:
            QObject.disconnect(sender, signature, None, None)
