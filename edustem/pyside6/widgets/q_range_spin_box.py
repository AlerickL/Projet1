"""Boîtes numériques qui choisissent un intervalle : `QRangeSpinBox` (entiers) et `QRealRangeSpinBox` (réels).

Un seul champ, de la hauteur d'une `QDoubleSpinBox`, porte les deux bornes d'un intervalle
`[lowerValue, upperValue]` choisi dans des limites `[minimum, maximum]`. Il complète
`QRangeSlider` et `QRealRangeSlider` quand il faut une valeur précise : même vocabulaire, mêmes
règles de rencontre des bornes, même arrondi des réels, même notation (`QIntervalFormat`).

    box = QRealRangeSpinBox()
    box.setLimits(-10.0, 10.0)
    box.setRange(-2.5, 3.75)          # the field shows [-2.50, 3.75]
    box.rangeChanged.connect(print)

Voir `QAbstractRangeSpinBox` pour la documentation complète.

Dépendances locales : la métaclasse abstraite vient de `q_abstract_widget` ; l'énumération
`CollisionMode` vient de `q_range_slider`, pour que les deux familles partagent le même type ;
la notation vient de `QIntervalFormat` (`core/q_interval_format`), les règles de l'intervalle de
`IntervalRules` (`core/interval_rules`) et l'arrondi des réels de `rounded_to_steps`
(`core/real_steps`).
"""

from __future__ import annotations

import copy
from abc import abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, Final, cast, override

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, Signal, SignalInstance, Slot
from PySide6.QtGui import (QFocusEvent, QKeyEvent, QKeySequence, QPainter, QPaintEvent, QPalette, QResizeEvent,
                           QValidator, QWheelEvent)
from PySide6.QtWidgets import QAbstractSpinBox, QStyle, QStyleOptionSpinBox, QWidget

from ..core.interval_rules import IntervalRules
from ..core.q_interval_format import QIntervalFormat
from ..core.real_steps import rounded_to_steps
from .q_abstract_widget import QWidgetABCMeta
from .q_range_slider import QAbstractRangeSlider


class QAbstractRangeSpinBox[T: (int, float)](QAbstractSpinBox, metaclass=QWidgetABCMeta):
    """Base abstraite d'une boîte numérique qui choisit un intervalle de nombres de type `T`.

    Les classes concrètes sont `QRangeSpinBox` (`int`) et `QRealRangeSpinBox` (`float`). Cette
    base fait l'affichage, la saisie, le clavier, la molette, la piste et toutes les règles ;
    chaque classe concrète fournit la conversion et l'écriture de ses nombres, et déclare ses
    signaux typés.

    Deux intervalles
    ----------------
    Comme pour `QAbstractRangeSlider` :

    - **les limites** (`limits`) sont l'intervalle possible, `[minimum, maximum]` ;
    - **l'intervalle choisi** (`range`) est `[lowerValue, upperValue]`.

    L'ordre `minimum <= lowerValue <= upperValue <= maximum` est toujours vrai.

    Le champ
    --------
    Le champ montre l'intervalle choisi, `[-2.50, 3.75]`, entre le préfixe et le suffixe
    (`prefix`, `suffix`), qui portent sur tout l'intervalle : `[-2.50, 3.75] cm`. Les
    délimiteurs et le séparateur viennent du format (`intervalFormat`, un `QIntervalFormat`
    partagé avec `QRangeSlider`) ; les nombres suivent la langue du widget (`locale()`).
    Quand la virgule y est la marque décimale, le séparateur automatique est le
    point-virgule : `[-2,50; 3,75]`.

    Édition structurée
    ------------------
    Comme dans `QDateTimeEdit`, le champ a deux sections, la borne inférieure et la borne
    supérieure, et seules les sections s'éditent. Le préfixe, les délimiteurs, le
    séparateur et le suffixe sont protégés : une frappe qui les toucherait est refusée, et
    le curseur de texte revient dans la section la plus proche. Taper le séparateur (`,` ou
    `;`) dans la borne inférieure passe à la borne supérieure. La section courante
    (`currentSection`) est celle du curseur de texte ; c'est elle que les flèches font
    avancer.

    Saisie libre
    ------------
    Quand tout le texte est sélectionné, taper (ou coller par Ctrl+V, ou effacer) ouvre la
    saisie libre, qui accepte plusieurs notations, avec ou sans délimiteurs, préfixe et
    suffixe :

    - deux bornes séparées par le séparateur du format, `,` (sauf si la virgule est la
      marque décimale), `;`, `..`, `…` ou des espaces : `-2.5, 3.75`, `-2.5 .. 3.75` ;
    - un centre et une demi-longueur, séparés par `±`, `+/-` ou `+-` : `0.625 ± 3.125` donne
      `[-2.50, 3.75]`.

    La saisie libre se referme à Entrée ou à la perte du focus (`interpretText`) : le texte
    est lu, puis réécrit dans le format. `setFreeEntryEnabled(False)` la coupe, pour une
    édition strictement structurée. Un collage par le menu contextuel n'ouvre pas la saisie
    libre, faute de signal qui le distingue d'une frappe : il n'est lu que s'il est écrit
    dans le format.

    Dans les deux modes, les bornes tapées dans le désordre sont remises dans l'ordre, et une
    valeur hors des limites y est ramenée. Avec le suivi du clavier (`keyboardTracking`, vrai
    par défaut), un texte complet et dans les limites s'applique à chaque frappe ; sinon, à
    Entrée ou à la perte du focus. Un texte qui ne se lit pas est alors remplacé par
    l'intervalle courant. Les nombres s'écrivent dans la langue du widget, ou avec un point
    décimal.

    Clavier
    -------
    - Flèches haut et bas, boutons du champ : la section courante avance d'un pas simple
      (`singleStep`) ; Page précédente et Page suivante, de dix pas. Avec Ctrl, une flèche
      avance de dix pas, comme dans `QSpinBox` (le modificateur vient du style,
      `SH_SpinBox_StepModifier`).
    - Tab passe de la borne inférieure à la borne supérieure, Maj + Tab revient ; au-delà, le
      focus quitte le widget. Entrer par Tab sélectionne la borne inférieure, revenir par
      Maj + Tab la borne supérieure.
    - Maj + flèche, ou Maj + Page précédente et Page suivante, élargit ou resserre
      l'intervalle autour de son centre (`widenBy`). Qt ne donne pas de sens à Maj ici.
    - Quand tout le texte est sélectionné (Ctrl + A), les flèches et les touches de page
      déplacent tout l'intervalle, sans changer sa longueur (`shiftBy`) : le geste agit sur
      ce qui est sélectionné, une borne ou les deux. La sélection reste entière.

    Molette
    -------
    La molette fait avancer la borne sous le pointeur, qui devient la section courante ; quand
    tout le texte est sélectionné, elle déplace tout l'intervalle. Avec Ctrl, elle avance de
    dix pas, comme dans `QSpinBox`. Avec Maj, elle élargit ou resserre l'intervalle autour de
    son centre.

    Piste
    -----
    Une ligne fine au bas du champ situe l'intervalle choisi dans les limites, comme un
    curseur en miniature (`isTrackVisible`, `setTrackVisible`). Elle prend la couleur
    d'accent du système.

    Rencontre des deux bornes
    -------------------------
    Mêmes règles que `QAbstractRangeSlider`, avec le même type `CollisionMode` :

    - **égalité** (`overlapAllowed`, vrai par défaut) : interdite, un pas au moins sépare
      les bornes ;
    - **collision** (`collisionMode`) : en `Blocking` (par défaut), une borne s'arrête contre
      l'autre ; en `Pushing`, elle la pousse jusqu'à la limite.

    Tout l'intervalle
    -----------------
    Même API que `QAbstractRangeSlider`, avec le vocabulaire de `QRect` : `length()` et
    `center()` (un `float`, qui peut tomber entre deux pas) ; `setLength` (à borne inférieure
    constante) et `widenBy` (à centre constant) changent la longueur ; `moveLowerValue`,
    `moveUpperValue`, `moveCenter` et `shiftBy` déplacent tout l'intervalle, à longueur
    constante. Ce qu'une opération garde n'est jamais modifié ; c'est sa cible qui s'arrête
    aux limites. Ces règles sont celles de `IntervalRules` (`core/interval_rules`), communes
    à toute la famille.

    Propriétés:
        minimum (T): La limite inférieure. Accesseur `minimum()`, mutateur `setMinimum()`,
            signal `limitsChanged`.
        maximum (T): La limite supérieure. Accesseur `maximum()`, mutateur `setMaximum()`,
            signal `limitsChanged`.
        lowerValue (T): La borne inférieure. Accesseur `lowerValue()`, mutateur
            `setLowerValue()`, signal `lowerValueChanged`.
        upperValue (T): La borne supérieure. Accesseur `upperValue()`, mutateur
            `setUpperValue()`, signal `upperValueChanged`.
        singleStep (T): Le pas simple. Accesseur `singleStep()`, mutateur `setSingleStep()`.
        prefix (str): Accesseur `prefix()`, mutateur `setPrefix()`.
        suffix (str): Accesseur `suffix()`, mutateur `setSuffix()`.
        intervalFormat (QIntervalFormat): Accesseur `intervalFormat()` (une copie),
            mutateur `setIntervalFormat()`.
        freeEntryEnabled (bool): Accesseur `isFreeEntryEnabled()`, mutateur
            `setFreeEntryEnabled()`.
        currentSection (Section): Accesseur `currentSection()`, mutateur
            `setCurrentSection()`.
        trackVisible (bool): Accesseur `isTrackVisible()`, mutateur `setTrackVisible()`.
        overlapAllowed (bool): Accesseur `overlapAllowed()`, mutateur `setOverlapAllowed()`.
        collisionMode (CollisionMode): Accesseur `collisionMode()`, mutateur
            `setCollisionMode()`.

    Signaux:
        lowerValueChanged: Signal(T). Émis quand la borne inférieure change.
        upperValueChanged: Signal(T). Émis quand la borne supérieure change.
        rangeChanged: Signal(T, T). Émis une fois quand l'une ou l'autre borne change, après
            les deux signaux précédents.
        limitsChanged: Signal(T, T). Émis quand les limites changent, avant les signaux des
            bornes.
        textChanged: Signal(str). Émis quand le texte du champ change, frappe comprise.
        editingFinished: Signal(). Hérité : Entrée ou perte du focus.

    Slots:
        setLimits(T, T): Fixe les limites.
        setMinimum(T): Fixe la limite inférieure.
        setMaximum(T): Fixe la limite supérieure.
        setRange(T, T): Fixe l'intervalle choisi.
        setLowerValue(T): Fixe la borne inférieure.
        setUpperValue(T): Fixe la borne supérieure.
        setSingleStep(T): Fixe le pas simple.
        setLength(T): Fixe la longueur, à borne inférieure constante.
        widenBy(int): Écarte les bornes d'un nombre de pas simples, à centre constant.
        shiftBy(int): Déplace tout l'intervalle d'un nombre de pas simples.
        moveLowerValue(T): Déplace tout l'intervalle vers une borne inférieure.
        moveUpperValue(T): Déplace tout l'intervalle vers une borne supérieure.
        moveCenter(float): Déplace tout l'intervalle vers un centre.
        setPrefix(str): Fixe le préfixe.
        setSuffix(str): Fixe le suffixe.
        setIntervalFormat(QIntervalFormat): Fixe la notation de l'intervalle.
        setFreeEntryEnabled(bool): Permet ou coupe la saisie libre.
        setCurrentSection(Section): Choisit la borne que les flèches font avancer.
        setTrackVisible(bool): Affiche ou masque la piste.
        setOverlapAllowed(bool): Permet ou interdit l'égalité des bornes.
        setCollisionMode(CollisionMode): Choisit le comportement de collision.
        interpretText(): Applique le texte du champ.

    Sous-classes
    ------------
    Une classe concrète fournit ses conversions entre un nombre de type `T` et un nombre
    entier de pas (`_toBase`, `_fromBase`), le nombre de décimales d'un pas s'il en a
    (`_stepDecimals`), l'écriture et la lecture d'un nombre (`textFromValue`,
    `valueFromText`), et ses quatre signaux typés : `lowerValueChanged`,
    `upperValueChanged`, `rangeChanged` et `limitsChanged`. Le constructeur de la base écrit
    déjà le champ : un état dont dépendent ces méthodes se fixe avant `super().__init__()`.
    """

    class Section(Enum):
        """Désigne une borne du champ.

        Attributs:
            Lower: La borne inférieure.
            Upper: La borne supérieure.
        """

        Lower = 0
        Upper = 1

    CollisionMode = QAbstractRangeSlider.CollisionMode

    textChanged = Signal(str)

    # Abstract members: the typed signals, which a generic base cannot declare. See
    # `QAbstractRangeSlider`, which does the same, for why a property stands for them.
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

    def __init__(self, parent: QWidget | None = None) -> None:
        """Construit la boîte, l'intervalle choisi couvrant toutes les limites.

        Args:
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self.__minimum: int = 0                       # everything below is counted in steps
        self.__maximum: int = self._DefaultStepCount
        self.__lower: int = self.__minimum
        self.__upper: int = self.__maximum
        self.__requestedSingleStep: T = cast(T, 1)    # 1 or 1.0, as QSpinBox and QDoubleSpinBox
        self.__overlapAllowed: bool = True
        self.__collisionMode: QAbstractRangeSlider.CollisionMode = QAbstractRangeSlider.CollisionMode.Blocking
        self.__currentSection: QAbstractRangeSpinBox.Section = QAbstractRangeSpinBox.Section.Lower
        self.__prefix: str = ""
        self.__suffix: str = ""
        self.__format: QIntervalFormat = QIntervalFormat()
        self.__freeEntryEnabled: bool = True
        self.__freeEntry: bool = False                # the text was replaced whole: any notation, until committed
        self.__trackVisible: bool = True
        self.__typing: bool = False                   # the range follows typed text: do not rewrite it
        self.__refreshing: bool = False               # the text or the cursor is moved by the widget itself
        self.__wheelRemainder: int = 0
        self.__track: QAbstractRangeSpinBox._Track = QAbstractRangeSpinBox._Track(self)

        edit = self.lineEdit()
        edit.textEdited.connect(self.__applyTypedText)
        edit.textChanged.connect(self.textChanged)
        edit.cursorPositionChanged.connect(self.__followCursor)
        self.editingFinished.connect(self.interpretText)
        self.__refreshText()

    # ================================================================== limits

    def minimum(self) -> T:
        """La limite inférieure de l'intervalle possible."""
        return self._fromBase(self.__minimum)

    # Slots typed `object`: the slot is shared by the int and the float subclasses.
    @Slot(object)
    def setMinimum(self, minimum: T) -> None:
        """Fixe la limite inférieure, en déplaçant la limite supérieure au besoin (comme `QSpinBox.setMinimum`)."""
        self.setLimits(minimum, max(self.maximum(), minimum))

    def maximum(self) -> T:
        """La limite supérieure de l'intervalle possible."""
        return self._fromBase(self.__maximum)

    @Slot(object)
    def setMaximum(self, maximum: T) -> None:
        """Fixe la limite supérieure, en déplaçant la limite inférieure au besoin (comme `QSpinBox.setMaximum`)."""
        self.setLimits(min(self.minimum(), maximum), maximum)

    def limits(self) -> tuple[T, T]:
        """L'intervalle possible, `(minimum, maximum)`."""
        return self.minimum(), self.maximum()

    @Slot(object, object)
    def setLimits(self, minimum: T, maximum: T) -> None:
        """Fixe l'intervalle possible ; un maximum inférieur au minimum devient le minimum.

        L'intervalle choisi est ramené dans les nouvelles limites. `limitsChanged`, puis les
        signaux des bornes, sont émis pour ce qui change.

        Lève:
            TypeError: Si une limite n'est pas un nombre du type attendu.
            ValueError: Si une limite n'est pas finie.
        """
        lo = self._toBase(minimum)
        hi = max(lo, self._toBase(maximum))

        def change() -> None:
            self.__minimum, self.__maximum = lo, hi
            self.__lower, self.__upper = self.__resolved(None, self.__lower, self.__upper)

        self._applyAndReport(change)

    # =================================================================== range

    def lowerValue(self) -> T:
        """La borne inférieure de l'intervalle choisi."""
        return self._fromBase(self.__lower)

    @Slot(object)
    def setLowerValue(self, lower: T) -> None:
        """Fixe la borne inférieure, selon le mode de collision.

        Lève:
            TypeError: Si `lower` n'est pas un nombre du type attendu.
            ValueError: Si `lower` n'est pas fini.
        """
        self.__moveTo(QAbstractRangeSpinBox.Section.Lower, self._toBase(lower))

    def upperValue(self) -> T:
        """La borne supérieure de l'intervalle choisi."""
        return self._fromBase(self.__upper)

    @Slot(object)
    def setUpperValue(self, upper: T) -> None:
        """Fixe la borne supérieure, selon le mode de collision.

        Lève:
            TypeError: Si `upper` n'est pas un nombre du type attendu.
            ValueError: Si `upper` n'est pas fini.
        """
        self.__moveTo(QAbstractRangeSpinBox.Section.Upper, self._toBase(upper))

    def range(self) -> tuple[T, T]:
        """L'intervalle choisi, `(lowerValue, upperValue)`."""
        return self.lowerValue(), self.upperValue()

    @Slot(object, object)
    def setRange(self, lower: T, upper: T) -> None:
        """Fixe les deux bornes d'un seul coup : triées, puis ramenées dans les limites.

        Le mode de collision ne joue pas ici. `rangeChanged` n'est émis qu'une fois.

        Lève:
            TypeError: Si une borne n'est pas un nombre du type attendu.
            ValueError: Si une borne n'est pas finie.
        """
        lo, up = self.__resolved(None, self._toBase(lower), self._toBase(upper))
        self._applyAndReport(lambda: self.__setBoth(lo, up))

    # ========================================================== whole interval

    def length(self) -> T:
        """La longueur de l'intervalle choisi, `upperValue() - lowerValue()`, sans erreur d'arrondi."""
        return self._fromBase(self.__upper - self.__lower)

    @Slot(object)
    def setLength(self, length: T) -> None:
        """Fixe la longueur, à borne inférieure constante (comme `QLineF.setLength`).

        La longueur s'arrête à `maximum() - lowerValue()`. Elle ne descend pas sous 0, ni sous
        un pas si l'égalité des bornes est interdite.

        Lève:
            TypeError: Si `length` n'est pas un nombre du type attendu.
            ValueError: Si `length` n'est pas fini.
        """
        self.__applyBounds(self.__rules().with_length(self.__lower, self.__upper, self._toBase(length)))

    @Slot(int)
    def widenBy(self, steps: int) -> None:
        """Écarte chaque borne de `steps` pas simples, à centre constant ; un nombre négatif les rapproche.

        En s'écartant, les deux bornes s'arrêtent dès que l'une touche sa limite. En se
        rapprochant, elles s'arrêtent à la plus petite longueur permise qui garde le centre.
        """
        self.__applyBounds(self.__rules().widened(self.__lower, self.__upper, steps * self.__baseSingleStep()))

    def center(self) -> float:
        """Le centre de l'intervalle choisi ; un `float`, qui peut tomber entre deux pas."""
        return (self.__lower + self.__upper) / 2 / 10 ** self._stepDecimals()

    @Slot(float)
    def moveCenter(self, center: float) -> None:
        """Déplace tout l'intervalle pour que son centre soit au plus près de `center`, à longueur constante.

        Comme `QRect.moveCenter`. La borne inférieure qui en découle est arrondie au pas, les
        égalités en s'éloignant de zéro ; l'intervalle s'arrête contre une limite.

        Lève:
            TypeError: Si `center` n'est pas un nombre.
            ValueError: Si `center` n'est pas fini.
        """
        self.__applyBounds(self.__rules().centered_on(self.__lower, self.__upper, center, self._stepDecimals()))

    @Slot(object)
    def moveLowerValue(self, lower: T) -> None:
        """Déplace tout l'intervalle pour que sa borne inférieure soit `lower`, à longueur constante.

        Comme `QRect.moveLeft` ; l'intervalle s'arrête contre une limite.

        Lève:
            TypeError: Si `lower` n'est pas un nombre du type attendu.
            ValueError: Si `lower` n'est pas fini.
        """
        self.__applyBounds(self.__rules().moved_to(self.__lower, self.__upper, self._toBase(lower)))

    @Slot(object)
    def moveUpperValue(self, upper: T) -> None:
        """Déplace tout l'intervalle pour que sa borne supérieure soit `upper`, à longueur constante.

        Comme `QRect.moveRight` ; l'intervalle s'arrête contre une limite.

        Lève:
            TypeError: Si `upper` n'est pas un nombre du type attendu.
            ValueError: Si `upper` n'est pas fini.
        """
        target = self._toBase(upper) - (self.__upper - self.__lower)
        self.__applyBounds(self.__rules().moved_to(self.__lower, self.__upper, target))

    @Slot(int)
    def shiftBy(self, steps: int) -> None:
        """Déplace tout l'intervalle de `steps` pas simples, à longueur constante ; il s'arrête contre une limite."""
        self.__applyBounds(self.__rules().shifted(self.__lower, self.__upper, steps * self.__baseSingleStep()))

    # =================================================================== steps

    def resolution(self) -> T:
        """La taille d'un pas, la plus petite distance entre deux valeurs : 1 en entier, 10**-decimals en réel."""
        return self._fromBase(1)

    def singleStep(self) -> T:
        """Le pas simple effectif (flèches, molette) : un pas au moins (1 par défaut)."""
        return self._fromBase(self.__baseSingleStep())

    @Slot(object)
    def setSingleStep(self, step: T) -> None:
        """Fixe le pas simple ; un pas négatif est pris en valeur absolue.

        Lève:
            TypeError: Si `step` n'est pas un nombre du type attendu.
            ValueError: Si `step` n'est pas fini.
        """
        self._toBase(step)
        self.__requestedSingleStep = step
        self.update()

    # ===================================================================== text

    def prefix(self) -> str:
        """Le texte placé avant l'intervalle (vide par défaut)."""
        return self.__prefix

    @Slot(str)
    def setPrefix(self, prefix: str) -> None:
        """Fixe le texte placé avant l'intervalle."""
        self.__prefix = prefix
        self.__refreshText()
        self.updateGeometry()

    def suffix(self) -> str:
        """Le texte placé après l'intervalle (vide par défaut), une unité par exemple."""
        return self.__suffix

    @Slot(str)
    def setSuffix(self, suffix: str) -> None:
        """Fixe le texte placé après l'intervalle."""
        self.__suffix = suffix
        self.__refreshText()
        self.updateGeometry()

    def intervalFormat(self) -> QIntervalFormat:
        """Une copie de la notation de l'intervalle : délimiteurs et séparateur."""
        return copy.copy(self.__format)

    @Slot(QIntervalFormat)
    def setIntervalFormat(self, intervalFormat: QIntervalFormat) -> None:
        """Fixe la notation de l'intervalle (une copie est gardée), et réécrit le champ.

        Si la langue change ensuite et rend le séparateur ambigu, le séparateur automatique
        le remplace (voir `QIntervalFormat.separatorFor`).

        Lève:
            ValueError: Si le séparateur contient la marque décimale de la langue du widget.
        """
        if not intervalFormat.isValidFor(self.locale()):
            raise ValueError(f"The separator {intervalFormat.separator()!r} contains the decimal point of "
                             f"the locale {self.locale().name()}.")
        self.__format = copy.copy(intervalFormat)
        self.__refreshText()
        self.updateGeometry()

    def cleanText(self) -> str:
        """Le texte du champ sans le préfixe, le suffixe ni les espaces autour (comme `QSpinBox.cleanText`)."""
        text = self.text()
        if self.__prefix and text.startswith(self.__prefix):
            text = text[len(self.__prefix):]
        if self.__suffix and text.endswith(self.__suffix):
            text = text[:-len(self.__suffix)]
        return text.strip()

    def textFromRange(self, lower: T, upper: T) -> str:
        """Écrit un intervalle tel que le champ l'affiche, préfixe et suffixe compris."""
        return (f"{self.__prefix}{self.__format.toString(self.textFromValue(lower), self.textFromValue(upper),
                                                          self.locale())}{self.__suffix}")

    def rangeFromText(self, text: str) -> tuple[T, T] | None:
        """Lit un intervalle tapé, écrit dans le format ou dans une notation libre (voir « Saisie libre »).

        Retourne:
            Les deux bornes, dans l'ordre tapé et sans arrondi ni bornage, ou None si le
            texte ne se lit pas.
        """
        parts = self.__structuredParts(text) or self.__freeParts(text)
        if parts is None:
            return None
        first, second = self.valueFromText(parts.lower.strip()), self.valueFromText(parts.upper.strip())
        if first is None or second is None:
            return None
        if parts.centered:
            return cast(tuple[T, T], (first - abs(second), first + abs(second)))
        return first, second

    @abstractmethod
    def textFromValue(self, value: T) -> str:
        """Écrit un nombre dans la langue du widget. Point d'extension obligatoire."""

    @abstractmethod
    def valueFromText(self, text: str) -> T | None:
        """Lit un nombre écrit dans la langue du widget, ou avec un point décimal.

        Point d'extension obligatoire.

        Retourne:
            Le nombre, ou None si le texte ne se lit pas.
        """

    @override
    @Slot()
    def interpretText(self) -> None:
        """Applique le texte du champ, puis le réécrit dans le format, ce qui referme la saisie libre.

        Un texte qui ne se lit pas est remplacé par l'intervalle courant. Appelé à Entrée et
        à la perte du focus.
        """
        parsed = self.rangeFromText(self.text())
        self.__freeEntry = False
        if parsed is not None:
            self.setRange(*parsed)
        self.__refreshText()

    @override
    def validate(self, input: str, pos: int, /) -> tuple[QValidator.State, str, int]:
        """Juge un texte en cours de frappe.

        En édition structurée, une frappe qui touche au préfixe, aux délimiteurs, au
        séparateur ou au suffixe est refusée, comme un caractère qui ne peut pas faire partie
        d'un nombre. En saisie libre, tout caractère d'une notation acceptée passe.

        Retourne:
            `(état, texte, position)` : `Acceptable` pour un intervalle lisible et dans les
            limites, `Intermediate` pour un texte incomplet ou hors des limites, `Invalid`
            pour un texte refusé.
        """
        State = QValidator.State
        if self.__freeEntry:
            return self.__judgeFreeText(input), input, pos
        parts = self.__structuredParts(input)
        if parts is None:
            return State.Invalid, input, pos
        locale = self.locale()
        if not all(QIntervalFormat.isNumberCharacter(c, locale) for c in parts.lower + parts.upper):
            return State.Invalid, input, pos
        return self.__judgeRange(self.rangeFromText(input)), input, pos

    def isFreeEntryEnabled(self) -> bool:
        """Indique si la saisie libre peut s'ouvrir quand tout le texte est remplacé (vrai par défaut)."""
        return self.__freeEntryEnabled

    @Slot(bool)
    def setFreeEntryEnabled(self, enabled: bool) -> None:
        """Permet ou coupe la saisie libre ; coupée, l'édition reste strictement structurée."""
        self.__freeEntryEnabled = enabled

    # ================================================================ sections

    def currentSection(self) -> Section:
        """La borne que les flèches font avancer : celle où se trouve le curseur de texte."""
        return self.__currentSection

    @Slot(Section)
    def setCurrentSection(self, section: Section) -> None:
        """Choisit la borne que les flèches font avancer, et sélectionne son texte."""
        self.__currentSection = section
        self.__selectSection(section)
        self.update()

    # ==================================================================== track

    def isTrackVisible(self) -> bool:
        """Indique si la piste est affichée au bas du champ (vrai par défaut)."""
        return self.__trackVisible

    @Slot(bool)
    def setTrackVisible(self, visible: bool) -> None:
        """Affiche ou masque la piste qui situe l'intervalle dans les limites."""
        self.__trackVisible = visible
        self.__track.setVisible(visible)

    # =============================================================== collision

    def overlapAllowed(self) -> bool:
        """Indique si les deux bornes peuvent porter la même valeur (vrai par défaut)."""
        return self.__overlapAllowed

    @Slot(bool)
    def setOverlapAllowed(self, allowed: bool) -> None:
        """Permet ou interdit l'égalité des deux bornes.

        Si l'égalité devient interdite alors que les bornes se touchent, la borne supérieure
        monte d'un pas, ou la borne inférieure descend s'il n'y a plus de place.
        """
        def change() -> None:
            self.__overlapAllowed = allowed
            self.__lower, self.__upper = self.__resolved(None, self.__lower, self.__upper)

        self._applyAndReport(change)

    def collisionMode(self) -> CollisionMode:
        """Ce que fait une borne qui rencontre l'autre (`Blocking` par défaut)."""
        return self.__collisionMode

    @Slot(CollisionMode)
    def setCollisionMode(self, mode: CollisionMode) -> None:
        """Choisit entre une borne qui s'arrête contre l'autre et une borne qui la pousse."""
        self.__collisionMode = mode
        self.update()

    # ===================================================================== size

    @override
    def sizeHint(self) -> QSize:
        """La taille recommandée : de quoi afficher les deux bornes les plus larges possibles."""
        self.ensurePolished()
        metrics = self.fontMetrics()
        widest = max((self.textFromValue(value) for value in self.limits()), key=metrics.horizontalAdvance)
        text = f"{self.__prefix}{self.__format.toString(widest, widest, self.locale())}{self.__suffix} "
        size = QSize(metrics.horizontalAdvance(text) + 2, self.lineEdit().sizeHint().height())  # +2: the cursor
        option = QStyleOptionSpinBox()
        self.initStyleOption(option)
        return self.style().sizeFromContents(QStyle.ContentsType.CT_SpinBox, option, size, self)

    @override
    def minimumSizeHint(self) -> QSize:
        """La taille minimum recommandée : la taille recommandée, pour que l'intervalle reste lisible."""
        return self.sizeHint()

    # ================================================================== events

    @override
    def stepBy(self, steps: int) -> None:
        """Fait avancer la section courante de `steps` pas simples (flèches, boutons du champ)."""
        if self.__textWasEdited():
            self.interpretText()
        section = self.__currentSection
        self.__step(section, steps * self.__baseSingleStep())
        self.__selectSection(section)

    @override
    def stepEnabled(self) -> QAbstractSpinBox.StepEnabledFlag:
        Flag = QAbstractSpinBox.StepEnabledFlag
        if self.isReadOnly():
            return Flag.StepNone
        rules = self.__rules()
        pushing, gap = rules.pushing, rules.gap
        if self.__currentSection == QAbstractRangeSpinBox.Section.Lower:
            up = self.__lower < (self.__maximum - gap if pushing else self.__upper - gap)
            down = self.__lower > self.__minimum
        else:
            up = self.__upper < self.__maximum
            down = self.__upper > (self.__minimum + gap if pushing else self.__lower + gap)
        flags = Flag.StepNone
        if up:
            flags |= Flag.StepUpEnabled
        if down:
            flags |= Flag.StepDownEnabled
        return flags

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        steps = self._KeySteps.get(event.key())
        modifiers = event.modifiers()
        widen = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        if steps is not None and not self.isReadOnly() and (widen or self.__isAllSelected()):
            if abs(steps) == 1 and modifiers & self.__stepModifier():
                steps *= 10             # as QAbstractSpinBox: the step modifier multiplies an arrow, not a page
            self.__moveWholeInterval(steps, widen)
            event.accept()
            return
        if not self.__freeEntry and not self.isReadOnly():
            if self.__freeEntryEnabled and self.__replacesAllText(event):
                self.__freeEntry = True
            elif self.__jumpsToUpper(event):
                self.interpretText()
                self.setCurrentSection(QAbstractRangeSpinBox.Section.Upper)
                event.accept()
                return
        super().keyPressEvent(event)

    @override
    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y() or event.angleDelta().x()
        if self.isReadOnly() or delta == 0 or self.__minimum == self.__maximum:
            event.ignore()
            return
        event.accept()
        self.__wheelRemainder += -delta if event.inverted() else delta
        notches = int(self.__wheelRemainder / self._WheelNotch)
        if notches == 0:
            return
        self.__wheelRemainder -= notches * self._WheelNotch
        modifiers = event.modifiers()
        if modifiers & self.__stepModifier():
            notches *= 10
        widen = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        if widen or self.__isAllSelected():
            self.__moveWholeInterval(notches, widen)
            return
        if self.__textWasEdited():
            self.interpretText()
        section = self.__sectionAtPoint(event.position().toPoint())
        self.__currentSection = section
        self.__step(section, notches * self.__baseSingleStep())
        self.__selectSection(section)

    @override
    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        if event.reason() == Qt.FocusReason.TabFocusReason:
            self.setCurrentSection(QAbstractRangeSpinBox.Section.Lower)
        elif event.reason() == Qt.FocusReason.BacktabFocusReason:
            self.setCurrentSection(QAbstractRangeSpinBox.Section.Upper)

    @override
    def focusNextPrevChild(self, next: bool) -> bool:
        """Tab passe d'une borne à l'autre avant de quitter le widget, comme dans `QDateTimeEdit`."""
        Section = QAbstractRangeSpinBox.Section
        target = Section.Upper if next else Section.Lower
        if self.hasFocus() and self.__currentSection != target:
            self.interpretText()
            self.setCurrentSection(target)
            return True
        return super().focusNextPrevChild(next)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.__placeTrack()

    @override
    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        kind = event.type()
        if kind == QEvent.Type.LocaleChange:
            self.__refreshText()
            self.updateGeometry()
        elif kind in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self.updateGeometry()
            self.__placeTrack()
        elif kind in (QEvent.Type.EnabledChange, QEvent.Type.PaletteChange):
            self.__track.update()

    # ================================================================ protected

    _DefaultStepCount: ClassVar[int] = 99   # initial limits, in steps: [0, 99], as QSpinBox
    _WheelNotch: Final[int] = 120           # eighths of a degree for one notch of a wheel
    _TrackHeight: Final[int] = 2
    _KeySteps: Final[dict[int, int]] = {   # QKeyEvent.key() is an int
        Qt.Key.Key_Up.value: 1, Qt.Key.Key_Down.value: -1, Qt.Key.Key_PageUp.value: 10, Qt.Key.Key_PageDown.value: -10,
    }

    @abstractmethod
    def _toBase(self, value: T) -> int:
        """Convertit un nombre en un nombre entier de pas, sans le borner.

        Point d'extension obligatoire. La conversion valide son argument.

        Lève:
            TypeError: Si `value` n'est pas un nombre du type attendu.
            ValueError: Si `value` n'est pas fini.
        """

    @abstractmethod
    def _fromBase(self, steps: int) -> T:
        """Convertit un nombre entier de pas en un nombre de type `T`. Point d'extension obligatoire."""

    def _stepDecimals(self) -> int:
        """Le nombre de décimales d'un pas : 0 par défaut, pour des entiers. À surcharger en réel."""
        return 0

    def _trackSpan(self) -> tuple[float, float] | None:
        """La place de l'intervalle choisi dans les limites, en fractions de 0 à 1 ; None si les limites sont réduites à un point."""
        width = self.__maximum - self.__minimum
        if width == 0:
            return None
        return (self.__lower - self.__minimum) / width, (self.__upper - self.__minimum) / width

    def _applyAndReport(self, change: Callable[[], object], announce: Callable[[], object] | None = None) -> None:
        """Applique `change`, réécrit le champ, puis émet les signaux de ce qui a changé.

        Args:
            change: La modification de l'état. Si elle lève, rien n'est émis.
            announce: Appelé après la modification, avant `limitsChanged` et les signaux des
                bornes (ex. pour émettre `decimalsChanged` en premier).
        """
        oldLimits, oldRange = self.limits(), self.range()
        change()
        if not self.__typing:
            self.__refreshText()
        self.__track.update()
        self.update()
        newLimits, newRange = self.limits(), self.range()
        if announce is not None:
            announce()
        if newLimits != oldLimits:
            self.updateGeometry()
            self.limitsChanged.emit(*newLimits)
        if newRange[0] != oldRange[0]:
            self.lowerValueChanged.emit(newRange[0])
        if newRange[1] != oldRange[1]:
            self.upperValueChanged.emit(newRange[1])
        if newRange != oldRange:
            self.rangeChanged.emit(*newRange)

    def _rebase(self, change: Callable[[], object], announce: Callable[[], object] | None = None) -> None:
        """Change la conversion entre nombres et pas, en gardant les limites et l'intervalle choisi.

        Les limites et les bornes sont relues avant le changement, puis reconverties après,
        arrondies au besoin.

        Args:
            change: Modifie ce dont `_toBase` et `_fromBase` dépendent.
            announce: Voir `_applyAndReport`.
        """
        minimum, maximum, lower, upper = self.minimum(), self.maximum(), self.lowerValue(), self.upperValue()

        def apply() -> None:
            change()
            self.__minimum = self._toBase(minimum)
            self.__maximum = max(self.__minimum, self._toBase(maximum))
            self.__lower, self.__upper = self.__resolved(None, self._toBase(lower), self._toBase(upper))

        self._applyAndReport(apply, announce)
        self.updateGeometry()

    # ================================================================== private

    class _Track(QWidget):
        """La piste : une ligne fine qui situe l'intervalle choisi dans les limites.

        Posée sur le champ de texte, elle laisse passer la souris.
        """

        def __init__(self, spinBox: QAbstractRangeSpinBox[Any]) -> None:
            super().__init__(spinBox)
            self.__spinBox: QAbstractRangeSpinBox[Any] = spinBox
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        @override
        def paintEvent(self, event: QPaintEvent) -> None:
            spinBox = self.__spinBox
            palette = spinBox.palette()
            group = QPalette.ColorGroup.Active if spinBox.isEnabled() else QPalette.ColorGroup.Disabled
            painter = QPainter(self)
            area = self.rect()
            rail = palette.color(group, QPalette.ColorRole.Text)
            rail.setAlpha(self._RailAlpha)      # a faint rail reads in light and dark themes alike
            painter.fillRect(QRect(area.left(), area.bottom(), area.width(), 1), rail)
            span = spinBox._trackSpan()
            if span is None:
                return
            start, stop = span
            if spinBox.isRightToLeft():
                start, stop = 1 - stop, 1 - start
            left = area.left() + round(start * area.width())
            width = max(self._MinSegment, round(stop * area.width()) - round(start * area.width()))
            left = min(left, area.right() - width + 1)
            painter.fillRect(QRect(left, area.top(), width, area.height()), palette.color(group, QPalette.ColorRole.Accent))

        _MinSegment: Final[int] = 2         # an empty interval still shows where it is
        _RailAlpha: Final[int] = 70

    def __refreshText(self) -> None:
        """Rewrites the field from the range, and keeps the current section selected when focused."""
        self.__refreshing = True
        try:
            edit = self.lineEdit()
            edit.setText(self.textFromRange(self.lowerValue(), self.upperValue()))
            # setText leaves the cursor after the suffix: a click there would not move it, and
            # nothing would bring it back into a section. It waits at the end of the upper bound.
            parts = self.__structuredParts(edit.text())
            if parts is not None:
                edit.setCursorPosition(parts.upperSpan[1])
        finally:
            self.__refreshing = False
        if self.hasFocus():
            self.__selectSection(self.__currentSection)

    def __stepModifier(self) -> Qt.KeyboardModifier:
        """The modifier that multiplies a step by ten, as the style sets it for `QAbstractSpinBox`."""
        return Qt.KeyboardModifier(self.style().styleHint(QStyle.StyleHint.SH_SpinBox_StepModifier))

    def __isAllSelected(self) -> bool:
        edit = self.lineEdit()
        return edit.hasSelectedText() and len(edit.selectedText()) == len(edit.text())

    def __moveWholeInterval(self, steps: int, widen: bool) -> None:
        """Widens the interval, or shifts it, by `steps` single steps, and keeps the selection as it was."""
        whole = self.__isAllSelected()
        if self.__textWasEdited():
            self.interpretText()
        if widen:
            self.widenBy(steps)
        else:
            self.shiftBy(steps)
        if whole:
            self.__refreshing = True
            try:
                self.lineEdit().selectAll()
            finally:
                self.__refreshing = False
        else:
            self.__selectSection(self.__currentSection)

    def __textWasEdited(self) -> bool:
        return self.text() != self.textFromRange(self.lowerValue(), self.upperValue())

    def __replacesAllText(self, event: QKeyEvent) -> bool:
        """Whether a key press replaces the whole text: typing, pasting or erasing over a full selection."""
        edit = self.lineEdit()
        if not edit.hasSelectedText() or len(edit.selectedText()) != len(edit.text()):
            return False
        if event.matches(QKeySequence.StandardKey.Paste):
            return True
        if event.key() in (Qt.Key.Key_Backspace.value, Qt.Key.Key_Delete.value):
            return True
        commands = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier
        return bool(event.text()) and event.text().isprintable() and not event.modifiers() & commands

    def __jumpsToUpper(self, event: QKeyEvent) -> bool:
        """Whether a key press types the separator in the lower section."""
        mark = self.__format.separatorFor(self.locale()).strip()[:1]
        return bool(mark) and event.text() == mark and self.__currentSection == QAbstractRangeSpinBox.Section.Lower

    def __judgeRange(self, parsed: tuple[T, T] | None) -> QValidator.State:
        State = QValidator.State
        if parsed is None:
            return State.Intermediate
        try:
            lo, hi = sorted(self._toBase(value) for value in parsed)
        except (TypeError, ValueError):
            return State.Intermediate
        return State.Acceptable if self.__minimum <= lo and hi <= self.__maximum else State.Intermediate

    def __judgeFreeText(self, text: str) -> QValidator.State:
        parsed = self.rangeFromText(text)
        if parsed is not None:
            return self.__judgeRange(parsed)
        locale = self.locale()
        allowed = set(" \t;…[]()/±") | set(self.__prefix) | set(self.__suffix) | set(
            self.__format.openingDelimiter()) | set(self.__format.closingDelimiter()) | set(
            self.__format.separatorFor(locale))
        if all(c in allowed or QIntervalFormat.isNumberCharacter(c, locale) for c in text):
            return QValidator.State.Intermediate
        return QValidator.State.Invalid

    @Slot(str)
    def __applyTypedText(self, text: str) -> None:
        if self.__structuredParts(text) is None and self.__freeEntryEnabled:
            self.__freeEntry = True     # a whole interval pasted by the context menu
        if not self.keyboardTracking() or self.validate(text, 0)[0] != QValidator.State.Acceptable:
            return
        parsed = self.rangeFromText(text)
        if parsed is None:
            return
        self.__typing = True
        try:
            self.setRange(*parsed)
        finally:
            self.__typing = False

    @Slot(int, int)
    def __followCursor(self, old: int, new: int) -> None:
        """Keeps the text cursor in a section during structured editing, and follows it."""
        if self.__refreshing:
            return
        edit = self.lineEdit()
        if not self.__freeEntry and not edit.hasSelectedText():
            parts = self.__structuredParts(self.text())
            if parts is not None:
                inside = _nearestInside(new, parts.lowerSpan, parts.upperSpan)
                if inside != new:
                    self.__refreshing = True
                    try:
                        edit.setCursorPosition(inside)
                    finally:
                        self.__refreshing = False
                    new = inside
        self.__currentSection = self.__sectionAt(new)
        self.update()

    def __structuredParts(self, text: str) -> QIntervalFormat.Parts | None:
        """The two numbers of a text written exactly in the format, with prefix and suffix."""
        prefix, suffix = self.__prefix, self.__suffix
        if len(text) < len(prefix) + len(suffix) or not text.startswith(prefix) or not text.endswith(suffix):
            return None
        parts = self.__format.structuredParts(text[len(prefix):len(text) - len(suffix)], self.locale())
        return None if parts is None else _shifted(parts, len(prefix))

    def __freeParts(self, text: str) -> QIntervalFormat.Parts | None:
        """The two numbers of a text in any accepted notation, prefix and suffix optional."""
        start, stop = 0, len(text)
        if self.__prefix and text.startswith(self.__prefix):
            start = len(self.__prefix)
        if self.__suffix and text.endswith(self.__suffix) and stop - len(self.__suffix) >= start:
            stop -= len(self.__suffix)
        parts = self.__format.freeParts(text[start:stop], self.locale())
        return None if parts is None else _shifted(parts, start)

    def __sectionAt(self, position: int) -> Section:
        Section = QAbstractRangeSpinBox.Section
        text = self.text()
        parts = self.__structuredParts(text) or self.__freeParts(text)
        if parts is None:
            return Section.Lower
        return Section.Lower if position < parts.upperSpan[0] else Section.Upper

    def __sectionAtPoint(self, point: QPoint) -> Section:
        edit = self.lineEdit()
        return self.__sectionAt(edit.cursorPositionAt(edit.mapFrom(self, point)))

    def __selectSection(self, section: Section) -> None:
        text = self.text()
        parts = self.__structuredParts(text) or self.__freeParts(text)
        if parts is None:
            return
        start, stop = parts.lowerSpan if section == QAbstractRangeSpinBox.Section.Lower else parts.upperSpan
        self.__refreshing = True
        try:
            self.lineEdit().setSelection(start, stop - start)
        finally:
            self.__refreshing = False

    def __placeTrack(self) -> None:
        edit = self.lineEdit().geometry()
        height = self._TrackHeight
        self.__track.setGeometry(edit.left() + 2, edit.bottom() - height, max(0, edit.width() - 4), height)
        self.__track.setVisible(self.__trackVisible)
        self.__track.raise_()

    def __baseSingleStep(self) -> int:
        return max(1, abs(self._toBase(self.__requestedSingleStep)))

    def __rules(self) -> IntervalRules:
        lo, hi = self.__minimum, self.__maximum
        pushing = self.__collisionMode == QAbstractRangeSlider.CollisionMode.Pushing
        return IntervalRules(lo, hi, IntervalRules.gap_for(lo, hi, self.__overlapAllowed), pushing)

    def __resolved(self, moved: Section | None, lower: int, upper: int) -> tuple[int, int]:
        """The legal bounds closest to a request, given which bound asks to move.

        A moved bound meets the other one by the collision mode; `None` takes two free values.
        """
        Section = QAbstractRangeSpinBox.Section
        rules = self.__rules()
        if moved == Section.Lower:
            return rules.with_lower(self.__lower, self.__upper, lower)
        if moved == Section.Upper:
            return rules.with_upper(self.__lower, self.__upper, upper)
        return rules.resolved(lower, upper)

    def __setBoth(self, lower: int, upper: int) -> None:
        self.__lower, self.__upper = lower, upper

    def __applyBounds(self, bounds: tuple[int, int]) -> None:
        """Retains new bounds, then rewrites the field and emits what changed."""
        self._applyAndReport(lambda: self.__setBoth(*bounds))

    def __moveTo(self, section: Section, target: int) -> None:
        self.__applyBounds(self.__resolved(section, target, target))

    def __step(self, section: Section, offset: int) -> None:
        origin = self.__upper if section == QAbstractRangeSpinBox.Section.Upper else self.__lower
        self.__moveTo(section, origin + offset)


# -----------------------------------------------------------------------------
#                              Concrete classes
# -----------------------------------------------------------------------------

class QRangeSpinBox(QAbstractRangeSpinBox[int]):
    """Boîte numérique qui choisit un intervalle d'entiers.

    Voir `QAbstractRangeSpinBox` pour la documentation complète. Valeurs initiales : les
    limites [0, 99] de `QSpinBox`, l'intervalle choisi (0, 99), un pas simple de 1.

    Un nombre qui n'est pas un `int` lève `TypeError` ; un booléen aussi.

    Signaux:
        lowerValueChanged: Signal(int). Voir `QAbstractRangeSpinBox`.
        upperValueChanged: Signal(int). Voir `QAbstractRangeSpinBox`.
        rangeChanged: Signal(int, int). Voir `QAbstractRangeSpinBox`.
        limitsChanged: Signal(int, int). Voir `QAbstractRangeSpinBox`.

    Exemple :
        >>> from PySide6.QtCore import QLocale
        >>> box = QRangeSpinBox()
        >>> box.setLocale(QLocale.c())
        >>> box.setLimits(0, 10)
        >>> box.setRange(8, 3)
        >>> box.text()
        '[3, 8]'
        >>> box.rangeFromText("5 ± 2")
        (3, 7)
    """

    lowerValueChanged = Signal(int)
    upperValueChanged = Signal(int)
    rangeChanged = Signal(int, int)
    limitsChanged = Signal(int, int)

    @override
    def textFromValue(self, value: int) -> str:
        return QIntervalFormat.textFromNumber(value, self.locale(), None)

    @override
    def valueFromText(self, text: str) -> int | None:
        value = QIntervalFormat.numberFromText(text, self.locale(), None)
        return None if value is None else int(value)

    @override
    def _toBase(self, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"An integer value must be an int, got {type(value).__name__}.")
        return value

    @override
    def _fromBase(self, steps: int) -> int:
        return steps


class QRealRangeSpinBox(QAbstractRangeSpinBox[float]):
    """Boîte numérique qui choisit un intervalle de nombres réels.

    Voir `QAbstractRangeSpinBox` pour la documentation complète. Valeurs initiales : 2
    décimales, les limites [0.0, 99.99] et le pas simple de 1.0 de `QDoubleSpinBox`,
    l'intervalle choisi (0.0, 99.99).

    Décimales
    ---------
    Le nombre de décimales (`decimals()`, 2 par défaut) fixe la taille d'un pas et l'écriture
    des nombres, comme pour `QDoubleSpinBox`. L'arrondi est celui de `QRealRangeSlider` et de
    `QRealSlider` (`rounded_to_steps`) : pour les mêmes décimales, les trois widgets retiennent
    la même valeur. Changer les décimales ré-exprime les limites et les bornes, arrondies au
    besoin : `decimalsChanged` est émis, puis `limitsChanged` et les signaux des bornes.

    NaN et l'infini lèvent `ValueError` ; une valeur qui n'est pas un nombre lève `TypeError`.
    Les décimales vont de 0 à 15.

    Propriétés:
        decimals (int): Le nombre de décimales. Accesseur `decimals()`, mutateur
            `setDecimals()`, signal `decimalsChanged`.

    Signaux:
        lowerValueChanged: Signal(float). Voir `QAbstractRangeSpinBox`.
        upperValueChanged: Signal(float). Voir `QAbstractRangeSpinBox`.
        rangeChanged: Signal(float, float). Voir `QAbstractRangeSpinBox`.
        limitsChanged: Signal(float, float). Voir `QAbstractRangeSpinBox`.
        decimalsChanged: Signal(int). Émis quand le nombre de décimales change, avant
            `limitsChanged` et les signaux des bornes.

    Slots:
        setDecimals(int): Fixe le nombre de décimales.

    Exemple :
        >>> from PySide6.QtCore import QLocale
        >>> box = QRealRangeSpinBox()
        >>> box.setLocale(QLocale.c())
        >>> box.setLimits(-10.0, 10.0)
        >>> box.setRange(3.75, -2.5)
        >>> box.text()
        '[-2.50, 3.75]'
        >>> box.rangeFromText("0.625 ± 3.125")
        (-2.5, 3.75)
    """

    lowerValueChanged = Signal(float)
    upperValueChanged = Signal(float)
    rangeChanged = Signal(float, float)
    limitsChanged = Signal(float, float)
    decimalsChanged = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Construit la boîte, avec 2 décimales et les limites [0.0, 99.99].

        Args:
            parent: Widget parent, ou None.
        """
        self.__decimals: int = self._DefaultDecimals   # set first: the base writes the field
        super().__init__(parent)

    # ================================================================ decimals

    def decimals(self) -> int:
        """Le nombre de décimales, qui fixe la taille d'un pas (2 par défaut)."""
        return self.__decimals

    @Slot(int)
    def setDecimals(self, digits: int) -> None:
        """Fixe le nombre de décimales, en ré-exprimant les limites, les bornes et le pas.

        Émet `decimalsChanged`, puis `limitsChanged` et les signaux des bornes si l'arrondi
        les a changés.

        Lève:
            TypeError: Si `digits` n'est pas un entier.
            ValueError: Si `digits` n'est pas dans [0, 15].
        """
        if isinstance(digits, bool) or not isinstance(digits, int): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"decimals must be an int, got {type(digits).__name__}.")
        if not 0 <= digits <= self._MaxDecimals:
            raise ValueError(f"decimals must be between 0 and {self._MaxDecimals}.")
        if digits == self.__decimals:
            return

        def change() -> None:
            self.__decimals = digits

        self._rebase(change, lambda: self.decimalsChanged.emit(digits))

    @override
    def textFromValue(self, value: float) -> str:
        return QIntervalFormat.textFromNumber(value, self.locale(), self.__decimals)

    @override
    def valueFromText(self, text: str) -> float | None:
        value = QIntervalFormat.numberFromText(text, self.locale(), self.__decimals)
        return None if value is None else float(value)

    # ================================================================ protected

    _DefaultDecimals: Final[int] = 2
    _MaxDecimals: Final[int] = 15
    _DefaultStepCount: ClassVar[int] = 9999   # initial limits: [0.0, 99.99], as QDoubleSpinBox

    @override
    def _toBase(self, value: float) -> int:
        return rounded_to_steps(value, self.__decimals)

    @override
    def _fromBase(self, steps: int) -> float:
        return steps / 10 ** self.__decimals

    @override
    def _stepDecimals(self) -> int:
        return self.__decimals


def _shifted(parts: QIntervalFormat.Parts, offset: int) -> QIntervalFormat.Parts:
    """The same parts, their spans moved by `offset` characters."""
    return parts._replace(lowerSpan=(parts.lowerSpan[0] + offset, parts.lowerSpan[1] + offset),
                          upperSpan=(parts.upperSpan[0] + offset, parts.upperSpan[1] + offset))


def _nearestInside(position: int, lowerSpan: tuple[int, int], upperSpan: tuple[int, int]) -> int:
    """The closest cursor position that lies in one of the two sections."""
    if position < lowerSpan[0]:
        return lowerSpan[0]
    if lowerSpan[1] < position < upperSpan[0]:
        return lowerSpan[1] if position - lowerSpan[1] <= upperSpan[0] - position else upperSpan[0]
    if position > upperSpan[1]:
        return upperSpan[1]
    return position
