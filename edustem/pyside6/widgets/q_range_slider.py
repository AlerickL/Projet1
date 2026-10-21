"""Curseurs à deux poignées, qui choisissent un intervalle : `QRangeSlider` (entiers) et `QRealRangeSlider` (réels).

L'utilisateur choisit un intervalle `[lowerValue, upperValue]` à l'intérieur d'un intervalle
possible `[minimum, maximum]`. Le widget se dessine comme un `QSlider`, par le style courant,
avec deux poignées au lieu d'une. La portion colorée de la rainure va d'une poignée à
l'autre.

    slider = QRangeSlider()
    slider.setLimits(0, 100)          # the possible interval
    slider.setRange(20, 60)           # the chosen interval
    slider.rangeChanged.connect(print)

Attention au vocabulaire. Ici, `range` désigne l'intervalle choisi, comme l'annonce le nom du
widget. L'intervalle possible, que `QSlider` règle par `setRange`, se règle par `setLimits`.
Voir `QAbstractRangeSlider` pour la documentation complète.

Dépendances locales : ce fichier hérite de `QAbstractWidget` (`q_abstract_widget`) ; l'arrondi
des réels vient de `rounded_to_steps` (`core/real_steps`), partagé avec les autres widgets réels ;
les règles de l'intervalle viennent de `IntervalRules` (`core/interval_rules`) et sa notation de
`QIntervalFormat` (`core/q_interval_format`), toutes deux partagées avec `QRangeSpinBox`.
"""

from __future__ import annotations

import copy
from abc import abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, ClassVar, Final, override

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, Signal, SignalInstance, Slot
from PySide6.QtGui import QHoverEvent, QKeyEvent, QMouseEvent, QPaintEvent, QWheelEvent
from PySide6.QtWidgets import QApplication, QSizePolicy, QSlider, QStyle, QStyleOptionSlider, QStylePainter, QWidget

from ..core.interval_rules import IntervalRules
from ..core.q_interval_format import QIntervalFormat
from ..core.real_steps import rounded_to_steps
from .q_abstract_widget import QAbstractWidget


class QAbstractRangeSlider[T: (int, float)](QAbstractWidget):
    """Base abstraite d'un curseur à deux poignées, qui choisit un intervalle de nombres de type `T`.

    Les classes concrètes sont `QRangeSlider` (`int`) et `QRealRangeSlider` (`float`). Cette
    base fait le dessin, la souris, le clavier, la molette et toutes les règles ; chaque
    classe concrète fournit la conversion de ses nombres et déclare ses signaux typés.

    Deux intervalles
    ----------------
    - **Les limites** (`limits`) sont l'intervalle possible, `[minimum, maximum]`. Elles
      jouent le rôle de `setRange` dans `QSlider`.
    - **L'intervalle choisi** (`range`) est `[lowerValue, upperValue]`. C'est la donnée que
      le widget produit.

    L'ordre `minimum <= lowerValue <= upperValue <= maximum` est toujours vrai. Les poignées
    ne se croisent jamais : chacune garde son rôle.

    ====================================  ==========================================
    `QSlider`                             Ici
    ====================================  ==========================================
    setRange(min, max)                    setLimits(minimum, maximum)
    rangeChanged(min, max)                limitsChanged(minimum, maximum)
    value / setValue                      lowerValue, upperValue, range / setRange
    valueChanged(v)                       lowerValueChanged, upperValueChanged,
                                          rangeChanged(lower, upper)
    sliderPosition                        lowerSliderPosition, upperSliderPosition
    sliderMoved(position)                 sliderMoved(lower, upper)
    Qt.Orientation.Vertical par défaut    Qt.Orientation.Horizontal par défaut
    ====================================  ==========================================

    Rencontre des deux poignées
    ---------------------------
    - **Égalité** (`overlapAllowed`, vrai par défaut). Si elle est permise, les deux bornes
      peuvent porter la même valeur. Sinon, un pas au moins les sépare.
    - **Collision** (`collisionMode`). En `Blocking` (par défaut), une poignée s'arrête contre
      l'autre. En `Pushing`, elle pousse l'autre, jusqu'à la limite ; la poignée poussée ne
      revient pas d'elle-même.
    - Ces deux règles valent pour la souris, le clavier, la molette et les mutateurs
      `setLowerValue` et `setUpperValue`.
    - `setRange(a, b)` fixe les deux bornes d'un coup. Il trie ses arguments et les ramène
      dans les limites. Si l'égalité est interdite et que les bornes se touchent, la borne
      supérieure monte d'un pas, ou la borne inférieure descend s'il n'y a plus de place.
    - **Limites de longueur nulle.** Quand `minimum == maximum`, les deux bornes valent cette
      valeur, même si l'égalité est interdite : aucun autre choix n'existe.

    Tout l'intervalle
    -----------------
    Le vocabulaire est celui de `QRect`, qui distingue les mutateurs qui changent la taille
    (`setLeft`) de ceux qui la gardent (`moveLeft`, `moveCenter`). La taille d'un intervalle
    est sa longueur, comme en mathématiques et dans `QLineF` : `width()` est déjà, dans
    `QWidget`, la largeur du widget en pixels.

    - `length()` lit la longueur, `upperValue() - lowerValue()`, et `center()` le centre. Le
      centre est un `float` dans les deux familles : il peut tomber entre deux pas (3.5 pour
      [2, 5], 0.015 pour [0.01, 0.02]).
    - `setLength` change la longueur à borne inférieure constante ; `widenBy` écarte (ou
      rapproche) les deux bornes d'un nombre de pas simples, à centre constant.
    - `moveLowerValue`, `moveUpperValue` et `moveCenter` déplacent tout l'intervalle, à
      longueur constante ; `shiftBy` le déplace d'un nombre de pas simples. Un centre visé
      entre deux pas est arrondi au pas, les égalités en s'éloignant de zéro.

    **Ce qu'une opération garde n'est jamais modifié ; c'est sa cible qui s'arrête aux
    limites.** Déplacé, l'intervalle s'arrête contre une limite. Élargi, il s'arrête dès
    qu'une borne touche sa limite, pour garder son centre. `setLength` s'arrête quand la
    borne supérieure atteint le maximum. La longueur ne descend jamais sous un pas si
    l'égalité est interdite. Seul le mode `Pushing` fait exception, et c'est son rôle : une
    borne pousse l'autre. Ces règles sont celles de `IntervalRules` (`core/interval_rules`),
    communes à toute la famille des widgets à intervalle.

    Souris
    ------
    - Glisser une poignée la déplace. Quand les deux poignées se recouvrent, chacune ne
      montre que sa part (voir « Apparence ») : on saisit la poignée dont on touche la part.
    - Glisser le segment entre les poignées déplace tout l'intervalle, sans changer sa
      longueur, jusqu'à une limite.
    - Cliquer dans la rainure, hors du segment, agit sur la poignée la plus proche. Selon
      le style, elle saute au clic (puis se glisse), ou avance d'un pas de page.

    Clavier et molette
    ------------------
    Le widget n'a qu'un arrêt de tabulation. Une poignée est donc « courante »
    (`currentHandle`) : la dernière saisie à la souris, ou `Handle.Both` après un glissement
    du segment. Espace passe à la suivante (inférieure, supérieure, les deux). Les flèches
    déplacent la poignée courante d'un pas simple, Page précédente et Page suivante d'un pas
    de page, Début et Fin vont aux limites. Avec `Handle.Both`, tout l'intervalle se
    déplace. Avec Maj, ces touches élargissent ou resserrent l'intervalle autour de son
    centre (`widenBy`), comme Maj + flèche dans `QRangeSpinBox` ; Qt ne donne pas de sens à
    Maj ici. La molette agit sur la poignée sous le pointeur, sinon sur la poignée courante ;
    avec Ctrl ou Maj, elle avance d'un pas de page, comme dans `QSlider`.

    Suivi
    -----
    Avec suivi (`hasTracking`, vrai par défaut), les valeurs changent pendant le glissement.
    Sans suivi, seules les positions changent (`sliderMoved`), et les valeurs sont retenues
    au relâchement. Le clavier, la molette et les mutateurs changent les valeurs tout de
    suite, dans les deux cas.

    Apparence
    ---------
    Le style courant dessine tout, avec les mesures de `QSlider` : rainure, poignées,
    graduations, taille recommandée. `tickPosition`, `tickInterval`, `invertedAppearance` et
    `invertedControls` ont le sens qu'ils ont dans `QSlider`. Comme `QSlider.setOrientation`,
    changer l'orientation transpose la politique de taille. Une feuille de style
    `QSlider::handle` ne s'applique pas : le widget n'est pas un `QSlider`.

    Deux poignées qui se recouvrent restent à leur position exacte, mais chacune n'est
    dessinée qu'en partie. La zone commune est partagée en deux, avec un dégagement au
    milieu où la rainure reste visible, colorée comme le reste de l'intervalle choisi,
    même quand les deux bornes sont égales. La borne inférieure garde le côté des petites
    valeurs, la borne supérieure l'autre. Le dégagement vaut un cinquième de la longueur
    d'une poignée, deux pixels au moins. Il grandit avec le recouvrement, sans jamais
    le dépasser : une poignée ne perd donc rien tant que l'autre ne la touche pas. Dès
    que les poignées se séparent, elles se dessinent entières.

    Texte
    -----
    Le curseur n'affiche pas de texte, mais il sait écrire son intervalle choisi, comme
    `QProgressBar` écrit sa valeur : `text()` rend `[-2.50, 3.75]`, pour un libellé ou une
    infobulle. La notation vient du format (`intervalFormat`, un `QIntervalFormat` partagé
    avec `QRangeSpinBox`) et les nombres suivent la langue du widget (`locale()`).
    `textFromRange` écrit n'importe quel intervalle.

    Limites techniques
    ------------------
    Le style travaille avec un `int` C++ : comptées en pas, les limites doivent tenir dans
    +-(2**31 - 1), de même que leur différence. Au-delà, `ValueError` est levée et le widget
    reste inchangé. Un pas simple ou un pas de page vaut au moins un pas.

    Propriétés:
        minimum (T): La limite inférieure. Accesseur `minimum()`, mutateur `setMinimum()`,
            signal `limitsChanged`.
        maximum (T): La limite supérieure. Accesseur `maximum()`, mutateur `setMaximum()`,
            signal `limitsChanged`.
        lowerValue (T): La borne inférieure choisie. Accesseur `lowerValue()`, mutateur
            `setLowerValue()`, signal `lowerValueChanged`.
        upperValue (T): La borne supérieure choisie. Accesseur `upperValue()`, mutateur
            `setUpperValue()`, signal `upperValueChanged`.
        orientation (Qt.Orientation): Accesseur `orientation()`, mutateur `setOrientation()`.
        tracking (bool): Accesseur `hasTracking()`, mutateur `setTracking()`.
        overlapAllowed (bool): Accesseur `overlapAllowed()`, mutateur `setOverlapAllowed()`.
        collisionMode (CollisionMode): Accesseur `collisionMode()`, mutateur
            `setCollisionMode()`.
        currentHandle (Handle): Accesseur `currentHandle()`, mutateur `setCurrentHandle()`.
        intervalFormat (QIntervalFormat): Accesseur `intervalFormat()` (une copie),
            mutateur `setIntervalFormat()`.

    Signaux:
        lowerValueChanged: Signal(T). Émis quand la borne inférieure change.
        upperValueChanged: Signal(T). Émis quand la borne supérieure change.
        rangeChanged: Signal(T, T). Émis une fois quand l'une ou l'autre borne change, après
            les deux signaux précédents.
        limitsChanged: Signal(T, T). Émis quand les limites changent, avant les signaux des
            bornes.
        sliderMoved: Signal(T, T). Émis pendant un glissement, avec les deux positions.
        sliderPressed: Signal(Handle). Émis quand l'utilisateur saisit une poignée, ou le
            segment (`Handle.Both`).
        sliderReleased: Signal(Handle). Émis au relâchement, après les signaux des bornes.

    Slots:
        setLimits(T, T): Fixe les limites.
        setMinimum(T): Fixe la limite inférieure.
        setMaximum(T): Fixe la limite supérieure.
        setRange(T, T): Fixe l'intervalle choisi.
        setLowerValue(T): Fixe la borne inférieure.
        setUpperValue(T): Fixe la borne supérieure.
        setLength(T): Fixe la longueur, à borne inférieure constante.
        widenBy(int): Écarte les bornes d'un nombre de pas simples, à centre constant.
        shiftBy(int): Déplace tout l'intervalle d'un nombre de pas simples.
        moveLowerValue(T): Déplace tout l'intervalle vers une borne inférieure.
        moveUpperValue(T): Déplace tout l'intervalle vers une borne supérieure.
        moveCenter(float): Déplace tout l'intervalle vers un centre.
        setSingleStep(T): Fixe le pas simple.
        setPageStep(T): Fixe le pas de page.
        setTickInterval(T): Fixe l'écart des graduations.
        setTickPosition(QSlider.TickPosition): Place les graduations.
        setOrientation(Qt.Orientation): Fixe l'orientation.
        setTracking(bool): Active ou désactive le suivi.
        setInvertedAppearance(bool): Inverse le sens du dessin.
        setInvertedControls(bool): Inverse le sens du clavier et de la molette.
        setOverlapAllowed(bool): Permet ou interdit l'égalité des bornes.
        setCollisionMode(CollisionMode): Choisit le comportement de collision.
        setCurrentHandle(Handle): Choisit la poignée que le clavier déplace.
        setIntervalFormat(QIntervalFormat): Fixe la notation de l'intervalle.

    Sous-classes
    ------------
    Une classe concrète fournit ses deux conversions, `_toBase` et `_fromBase`, entre un
    nombre de type `T` et un nombre entier de pas, l'écriture d'un nombre (`textFromValue`),
    le nombre de décimales d'un pas s'il en a (`_stepDecimals`), et ses cinq signaux typés :
    `lowerValueChanged`, `upperValueChanged`, `rangeChanged`, `limitsChanged` et
    `sliderMoved`. Tant qu'un de ces membres manque, instancier la classe lève `TypeError`
    en le nommant (voir `QAbstractWidget`).
    """

    class Handle(Enum):
        """Désigne une poignée du curseur.

        Attributs:
            NoHandle: Aucune poignée.
            Lower: La poignée de la borne inférieure.
            Upper: La poignée de la borne supérieure.
            Both: Les deux poignées ensemble, c'est-à-dire le segment qui les relie.
        """

        NoHandle = 0
        Lower = 1
        Upper = 2
        Both = 3

    class CollisionMode(Enum):
        """Ce que fait une poignée qui rencontre l'autre.

        Attributs:
            Blocking: Elle s'arrête contre l'autre.
            Pushing: Elle pousse l'autre, jusqu'à la limite.
        """

        Blocking = 0
        Pushing = 1

    sliderPressed = Signal(Handle)
    sliderReleased = Signal(Handle)

    # Abstract members: the typed signals, which a generic base cannot declare (`Signal(T)` does
    # not exist). At run time, an abstract property is the standard way to require an attribute
    # from a subclass, which replaces it with its `Signal` (these bodies never run). A type
    # checker rejects a `Signal` replacing a property, so it is shown the class attribute instead.
    if TYPE_CHECKING:
        lowerValueChanged: ClassVar[Signal]
        upperValueChanged: ClassVar[Signal]
        rangeChanged: ClassVar[Signal]
        limitsChanged: ClassVar[Signal]
        sliderMoved: ClassVar[Signal]
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

        @property
        @abstractmethod
        def sliderMoved(self) -> SignalInstance:
            """Signal(T, T), déclaré par chaque classe concrète."""

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        """Construit le curseur, l'intervalle choisi couvrant toutes les limites.

        Args:
            orientation: Orientation du curseur.
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self.__minimum: int = 0                       # everything below is counted in steps
        self.__maximum: int = self._DefaultStepCount
        self.__lower: int = self.__minimum
        self.__upper: int = self.__maximum
        self.__lowerPosition: int = self.__lower
        self.__upperPosition: int = self.__upper
        self.__requestedSingleStep: T | None = None   # what was asked; None: one step
        self.__requestedPageStep: T | None = None     # None: ten steps
        self.__requestedTickInterval: T | None = None  # None: automatic
        self.__tickPosition: QSlider.TickPosition = QSlider.TickPosition.NoTicks
        self.__orientation: Qt.Orientation = orientation
        self.__tracking: bool = True
        self.__invertedAppearance: bool = False
        self.__invertedControls: bool = False
        self.__overlapAllowed: bool = True
        self.__collisionMode: QAbstractRangeSlider.CollisionMode = QAbstractRangeSlider.CollisionMode.Blocking
        self.__format: QIntervalFormat = QIntervalFormat()

        Handle = QAbstractRangeSlider.Handle
        self.__currentHandle: QAbstractRangeSlider.Handle = Handle.Lower
        self.__pressedHandle: QAbstractRangeSlider.Handle = Handle.NoHandle
        self.__hoverHandle: QAbstractRangeSlider.Handle = Handle.NoHandle
        self.__clickOffset: int = 0                   # pixels from the handle's leading edge to the press
        self.__pressPositions: tuple[int, int] = (self.__lower, self.__upper)
        self.__pressValue: int = 0                    # value under the press, for a drag of the segment
        self.__wheelRemainder: int = 0

        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed, QSizePolicy.ControlType.Slider)
        if orientation == Qt.Orientation.Vertical:
            policy.transpose()
        self.setSizePolicy(policy)
        self.setAttribute(Qt.WidgetAttribute.WA_WState_OwnSizePolicy, False)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)    # styles only set it on a real QSlider
        self.setFocusPolicy(Qt.FocusPolicy(self.style().styleHint(QStyle.StyleHint.SH_Button_FocusPolicy)))

    # ================================================================== limits

    def minimum(self) -> T:
        """La limite inférieure de l'intervalle possible."""
        return self._fromBase(self.__minimum)

    # Slots typed `object`: the slot is shared by the int and the float subclasses.
    @Slot(object)
    def setMinimum(self, minimum: T) -> None:
        """Fixe la limite inférieure, en déplaçant la limite supérieure au besoin (comme `QSlider.setMinimum`)."""
        self.setLimits(minimum, max(self.maximum(), minimum))

    def maximum(self) -> T:
        """La limite supérieure de l'intervalle possible."""
        return self._fromBase(self.__maximum)

    @Slot(object)
    def setMaximum(self, maximum: T) -> None:
        """Fixe la limite supérieure, en déplaçant la limite inférieure au besoin (comme `QSlider.setMaximum`)."""
        self.setLimits(min(self.minimum(), maximum), maximum)

    def limits(self) -> tuple[T, T]:
        """L'intervalle possible, `(minimum, maximum)`."""
        return self.minimum(), self.maximum()

    @Slot(object, object)
    def setLimits(self, minimum: T, maximum: T) -> None:
        """Fixe l'intervalle possible ; un maximum inférieur au minimum devient le minimum.

        L'intervalle choisi est ramené dans les nouvelles limites. `limitsChanged`, puis les
        signaux des bornes, sont émis pour ce qui change.

        Args:
            minimum: La limite inférieure.
            maximum: La limite supérieure.

        Lève:
            TypeError: Si une limite n'est pas un nombre du type attendu.
            ValueError: Si les limites comptent trop de pas (voir « Limites techniques »).
        """
        lo = self._toBase(minimum)
        hi = max(lo, self._toBase(maximum))
        self.__checkLimits(lo, hi)

        def change() -> None:
            self.__minimum, self.__maximum = lo, hi
            self.__setBoth(*self.__resolved(QAbstractRangeSlider.Handle.Both, self.__lower, self.__upper))

        self._applyAndReport(change)

    # =================================================================== range

    def lowerValue(self) -> T:
        """La borne inférieure de l'intervalle choisi (celle retenue ; sans suivi, pas la position d'une poignée glissée)."""
        return self._fromBase(self.__lower)

    @Slot(object)
    def setLowerValue(self, lower: T) -> None:
        """Fixe la borne inférieure, selon le mode de collision.

        En `Blocking`, elle s'arrête contre la borne supérieure. En `Pushing`, elle la pousse.

        Lève:
            TypeError: Si `lower` n'est pas un nombre du type attendu.
            ValueError: Si `lower` n'est pas fini.
        """
        self.__moveTo(QAbstractRangeSlider.Handle.Lower, self._toBase(lower))

    def upperValue(self) -> T:
        """La borne supérieure de l'intervalle choisi (celle retenue ; sans suivi, pas la position d'une poignée glissée)."""
        return self._fromBase(self.__upper)

    @Slot(object)
    def setUpperValue(self, upper: T) -> None:
        """Fixe la borne supérieure, selon le mode de collision.

        En `Blocking`, elle s'arrête contre la borne inférieure. En `Pushing`, elle la pousse.

        Lève:
            TypeError: Si `upper` n'est pas un nombre du type attendu.
            ValueError: Si `upper` n'est pas fini.
        """
        self.__moveTo(QAbstractRangeSlider.Handle.Upper, self._toBase(upper))

    def range(self) -> tuple[T, T]:
        """L'intervalle choisi, `(lowerValue, upperValue)`."""
        return self.lowerValue(), self.upperValue()

    @Slot(object, object)
    def setRange(self, lower: T, upper: T) -> None:
        """Fixe les deux bornes de l'intervalle choisi d'un seul coup.

        Les deux valeurs sont triées, puis ramenées dans les limites. Le mode de collision ne
        joue pas ici. `rangeChanged` n'est émis qu'une fois.

        Args:
            lower: Une borne.
            upper: L'autre borne.

        Lève:
            TypeError: Si une borne n'est pas un nombre du type attendu.
            ValueError: Si une borne n'est pas finie.
        """
        lo, up = self.__resolved(QAbstractRangeSlider.Handle.Both, self._toBase(lower), self._toBase(upper))
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

    # ================================================================= sliding

    def lowerSliderPosition(self) -> T:
        """La position de la poignée inférieure ; sans suivi, elle précède `lowerValue()` pendant un glissement."""
        return self._fromBase(self.__lowerPosition)

    def upperSliderPosition(self) -> T:
        """La position de la poignée supérieure ; sans suivi, elle précède `upperValue()` pendant un glissement."""
        return self._fromBase(self.__upperPosition)

    def isSliderDown(self) -> bool:
        """Indique si l'utilisateur tient une poignée ou le segment."""
        return self.__pressedHandle != QAbstractRangeSlider.Handle.NoHandle

    def pressedHandle(self) -> Handle:
        """La poignée tenue par l'utilisateur.

        Retourne:
            `Handle.Both` pour le segment, `Handle.NoHandle` si rien n'est tenu.
        """
        return self.__pressedHandle

    def hasTracking(self) -> bool:
        """Indique si les valeurs suivent le glissement (vrai par défaut)."""
        return self.__tracking

    @Slot(bool)
    def setTracking(self, enable: bool) -> None:
        """Active ou désactive le suivi des valeurs pendant un glissement."""
        self.__tracking = enable

    def currentHandle(self) -> Handle:
        """La poignée que le clavier déplace : `Lower`, `Upper` ou `Both`."""
        return self.__currentHandle

    @Slot(Handle)
    def setCurrentHandle(self, handle: Handle) -> None:
        """Choisit la poignée que le clavier déplace.

        Lève:
            ValueError: Si `handle` vaut `Handle.NoHandle`.
        """
        if handle == QAbstractRangeSlider.Handle.NoHandle:
            raise ValueError("The current handle must be Lower, Upper or Both.")
        self.__currentHandle = handle
        self.update()

    # =================================================================== steps

    def resolution(self) -> T:
        """La taille d'un pas, la plus petite distance entre deux valeurs : 1 en entier, 10**-decimals en réel."""
        return self._fromBase(1)

    def singleStep(self) -> T:
        """Le pas simple effectif (flèches, molette) : un pas au moins."""
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

    def pageStep(self) -> T:
        """Le pas de page effectif (touches de page, clic dans la rainure) : un pas au moins."""
        return self._fromBase(self.__basePageStep())

    @Slot(object)
    def setPageStep(self, step: T) -> None:
        """Fixe le pas de page ; un pas négatif est pris en valeur absolue.

        Lève:
            TypeError: Si `step` n'est pas un nombre du type attendu.
            ValueError: Si `step` n'est pas fini.
        """
        self._toBase(step)
        self.__requestedPageStep = step

    # ============================================================== appearance

    def orientation(self) -> Qt.Orientation:
        """L'orientation du curseur (horizontale par défaut)."""
        return self.__orientation

    @Slot(Qt.Orientation)
    def setOrientation(self, orientation: Qt.Orientation) -> None:
        """Fixe l'orientation ; comme `QSlider.setOrientation`, la politique de taille est transposée."""
        if orientation == self.__orientation:
            return
        self.__orientation = orientation
        if not self.testAttribute(Qt.WidgetAttribute.WA_WState_OwnSizePolicy):
            self.setSizePolicy(self.sizePolicy().transposed())
            self.setAttribute(Qt.WidgetAttribute.WA_WState_OwnSizePolicy, False)
        self.update()
        self.updateGeometry()

    def tickPosition(self) -> QSlider.TickPosition:
        """La position des graduations (aucune par défaut)."""
        return self.__tickPosition

    @Slot(QSlider.TickPosition)
    def setTickPosition(self, position: QSlider.TickPosition) -> None:
        """Place les graduations, comme `QSlider.setTickPosition`."""
        self.__tickPosition = position
        self.update()
        self.updateGeometry()

    def tickInterval(self) -> T:
        """L'écart entre deux graduations, en unités de valeur ; 0 laisse le style choisir."""
        return self._fromBase(self.__baseTickInterval())

    @Slot(object)
    def setTickInterval(self, interval: T) -> None:
        """Fixe l'écart entre deux graduations ; 0 laisse le style choisir.

        Lève:
            TypeError: Si `interval` n'est pas un nombre du type attendu.
            ValueError: Si `interval` n'est pas fini.
        """
        self._toBase(interval)
        self.__requestedTickInterval = interval
        self.update()

    def invertedAppearance(self) -> bool:
        """Indique si le dessin est inversé (le minimum à droite, ou en haut)."""
        return self.__invertedAppearance

    @Slot(bool)
    def setInvertedAppearance(self, inverted: bool) -> None:
        """Inverse le sens du dessin, comme `QSlider.setInvertedAppearance`."""
        self.__invertedAppearance = inverted
        self.update()

    def invertedControls(self) -> bool:
        """Indique si le sens du clavier et de la molette est inversé."""
        return self.__invertedControls

    @Slot(bool)
    def setInvertedControls(self, inverted: bool) -> None:
        """Inverse le sens du clavier et de la molette, comme `QSlider.setInvertedControls`."""
        self.__invertedControls = inverted

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
            self.__setBoth(*self.__resolved(QAbstractRangeSlider.Handle.Both, self.__lower, self.__upper))

        self._applyAndReport(change)

    def collisionMode(self) -> CollisionMode:
        """Ce que fait une poignée qui rencontre l'autre (`Blocking` par défaut)."""
        return self.__collisionMode

    @Slot(CollisionMode)
    def setCollisionMode(self, mode: CollisionMode) -> None:
        """Choisit entre une poignée qui s'arrête contre l'autre et une poignée qui la pousse."""
        self.__collisionMode = mode

    # ==================================================================== text

    def text(self) -> str:
        """L'intervalle choisi écrit dans le format : `[-2.50, 3.75]`."""
        return self.textFromRange(self.lowerValue(), self.upperValue())

    def textFromRange(self, lower: T, upper: T) -> str:
        """Écrit un intervalle dans le format et la langue du widget."""
        return self.__format.toString(self.textFromValue(lower), self.textFromValue(upper), self.locale())

    @abstractmethod
    def textFromValue(self, value: T) -> str:
        """Écrit un nombre dans la langue du widget. Point d'extension obligatoire."""

    def intervalFormat(self) -> QIntervalFormat:
        """Une copie de la notation de l'intervalle : délimiteurs et séparateur."""
        return copy.copy(self.__format)

    @Slot(QIntervalFormat)
    def setIntervalFormat(self, intervalFormat: QIntervalFormat) -> None:
        """Fixe la notation de l'intervalle ; une copie est gardée.

        Si la langue change ensuite et rend le séparateur ambigu, le séparateur automatique
        le remplace (voir `QIntervalFormat.separatorFor`).

        Lève:
            ValueError: Si le séparateur contient la marque décimale de la langue du widget.
        """
        if not intervalFormat.isValidFor(self.locale()):
            raise ValueError(f"The separator {intervalFormat.separator()!r} contains the decimal point of "
                             f"the locale {self.locale().name()}.")
        self.__format = copy.copy(intervalFormat)

    # ==================================================================== size

    @override
    def sizeHint(self) -> QSize:
        """La taille recommandée, calculée comme celle de `QSlider`."""
        self.ensurePolished()
        option = self._styleOption(self.__lowerPosition)
        thickness = self.style().pixelMetric(QStyle.PixelMetric.PM_SliderThickness, option, self)
        if self.__tickPosition.value & QSlider.TickPosition.TicksAbove.value:
            thickness += self._TickSpace
        if self.__tickPosition.value & QSlider.TickPosition.TicksBelow.value:
            thickness += self._TickSpace
        size = QSize(self._HintLength, thickness)
        if self.__orientation == Qt.Orientation.Vertical:
            size.transpose()
        return self.style().sizeFromContents(QStyle.ContentsType.CT_Slider, option, size, self)

    @override
    def minimumSizeHint(self) -> QSize:
        """La taille minimum recommandée : la place de deux poignées dans le sens du curseur."""
        size = self.sizeHint()
        option = self._styleOption(self.__lowerPosition)
        length = 2 * self.style().pixelMetric(QStyle.PixelMetric.PM_SliderLength, option, self)
        if self.__orientation == Qt.Orientation.Horizontal:
            size.setWidth(length)
        else:
            size.setHeight(length)
        return size

    # ================================================================== events

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        Handle = QAbstractRangeSlider.Handle
        Control, Sub = QStyle.ComplexControl.CC_Slider, QStyle.SubControl
        painter = QStylePainter(self)

        # The style fills a groove from the minimum end up to the handle. Three clipped passes
        # put that fill between the two handles instead. Each outer zone uses a groove whose
        # empty fill starts at the opposite end, so that no stub of it shows.
        a, b = sorted((self.__pick(self.__handleRect(self.__lowerPosition).center()),
                       self.__pick(self.__handleRect(self.__upperPosition).center())))
        spans = self.__visibleSpans()
        if self.__handlesOverlap():
            # The clearance between two overlapping handles is part of the chosen range: it is
            # filled too, even when the two centers meet.
            a, b = min(a, spans[0][2]), max(b, spans[1][1])
        end = self.width() if self.__orientation == Qt.Orientation.Horizontal else self.height()
        for start, stop, position, upsideDown in ((0, a, self.__minimum, True), (b, end, self.__minimum, False),
                                                  (a, b, self.__maximum, False)):
            if stop <= start:
                continue
            option = self._styleOption(position)
            option.upsideDown = upsideDown
            option.subControls = Sub.SC_SliderGroove
            option.state &= ~QStyle.StateFlag.State_HasFocus
            painter.save()
            painter.setClipRect(self.__alongRect(start, stop))
            painter.drawComplexControl(Control, option)
            painter.restore()

        if self.__tickPosition != QSlider.TickPosition.NoTicks:
            option = self._styleOption(self.__minimum)
            option.subControls = Sub.SC_SliderTickmarks
            painter.drawComplexControl(Control, option)

        active = self.__pressedHandle if self.isSliderDown() else self.__hoverHandle
        # Each handle is clipped to its visible span: two handles that overlap show a part each.
        for handle, start, stop in spans:
            option = self._styleOption(self.__lowerPosition if handle == Handle.Lower else self.__upperPosition)
            option.subControls = Sub.SC_SliderHandle
            if active in (handle, Handle.Both):
                option.activeSubControls = Sub.SC_SliderHandle
                if self.isSliderDown():
                    option.state |= QStyle.StateFlag.State_Sunken
            else:
                option.state &= ~QStyle.StateFlag.State_MouseOver
            if self.__currentHandle not in (handle, Handle.Both):
                option.state &= ~QStyle.StateFlag.State_HasFocus
            painter.save()
            painter.setClipRect(self.__alongRect(start, stop))
            painter.drawComplexControl(Control, option)
            painter.restore()

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        Handle = QAbstractRangeSlider.Handle
        button = event.button()
        absolute = self.__matches(button, QStyle.StyleHint.SH_Slider_AbsoluteSetButtons)
        page = self.__matches(button, QStyle.StyleHint.SH_Slider_PageSetButtons)
        if (self.__minimum == self.__maximum or event.buttons() != button
                or not (absolute or page or button == Qt.MouseButton.LeftButton)):
            event.ignore()
            return
        event.accept()
        position = event.position().toPoint()
        self.__pressPositions = (self.__lowerPosition, self.__upperPosition)
        hit = self.__handleAt(position)

        if hit == Handle.Both:
            self.__pressValue = self.__valueAt(self.__pick(position) - self.__handleLength() // 2)
            self.__press(Handle.Both)
        elif hit != Handle.NoHandle:
            rect = self.__handleRect(self.__lowerPosition if hit == Handle.Lower else self.__upperPosition)
            self.__clickOffset = self.__pick(position) - self.__pick(rect.topLeft())
            self.__press(hit)
        else:
            value = self.__valueAt(self.__pick(position) - self.__handleLength() // 2)
            nearest = self.__nearestHandle(value)
            if absolute:
                self.__clickOffset = self.__handleLength() // 2
                self.__press(nearest)
                self.__drag(nearest, value)
            elif page:
                current = self.__lowerPosition if nearest == Handle.Lower else self.__upperPosition
                self.__currentHandle = nearest
                self.__step(nearest, self.__basePageStep() if value > current else -self.__basePageStep())
            else:
                event.ignore()

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        Handle = QAbstractRangeSlider.Handle
        if not self.isSliderDown():
            event.ignore()
            return
        event.accept()
        position = event.position().toPoint()
        if self.__pressedHandle == Handle.Both:
            value = self.__valueAt(self.__pick(position) - self.__handleLength() // 2)
            if self.__strayed(position):
                value = self.__pressValue
            self.__drag(Handle.Both, self.__pressPositions[0] + value - self.__pressValue)
            return
        value = self.__valueAt(self.__pick(position) - self.__clickOffset)
        if self.__strayed(position):
            value = self.__pressPositions[0 if self.__pressedHandle == Handle.Lower else 1]
        self.__drag(self.__pressedHandle, value)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self.isSliderDown() or event.buttons() != Qt.MouseButton.NoButton:
            event.ignore()
            return
        event.accept()
        released = self.__pressedHandle
        self.__pressedHandle = QAbstractRangeSlider.Handle.NoHandle
        self._applyAndReport(lambda: self.__setBoth(self.__lowerPosition, self.__upperPosition))
        self.sliderReleased.emit(released)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        Handle = QAbstractRangeSlider.Handle
        key = event.key()
        single, page = self.__baseSingleStep(), self.__basePageStep()
        forward = -1 if self.__invertedControls else 1
        sideways = -forward if self.isRightToLeft() else forward
        offsets: dict[int, int] = {
            Qt.Key.Key_Left: -sideways * single, Qt.Key.Key_Right: sideways * single,
            Qt.Key.Key_Down: -forward * single, Qt.Key.Key_Up: forward * single,
            Qt.Key.Key_PageDown: -forward * page, Qt.Key.Key_PageUp: forward * page,
            Qt.Key.Key_Home: self.__minimum - self.__maximum, Qt.Key.Key_End: self.__maximum - self.__minimum,
        }
        if key == Qt.Key.Key_Space:
            following = {Handle.Lower: Handle.Upper, Handle.Upper: Handle.Both, Handle.Both: Handle.Lower}
            self.setCurrentHandle(following[self.__currentHandle])
        elif key in offsets and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.__applyBounds(self.__rules().widened(self.__lower, self.__upper, offsets[key]))
        elif key in offsets:
            self.__step(self.__currentHandle, offsets[key])
        else:
            event.ignore()
            return
        event.accept()

    @override
    def wheelEvent(self, event: QWheelEvent) -> None:
        Handle = QAbstractRangeSlider.Handle
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta == 0 or self.__minimum == self.__maximum:
            event.ignore()
            return
        event.accept()
        self.__wheelRemainder += -delta if event.inverted() else delta
        notches = int(self.__wheelRemainder / self._WheelNotch)
        if notches == 0:
            return
        self.__wheelRemainder -= notches * self._WheelNotch
        page = self.__basePageStep()
        if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            offset = notches * page
        else:
            offset = notches * self.__baseSingleStep() * max(1, QApplication.wheelScrollLines())
            offset = max(-page, min(page, offset))
        under = self.__handleAt(event.position().toPoint())
        handle = under if under != Handle.NoHandle else self.__currentHandle
        self.__step(handle, -offset if self.__invertedControls else offset)

    @override
    def event(self, event: QEvent) -> bool:
        kind = event.type()
        if kind in (QEvent.Type.HoverEnter, QEvent.Type.HoverMove) and isinstance(event, QHoverEvent):
            self.__setHoverHandle(self.__handleAt(event.position().toPoint()))
        elif kind == QEvent.Type.HoverLeave:
            self.__setHoverHandle(QAbstractRangeSlider.Handle.NoHandle)
        return super().event(event)

    # ================================================================ protected

    _DefaultStepCount: ClassVar[int] = 99      # initial limits, in steps: [0, 99], as QSlider
    _IntMax: Final[int] = 2**31 - 1            # a C++ int, which is what a QStyleOptionSlider holds
    _HintLength: Final[int] = 84               # as QSlider::sizeHint
    _TickSpace: Final[int] = 5                 # as QSlider::sizeHint
    _WheelNotch: Final[int] = 120              # eighths of a degree for one notch of a wheel
    _SplitGapRatio: Final[float] = 0.2         # clearance between two stacked handles, in handle lengths
    _MinSplitGap: Final[int] = 2               # and in pixels at least: one pixel does not read as a gap

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

    def _styleOption(self, position: int) -> QStyleOptionSlider:
        """L'option de style d'un `QSlider` qui aurait sa poignée à `position`, sans sous-contrôle.

        Remplie comme le fait `QSlider.initStyleOption`.

        Args:
            position: La position de la poignée, en pas.
        """
        option = QStyleOptionSlider()
        option.initFrom(self)
        option.subControls = QStyle.SubControl.SC_None
        option.activeSubControls = QStyle.SubControl.SC_None
        option.orientation = self.__orientation
        option.minimum = self.__minimum
        option.maximum = self.__maximum
        option.tickPosition = self.__tickPosition
        option.tickInterval = self.__baseTickInterval()
        option.upsideDown = self.__upsideDown()
        option.direction = Qt.LayoutDirection.LeftToRight    # upsideDown carries the direction, as in QSlider
        option.sliderPosition = position
        option.sliderValue = position
        option.singleStep = self.__baseSingleStep()
        option.pageStep = self.__basePageStep()
        if self.__orientation == Qt.Orientation.Horizontal:
            option.state |= QStyle.StateFlag.State_Horizontal
        return option

    def _applyAndReport(self, change: Callable[[], object], announce: Callable[[], object] | None = None) -> None:
        """Applique `change`, redessine, puis émet les signaux de ce qui a changé.

        Args:
            change: La modification de l'état. Si elle lève, rien n'est émis.
            announce: Appelé après la modification, avant `limitsChanged` et les signaux des
                bornes (ex. pour émettre `decimalsChanged` en premier).
        """
        oldLimits, oldRange = self.limits(), self.range()
        change()
        self.update()
        newLimits, newRange = self.limits(), self.range()
        if announce is not None:
            announce()
        if newLimits != oldLimits:
            self.limitsChanged.emit(*newLimits)
        if newRange[0] != oldRange[0]:
            self.lowerValueChanged.emit(newRange[0])
        if newRange[1] != oldRange[1]:
            self.upperValueChanged.emit(newRange[1])
        if newRange != oldRange:
            self.rangeChanged.emit(*newRange)

    def _rebase(self, change: Callable[[], object], revert: Callable[[], object],
                announce: Callable[[], object] | None = None) -> None:
        """Change la conversion entre nombres et pas, en gardant les limites et l'intervalle choisi.

        Les limites et les bornes sont relues avant le changement, puis reconverties après,
        arrondies au besoin.

        Args:
            change: Modifie ce dont `_toBase` et `_fromBase` dépendent.
            revert: Défait `change`, appelé si les limites ne tiennent plus.
            announce: Voir `_applyAndReport`.

        Lève:
            ValueError: Si les limites comptent trop de pas après le changement. Le widget
                reste alors inchangé.
        """
        minimum, maximum, lower, upper = self.minimum(), self.maximum(), self.lowerValue(), self.upperValue()

        def apply() -> None:
            change()
            try:
                lo = self._toBase(minimum)
                hi = max(lo, self._toBase(maximum))
                self.__checkLimits(lo, hi)
            except ValueError:
                revert()
                raise
            self.__minimum, self.__maximum = lo, hi
            self.__setBoth(*self.__resolved(QAbstractRangeSlider.Handle.Both, self._toBase(lower), self._toBase(upper)))

        self._applyAndReport(apply, announce)

    # ================================================================== private

    def __checkLimits(self, lo: int, hi: int) -> None:
        limit = self._IntMax
        if abs(lo) > limit or abs(hi) > limit or hi - lo > limit:
            raise ValueError(
                f"The limits [{self._fromBase(lo)}, {self._fromBase(hi)}] exceed what a slider supports "
                f"(bounds within +-{limit} steps, difference too).")

    def __baseSingleStep(self) -> int:
        requested = self.__requestedSingleStep
        return 1 if requested is None else max(1, abs(self._toBase(requested)))

    def __basePageStep(self) -> int:
        requested = self.__requestedPageStep
        return 10 if requested is None else max(1, abs(self._toBase(requested)))

    def __baseTickInterval(self) -> int:
        requested = self.__requestedTickInterval
        return 0 if requested is None else min(self._IntMax, abs(self._toBase(requested)))

    def __rules(self) -> IntervalRules:
        lo, hi = self.__minimum, self.__maximum
        pushing = self.__collisionMode == QAbstractRangeSlider.CollisionMode.Pushing
        return IntervalRules(lo, hi, IntervalRules.gap_for(lo, hi, self.__overlapAllowed), pushing)

    def __resolved(self, moved: Handle, lower: int, upper: int) -> tuple[int, int]:
        """The legal positions closest to a request, given which handle asks to move.

        `Lower` and `Upper` move one handle against the other one's current position, by the
        collision mode. `Both` takes two free values.
        """
        Handle = QAbstractRangeSlider.Handle
        rules = self.__rules()
        if moved == Handle.Lower:
            return rules.with_lower(self.__lowerPosition, self.__upperPosition, lower)
        if moved == Handle.Upper:
            return rules.with_upper(self.__lowerPosition, self.__upperPosition, upper)
        return rules.resolved(lower, upper)

    def __setBoth(self, lower: int, upper: int) -> None:
        """Sets the values and the positions together."""
        self.__lower = self.__lowerPosition = lower
        self.__upper = self.__upperPosition = upper

    def __applyBounds(self, bounds: tuple[int, int]) -> None:
        """Retains new values, then emits what changed."""
        self._applyAndReport(lambda: self.__setBoth(*bounds))

    def __moveTo(self, handle: Handle, target: int) -> None:
        """Moves a handle (or, for `Both`, the lower end of the segment) and retains the values."""
        if handle == QAbstractRangeSlider.Handle.Both:
            lower, upper = self.__rules().moved_to(self.__lowerPosition, self.__upperPosition, target)
        else:
            lower, upper = self.__resolved(handle, target, target)
        self.__applyBounds((lower, upper))

    def __step(self, handle: Handle, offset: int) -> None:
        origin = self.__upperPosition if handle == QAbstractRangeSlider.Handle.Upper else self.__lowerPosition
        self.__moveTo(handle, origin + offset)

    def __press(self, handle: Handle) -> None:
        self.__pressedHandle = handle
        self.__currentHandle = handle
        self.update()
        self.sliderPressed.emit(handle)

    def __drag(self, handle: Handle, target: int) -> None:
        """Moves the held handle; the values follow only with tracking."""
        if handle == QAbstractRangeSlider.Handle.Both:
            lower, upper = self.__rules().moved_to(*self.__pressPositions, target)
        else:
            lower, upper = self.__resolved(handle, target, target)
        if (lower, upper) == (self.__lowerPosition, self.__upperPosition):
            return
        self.__lowerPosition, self.__upperPosition = lower, upper
        self.update()
        self.sliderMoved.emit(self._fromBase(lower), self._fromBase(upper))
        if self.__tracking:
            self._applyAndReport(lambda: self.__setBoth(lower, upper))

    def __setHoverHandle(self, handle: Handle) -> None:
        if handle != self.__hoverHandle:
            self.__hoverHandle = handle
            self.update()

    def __matches(self, button: Qt.MouseButton, hint: QStyle.StyleHint) -> bool:
        """Whether `button` is one of the buttons a style hint names."""
        return button != Qt.MouseButton.NoButton and (button.value & self.style().styleHint(hint)) == button.value

    def __upsideDown(self) -> bool:
        if self.__orientation == Qt.Orientation.Horizontal:
            return self.__invertedAppearance != self.isRightToLeft()
        return not self.__invertedAppearance

    def __pick(self, point: QPoint) -> int:
        return point.x() if self.__orientation == Qt.Orientation.Horizontal else point.y()

    def __alongRect(self, start: int, stop: int) -> QRect:
        """The slice of the widget between two pixel positions along the slider."""
        if self.__orientation == Qt.Orientation.Horizontal:
            return QRect(start, 0, stop - start, self.height())
        return QRect(0, start, self.width(), stop - start)

    def __handleRect(self, position: int) -> QRect:
        return self.style().subControlRect(QStyle.ComplexControl.CC_Slider, self._styleOption(position),
                                           QStyle.SubControl.SC_SliderHandle, self)

    def __handleLength(self) -> int:
        rect = self.__handleRect(self.__minimum)
        return rect.width() if self.__orientation == Qt.Orientation.Horizontal else rect.height()

    def __valueAt(self, pixel: int) -> int:
        """The position, in steps, of a handle whose leading edge is at `pixel`, as in QSlider."""
        option = self._styleOption(self.__minimum)
        groove = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, option,
                                             QStyle.SubControl.SC_SliderGroove, self)
        length = self.__handleLength()
        if self.__orientation == Qt.Orientation.Horizontal:
            first, last = groove.x(), groove.right() - length + 1
        else:
            first, last = groove.y(), groove.bottom() - length + 1
        return QStyle.sliderValueFromPosition(self.__minimum, self.__maximum, pixel - first, last - first,
                                              option.upsideDown)

    def __handleAt(self, point: QPoint) -> Handle:
        """What is under a point: a handle, the segment between the two (`Both`), or nothing."""
        Handle = QAbstractRangeSlider.Handle
        lowerRect, upperRect = self.__handleRect(self.__lowerPosition), self.__handleRect(self.__upperPosition)
        if not lowerRect.united(upperRect).contains(point):
            return Handle.NoHandle
        (first, _, firstStop), (second, secondStart, _) = self.__visibleSpans()
        along = self.__pick(point)
        if along < firstStop:
            return first
        if along >= secondStart:
            return second
        if self.__handlesOverlap():
            # The clearance between two overlapping handles: each side of its middle takes its handle.
            return first if 2 * along < firstStop + secondStart else second
        return Handle.Both

    def __spanStart(self, rect: QRect) -> int:
        return rect.x() if self.__orientation == Qt.Orientation.Horizontal else rect.y()

    def __handlesOverlap(self) -> bool:
        lowerStart = self.__spanStart(self.__handleRect(self.__lowerPosition))
        upperStart = self.__spanStart(self.__handleRect(self.__upperPosition))
        return abs(upperStart - lowerStart) < self.__handleLength()

    def __visibleSpans(self) -> tuple[tuple[Handle, int, int], tuple[Handle, int, int]]:
        """The part of each handle that is drawn and grabbed, as pixel spans along the slider.

        Apart, each handle shows whole. Overlapping, they share the overlap: a clearance sits in
        its middle, as wide as `_SplitGap` allows, and each handle keeps what is on its side. The
        first span is the one at the lower pixels.
        """
        Handle = QAbstractRangeSlider.Handle
        length = self.__handleLength()
        lowerStart = self.__spanStart(self.__handleRect(self.__lowerPosition))
        upperStart = self.__spanStart(self.__handleRect(self.__upperPosition))
        if self.__upsideDown():     # the lower bound is at the higher pixels
            first, firstStart, second, secondStart = Handle.Upper, upperStart, Handle.Lower, lowerStart
        else:
            first, firstStart, second, secondStart = Handle.Lower, lowerStart, Handle.Upper, upperStart
        overlap = firstStart + length - secondStart
        if overlap <= 0:
            return (first, firstStart, firstStart + length), (second, secondStart, secondStart + length)
        gap = min(self.__splitGap(length), overlap)
        gapStart = secondStart + (overlap - gap) // 2
        return (first, firstStart, gapStart), (second, gapStart + gap, secondStart + length)

    def __splitGap(self, length: int) -> int:
        """The clearance between two stacked handles, of the parity that leaves two equal parts."""
        gap = max(self._MinSplitGap, round(length * self._SplitGapRatio))
        return gap + (length - gap) % 2

    def __nearestHandle(self, value: int) -> Handle:
        Handle = QAbstractRangeSlider.Handle
        if value <= self.__lowerPosition:
            return Handle.Lower
        if value >= self.__upperPosition:
            return Handle.Upper
        return Handle.Lower if value - self.__lowerPosition <= self.__upperPosition - value else Handle.Upper

    def __strayed(self, point: QPoint) -> bool:
        """Whether the pointer left the slider by more than the style allows during a drag."""
        distance = self.style().pixelMetric(QStyle.PixelMetric.PM_MaximumDragDistance, self._styleOption(self.__minimum), self)
        return distance >= 0 and not self.rect().adjusted(-distance, -distance, distance, distance).contains(point)


# -----------------------------------------------------------------------------
#                              Concrete classes
# -----------------------------------------------------------------------------

class QRangeSlider(QAbstractRangeSlider[int]):
    """Curseur à deux poignées qui choisit un intervalle d'entiers.

    Voir `QAbstractRangeSlider` pour la documentation complète. Valeurs initiales : les
    limites [0, 99] de `QSlider`, l'intervalle choisi (0, 99), un pas simple de 1 et un pas de
    page de 10.

    Un nombre qui n'est pas un `int` lève `TypeError` ; un booléen aussi. Des limites qui ne
    tiennent pas dans un `int` C++ (32 bits) lèvent `ValueError`.

    Signaux:
        lowerValueChanged: Signal(int). Voir `QAbstractRangeSlider`.
        upperValueChanged: Signal(int). Voir `QAbstractRangeSlider`.
        rangeChanged: Signal(int, int). Voir `QAbstractRangeSlider`.
        limitsChanged: Signal(int, int). Voir `QAbstractRangeSlider`.
        sliderMoved: Signal(int, int). Voir `QAbstractRangeSlider`.

    Exemple:
        >>> slider = QRangeSlider()
        >>> slider.setLimits(0, 10)
        >>> slider.setRange(8, 3)
        >>> slider.range()
        (3, 8)
        >>> slider.setLowerValue(9)
        >>> slider.range()
        (8, 8)
        >>> slider.setCollisionMode(QRangeSlider.CollisionMode.Pushing)
        >>> slider.setLowerValue(9)
        >>> slider.range()
        (9, 9)
    """

    lowerValueChanged = Signal(int)
    upperValueChanged = Signal(int)
    rangeChanged = Signal(int, int)
    limitsChanged = Signal(int, int)
    sliderMoved = Signal(int, int)

    @override
    def _toBase(self, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"An integer value must be an int, got {type(value).__name__}.")
        return value

    @override
    def textFromValue(self, value: int) -> str:
        return QIntervalFormat.textFromNumber(value, self.locale(), None)

    @override
    def _fromBase(self, steps: int) -> int:
        return steps


class QRealRangeSlider(QAbstractRangeSlider[float]):
    """Curseur à deux poignées qui choisit un intervalle de nombres réels.

    Voir `QAbstractRangeSlider` pour la documentation complète. Valeurs initiales : 2
    décimales, les limites [0.0, 1.0], l'intervalle choisi (0.0, 1.0).

    Décimales
    ---------
    Le nombre de décimales (`decimals()`, 2 par défaut) fixe la taille d'un pas, comme pour
    `QRealSlider` et `QDoubleSpinBox` : avec 2 décimales, une poignée avance par pas de 0.01.
    Un nombre est arrondi comme le fait `QDoubleSpinBox` : sur la valeur binaire exacte du
    `float`, les égalités en s'éloignant de zéro. 0.125 donne 0.13, mais 2.675 (en réalité
    2.67499...) donne 2.67. Ce qui est relu est ce que le curseur retient.

    Changer les décimales ré-exprime les limites et les bornes dans la nouvelle taille de pas,
    en les arrondissant au besoin. `decimalsChanged` est émis, puis `limitsChanged` et les
    signaux des bornes pour ce qui a changé. Un pas demandé est mémorisé : 0.05 vaut un pas de
    0.1 avec 1 décimale, et redevient 0.05 avec 2 décimales.

    Quand l'égalité des bornes est interdite, un pas au moins les sépare : `resolution()`.

    NaN et l'infini lèvent `ValueError` ; une valeur qui n'est pas un nombre lève
    `TypeError`. Les décimales vont de 0 à 15.

    Propriétés:
        decimals (int): Le nombre de décimales. Accesseur `decimals()`, mutateur
            `setDecimals()`, signal `decimalsChanged`.

    Signaux:
        lowerValueChanged: Signal(float). Voir `QAbstractRangeSlider`.
        upperValueChanged: Signal(float). Voir `QAbstractRangeSlider`.
        rangeChanged: Signal(float, float). Voir `QAbstractRangeSlider`.
        limitsChanged: Signal(float, float). Voir `QAbstractRangeSlider`.
        sliderMoved: Signal(float, float). Voir `QAbstractRangeSlider`.
        decimalsChanged: Signal(int). Émis quand le nombre de décimales change, avant
            `limitsChanged` et les signaux des bornes.

    Slots:
        setDecimals(int): Fixe le nombre de décimales.

    Exemple:
        >>> slider = QRealRangeSlider()
        >>> slider.setLimits(-5.0, 5.0)
        >>> slider.setDecimals(1)
        >>> slider.setRange(1.25, -2.0)
        >>> slider.range()
        (-2.0, 1.3)
    """

    lowerValueChanged = Signal(float)
    upperValueChanged = Signal(float)
    rangeChanged = Signal(float, float)
    limitsChanged = Signal(float, float)
    sliderMoved = Signal(float, float)
    decimalsChanged = Signal(int)

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        """Construit le curseur, avec 2 décimales et les limites [0.0, 1.0].

        Args:
            orientation: Orientation du curseur.
            parent: Widget parent, ou None.
        """
        super().__init__(orientation, parent)
        self.__decimals: int = self._DefaultDecimals

    # ================================================================ decimals

    def decimals(self) -> int:
        """Le nombre de décimales, qui fixe la taille d'un pas (2 par défaut)."""
        return self.__decimals

    @Slot(int)
    def setDecimals(self, digits: int) -> None:
        """Fixe le nombre de décimales, en ré-exprimant les limites, les bornes et les pas.

        Émet `decimalsChanged`, puis `limitsChanged` et les signaux des bornes si l'arrondi
        les a changés.

        Lève:
            TypeError: Si `digits` n'est pas un entier.
            ValueError: Si `digits` n'est pas dans [0, 15], ou si les limites compteraient
                trop de pas.
        """
        if isinstance(digits, bool) or not isinstance(digits, int): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"decimals must be an int, got {type(digits).__name__}.")
        if not 0 <= digits <= self._MaxDecimals:
            raise ValueError(f"decimals must be between 0 and {self._MaxDecimals}.")
        if digits == self.__decimals:
            return
        old = self.__decimals

        def change() -> None:
            self.__decimals = digits

        def revert() -> None:
            self.__decimals = old

        self._rebase(change, revert, lambda: self.decimalsChanged.emit(digits))

    @override
    def textFromValue(self, value: float) -> str:
        return QIntervalFormat.textFromNumber(value, self.locale(), self.__decimals)

    def stepCount(self) -> int:
        """Le nombre de pas entre les limites."""
        return self._toBase(self.maximum()) - self._toBase(self.minimum())

    # ================================================================ protected

    _DefaultDecimals: Final[int] = 2
    _MaxDecimals: Final[int] = 15
    _DefaultStepCount: ClassVar[int] = 10 ** _DefaultDecimals   # initial limits: [0.0, 1.0]

    @override
    def _toBase(self, value: float) -> int:
        return rounded_to_steps(value, self.__decimals)

    @override
    def _fromBase(self, steps: int) -> float:
        return steps / 10 ** self.__decimals

    @override
    def _stepDecimals(self) -> int:
        return self.__decimals
