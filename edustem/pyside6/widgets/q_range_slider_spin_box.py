"""Curseur à deux poignées et boîte à intervalle côte à côte, toujours synchronisés :
`QRangeSliderSpinBox` (entiers) et `QRealRangeSliderSpinBox` (réels).

L'utilisateur choisit un intervalle en glissant les poignées ou en le tapant ; le programme ne
voit qu'un seul widget, un seul intervalle et un seul `rangeChanged`. Les deux widgets internes
ne sont pas exposés : l'interface publique reprend les noms de `QRangeSlider` (`limits`,
`setLimits`, `range`, `setRange`, `lowerValue`, `collisionMode`...), avec le type de nombre de
la classe concrète.

    box = QRealRangeSliderSpinBox()
    box.setLimits(-10.0, 10.0)
    box.setRange(-2.5, 3.75)
    box.setSuffix(" m")
    box.rangeChanged.connect(print)

Dépendances locales : ce fichier compose `QRangeSlider` (`q_range_slider`) et `QRangeSpinBox`
(`q_range_spin_box`), et hérite de `QAbstractWidget` (`q_abstract_widget`). C'est sa raison
d'être. La notation vient de `QIntervalFormat` (`core/q_interval_format`).
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

from PySide6.QtCore import QSignalBlocker, Qt, Signal, SignalInstance, Slot
from PySide6.QtWidgets import QBoxLayout, QSizePolicy, QSlider, QWidget

from ..core.q_interval_format import QIntervalFormat
from .q_abstract_widget import QAbstractWidget
from .q_range_slider import QAbstractRangeSlider, QRangeSlider, QRealRangeSlider
from .q_range_spin_box import QAbstractRangeSpinBox, QRangeSpinBox, QRealRangeSpinBox


class QAbstractRangeSliderSpinBox[T: (int, float)](QAbstractWidget):
    """Base abstraite d'un curseur à deux poignées et d'une boîte à intervalle côte à côte, qui
    portent un seul intervalle de nombres de type `T` (`int` ou `float`).

    Les classes concrètes sont `QRangeSliderSpinBox` (`QRangeSlider` et `QRangeSpinBox`) et
    `QRealRangeSliderSpinBox` (`QRealRangeSlider` et `QRealRangeSpinBox`). Cette base fait la
    disposition, la synchronisation et toute l'interface commune ; chaque classe concrète
    choisit ses deux widgets internes et déclare ses signaux typés.

    Deux intervalles
    ----------------
    Le vocabulaire est celui de `QAbstractRangeSlider` :

    - **les limites** (`limits`) sont l'intervalle possible, `[minimum, maximum]` ;
    - **l'intervalle choisi** (`range`) est `[lowerValue, upperValue]`.

    L'ordre `minimum <= lowerValue <= upperValue <= maximum` est toujours vrai.

    Règles
    ------
    Les mutateurs suivent les règles du curseur interne, qui sert de référence : bornage,
    arrondi, rencontre des bornes (`overlapAllowed`, `collisionMode`), pas minimal, nombre de
    pas permis, exceptions. La boîte à intervalle reçoit ensuite exactement ce que le curseur a
    retenu. Une opération refusée (exception) ne change ni l'un ni l'autre.

    Les réglages dont dépendent ces règles sont toujours les mêmes dans les deux widgets :
    limites, pas simple, `overlapAllowed`, `collisionMode`, format de l'intervalle et, en réel,
    décimales. Une borne poussée au clavier dans la boîte suit donc la même règle qu'une
    poignée glissée.

    Tout l'intervalle
    -----------------
    Même API que `QAbstractRangeSlider`, avec le vocabulaire de `QRect` : `length()` et
    `center()` (un `float`, qui peut tomber entre deux pas) ; `setLength` (à borne inférieure
    constante) et `widenBy` (à centre constant) changent la longueur ; `moveLowerValue`,
    `moveUpperValue`, `moveCenter` et `shiftBy` déplacent tout l'intervalle, à longueur
    constante. Ce qu'une opération garde n'est jamais modifié ; c'est sa cible qui s'arrête
    aux limites (voir `IntervalRules`, `core/interval_rules`).

    Les gestes sont ceux des deux widgets internes, qui gardent les conventions de `QSlider`
    et de `QSpinBox` : Maj + flèche élargit ou resserre l'intervalle dans l'un et l'autre ;
    tout l'intervalle se déplace en glissant le segment ou avec `Handle.Both` dans le
    curseur, ou quand tout le texte est sélectionné dans la boîte.

    - **Le pas simple** sert aux flèches de la boîte, aux flèches du clavier et à la molette sur
      le curseur.
    - **Le pas de page** ne concerne que le curseur (touches de page, clic dans la rainure).

    Synchronisation
    ---------------
    - Le curseur et la boîte affichent toujours le même intervalle, quelle que soit la source du
      changement : l'un ou l'autre widget, un mutateur, un bornage ou un arrondi.
    - **Chaque signal est émis une seule fois par changement**, et jamais si ce qu'il rapporte
      ne change pas. `limitsChanged` précède `lowerValueChanged` et `upperValueChanged`, qui
      précèdent `rangeChanged`, comme dans `QAbstractRangeSlider`.

    Suivi
    -----
    `hasTracking`/`setTracking` (vrai par défaut) règle à la fois le suivi du curseur et celui du
    clavier de la boîte (`QAbstractSpinBox.keyboardTracking`).

    - **Avec suivi**, l'intervalle change pendant le glissement et à chaque touche tapée.
    - **Sans suivi**, la boîte affiche la position des poignées pendant le glissement, mais
      l'intervalle ne change qu'au relâchement. Un intervalle tapé ne compte qu'à Entrée ou à la
      perte du focus. Les flèches, les touches de page et la molette changent l'intervalle
      immédiatement, dans les deux cas.

    Fin d'une interaction
    ---------------------
    `editingFinished` est émis au relâchement d'une poignée ou du segment (après les signaux de
    l'intervalle qu'il provoque), ou quand la boîte termine une saisie (Entrée, perte du focus),
    comme `QAbstractSpinBox.editingFinished`.

    Affichage
    ---------
    - Boîte : `prefix`/`setPrefix`, `suffix`/`setSuffix` (ex. une unité) et
      `isFreeEntryEnabled`/`setFreeEntryEnabled` (voir `QAbstractRangeSpinBox`). La piste de la
      boîte est masquée : le curseur montre déjà où se trouve l'intervalle.
    - Curseur : `tickPosition`/`setTickPosition` et `tickInterval`/`setTickInterval`, en unités
      de valeur.
    - Texte : `text()` écrit l'intervalle choisi dans le format, sans préfixe ni suffixe, comme
      `QAbstractRangeSlider.text()` ; `textFromRange` écrit n'importe quel intervalle. Le format
      (`intervalFormat`/`setIntervalFormat`) sert aux deux widgets, et les nombres suivent la
      langue du widget (`locale()`), que les deux widgets internes reprennent.
    - Disposition : `orientation`/`setOrientation`. À l'horizontale (par défaut), la boîte est à
      droite du curseur ; à la verticale, elle est en dessous. Comme
      `QSlider.setOrientation`, changer l'orientation remplace la politique de taille du
      widget.

    Le focus du widget est délégué à la boîte (`focusProxy`).

    Propriétés:
        minimum (T): La limite inférieure. Accesseur `minimum()`, mutateur `setMinimum()`,
            signal `limitsChanged`.
        maximum (T): La limite supérieure. Accesseur `maximum()`, mutateur `setMaximum()`,
            signal `limitsChanged`.
        lowerValue (T): La borne inférieure. Accesseur `lowerValue()`, mutateur
            `setLowerValue()`, signal `lowerValueChanged`.
        upperValue (T): La borne supérieure. Accesseur `upperValue()`, mutateur
            `setUpperValue()`, signal `upperValueChanged`.
        singleStep (T): Accesseur `singleStep()`, mutateur `setSingleStep()`.
        pageStep (T): Accesseur `pageStep()`, mutateur `setPageStep()`.
        tracking (bool): Accesseur `hasTracking()`, mutateur `setTracking()`.
        overlapAllowed (bool): Accesseur `overlapAllowed()`, mutateur `setOverlapAllowed()`.
        collisionMode (CollisionMode): Accesseur `collisionMode()`, mutateur
            `setCollisionMode()`.
        intervalFormat (QIntervalFormat): Accesseur `intervalFormat()` (une copie), mutateur
            `setIntervalFormat()`.
        prefix (str): Accesseur `prefix()`, mutateur `setPrefix()`.
        suffix (str): Accesseur `suffix()`, mutateur `setSuffix()`.
        freeEntryEnabled (bool): Accesseur `isFreeEntryEnabled()`, mutateur
            `setFreeEntryEnabled()`.
        orientation (Qt.Orientation): Accesseur `orientation()`, mutateur `setOrientation()`.
        tickPosition (QSlider.TickPosition): Accesseur `tickPosition()`, mutateur
            `setTickPosition()`.
        tickInterval (T): Accesseur `tickInterval()`, mutateur `setTickInterval()`.

    Signaux:
        lowerValueChanged: Signal(T). Émis quand la borne inférieure change. Déclaré par chaque
            classe concrète.
        upperValueChanged: Signal(T). Émis quand la borne supérieure change. Déclaré par chaque
            classe concrète.
        rangeChanged: Signal(T, T). Émis une fois quand l'une ou l'autre borne change, après les
            deux signaux précédents. Déclaré par chaque classe concrète.
        limitsChanged: Signal(T, T). Émis quand les limites changent, avant les signaux des
            bornes. Déclaré par chaque classe concrète.
        editingFinished: Signal(). Émis à la fin d'une interaction (voir plus haut).

    Slots:
        setLimits(T, T), setMinimum(T), setMaximum(T), setRange(T, T), setLowerValue(T),
        setUpperValue(T), setLength(T), widenBy(int), shiftBy(int), moveLowerValue(T),
        moveUpperValue(T), moveCenter(float), setSingleStep(T), setPageStep(T), setTickInterval(T),
        setTracking(bool), setOverlapAllowed(bool), setCollisionMode(CollisionMode),
        setIntervalFormat(QIntervalFormat), setPrefix(str), setSuffix(str),
        setFreeEntryEnabled(bool), setOrientation(Qt.Orientation),
        setTickPosition(QSlider.TickPosition).

    Sous-classes
    ------------
    Une classe concrète fournit deux choses, et seulement celles-là :

    - **ses deux widgets internes**, créés dans son propre constructeur puis passés à celui de
      cette base (injection par le constructeur). La base recopie les réglages du curseur dans
      la boîte ; les décimales, propres aux réels, sont l'affaire de la classe concrète ;
    - **ses quatre signaux typés**, `lowerValueChanged`, `upperValueChanged`, `rangeChanged` et
      `limitsChanged`, déclarés comme attributs de classe. Ce sont les membres abstraits de
      cette base : tant qu'un d'eux manque, instancier la classe lève `TypeError` en le
      nommant (voir `QAbstractWidget`).
    """

    CollisionMode = QAbstractRangeSlider.CollisionMode

    editingFinished = Signal()

    # Abstract members: the typed signals, which a generic base cannot declare. See
    # `QAbstractSliderSpinBox`, which does the same, for why a property stands for them.
    if TYPE_CHECKING:
        lowerValueChanged: ClassVar[Signal]
        upperValueChanged: ClassVar[Signal]
        rangeChanged: ClassVar[Signal]
        limitsChanged: ClassVar[Signal]
    else:
        @property
        @abstractmethod
        def lowerValueChanged(self) -> SignalInstance:
            """Signal(T), déclaré par chaque classe concrète."""

        @property
        @abstractmethod
        def upperValueChanged(self) -> SignalInstance:
            """Signal(T), déclaré par chaque classe concrète."""

        @property
        @abstractmethod
        def rangeChanged(self) -> SignalInstance:
            """Signal(T, T), déclaré par chaque classe concrète."""

        @property
        @abstractmethod
        def limitsChanged(self) -> SignalInstance:
            """Signal(T, T), déclaré par chaque classe concrète."""

    def __init__(self, slider: QAbstractRangeSlider[T], spinBox: QAbstractRangeSpinBox[T],
                 orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        """Dispose côte à côte les deux widgets internes fournis par la classe concrète.

        Les valeurs initiales et les réglages sont ceux du curseur (ex. les limites [0, 99] de
        `QRangeSlider`, [0.0, 1.0] pour `QRealRangeSlider`) ; la boîte les reprend. Les deux
        widgets deviennent des enfants Qt de ce widget, qui ne les expose pas.

        Args:
            slider: Le curseur interne, qui porte des nombres de type `T`.
            spinBox: La boîte à intervalle interne, qui porte des nombres de type `T`.
            orientation: Orientation du curseur, qui fixe aussi la disposition.
            parent: Widget parent, ou None.

        Lève:
            TypeError: Si `slider` n'est pas un `QAbstractRangeSlider`, ou `spinBox` pas un
                `QAbstractRangeSpinBox`.
        """
        super().__init__(parent)
        if not isinstance(slider, QAbstractRangeSlider):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("slider must be a QAbstractRangeSlider.")
        if not isinstance(spinBox, QAbstractRangeSpinBox):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("spinBox must be a QAbstractRangeSpinBox.")
        self.__slider: QAbstractRangeSlider[T] = slider
        self.__spinBox: QAbstractRangeSpinBox[T] = spinBox

        self.__layout: QBoxLayout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.addWidget(slider, 1)
        self.__layout.addWidget(spinBox)
        self.setFocusProxy(spinBox)

        with QSignalBlocker(spinBox):
            spinBox.setTrackVisible(False)
            spinBox.setKeyboardTracking(slider.hasTracking())
            spinBox.setOverlapAllowed(slider.overlapAllowed())
            spinBox.setCollisionMode(slider.collisionMode())
            spinBox.setIntervalFormat(slider.intervalFormat())
            self.__syncSpinBox()
        self.__reportedLimits: tuple[T, T] = slider.limits()
        self.__reportedRange: tuple[T, T] = slider.range()

        slider.rangeChanged.connect(self.__copySliderRange)
        slider.sliderMoved.connect(self.__showSliderPositions)
        slider.sliderReleased.connect(self.__finishEditing)
        spinBox.rangeChanged.connect(self.__copySpinBoxRange)
        spinBox.editingFinished.connect(self.editingFinished)
        self.setOrientation(orientation)

    # ================================================================== limits

    def minimum(self) -> T:
        """La limite inférieure de l'intervalle possible."""
        return self.__slider.minimum()

    # Slots typed `object`: the slot is shared by the int and the float subclasses.
    @Slot(object)
    def setMinimum(self, minimum: T) -> None:
        """Fixe la limite inférieure, en déplaçant la limite supérieure au besoin (comme `QSlider.setMinimum`)."""
        self.setLimits(minimum, max(self.maximum(), minimum))

    def maximum(self) -> T:
        """La limite supérieure de l'intervalle possible."""
        return self.__slider.maximum()

    @Slot(object)
    def setMaximum(self, maximum: T) -> None:
        """Fixe la limite supérieure, en déplaçant la limite inférieure au besoin (comme `QSlider.setMaximum`)."""
        self.setLimits(min(self.minimum(), maximum), maximum)

    def limits(self) -> tuple[T, T]:
        """L'intervalle possible, `(minimum, maximum)`."""
        return self.__slider.limits()

    @Slot(object, object)
    def setLimits(self, minimum: T, maximum: T) -> None:
        """Fixe l'intervalle possible ; un maximum inférieur au minimum devient le minimum.

        L'intervalle choisi est ramené dans les nouvelles limites. `limitsChanged`, puis les
        signaux des bornes, sont émis pour ce qui change.

        Lève:
            TypeError: Si une limite n'est pas un nombre du type attendu.
            ValueError: Si une limite n'est pas finie, ou si les limites comptent trop de pas
                pour le curseur (voir `QAbstractRangeSlider`).
        """
        self._applyAndReport(lambda: self.__slider.setLimits(minimum, maximum))

    # =================================================================== range

    def lowerValue(self) -> T:
        """La borne inférieure (celle retenue ; sans suivi, pas la position d'une poignée glissée)."""
        return self.__slider.lowerValue()

    @Slot(object)
    def setLowerValue(self, lower: T) -> None:
        """Fixe la borne inférieure, selon le mode de collision.

        Lève:
            TypeError: Si `lower` n'est pas un nombre du type attendu.
            ValueError: Si `lower` n'est pas fini.
        """
        self._applyAndReport(lambda: self.__slider.setLowerValue(lower))

    def upperValue(self) -> T:
        """La borne supérieure (celle retenue ; sans suivi, pas la position d'une poignée glissée)."""
        return self.__slider.upperValue()

    @Slot(object)
    def setUpperValue(self, upper: T) -> None:
        """Fixe la borne supérieure, selon le mode de collision.

        Lève:
            TypeError: Si `upper` n'est pas un nombre du type attendu.
            ValueError: Si `upper` n'est pas fini.
        """
        self._applyAndReport(lambda: self.__slider.setUpperValue(upper))

    def range(self) -> tuple[T, T]:
        """L'intervalle choisi, `(lowerValue, upperValue)`."""
        return self.__slider.range()

    @Slot(object, object)
    def setRange(self, lower: T, upper: T) -> None:
        """Fixe les deux bornes d'un seul coup : triées, puis ramenées dans les limites.

        Le mode de collision ne joue pas ici. `rangeChanged` n'est émis qu'une fois.

        Lève:
            TypeError: Si une borne n'est pas un nombre du type attendu.
            ValueError: Si une borne n'est pas finie.
        """
        self._applyAndReport(lambda: self.__slider.setRange(lower, upper))

    # ========================================================== whole interval

    def length(self) -> T:
        """La longueur de l'intervalle choisi, `upperValue() - lowerValue()`, sans erreur d'arrondi."""
        return self.__slider.length()

    @Slot(object)
    def setLength(self, length: T) -> None:
        """Fixe la longueur, à borne inférieure constante (comme `QLineF.setLength`).

        La longueur s'arrête à `maximum() - lowerValue()`. Elle ne descend pas sous 0, ni sous
        un pas si l'égalité des bornes est interdite.

        Lève:
            TypeError: Si `length` n'est pas un nombre du type attendu.
            ValueError: Si `length` n'est pas fini.
        """
        self._applyAndReport(lambda: self.__slider.setLength(length))

    @Slot(int)
    def widenBy(self, steps: int) -> None:
        """Écarte chaque borne de `steps` pas simples, à centre constant ; un nombre négatif les rapproche.

        En s'écartant, les deux bornes s'arrêtent dès que l'une touche sa limite. En se
        rapprochant, elles s'arrêtent à la plus petite longueur permise qui garde le centre.
        """
        self._applyAndReport(lambda: self.__slider.widenBy(steps))

    def center(self) -> float:
        """Le centre de l'intervalle choisi ; un `float`, qui peut tomber entre deux pas."""
        return self.__slider.center()

    @Slot(float)
    def moveCenter(self, center: float) -> None:
        """Déplace tout l'intervalle pour que son centre soit au plus près de `center`, à longueur constante.

        Comme `QRect.moveCenter`. La borne inférieure qui en découle est arrondie au pas, les
        égalités en s'éloignant de zéro ; l'intervalle s'arrête contre une limite.

        Lève:
            TypeError: Si `center` n'est pas un nombre.
            ValueError: Si `center` n'est pas fini.
        """
        self._applyAndReport(lambda: self.__slider.moveCenter(center))

    @Slot(object)
    def moveLowerValue(self, lower: T) -> None:
        """Déplace tout l'intervalle pour que sa borne inférieure soit `lower`, à longueur constante.

        Comme `QRect.moveLeft` ; l'intervalle s'arrête contre une limite.

        Lève:
            TypeError: Si `lower` n'est pas un nombre du type attendu.
            ValueError: Si `lower` n'est pas fini.
        """
        self._applyAndReport(lambda: self.__slider.moveLowerValue(lower))

    @Slot(object)
    def moveUpperValue(self, upper: T) -> None:
        """Déplace tout l'intervalle pour que sa borne supérieure soit `upper`, à longueur constante.

        Comme `QRect.moveRight` ; l'intervalle s'arrête contre une limite.

        Lève:
            TypeError: Si `upper` n'est pas un nombre du type attendu.
            ValueError: Si `upper` n'est pas fini.
        """
        self._applyAndReport(lambda: self.__slider.moveUpperValue(upper))

    @Slot(int)
    def shiftBy(self, steps: int) -> None:
        """Déplace tout l'intervalle de `steps` pas simples, à longueur constante ; il s'arrête contre une limite."""
        self._applyAndReport(lambda: self.__slider.shiftBy(steps))

    # =================================================================== steps

    def resolution(self) -> T:
        """La taille d'un pas, la plus petite distance entre deux valeurs : 1 en entier, 10**-decimals en réel."""
        return self.__slider.resolution()

    def singleStep(self) -> T:
        """Le pas simple effectif, commun aux deux widgets : un pas au moins."""
        return self.__slider.singleStep()

    @Slot(object)
    def setSingleStep(self, step: T) -> None:
        """Fixe le pas simple des deux widgets ; un pas négatif est pris en valeur absolue.

        Lève:
            TypeError: Si `step` n'est pas un nombre du type attendu.
            ValueError: Si `step` n'est pas fini.
        """
        self._applyAndReport(lambda: self.__slider.setSingleStep(step))

    def pageStep(self) -> T:
        """Le pas de page effectif du curseur."""
        return self.__slider.pageStep()

    @Slot(object)
    def setPageStep(self, step: T) -> None:
        """Fixe le pas de page du curseur (touches de page, clic dans la rainure).

        Lève:
            TypeError: Si `step` n'est pas un nombre du type attendu.
            ValueError: Si `step` n'est pas fini.
        """
        self.__slider.setPageStep(step)

    # ================================================================ tracking

    def hasTracking(self) -> bool:
        """Indique si l'intervalle suit le glissement des poignées et la frappe au clavier."""
        return self.__slider.hasTracking()

    @Slot(bool)
    def setTracking(self, enable: bool) -> None:
        """Active ou désactive le suivi du curseur et celui du clavier de la boîte."""
        self.__slider.setTracking(enable)
        self.__spinBox.setKeyboardTracking(enable)

    # =============================================================== collision

    def overlapAllowed(self) -> bool:
        """Indique si les deux bornes peuvent porter la même valeur (vrai par défaut)."""
        return self.__slider.overlapAllowed()

    @Slot(bool)
    def setOverlapAllowed(self, allowed: bool) -> None:
        """Permet ou interdit l'égalité des deux bornes, dans les deux widgets.

        Si l'égalité devient interdite alors que les bornes se touchent, la borne supérieure
        monte d'un pas, ou la borne inférieure descend s'il n'y a plus de place.
        """
        def change() -> None:
            self.__slider.setOverlapAllowed(allowed)
            self.__spinBox.setOverlapAllowed(allowed)

        self._applyAndReport(change)

    def collisionMode(self) -> CollisionMode:
        """Ce que fait une borne qui rencontre l'autre (`Blocking` par défaut)."""
        return self.__slider.collisionMode()

    @Slot(CollisionMode)
    def setCollisionMode(self, mode: CollisionMode) -> None:
        """Choisit, dans les deux widgets, entre une borne qui s'arrête contre l'autre et une borne qui la pousse."""
        self.__slider.setCollisionMode(mode)
        self.__spinBox.setCollisionMode(mode)

    # ==================================================================== text

    def text(self) -> str:
        """L'intervalle choisi écrit dans le format, sans préfixe ni suffixe : `[-2.50, 3.75]`."""
        return self.__slider.text()

    def textFromRange(self, lower: T, upper: T) -> str:
        """Écrit un intervalle dans le format et la langue du widget, sans préfixe ni suffixe."""
        return self.__slider.textFromRange(lower, upper)

    def intervalFormat(self) -> QIntervalFormat:
        """Une copie de la notation de l'intervalle : délimiteurs et séparateur."""
        return self.__slider.intervalFormat()

    @Slot(QIntervalFormat)
    def setIntervalFormat(self, intervalFormat: QIntervalFormat) -> None:
        """Fixe la notation de l'intervalle des deux widgets ; une copie est gardée.

        Lève:
            ValueError: Si le séparateur contient la marque décimale de la langue du widget.
        """
        self.__slider.setIntervalFormat(intervalFormat)      # validates first: raises before any change
        self.__spinBox.setIntervalFormat(intervalFormat)

    # ================================================================ spin box

    def prefix(self) -> str:
        """Le texte placé avant l'intervalle dans la boîte (vide par défaut)."""
        return self.__spinBox.prefix()

    @Slot(str)
    def setPrefix(self, prefix: str) -> None:
        """Fixe le texte placé avant l'intervalle dans la boîte."""
        self.__spinBox.setPrefix(prefix)

    def suffix(self) -> str:
        """Le texte placé après l'intervalle dans la boîte (vide par défaut)."""
        return self.__spinBox.suffix()

    @Slot(str)
    def setSuffix(self, suffix: str) -> None:
        """Fixe le texte placé après l'intervalle dans la boîte (ex. une unité)."""
        self.__spinBox.setSuffix(suffix)

    def isFreeEntryEnabled(self) -> bool:
        """Indique si la saisie libre de la boîte peut s'ouvrir (vrai par défaut)."""
        return self.__spinBox.isFreeEntryEnabled()

    @Slot(bool)
    def setFreeEntryEnabled(self, enabled: bool) -> None:
        """Permet ou coupe la saisie libre de la boîte (voir `QAbstractRangeSpinBox`)."""
        self.__spinBox.setFreeEntryEnabled(enabled)

    # ================================================================== slider

    def orientation(self) -> Qt.Orientation:
        """L'orientation du curseur, qui fixe aussi la disposition."""
        return self.__slider.orientation()

    @Slot(Qt.Orientation)
    def setOrientation(self, orientation: Qt.Orientation) -> None:
        """Oriente le curseur et la disposition : boîte à droite (horizontale) ou en dessous
        (verticale). Remplace la politique de taille du widget, comme `QSlider`."""
        self.__slider.setOrientation(orientation)
        if orientation == Qt.Orientation.Horizontal:
            self.__layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self.__layout.setAlignment(self.__slider, Qt.AlignmentFlag(0))
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.__layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self.__layout.setAlignment(self.__slider, Qt.AlignmentFlag.AlignHCenter)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def tickPosition(self) -> QSlider.TickPosition:
        """La position des graduations du curseur (aucune par défaut)."""
        return self.__slider.tickPosition()

    @Slot(QSlider.TickPosition)
    def setTickPosition(self, position: QSlider.TickPosition) -> None:
        """Place les graduations du curseur (`NoTicks` pour les masquer)."""
        self.__slider.setTickPosition(position)

    def tickInterval(self) -> T:
        """L'écart entre deux graduations, en unités de valeur ; 0 laisse le style choisir."""
        return self.__slider.tickInterval()

    @Slot(object)
    def setTickInterval(self, interval: T) -> None:
        """Fixe l'écart entre deux graduations, selon les règles du curseur.

        Lève:
            TypeError: Si `interval` n'est pas un nombre du type attendu.
            ValueError: Si `interval` n'est pas fini.
        """
        self.__slider.setTickInterval(interval)

    # ================================================================ protected

    def _applyAndReport(self, change: Callable[[], object], announce: Callable[[], object] | None = None) -> None:
        """Applique `change` sans qu'aucun widget interne n'émette, recopie le résultat du
        curseur dans la boîte, puis émet ce qui a changé.

        Args:
            change: La modification, appliquée au curseur interne (et, au besoin, à la boîte),
                signaux bloqués. Si elle lève, rien n'est émis.
            announce: Appelé après la modification, avant `limitsChanged` et les signaux des
                bornes (ex. pour émettre `decimalsChanged` en premier, comme `QRealRangeSlider`).
        """
        with QSignalBlocker(self.__slider), QSignalBlocker(self.__spinBox):
            try:
                change()
            finally:
                self.__syncSpinBox()
        if announce is not None:
            announce()
        self.__report()

    # ================================================================== private

    def __syncSpinBox(self) -> None:
        """Copies into the spin box the limits, the step and the range the slider holds."""
        slider, spinBox = self.__slider, self.__spinBox
        spinBox.setLimits(*slider.limits())
        spinBox.setSingleStep(slider.singleStep())
        spinBox.setRange(*slider.range())

    def __report(self) -> None:
        """Emits, in the order of `QAbstractRangeSlider`, what changed since the last report."""
        limits, (lower, upper) = self.limits(), self.range()
        oldLimits, (oldLower, oldUpper) = self.__reportedLimits, self.__reportedRange
        self.__reportedLimits, self.__reportedRange = limits, (lower, upper)
        if limits != oldLimits:
            self.limitsChanged.emit(*limits)
        if lower != oldLower:
            self.lowerValueChanged.emit(lower)
        if upper != oldUpper:
            self.upperValueChanged.emit(upper)
        if (lower, upper) != (oldLower, oldUpper):
            self.rangeChanged.emit(lower, upper)

    @Slot(object, object)
    def __copySliderRange(self, lower: T, upper: T) -> None:
        self.__showSliderPositions(lower, upper)
        self.__report()

    @Slot(object, object)
    def __showSliderPositions(self, lower: T, upper: T) -> None:
        with QSignalBlocker(self.__spinBox):    # shows the positions, even without tracking
            self.__spinBox.setRange(lower, upper)

    @Slot(object, object)
    def __copySpinBoxRange(self, lower: T, upper: T) -> None:
        # The spin box is not written back: it may be in the middle of a typed text.
        with QSignalBlocker(self.__slider):
            self.__slider.setRange(lower, upper)
        self.__report()

    @Slot(QAbstractRangeSlider.Handle)
    def __finishEditing(self, handle: QAbstractRangeSlider.Handle) -> None:
        self.editingFinished.emit()


# -----------------------------------------------------------------------------
#                              Concrete classes
# -----------------------------------------------------------------------------

class QRangeSliderSpinBox(QAbstractRangeSliderSpinBox[int]):
    """Un `QRangeSlider` et un `QRangeSpinBox` côte à côte, qui portent un seul intervalle d'entiers.

    Voir `QAbstractRangeSliderSpinBox` pour la documentation complète. Valeurs initiales : celles
    de `QRangeSlider`, soit les limites [0, 99], l'intervalle choisi (0, 99), un pas simple de 1
    et un pas de page de 10.

    Un nombre qui n'est pas un `int` lève `TypeError` ; un booléen aussi. Des limites qui ne
    tiennent pas dans un `int` C++ (32 bits) lèvent `ValueError`.

    Signaux:
        lowerValueChanged: Signal(int). Voir `QAbstractRangeSliderSpinBox`.
        upperValueChanged: Signal(int). Voir `QAbstractRangeSliderSpinBox`.
        rangeChanged: Signal(int, int). Voir `QAbstractRangeSliderSpinBox`.
        limitsChanged: Signal(int, int). Voir `QAbstractRangeSliderSpinBox`.

    Exemple :
        >>> box = QRangeSliderSpinBox()
        >>> box.setLimits(0, 10)
        >>> box.setRange(8, 3)
        >>> box.range()
        (3, 8)
        >>> box.setCollisionMode(QRangeSliderSpinBox.CollisionMode.Pushing)
        >>> box.setLowerValue(9)
        >>> box.range()
        (9, 9)
    """

    lowerValueChanged = Signal(int)
    upperValueChanged = Signal(int)
    rangeChanged = Signal(int, int)
    limitsChanged = Signal(int, int)

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        """Construit le widget.

        Args:
            orientation: Orientation du curseur, qui fixe aussi la disposition.
            parent: Widget parent, ou None.
        """
        super().__init__(QRangeSlider(), QRangeSpinBox(), orientation, parent)


class QRealRangeSliderSpinBox(QAbstractRangeSliderSpinBox[float]):
    """Un `QRealRangeSlider` et un `QRealRangeSpinBox` côte à côte, qui portent un seul
    intervalle de nombres réels.

    Voir `QAbstractRangeSliderSpinBox` pour la documentation complète. Valeurs initiales :
    celles de `QRealRangeSlider`, soit 2 décimales, les limites [0.0, 1.0], l'intervalle choisi
    (0.0, 1.0) et un pas simple de 0.01.

    Décimales
    ---------
    `decimals`/`setDecimals` règlent les deux widgets à la fois ; `resolution()` donne la taille
    d'un pas (10**-decimals). Les deux widgets arrondissent de la même façon : celle de
    `QDoubleSpinBox`. Les règles sont celles de `QRealRangeSlider` : changer les décimales
    ré-exprime les limites et les bornes, puis `decimalsChanged`, `limitsChanged` et les signaux
    des bornes sont émis, dans cet ordre, pour ce qui a changé. Un pas demandé est mémorisé :
    0.05 vaut un pas de 0.1 avec 1 décimale, et redevient 0.05 avec 2 décimales.

    Limites
    -------
    Celles de `QRealRangeSlider` : les limites comptent au plus 2**31 - 1 pas, et les décimales
    vont de 0 à 15. Au-delà, `ValueError` est levée et le widget reste inchangé. NaN et l'infini
    lèvent `ValueError` ; une valeur qui n'est pas un nombre lève `TypeError`.

    Propriétés:
        decimals (int): Le nombre de décimales. Accesseur `decimals()`, mutateur
            `setDecimals()`, signal `decimalsChanged`.

    Signaux:
        lowerValueChanged: Signal(float). Voir `QAbstractRangeSliderSpinBox`.
        upperValueChanged: Signal(float). Voir `QAbstractRangeSliderSpinBox`.
        rangeChanged: Signal(float, float). Voir `QAbstractRangeSliderSpinBox`.
        limitsChanged: Signal(float, float). Voir `QAbstractRangeSliderSpinBox`.
        decimalsChanged: Signal(int). Émis quand le nombre de décimales change, avant
            `limitsChanged` et les signaux des bornes.

    Slots:
        setDecimals(int): En plus des slots de `QAbstractRangeSliderSpinBox`.

    Exemple :
        >>> box = QRealRangeSliderSpinBox()
        >>> box.setLimits(-5.0, 5.0)
        >>> box.setDecimals(1)
        >>> box.setRange(1.25, -2.0)
        >>> box.range()
        (-2.0, 1.3)
    """

    lowerValueChanged = Signal(float)
    upperValueChanged = Signal(float)
    rangeChanged = Signal(float, float)
    limitsChanged = Signal(float, float)
    decimalsChanged = Signal(int)

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        """Construit le widget, avec 2 décimales et les limites [0.0, 1.0].

        Args:
            orientation: Orientation du curseur, qui fixe aussi la disposition.
            parent: Widget parent, ou None.
        """
        slider = QRealRangeSlider()
        spinBox = QRealRangeSpinBox()
        spinBox.setDecimals(slider.decimals())
        super().__init__(slider, spinBox, orientation, parent)
        self.__realSlider: QRealRangeSlider = slider
        self.__realSpinBox: QRealRangeSpinBox = spinBox

    # ================================================================ decimals

    def decimals(self) -> int:
        """Le nombre de décimales des deux widgets (2 par défaut)."""
        return self.__realSlider.decimals()

    @Slot(int)
    def setDecimals(self, digits: int) -> None:
        """Fixe le nombre de décimales des deux widgets, en ré-exprimant limites, bornes et pas.

        Lève:
            TypeError: Si `digits` n'est pas un entier.
            ValueError: Si `digits` n'est pas dans [0, 15], ou si les limites compteraient trop
                de pas.
        """
        old = self.decimals()

        def change() -> None:
            self.__realSlider.setDecimals(digits)    # validates first: raises before any change
            self.__realSpinBox.setDecimals(digits)

        def announce() -> None:
            if self.decimals() != old:
                self.decimalsChanged.emit(self.decimals())

        self._applyAndReport(change, announce)
