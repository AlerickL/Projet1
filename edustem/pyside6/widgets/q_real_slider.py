"""Curseurs qui travaillent avec des nombres réels : `QRealSlider`, `QRealScrollBar` et `QRealDial`.

Ce sont un `QSlider`, un `QScrollBar` et un `QDial` dont l'interface publique est la même que
celle de tout `QAbstractSlider` (`value`, `setValue`, `valueChanged`, `minimum`, `setRange`,
...), sauf que chacun de ces membres porte désormais un nombre réel plutôt qu'un entier. Le
nombre de décimales (`decimals`, 2 par défaut) fixe la résolution : avec 2 décimales, la
poignée se déplace par pas de 0.01.

    slider = QRealSlider(Qt.Orientation.Horizontal)
    slider.setRange(-5.0, 5.0)
    slider.setValue(1.25)
    v: float = slider.value()   # v = 1.25
    slider.valueChanged.connect(print)

L'implémentation entière propre à Qt reste présente en dessous, mais elle est privée : ce
mixin n'expose pas d'API entière à côté de l'API réelle, si bien qu'un `QRealSlider` ne peut
pas être utilisé par erreur comme un `QSlider` ordinaire. Voir `QRealSliderMixin` pour l'API
complète et la note technique sur la façon dont ce renommage est fait de manière sûre.
`QRealSlider` rend aussi réel l'intervalle des graduations (`tickInterval`), propre à `QSlider`,
et `QRealDial` l'écart entre deux crans (`notchSize`), propre à `QDial`.

Dépendance locale : l'arrondi des réels vient de `rounded_to_steps` (`core/real_steps`),
partagé avec les autres widgets réels pour qu'ils retiennent tous la même valeur.
"""

from __future__ import annotations

from typing import Final, cast, override

from PySide6.QtCore import Signal, SignalInstance, Slot
from PySide6.QtWidgets import QAbstractSlider, QDial, QScrollBar, QSlider

from ..core.real_steps import rounded_to_steps


# No explicit base (implicitly `object`): each Shiboken-wrapped Qt class fixes
# its own C-level instance layout, and CPython allows only one such base per
# MRO. Staying layout-free lets this mixin pair with QSlider, QScrollBar, or QDial.
#
# Since this is not an official Qt class, we cannot rely on Shiboken to handle the
# mixin's Signals. Therefore, each concrete subclass must redeclare them
# (this is checked when the subclass is created; see `__init_subclass__`).
class QRealSliderMixin:
    """Transforme un `QAbstractSlider` (`QSlider`, `QScrollBar`, `QDial`) en un curseur qui
    travaille avec des nombres réels, sous exactement les mêmes noms publics que ceux de Qt.

    `value`, `setValue`, `valueChanged`, `minimum`, `maximum`, `setRange`, `rangeChanged`,
    `sliderPosition`, `setSliderPosition`, `sliderMoved`, `singleStep`, `setSingleStep`,
    `pageStep` et `setPageStep` portent désormais tous un nombre réel plutôt qu'un entier. Un
    `QRealSlider` ressemble donc, de l'extérieur, exactement à un `QSlider` — simplement réel
    au lieu d'entier. Il ne reste aucune API entière parallèle accessible : l'implémentation
    entière propre à Qt continue de faire le travail en dessous, mais de façon privée.

    Décimales et résolution
    ------------------------
    Le nombre de décimales (`decimals()`, 2 par défaut) définit la résolution, comme pour
    `QDoubleSpinBox` : avec 2 décimales, la poignée se déplace par pas de 0.01. `resolution()`
    renvoie la taille d'un pas (10**-decimals) et `stepCount()` le nombre de pas entre les
    bornes.

    ```python
    slider = QRealSlider(Qt.Orientation.Horizontal)
    slider.setRange(-5.0, 5.0)
    slider.setDecimals(1)
    slider.setValue(1.25)                  # le curseur retient 1.3 (voir « Comportement »)
    slider.valueChanged.connect(print)
    ```

    Comparé à un `QAbstractSlider` ordinaire
    ------------------------------------------
    ==============================  ===============================================
    Nom (identique à Qt natif)      Signifie désormais
    ==============================  ===============================================
    value / setValue                la valeur réelle
    minimum / maximum               les bornes réelles
    setRange                        fixe les bornes réelles
    sliderPosition / set...         la position réelle de la poignée pendant le glissement
    singleStep / setSingleStep      le pas réel des flèches et de la molette
    pageStep / setPageStep          le pas réel des touches de page et d'un clic dans la piste
    valueChanged(float)             émis avec la valeur réelle
    sliderMoved(float)              émis avec la position réelle pendant le glissement
    rangeChanged(float, float)      émis avec les bornes réelles
    ==============================  ===============================================

    Les membres qui ne portent aucune valeur sont utilisés tels quels : `tracking`,
    `sliderDown`, `orientation`, `invertedAppearance`, `invertedControls`, `triggerAction`,
    `sliderPressed`, `sliderReleased` et `actionTriggered`. Nouveaux membres, absents de
    `QAbstractSlider` : `decimals`, `setDecimals`, `decimalsChanged(int)`, `resolution`,
    `stepCount`, et les conversions `baseFromValue` et `valueFromBase` (entre la valeur réelle
    et l'entier interne de Qt, pour l'appelant qui en aurait vraiment besoin).

    Un membre qui porte une valeur mais n'existe que sur une classe concrète revient à cette
    classe : `QRealSlider` rend réels `tickInterval`/`setTickInterval`, propres à `QSlider`, et
    `QRealDial` rend réel `notchSize`, propre à `QDial`.

    Comportement
    ------------
    - **Arrondi.** Une quantité réelle est arrondie aux décimales configurées exactement comme
      le fait `QDoubleSpinBox` : sur la valeur binaire réelle du `float`, et non sur son
      écriture décimale, avec les égalités arrondies en s'éloignant de zéro. Avec 2 décimales,
      0.125 (exact en binaire) donne 0.13, mais 2.675 (en réalité 2.67499999...) donne 2.67 et
      `setMinimum(0.105)` donne 0.1. Un curseur et un `QDoubleSpinBox` réglés aux mêmes
      décimales retiennent donc toujours la même valeur. Ce qui est relu est ce que le curseur
      affiche : `setValue(3.14159)` relit 3.14.
    - **Mêmes règles que `QAbstractSlider`.** La valeur est bornée à l'intervalle ; un maximum
      inférieur au minimum devient le minimum ; `setMinimum` et `setMaximum` déplacent l'autre
      borne au besoin. Un intervalle dégénéré (minimum égal au maximum) est légal.
    - **Les signaux ne sont émis que lorsque ce qu'ils rapportent change**, que la cause soit
      l'utilisateur, un mutateur, ou un changement d'intervalle ou de décimales (bornage,
      arrondi).
    - **Changer les décimales** ré-exprime les bornes et la valeur dans la nouvelle résolution,
      en les arrondissant au besoin, comme `QDoubleSpinBox.setDecimals` : 0.25 devient 0.3
      avec 1 décimale, mais 0.95 (en réalité 0.94999...) devient 0.9. `decimalsChanged` est
      émis, puis `rangeChanged` et `valueChanged` si les bornes ou la valeur ont changé.
    - **Pas.** `setSingleStep` (flèches, molette) et `setPageStep` (touches de page, clic dans
      la piste) valent au moins un pas. La valeur demandée est mémorisée : 0.05 vaut un pas de
      0.1 avec 1 décimale, et redevient 0.05 avec 2 décimales. Les accesseurs renvoient le pas
      effectivement appliqué.
    - **Limites.** Un curseur Qt travaille avec un `int` C++ : les bornes entières internes
      doivent tenir dans +-(2**31 - 1), de même que leur différence. Une opération qui
      dépasserait cette limite lève `ValueError` et laisse le widget inchangé. Ceci limite le
      nombre de décimales possibles pour un intervalle donné (passer de [0, 1] à 15 décimales,
      par exemple, requiert des étapes intermédiaires). Les décimales vont de 0 à 15.
    - **Valeurs invalides.** NaN et l'infini lèvent `ValueError` ; une valeur qui n'est pas un
      nombre lève `TypeError`.

    Note technique : renommer un nom que Qt utilise déjà
    -------------------------------------------------------
    `value`, `setValue`, `minimum`, `setRange`, `singleStep`, etc. ne sont pas des noms libres :
    `QAbstractSlider` les définit déjà tous, en version entière. Ce mixin n'ajoute pas
    simplement de nouveaux membres réels à côté d'eux (comme le faisait une version antérieure
    de ce fichier, sous des noms tels que `realValue`) ; il les remplace, de sorte que les
    mêmes noms que Qt utilise signifient toujours ici la quantité réelle. Ceci a été vérifié,
    pas supposé, avant d'être écrit ainsi :

    - **`value()` / `setValue()` ne sont pas `virtual` dans le C++ de Qt.** Le dessin de la
      poignée, le clavier, `triggerAction`, et le reste de la propre implémentation C++ de
      `QAbstractSlider` lisent et écrivent son état entier privé directement — jamais par
      l'accesseur public. Surcharger `value`/`setValue`/`minimum`/`setRange`/... en Python ne
      peut donc pas affecter la façon dont le widget se dessine ou réagit en interne ; cela
      continue de fonctionner sur la position entière réelle et correcte, exactement comme
      avant. Seuls les *appelants* — du code Python, y compris celui de ce mixin — passent par
      l'accesseur surchargé.
    - **Les alias privés ci-dessous (`__baseValue`, `__setBaseValue`, ...) capturent les
      méthodes Qt d'origine avant que quoi que ce soit ne soit surchargé.** `__baseValue =
      QAbstractSlider.value` lie le nom à la propre `value()` non modifiée de Qt ; définir
      ensuite une méthode *différente* nommée `value` n'affecte pas cet alias, puisqu'il s'agit
      d'un nom entièrement distinct (ceci a été vérifié : l'aliasing fonctionne identiquement
      pour une méthode Python ordinaire et pour une méthode Qt enveloppée par Shiboken). Le
      préfixe à double tiret bas mangle ces noms en `_QRealSliderMixin__baseValue`, etc., si
      bien qu'ils ne restent atteignables que depuis du code écrit dans cette classe.
    - **Les signaux forment un second canal, indépendant.** Un signal notifie chaque
      emplacement connecté dès que les internes C++ de Qt changent son état privé — ceci ne
      passe pas du tout par l'accesseur public (non virtuel), et n'est donc pas affecté par la
      surcharge. C'est ainsi que ce mixin observe un changement fait en interne par Qt (par
      exemple par `triggerAction` ou un glissement) : il se connecte à `__baseValueChanged` (le
      *véritable* `valueChanged(int)` d'origine), pas au signal nouvellement renommé. Redéclarer
      `valueChanged = Signal(float)` dans une sous-classe concrète, sous le même nom que Qt
      utilise déjà pour `valueChanged(int)`, a été vérifié comme fonctionnant proprement :
      aucune erreur, aucune ambiguïté, et un emplacement connecté de façon ordinaire
      (`spin.valueChanged.connect(slider.setValue)`) ou décoré par `@Slot(float)` reçoit
      correctement la valeur réelle.
    - **`__init_subclass__` ne peut pas utiliser `hasattr` pour vérifier qu'un signal a été
      redéclaré**, puisque `hasattr(cls, "valueChanged")` est toujours vrai — `QAbstractSlider`
      en fournit déjà un. Il compare plutôt l'identité : `getattr(cls, name, None) is getattr
      (QAbstractSlider, name, None)`. Si rien dans le MRO de `cls` n'a jamais redéclaré le
      signal, cet attribut se résout, par héritage ordinaire, au même objet exactement que celui
      de `QAbstractSlider` — détecté. Si une sous-classe (ou un de ses ancêtres) l'a redéclaré,
      les deux sont des objets différents — accepté, y compris pour une sous-classe ultérieure
      qui ne le redéclare pas à nouveau mais hérite correctement du véritable signal de
      l'ancêtre. Cette même vérification fonctionne aussi sans modification pour
      `decimalsChanged`, que `QAbstractSlider` ne possède pas du tout (`getattr` renvoie `None`
      des deux côtés quand rien n'a été déclaré, et `None is None`).

    Sous-classes
    ------------
    Doivent déclarer `valueChanged = Signal(float)`, `sliderMoved = Signal(float)`,
    `rangeChanged = Signal(float, float)` et `decimalsChanged = Signal(int)` ; sinon
    `TypeError` est levée à la création de la classe.
    """

    _DefaultDecimals: Final[int] = 2
    _MaxDecimals: Final[int] = 15
    _IntMax: Final[int] = 2**31 - 1     # QAbstractSlider works with C++ `int`
    _RequiredSignals: Final[tuple[str, ...]] = (
        "valueChanged", "sliderMoved", "rangeChanged", "decimalsChanged",
    )

    # Captured once here, valid for QSlider, QScrollBar and QDial alike (all three inherit
    # them, unmodified, from QAbstractSlider). Private (name-mangled): nothing outside this
    # class should reach Qt's own integer-valued implementation directly. See the "Technical
    # note" above for why aliasing these, then giving their names a new meaning below, is safe.
    __baseValue = QAbstractSlider.value
    __setBaseValue = QAbstractSlider.setValue
    __baseValueChanged = QAbstractSlider.valueChanged
    __baseMinimum = QAbstractSlider.minimum
    __baseMaximum = QAbstractSlider.maximum
    __setBaseRange = QAbstractSlider.setRange
    __baseRangeChanged = QAbstractSlider.rangeChanged
    __baseSliderPosition = QAbstractSlider.sliderPosition
    __setBaseSliderPosition = QAbstractSlider.setSliderPosition
    __baseSliderMoved = QAbstractSlider.sliderMoved
    __baseSingleStep = QAbstractSlider.singleStep
    __setBaseSingleStep = QAbstractSlider.setSingleStep
    __basePageStep = QAbstractSlider.pageStep
    __setBasePageStep = QAbstractSlider.setPageStep

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Rejette une classe concrète qui n'aurait pas redéclaré les quatre signaux requis.

        Lève:
            TypeError: Si `valueChanged`, `sliderMoved`, `rangeChanged` ou `decimalsChanged`
                se résout encore à celui de `QAbstractSlider` (`decimalsChanged` n'existe pas
                là, donc le simple fait de ne jamais l'avoir déclaré est détecté de la même
                façon). Voir la « Note technique » ci-dessus pour la raison pour laquelle c'est
                l'identité, pas `hasattr`, qui doit être vérifiée ici.
        """
        super().__init_subclass__(**kwargs)
        missing = [name for name in cls._RequiredSignals
                   if getattr(cls, name, None) is getattr(QAbstractSlider, name, None)]
        if missing:
            raise TypeError(
                f"{cls.__name__} must declare the signal(s) {', '.join(missing)}: "
                "Shiboken does not inspect the signals of a mixin, and these names already "
                "exist on QAbstractSlider, so they must be genuinely redeclared here."
            )

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Constructeur coopératif : transmet `*args`/`**kwargs` à la classe suivante du MRO
        (la sous-classe concrète de `QAbstractSlider`), puis amène le widget à ses valeurs
        réelles par défaut : intervalle [0.0, 1.0], valeur 0.0, `decimals()` à
        `_DefaultDecimals` (2)."""
        super().__init__(*args, **kwargs)    # cooperative init, mandatory
        self._decimals: int = self._DefaultDecimals
        self._scale: int = 10 ** self._decimals
        self._guard: bool = False            # True while a decimals change is re-expressing the base state
        self._requestedSingleStep: float | None = None   # what was asked; None: default (one step, ten steps)
        self._requestedPageStep: float | None = None

        self.__setBaseRange(0, self._scale)  # [0.0, 1.0]
        self.__setBaseValue(0)
        self._applyBaseSteps()
        self._baseSignal("__baseValueChanged").connect(self.__relayValue)
        self._baseSignal("__baseSliderMoved").connect(self.__relaySliderPosition)
        self._baseSignal("__baseRangeChanged").connect(self.__relayRange)

    def _emit(self, signalName: str, *args: object) -> None:
        cast(SignalInstance, getattr(self, signalName)).emit(*args)   # declared by the concrete subclass

    def _baseSignal(self, name: str) -> SignalInstance:
        """Atteint l'un des alias `__base*Changed`/`__baseSliderMoved` déclarés plus haut, pour `.connect()`.

        Un simple `self.__baseValueChanged` échoue la vérification statique de type ici : le
        stub de `Signal.__get__` exige une instance statiquement connue comme étant un
        `QObject`, ce que ce mixin sans base n'est pas (voir la « Note technique » de la
        docstring de classe) — même si, à l'exécution, c'en est toujours un, puisque le mixin
        n'est jamais combiné qu'avec une sous-classe de `QAbstractSlider`. `getattr` contourne
        la vérification statique ; le nom mangé (`_QRealSliderMixin` + le nom à double tiret
        bas) est exactement celui sous lequel Python lui-même le range, comme il résoudrait
        `self.__baseValueChanged` écrit directement.
        """
        return cast(SignalInstance, getattr(self, f"_QRealSliderMixin{name}"))

    # -- Conversions ---------------------------------------------------------

    @staticmethod
    def _toBase(v: float, decimals: int) -> int:
        """Arrondit `v` (sur sa valeur binaire exacte, égalités loin de zéro, comme `QDoubleSpinBox`) en un nombre entier d'unités de 10**-decimals."""
        return rounded_to_steps(v, decimals)

    def baseFromValue(self, v: float) -> int:
        """L'entier interne propre à Qt pour la valeur réelle `v` (arrondi, non borné)."""
        return self._toBase(v, self._decimals)

    def valueFromBase(self, i: int) -> float:
        """La valeur réelle correspondant à l'entier interne `i` propre à Qt."""
        return i / self._scale

    def _checkedBaseRange(self, minU: int, maxU: int, decimals: int) -> None:
        """Lève ValueError si la plage tout entière, en unités de 10**-decimals, dépasse ce qu'un curseur Qt supporte."""
        limit = self._IntMax
        if abs(minU) > limit or abs(maxU) > limit or maxU - minU > limit:
            raise ValueError(
                f"The range [{minU / 10 ** decimals}, {maxU / 10 ** decimals}] with {decimals} decimals "
                f"exceeds what a slider supports (integer bounds within +-{limit}, difference too)."
            )

    # -- Decimals, resolution ------------------------------------------------

    def decimals(self) -> int:
        """Le nombre de décimales de précision, qui définit la résolution (2 par défaut)."""
        return self._decimals

    @Slot(int)
    def setDecimals(self, digits: int) -> None:
        """Fixe le nombre de décimales, en ré-exprimant l'intervalle, la valeur et les pas dans la nouvelle unité.

        Les bornes et la valeur sont arrondies au besoin ; `rangeChanged` et `valueChanged` ne
        sont chacun émis que si ce qu'ils rapportent a changé. `decimalsChanged` est ensuite
        émis.

        Lève:
            TypeError: Si `digits` n'est pas un entier.
            ValueError: Si `digits` n'est pas dans [0, 15], ou si l'intervalle dépasserait les
                limites d'un curseur Qt.
        """
        if isinstance(digits, bool) or not isinstance(digits, int): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"decimals must be an int, got {type(digits).__name__}.")
        if not 0 <= digits <= self._MaxDecimals:
            raise ValueError(f"decimals must be between 0 and {self._MaxDecimals}.")
        if digits == self._decimals:
            return

        oldMin, oldMax, oldValue = self.minimum(), self.maximum(), self.value()
        minU = self._toBase(oldMin, digits)
        maxU = self._toBase(oldMax, digits)
        valueU = max(minU, min(maxU, self._toBase(oldValue, digits)))
        self._checkedBaseRange(minU, maxU, digits)

        self._guard = True       # the base signals report the old units: re-emitted below in the new ones
        try:
            self._decimals = digits
            self._scale = 10 ** digits
            self.__setBaseRange(minU, maxU)
            self.__setBaseValue(valueU)
            self._applyBaseSteps()
        finally:
            self._guard = False

        self._emit("decimalsChanged", digits)
        if (self.minimum(), self.maximum()) != (oldMin, oldMax):
            self._emit("rangeChanged", self.minimum(), self.maximum())
        if self.value() != oldValue:
            self._emit("valueChanged", self.value())

    def resolution(self) -> float:
        """La taille réelle d'un pas du curseur : 10**-decimals."""
        return 1 / self._scale

    def stepCount(self) -> int:
        """Le nombre de pas entre les bornes : (maximum - minimum) / resolution."""
        return self.__baseMaximum() - self.__baseMinimum()

    # -- Range -----------------------------------------------------------------

    def minimum(self) -> float:
        """La borne inférieure réelle de l'intervalle."""
        return self.valueFromBase(self.__baseMinimum())

    def setMinimum(self, lo: float) -> None:
        """Fixe le minimum, en déplaçant le maximum au besoin s'il devenait inférieur (comme `setMinimum` de Qt)."""
        self.setRange(lo, max(self.maximum(), lo))

    def maximum(self) -> float:
        """La borne supérieure réelle de l'intervalle."""
        return self.valueFromBase(self.__baseMaximum())

    def setMaximum(self, hi: float) -> None:
        """Fixe le maximum, en déplaçant le minimum au besoin s'il devenait supérieur (comme `setMaximum` de Qt)."""
        self.setRange(min(self.minimum(), hi), hi)

    @Slot(float, float)
    def setRange(self, lo: float, hi: float) -> None:
        """Fixe l'intervalle ; un maximum inférieur au minimum devient le minimum (comme `setRange` de Qt).

        La valeur est bornée au nouvel intervalle. Émet `rangeChanged` et `valueChanged` si ce
        qu'ils rapportent change.

        Lève:
            TypeError: Si une borne n'est pas un nombre.
            ValueError: Si une borne n'est pas finie, ou si l'intervalle dépasse les limites
                d'un curseur Qt.
        """
        minU = self._toBase(lo, self._decimals)
        maxU = max(minU, self._toBase(hi, self._decimals))
        self._checkedBaseRange(minU, maxU, self._decimals)
        self.__setBaseRange(minU, maxU)

    # -- Value, position -----------------------------------------------------

    def value(self) -> float:
        """La valeur réelle actuelle."""
        return self.valueFromBase(self.__baseValue())

    @Slot(float)
    def setValue(self, v: float) -> None:
        """Fixe la valeur, arrondie aux décimales et bornée à l'intervalle (comme `setValue` de Qt).

        Lève:
            TypeError: Si `v` n'est pas un nombre.
            ValueError: Si `v` n'est pas fini.
        """
        self.__setBaseValue(self._clampedBase(v))

    def sliderPosition(self) -> float:
        """La position réelle de la poignée (peut différer de `value()` tant qu'elle est glissée sans suivi)."""
        return self.valueFromBase(self.__baseSliderPosition())

    @Slot(float)
    def setSliderPosition(self, v: float) -> None:
        """Fixe la position de la poignée, arrondie aux décimales et bornée (comme `setSliderPosition` de Qt)."""
        self.__setBaseSliderPosition(self._clampedBase(v))

    def _clampedBase(self, v: float) -> int:
        return max(self.__baseMinimum(), min(self.__baseMaximum(), self._toBase(v, self._decimals)))

    # -- Steps -----------------------------------------------------------------

    def singleStep(self) -> float:
        """Le pas des flèches et de la molette (le pas effectif, au moins une résolution)."""
        return self.valueFromBase(self.__baseSingleStep())

    @Slot(float)
    def setSingleStep(self, s: float) -> None:
        """Fixe le pas simple. Il vaut au moins un pas, mais la valeur demandée est mémorisée pour
        un changement ultérieur de décimales.

        Lève:
            ValueError: Si `s` n'est pas un nombre fini strictement positif.
        """
        self._requestedSingleStep = self._checkedStep(s)
        self._applyBaseSteps()

    def pageStep(self) -> float:
        """Le pas des touches de page et d'un clic dans la piste (le pas effectif)."""
        return self.valueFromBase(self.__basePageStep())

    @Slot(float)
    def setPageStep(self, p: float) -> None:
        """Fixe le pas de page. Il vaut au moins un pas, mais la valeur demandée est mémorisée
        pour un changement ultérieur de décimales.

        Lève:
            ValueError: Si `p` n'est pas un nombre fini strictement positif.
        """
        self._requestedPageStep = self._checkedStep(p)
        self._applyBaseSteps()

    def _checkedStep(self, s: float) -> float:
        self._toBase(s, self._decimals)       # type and finiteness
        if s <= 0:
            raise ValueError("A step must be strictly positive.")
        return s

    def _applyBaseSteps(self) -> None:
        """Fixe les pas entiers propres à Qt à partir des pas réels demandés (au moins 1), dans
        l'unité courante.

        Point d'extension : appelé à la construction et à chaque changement de pas ou de
        décimales. Une sous-classe qui porte d'autres grandeurs du même genre le surcharge en
        appelant `super()` (ex. `QRealSlider` et son intervalle de graduations). `QRealDial`
        n'en a pas besoin : son `notchSize()` est recalculé par Qt à chaque lecture.
        """
        single = 1 if self._requestedSingleStep is None else max(1, self._toBase(self._requestedSingleStep, self._decimals))
        page = 10 if self._requestedPageStep is None else max(1, self._toBase(self._requestedPageStep, self._decimals))
        self.__setBaseSingleStep(min(single, self._IntMax))
        self.__setBasePageStep(min(page, self._IntMax))

    # -- Reacting to Qt's own signals, reported in real units -------------------

    @Slot(int)
    def __relayValue(self, i: int) -> None:
        if not self._guard:
            self._emit("valueChanged", self.valueFromBase(i))

    @Slot(int)
    def __relaySliderPosition(self, i: int) -> None:
        if not self._guard:
            self._emit("sliderMoved", self.valueFromBase(i))

    @Slot(int, int)
    def __relayRange(self, lo: int, hi: int) -> None:
        if not self._guard:
            self._emit("rangeChanged", self.valueFromBase(lo), self.valueFromBase(hi))


# -----------------------------------------------------------------------------
#                        Concrete Real Controls
# -----------------------------------------------------------------------------

class QRealSlider(QRealSliderMixin, QSlider):  # pyright: ignore[reportIncompatibleMethodOverride]
    """Un `QSlider` qui travaille avec des nombres réels.

    Voir `QRealSliderMixin` pour la documentation complète de l'API réelle. `QRealSlider` y
    ajoute l'intervalle des graduations, propre à `QSlider` : `tickInterval` et
    `setTickInterval` portent eux aussi un nombre réel, sous les mêmes noms que Qt.

    Graduations
    -----------
    - **0 signifie « automatique »**, comme dans Qt : le curseur choisit alors lui-même entre
      le pas simple et le pas de page. Une valeur négative devient 0, comme dans Qt.
    - **Une valeur positive vaut au moins un pas** et suit les mêmes règles que les pas
      (voir « Pas » dans `QRealSliderMixin`) : elle est arrondie aux décimales, la valeur
      demandée est mémorisée pour un changement ultérieur de décimales, et l'accesseur
      renvoie l'intervalle effectivement appliqué. Avec 1 décimale, 0.05 donne 0.1, puis
      redevient 0.05 avec 2 décimales.
    - Aucun signal n'est émis, puisque Qt n'en a pas pour cette propriété.

    ```python
    slider = QRealSlider(Qt.Orientation.Horizontal)
    slider.setRange(0.0, 2.0)
    slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    slider.setTickInterval(0.25)           # une graduation tous les 0.25
    ```

    Slots:
        setTickInterval(float): En plus des slots de `QRealSliderMixin`.
    """
    valueChanged = Signal(float)         # to redeclare: Shiboken does not inspect the mixin,
    sliderMoved = Signal(float)          # and these names already exist (as int) on QAbstractSlider
    rangeChanged = Signal(float, float)
    decimalsChanged = Signal(int)

    # -- Ticks -----------------------------------------------------------------

    @override
    def tickInterval(self) -> float:
        """L'intervalle réel entre deux graduations (l'intervalle effectif ; 0 : automatique)."""
        return self.valueFromBase(self.__baseTickInterval())

    @override
    @Slot(float)
    def setTickInterval(self, t: float) -> None:
        """Fixe l'intervalle des graduations. 0 (ou une valeur négative) le rend automatique ;
        une valeur positive vaut au moins un pas, et la valeur demandée est mémorisée pour un
        changement ultérieur de décimales.

        Lève:
            TypeError: Si `t` n'est pas un nombre.
            ValueError: Si `t` n'est pas fini.
        """
        self._toBase(t, self._decimals)       # type and finiteness
        self._requestedTickInterval = max(0.0, float(t))
        self._applyBaseSteps()

    # -- Private ---------------------------------------------------------------

    # Class-level default: `_applyBaseSteps` reads it during the mixin's `__init__`, before any
    # instance attribute of this class could be set.
    _requestedTickInterval: float = 0.0

    # Same aliasing as in the mixin (see its "Technical note"): tickInterval exists only on QSlider.
    __baseTickInterval = QSlider.tickInterval
    __setBaseTickInterval = QSlider.setTickInterval

    def _applyBaseSteps(self) -> None:
        super()._applyBaseSteps()
        t = self._requestedTickInterval
        base = 0 if t == 0 else max(1, self._toBase(t, self._decimals))
        self.__setBaseTickInterval(min(base, self._IntMax))


class QRealScrollBar(QRealSliderMixin, QScrollBar):  # pyright: ignore[reportIncompatibleMethodOverride]
    """Un `QScrollBar` qui travaille avec des nombres réels.

    Voir `QRealSliderMixin` pour la documentation complète de l'API réelle.
    """
    valueChanged = Signal(float)
    sliderMoved = Signal(float)
    rangeChanged = Signal(float, float)
    decimalsChanged = Signal(int)


class QRealDial(QRealSliderMixin, QDial):  # pyright: ignore[reportIncompatibleMethodOverride]
    """Un `QDial` qui travaille avec des nombres réels.

    Voir `QRealSliderMixin` pour la documentation complète de l'API réelle. `QRealDial` y
    ajoute l'écart entre deux crans, propre à `QDial` : `notchSize` porte lui aussi un nombre
    réel, sous le même nom que Qt.

    Crans
    -----
    - **`notchSize()` est en lecture seule**, comme dans Qt. Qt le déduit de `notchTarget()`
      (l'écart visé entre deux crans, en pixels), de la taille du cadran, de l'intervalle et
      des pas. Il vaut toujours un multiple non nul de `singleStep()`.
    - **`notchTarget`/`setNotchTarget` ne portent pas de valeur** : ils restent en pixels, tels
      quels. Agrandir le cadran ou changer les pas change donc `notchSize()`.

    ```python
    dial = QRealDial()
    dial.setNotchesVisible(True)
    dial.setNotchTarget(20.0)              # environ 20 pixels entre deux crans
    size: float = dial.notchSize()         # l'écart réel qui en résulte, ex. 0.08
    ```
    """
    valueChanged = Signal(float)
    sliderMoved = Signal(float)
    rangeChanged = Signal(float, float)
    decimalsChanged = Signal(int)

    # -- Notches ---------------------------------------------------------------

    @override
    def notchSize(self) -> float:
        """L'écart réel entre deux crans, un multiple non nul de `singleStep()` (lecture seule)."""
        return self.valueFromBase(self.__baseNotchSize())

    # -- Private ---------------------------------------------------------------

    # Same aliasing as in the mixin (see its "Technical note"): notchSize exists only on QDial.
    __baseNotchSize = QDial.notchSize


# For type checking only (no effect at runtime): "any of the three controls". The mixin has no Qt base,
# so this union is what lets a checker see both the real API and the Qt API (`setEnabled`, `connect`...).
type QRealControl = QRealSlider | QRealScrollBar | QRealDial
