"""Curseur et boîte numérique côte à côte, toujours synchronisés : `QSliderSpinBox` (entiers) et
`QRealSliderSpinBox` (réels).

L'utilisateur choisit une valeur en glissant la poignée ou en la tapant ; le programme ne voit
qu'un seul widget, une seule valeur et un seul `valueChanged`. Les deux widgets internes ne
sont pas exposés : l'interface publique reprend les noms de Qt (`value`, `setValue`,
`setRange`, `singleStep`, `prefix`, `suffix`, `tickInterval`...), avec le type de nombre de la
classe concrète.

    box = QRealSliderSpinBox()
    box.setRange(0.0, 10.0)
    box.setDecimals(1)
    box.setSuffix(" cm")
    box.valueChanged.connect(print)

Dépendances locales : ce fichier compose `QRealSlider` (`q_real_slider`) et hérite de
`QAbstractWidget` (`q_abstract_widget`). C'est sa raison d'être.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar, Protocol

from PySide6.QtCore import QSignalBlocker, Qt, Signal, SignalInstance, Slot
from PySide6.QtWidgets import QBoxLayout, QDoubleSpinBox, QSizePolicy, QSlider, QSpinBox, QWidget

from .q_abstract_widget import QAbstractWidget
from .q_real_slider import QRealSlider


class QAbstractSliderSpinBox[T: (int, float)](QAbstractWidget):
    """Base abstraite d'un curseur et d'une boîte numérique côte à côte, qui portent une seule
    valeur de type `T` (`int` ou `float`).

    Les classes concrètes sont `QSliderSpinBox` (`QSlider` et `QSpinBox`) et
    `QRealSliderSpinBox` (`QRealSlider` et `QDoubleSpinBox`). Cette base fait la disposition, la
    synchronisation et toute l'interface commune ; chaque classe concrète choisit ses deux
    widgets internes et déclare ses signaux typés.

    Valeur et intervalle
    --------------------
    `value`/`setValue`, `minimum`/`setMinimum`, `maximum`/`setMaximum`, `setRange`,
    `singleStep`/`setSingleStep` et `pageStep`/`setPageStep` suivent les règles du curseur
    interne, qui sert de référence (bornage, arrondi, pas minimal, exceptions) ; la boîte
    numérique reçoit ensuite exactement ce que le curseur a retenu. Une opération refusée
    (exception) ne change ni l'un ni l'autre.

    - **Le pas simple** sert aux flèches de la boîte numérique, aux flèches du clavier et à la
      molette sur le curseur. Un pas négatif est pris en valeur absolue, comme dans `QSlider`.
    - **Le pas de page** ne concerne que le curseur (touches de page, clic dans la piste).

    Synchronisation
    ---------------
    - Le curseur et la boîte numérique affichent toujours la même valeur, quelle que soit la
      source du changement : l'un ou l'autre widget, un mutateur, un bornage ou un arrondi.
    - **`valueChanged` est émis une seule fois par changement**, et jamais si la valeur ne
      change pas. `rangeChanged` est émis avant `valueChanged` quand les deux changent, comme
      dans `QAbstractSlider`.

    Suivi
    -----
    `hasTracking`/`setTracking` (vrai par défaut) règle à la fois le suivi du curseur
    (`QAbstractSlider.tracking`) et celui du clavier de la boîte numérique
    (`QAbstractSpinBox.keyboardTracking`).

    - **Avec suivi**, la valeur change pendant le glissement et à chaque touche tapée.
    - **Sans suivi**, la boîte numérique affiche la position de la poignée pendant le
      glissement, mais la valeur ne change qu'au relâchement. Un nombre tapé ne compte qu'à
      Entrée ou à la perte du focus. Les flèches, les touches de page et la molette changent
      la valeur immédiatement, dans les deux cas, comme dans Qt.

    Fin d'une interaction
    ---------------------
    `editingFinished` est émis au relâchement de la poignée (après le `valueChanged` qu'il
    provoque), ou quand la boîte numérique termine une saisie (Entrée, perte du focus), comme
    `QAbstractSpinBox.editingFinished`.

    Affichage
    ---------
    - Boîte numérique : `prefix`/`setPrefix`, `suffix`/`setSuffix`,
      `specialValueText`/`setSpecialValueText` (texte affiché au minimum) et
      `wrapping`/`setWrapping` (les flèches passent du maximum au minimum ; le curseur suit).
    - Curseur : `tickPosition`/`setTickPosition` et `tickInterval`/`setTickInterval`, en
      unités de valeur.
    - Disposition : `orientation`/`setOrientation`. À l'horizontale (par défaut), la boîte
      numérique est à droite du curseur ; à la verticale, elle est en dessous. Comme
      `QSlider.setOrientation`, changer l'orientation remplace la politique de taille du
      widget.

    Le focus du widget est délégué à la boîte numérique (`focusProxy`).

    Attributs:
        valueChanged: Signal(T). Émis une fois quand la valeur change, quelle qu'en soit la
            cause. Déclaré par chaque classe concrète.
        rangeChanged: Signal(T, T). Émis quand les bornes changent. Déclaré par chaque classe
            concrète.
        editingFinished: Signal(). Émis à la fin d'une interaction (voir plus haut).

    Slots:
        setValue(T), setMinimum(T), setMaximum(T), setRange(T, T), setSingleStep(T),
        setPageStep(T), setTickInterval(T), setTracking(bool), setWrapping(bool),
        setPrefix(str), setSuffix(str), setSpecialValueText(str),
        setOrientation(Qt.Orientation), setTickPosition(QSlider.TickPosition).

    Sous-classes
    ------------
    Une classe concrète fournit deux choses, et seulement celles-là :

    - **ses deux widgets internes**, créés dans son propre constructeur puis passés à celui de
      cette base (injection par le constructeur) ;
    - **ses deux signaux typés**, `valueChanged` et `rangeChanged`, déclarés comme attributs de
      classe (`Signal(int)`, `Signal(float)`...). Ce sont les membres abstraits de cette base :
      tant qu'ils manquent, instancier la classe lève `TypeError` en les nommant, comme pour
      toute classe abstraite (voir `QAbstractWidget`).
    """

    editingFinished = Signal()

    # Abstract members: the typed signals, which a generic base cannot declare (`Signal(T)` does
    # not exist). At run time, an abstract property is the standard way to require an attribute
    # from a subclass, which replaces it with its `Signal` (these bodies never run). A type
    # checker rejects a `Signal` replacing a property, so it is shown the class attribute instead.
    if TYPE_CHECKING:
        valueChanged: ClassVar[Signal]
        rangeChanged: ClassVar[Signal]
    else:
        @property
        @abstractmethod
        def valueChanged(self) -> SignalInstance:
            """Signal(T), déclaré par chaque classe concrète (ex. `valueChanged = Signal(int)`)."""

        @property
        @abstractmethod
        def rangeChanged(self) -> SignalInstance:
            """Signal(T, T), déclaré par chaque classe concrète (ex. `rangeChanged = Signal(int, int)`)."""

    def __init__(self, slider: _ValueSlider[T], spinBox: _ValueControl[T],
                 orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        """Dispose côte à côte les deux widgets internes fournis par la classe concrète.

        Les valeurs initiales sont celles du curseur (ex. [0, 99] pour `QSlider`, [0.0, 1.0] pour
        `QRealSlider`) ; la boîte numérique les reprend. Les deux widgets deviennent des enfants
        Qt de ce widget, qui ne les expose pas.

        Args:
            slider: Le curseur interne, un `QSlider` qui porte des valeurs de type `T`.
            spinBox: La boîte numérique interne, un `QSpinBox` ou un `QDoubleSpinBox` qui porte
                des valeurs de type `T`.
            orientation: Orientation du curseur, qui fixe aussi la disposition.
            parent: Widget parent, ou None.

        Lève:
            TypeError: Si `slider` n'est pas un `QSlider`, ou `spinBox` ni un `QSpinBox` ni un
                `QDoubleSpinBox`.
        """
        super().__init__(parent)
        # Two views of each internal widget: the protocol types the members that carry a T
        # (QSlider alone would say int), the Qt type the members that carry no value. The
        # protocol views are taken first: the isinstance checks below narrow the arguments to
        # their Qt types, which say int or float instead of T.
        self.__slider: QAbstractSliderSpinBox._ValueSlider[T] = slider
        self.__spinBox: QAbstractSliderSpinBox._ValueControl[T] = spinBox
        if not isinstance(slider, QSlider):
            raise TypeError("slider must be a QSlider.")
        if not isinstance(spinBox, (QSpinBox, QDoubleSpinBox)):
            raise TypeError("spinBox must be a QSpinBox or a QDoubleSpinBox.")
        self.__sliderWidget: QSlider = slider
        self.__spinBoxWidget: QSpinBox | QDoubleSpinBox = spinBox

        self.__layout: QBoxLayout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.addWidget(slider, 1)
        self.__layout.addWidget(spinBox)
        self.setFocusProxy(spinBox)

        self.__syncSpinBox()
        slider.valueChanged.connect(self.__copySliderValue)
        slider.sliderMoved.connect(self.__showSliderPosition)
        slider.sliderReleased.connect(self.__commitSliderPosition)
        spinBox.valueChanged.connect(self.__copySpinBoxValue)
        spinBox.editingFinished.connect(self.editingFinished)
        self.setOrientation(orientation)

    # ============================================================ value, range

    def value(self) -> T:
        """La valeur actuelle (celle retenue ; sans suivi, pas la position d'une poignée glissée)."""
        return self.__slider.value()

    # Slots typed `object`: the slot is shared by the int and the float subclasses.
    @Slot(object)
    def setValue(self, v: T) -> None:
        """Fixe la valeur, bornée à l'intervalle (et arrondie aux décimales, en réel)."""
        self._applyAndReport(lambda: self.__slider.setValue(v))

    def minimum(self) -> T:
        """La borne inférieure."""
        return self.__slider.minimum()

    @Slot(object)
    def setMinimum(self, lo: T) -> None:
        """Fixe le minimum, en déplaçant le maximum au besoin (comme `setMinimum` de Qt)."""
        self.setRange(lo, max(self.maximum(), lo))

    def maximum(self) -> T:
        """La borne supérieure."""
        return self.__slider.maximum()

    @Slot(object)
    def setMaximum(self, hi: T) -> None:
        """Fixe le maximum, en déplaçant le minimum au besoin (comme `setMaximum` de Qt)."""
        self.setRange(min(self.minimum(), hi), hi)

    @Slot(object, object)
    def setRange(self, lo: T, hi: T) -> None:
        """Fixe l'intervalle ; un maximum inférieur au minimum devient le minimum (comme Qt).

        La valeur est bornée au nouvel intervalle. `rangeChanged` puis `valueChanged` sont émis
        si ce qu'ils rapportent change.
        """
        self._applyAndReport(lambda: self.__slider.setRange(lo, max(lo, hi)))

    # =================================================================== steps

    def singleStep(self) -> T:
        """Le pas simple effectif, commun aux deux widgets."""
        return self.__slider.singleStep()

    @Slot(object)
    def setSingleStep(self, s: T) -> None:
        """Fixe le pas simple des deux widgets, selon les règles du curseur interne."""
        self._applyAndReport(lambda: self.__slider.setSingleStep(s))

    def pageStep(self) -> T:
        """Le pas de page effectif du curseur."""
        return self.__slider.pageStep()

    @Slot(object)
    def setPageStep(self, p: T) -> None:
        """Fixe le pas de page du curseur (touches de page, clic dans la piste)."""
        self.__slider.setPageStep(p)

    # ================================================================ tracking

    def hasTracking(self) -> bool:
        """Indique si la valeur suit le glissement de la poignée et la frappe au clavier."""
        return self.__sliderWidget.hasTracking()

    @Slot(bool)
    def setTracking(self, enable: bool) -> None:
        """Active ou désactive le suivi du curseur et celui du clavier de la boîte numérique."""
        self.__sliderWidget.setTracking(enable)
        self.__spinBoxWidget.setKeyboardTracking(enable)

    # ========================================================= spin box display

    def prefix(self) -> str:
        """Le texte affiché devant la valeur dans la boîte numérique."""
        return self.__spinBoxWidget.prefix()

    @Slot(str)
    def setPrefix(self, text: str) -> None:
        """Fixe le texte affiché devant la valeur dans la boîte numérique."""
        self.__spinBoxWidget.setPrefix(text)

    def suffix(self) -> str:
        """Le texte affiché après la valeur dans la boîte numérique."""
        return self.__spinBoxWidget.suffix()

    @Slot(str)
    def setSuffix(self, text: str) -> None:
        """Fixe le texte affiché après la valeur dans la boîte numérique (ex. une unité)."""
        self.__spinBoxWidget.setSuffix(text)

    def specialValueText(self) -> str:
        """Le texte affiché à la place du minimum, ou une chaîne vide."""
        return self.__spinBoxWidget.specialValueText()

    @Slot(str)
    def setSpecialValueText(self, text: str) -> None:
        """Fixe le texte affiché à la place du minimum (ex. « Auto ») ; vide pour l'annuler."""
        self.__spinBoxWidget.setSpecialValueText(text)

    def wrapping(self) -> bool:
        """Indique si les flèches de la boîte numérique passent d'une borne à l'autre."""
        return self.__spinBoxWidget.wrapping()

    @Slot(bool)
    def setWrapping(self, enable: bool) -> None:
        """Active ou désactive le passage d'une borne à l'autre par les flèches de la boîte numérique."""
        self.__spinBoxWidget.setWrapping(enable)

    # =========================================================== slider display

    def orientation(self) -> Qt.Orientation:
        """L'orientation du curseur, qui fixe aussi la disposition."""
        return self.__sliderWidget.orientation()

    @Slot(Qt.Orientation)
    def setOrientation(self, orientation: Qt.Orientation) -> None:
        """Oriente le curseur et la disposition : boîte numérique à droite (horizontale) ou en
        dessous (verticale). Remplace la politique de taille du widget, comme `QSlider`."""
        self.__sliderWidget.setOrientation(orientation)
        if orientation == Qt.Orientation.Horizontal:
            self.__layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self.__layout.setAlignment(self.__sliderWidget, Qt.AlignmentFlag(0))
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.__layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self.__layout.setAlignment(self.__sliderWidget, Qt.AlignmentFlag.AlignHCenter)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def tickPosition(self) -> QSlider.TickPosition:
        """La position des graduations du curseur."""
        return self.__sliderWidget.tickPosition()

    @Slot(QSlider.TickPosition)
    def setTickPosition(self, position: QSlider.TickPosition) -> None:
        """Fixe la position des graduations du curseur (`NoTicks` pour les masquer)."""
        self.__sliderWidget.setTickPosition(position)

    def tickInterval(self) -> T:
        """L'intervalle entre deux graduations, en unités de valeur (0 : automatique)."""
        return self.__slider.tickInterval()

    @Slot(object)
    def setTickInterval(self, t: T) -> None:
        """Fixe l'intervalle entre deux graduations, selon les règles du curseur interne."""
        self.__slider.setTickInterval(t)

    # ================================================================ protected

    class _ValueControl[V](Protocol):
        """Les membres qui portent une valeur `V`, communs au curseur et à la boîte numérique.

        `QSlider` et `QSpinBox` le satisfont avec `int`, `QRealSlider` et `QDoubleSpinBox` avec
        `float`, sans ancêtre commun qui le dise.
        """

        def value(self) -> V: ...
        def setValue(self, v: V, /) -> None: ...
        def minimum(self) -> V: ...
        def maximum(self) -> V: ...
        def setRange(self, lo: V, hi: V, /) -> None: ...
        def singleStep(self) -> V: ...
        def setSingleStep(self, s: V, /) -> None: ...

    class _ValueSlider[V](_ValueControl[V], Protocol):
        """Les membres qui portent une valeur `V`, propres au curseur."""

        def sliderPosition(self) -> V: ...
        def pageStep(self) -> V: ...
        def setPageStep(self, p: V, /) -> None: ...
        def tickInterval(self) -> V: ...
        def setTickInterval(self, t: V, /) -> None: ...

    def _applyAndReport(self, change: Callable[[], object], announce: Callable[[], object] | None = None) -> None:
        """Applique `change` au curseur sans qu'aucun widget interne n'émette, recopie le
        résultat dans la boîte numérique, puis émet ce qui a changé.

        Args:
            change: La modification, appliquée au curseur interne (et, au besoin, à la boîte
                numérique), signaux bloqués. Si elle lève, rien n'est émis.
            announce: Appelé après la modification, avant `rangeChanged` et `valueChanged`
                (ex. pour émettre `decimalsChanged` en premier, comme `QRealSlider`).
        """
        oldRange = (self.minimum(), self.maximum())
        oldValue = self.value()
        with QSignalBlocker(self.__sliderWidget), QSignalBlocker(self.__spinBoxWidget):
            try:
                change()
            finally:
                self.__syncSpinBox()
        if announce is not None:
            announce()
        newRange = (self.minimum(), self.maximum())
        if newRange != oldRange:
            self.rangeChanged.emit(*newRange)
        if self.value() != oldValue:
            self.valueChanged.emit(self.value())

    # ================================================================== private

    def __syncSpinBox(self) -> None:
        """Recopie dans la boîte numérique les bornes, le pas et la valeur retenus par le curseur."""
        self.__spinBox.setRange(self.__slider.minimum(), self.__slider.maximum())
        self.__spinBox.setSingleStep(self.__slider.singleStep())
        self.__spinBox.setValue(self.__slider.value())

    @Slot(object)
    def __copySliderValue(self, v: T) -> None:
        with QSignalBlocker(self.__spinBoxWidget):
            self.__spinBox.setValue(v)
        self.valueChanged.emit(v)

    @Slot(object)
    def __showSliderPosition(self, position: T) -> None:
        with QSignalBlocker(self.__spinBoxWidget):   # shows the position, even without tracking
            self.__spinBox.setValue(position)

    @Slot()
    def __commitSliderPosition(self) -> None:
        # Qt reports the release before committing the position (without tracking): committing
        # it here keeps valueChanged ahead of editingFinished.
        self.__slider.setValue(self.__slider.sliderPosition())
        self.editingFinished.emit()

    @Slot(object)
    def __copySpinBoxValue(self, v: T) -> None:
        # With keyboard tracking, Qt emits valueChanged again on Enter, unchanged.
        old = self.value()
        with QSignalBlocker(self.__sliderWidget):
            self.__slider.setValue(v)
        if self.value() != old:
            self.valueChanged.emit(self.value())


# -----------------------------------------------------------------------------
#                              Concrete classes
# -----------------------------------------------------------------------------

class QSliderSpinBox(QAbstractSliderSpinBox[int]):
    """Un `QSlider` et un `QSpinBox` côte à côte, qui portent un seul entier.

    Voir `QAbstractSliderSpinBox` pour la documentation complète. Valeurs initiales : celles
    de `QSlider`, soit l'intervalle [0, 99], la valeur 0, un pas simple de 1 et un pas de page
    de 10.

    Limites
    -------
    Celles de `QSlider` sous PySide6 : une valeur qui ne tient pas dans un `int` C++ (32 bits),
    NaN compris, lève `OverflowError` (précédée d'un `RuntimeWarning` de PySide6), et une
    valeur qui n'est pas un nombre lève `TypeError`. Le widget reste alors inchangé.

    ```python
    box = QSliderSpinBox()
    box.setRange(0, 255)
    box.setPrefix("R = ")
    box.valueChanged.connect(print)
    ```
    """

    valueChanged = Signal(int)
    rangeChanged = Signal(int, int)

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        """Construit le widget.

        Args:
            orientation: Orientation du curseur, qui fixe aussi la disposition.
            parent: Widget parent, ou None.
        """
        super().__init__(QSlider(), QSpinBox(), orientation, parent)


class QRealSliderSpinBox(QAbstractSliderSpinBox[float]):
    """Un `QRealSlider` et un `QDoubleSpinBox` côte à côte, qui portent un seul réel.

    Voir `QAbstractSliderSpinBox` pour la documentation complète. Valeurs initiales : celles de
    `QRealSlider`, soit l'intervalle [0.0, 1.0], la valeur 0.0 et 2 décimales.

    Décimales
    ---------
    `decimals`/`setDecimals` règlent les deux widgets à la fois ; `resolution()` donne la taille
    d'un pas (10**-decimals). Les deux widgets arrondissent de la même façon : celle de
    `QDoubleSpinBox`. Les règles sont celles de `QRealSlider` : changer les décimales
    ré-exprime les bornes et la valeur, puis `decimalsChanged`, `rangeChanged` et
    `valueChanged` sont émis, dans cet ordre, pour ce qui a changé.

    Limites
    -------
    Celles de `QRealSlider` : l'intervalle compte au plus 2**31 - 1 pas, et les décimales vont
    de 0 à 15. Au-delà, `ValueError` est levée et le widget reste inchangé. NaN et l'infini
    lèvent `ValueError` ; une valeur qui n'est pas un nombre lève `TypeError`.

    ```python
    box = QRealSliderSpinBox()
    box.setDecimals(1)
    box.setRange(-5.0, 5.0)
    box.setSuffix(" V")
    box.setValue(1.25)        # retient 1.3, comme un QDoubleSpinBox à 1 décimale
    ```

    Attributs:
        decimalsChanged: Signal(int). Émis quand le nombre de décimales change, avant
            `rangeChanged` et `valueChanged`.

    Slots:
        setDecimals(int): En plus des slots de `QAbstractSliderSpinBox`.
    """

    valueChanged = Signal(float)
    rangeChanged = Signal(float, float)
    decimalsChanged = Signal(int)

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        """Construit le widget, avec 2 décimales.

        Args:
            orientation: Orientation du curseur, qui fixe aussi la disposition.
            parent: Widget parent, ou None.
        """
        slider = QRealSlider()
        spinBox = QDoubleSpinBox()
        spinBox.setDecimals(slider.decimals())
        super().__init__(slider, spinBox, orientation, parent)
        self.__realSlider: QRealSlider = slider
        self.__doubleSpinBox: QDoubleSpinBox = spinBox

    # ================================================================ decimals

    def decimals(self) -> int:
        """Le nombre de décimales des deux widgets (2 par défaut)."""
        return self.__realSlider.decimals()

    @Slot(int)
    def setDecimals(self, digits: int) -> None:
        """Fixe le nombre de décimales des deux widgets, en ré-exprimant bornes, valeur et pas.

        Lève:
            TypeError: Si `digits` n'est pas un entier.
            ValueError: Si `digits` n'est pas dans [0, 15], ou si l'intervalle compterait trop
                de pas.
        """
        old = self.decimals()

        def change() -> None:
            self.__realSlider.setDecimals(digits)    # validates first: raises before any change
            self.__doubleSpinBox.setDecimals(digits)

        def announce() -> None:
            if self.decimals() != old:
                self.decimalsChanged.emit(self.decimals())

        self._applyAndReport(change, announce)

    def resolution(self) -> float:
        """La taille d'un pas : 10**-decimals."""
        return self.__realSlider.resolution()
