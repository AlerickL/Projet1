"""Widget de navigation dans un domaine discret de positions, avec liaison
optionnelle à un élément externe.

Fournit :

* `QDomainExplorerBox` : le widget. Un axe à n repères, encadré de boutons d'action.
* `QDomainBinding` : relie le widget à un domaine externe (ex. une liste, un
  compteur), de façon polymorphique. Il porte aussi la valeur par défaut du
  domaine, exprimée dans le vocabulaire de l'élément lié.
* `QCallbackDomainBinding` : implémentation de `QDomainBinding` par fonctions
  de rappel, pour les cas où sous-classer `QDomainBinding` n'est pas nécessaire.
* Des implémentations prêtes à l'emploi de `QDomainBinding` pour des widgets Qt
  courants (curseurs, boutons cochables, listes déroulantes, vues-liste,
  compteurs entiers et décimaux, conteneurs à page courante, groupes de
  boutons). Chaque classe `Q*DomainBinding` nomme le widget qu'elle vise.

Ne dépend que de PySide6 et de la bibliothèque standard. Le module
`shiboken6`, livré avec PySide6 (c'est la couche qui relie les objets Python
aux objets C++ de Qt), sert à une seule chose : `shiboken6.isValid()`, pour
savoir si l'objet C++ d'une pilote existe encore. Une pilote peut être
détruite côté Qt (ex. par son parent) pendant qu'une suiveuse garde une
référence Python vers elle ; sans cette vérification, l'appeler lèverait
`RuntimeError`. Voir `QDomainExplorerBox.leader()`.
"""

from __future__ import annotations

import functools
import math
import random

import shiboken6
from typing import Any, ClassVar, Final, Protocol, cast, override
from collections.abc import Callable, Hashable, Sequence
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from enum import Enum, auto
from dataclasses import dataclass

from PySide6.QtCore import (Qt, Signal, Slot,
                            QObject,QEvent,
                            QTimer, QElapsedTimer,
                            QPointF, QRect, QRectF, QSize,
                            )
from PySide6.QtGui import ( QEnterEvent, QFocusEvent, QHelpEvent, QKeyEvent, QMouseEvent, QPaintEvent,
                            QColor, QFont, QFontDatabase, QPalette, QPen, QPainter, QPainterPath,
                          )
from PySide6.QtWidgets import ( QWidget,
                                QSizePolicy, QStyle, QStyleOption, QStyleOptionButton, QStyleOptionFrame,
                                QToolTip,
                                QAbstractButton, QAbstractSlider, QButtonGroup, QComboBox,
                                QDoubleSpinBox, QListView, QSpinBox,
                              )


class QDomainExplorerBox(QWidget):
    """Widget affichant un axe de navigation à n repères, encadré de boutons d'action.

    Le widget est composé de deux sections indépendantes, l'axe à repères et
    les boutons d'action. Chacune a son propre rôle, ses propres états et son
    propre jeu d'accesseurs et de mutateurs. De gauche à droite : les actions
    instantanées, l'axe, puis les animations ; s'y ajoute, à une extrémité,
    le bouton de repliement optionnel. Le focus clavier suit cet ordre, par
    groupes : Tab passe d'un groupe au suivant, les flèches se déplacent dans
    un groupe, et chaque groupe retient sa dernière tranche focalisée.

    Section repères (l'axe) :
        Rôle : matérialiser un domaine continu de positions normalisées, de
            0.0 (premier repère) à 1.0 (dernier), et permettre à l'utilisateur
            d'en activer une.
        États : chaque repère est indépendamment visible ou masqué, et
            activable ou désactivé. Un repère masqué conserve sa position sur
            l'axe mais n'est ni dessiné ni activable. Seul le repère survolé,
            pressé ou ayant le focus affiche son glyphe ; les autres ne sont
            représentés que par l'axe lui-même.
        Action : activer un repère (clic, Espace/Entrée au clavier une fois
            le focus dessus, ou `activateMarker()`) émet `markerActivated`
            avec son indice, puis `positionRequested` avec sa position
            normalisée.
        Accesseurs : `markerCount()`, `markerPosition()`, `isMarkerVisible()`,
            `isMarkerEnabled()`, `markerToolTip()`.
        Mutateurs (slots Qt) : `setMarkerCount()`, `setMarkerVisible()`,
            `setMarkerEnabled()`, `setMarkerToolTips()`, `resetMarkerToolTips()`.

    Section boutons (les actions) :
        Rôle : déclencher une action instantanée sur le domaine, ou démarrer
            une animation qui le parcourt automatiquement.
        États : chaque bouton est indépendamment visible ou masqué (un bouton
            masqué ne prend plus de largeur), et activable ou désactivé.
        Action : activer un bouton (clic, Espace/Entrée, ou
            `activateAction()`). `ResetToDefault` et `Randomize` sont
            instantanées et émettent le signal `triggered` ; `AnimWrap` et
            `AnimBounce` démarrent une animation (ou l'arrêtent, si
            l'animation correspondante est déjà en cours), qui émet
            `animationStepped` à chaque pas et `animationStateChanged` à
            chaque changement d'état.
        Animation : deux états seulement, au repos ou en marche. Le bouton
            de l'animation en cours affiche ⏸ ; l'activer, ou Échap, l'arrête
            sur place, le domaine restant à sa position courante. Relancer
            reprend depuis cette position : arrêter puis relancer tient lieu
            de pause. Activer toute autre tranche pendant une animation
            l'arrête d'abord, puis agit : aller à un repère, réinitialiser,
            tirer au hasard ou basculer vers l'autre mode.
        Sans binding : le widget suit une position interne, sur ses propres
            repères. Activer un repère l'y place, `ResetToDefault` la ramène
            au premier repère et `Randomize` la tire au hasard. Une animation
            part de cette position.
        Rythme : chaque pas avance le domaine d'une position, celui du
            `QDomainBinding` ou, sans binding, la position interne du widget.
            Deux réglages distincts en fixent la cadence, dans les deux cas.
            `stepInterval()` est le rythme de base, choisi par le programmeur :
            le temps entre deux pas à la vitesse ×1 (500 ms par défaut).
            `speedFactor()` est l'ajustement de l'usager en cours d'usage
            (touches +/−, par `speedFactorStep()`), relatif à ce rythme et
            borné par `speedFactorRange()`. Un pas a donc lieu toutes les
            stepInterval() / speedFactor() ms. Une pilote relaie le facteur à
            ses suiveuses, pas l'intervalle : chacune garde son rythme de base.
        Accesseurs : `isActionVisible()`, `isActionEnabled()`, `actionToolTip()`,
            `animationState()`, `animationMode()`.
        Mutateurs (slots Qt) : `setActionVisible()`, `setActionEnabled()`,
            `setActionToolTip()`, `resetActionToolTips()`, `activateAction()`,
            `startAnimation()`, `stopAnimation()`.

    Repliement (affiché par défaut, `setCollapsible(False)` le retire) :
        Un bouton étroit, à gauche ou à droite (`setCollapseButtonPosition()`),
        replie le widget sur lui seul ou le déplie. Il prend l'indicateur de
        dépliage du style (▸ replié, ▾ déplié) et forme son propre groupe de
        focus. Replier ne fait que cacher : une animation continue, et les
        repères et actions restent activables par programmation.
        Accesseurs : `isCollapsible()`, `isCollapsed()`, `collapseButtonPosition()`.
        Mutateurs (slots Qt) : `setCollapsible()`, `setCollapsed()`,
            `setCollapseButtonPosition()`.

    Pilote et suiveuses (contrôle global à sens unique) :
        `addFollower()` fait d'un widget la pilote d'autres widgets : chacun
        de ses gestes est rejoué chez ses suiveuses (voir `addFollower()`
        pour les règles). Accesseurs : `isLeader()`, `isFollower()`,
        `leader()`, `followers()`. Mutateurs
        (slots Qt) : `addFollower()`, `removeFollower()`.

    Interaction et programmation sont synchrones : `activateMarker()` et
    `activateAction()` empruntent exactement le chemin d'un clic (mêmes
    règles, mêmes signaux, même rendu), comme `QAbstractButton.click()`.
    `startAnimation()` et `stopAnimation()` fixent un état, comme
    `QAbstractButton.setChecked()`, avec le même rendu et les mêmes signaux.

    Dimensions :
        La hauteur est fixe : celle d'un bouton du style courant (politique
        verticale `Fixed`). La largeur fait intervenir les grandeurs standard
        de `QWidget` et trois réglages propres au widget. Toutes sont en
        pixels logiques.
        `minimumSizeHint()` : la largeur sous laquelle le contenu ne tient
            plus. Somme des boutons visibles (`buttonWidth()` chacun), des
            repères (`markerWidth()` chacun, n fois) et du bouton de
            repliement. Toujours calculée, jamais réglée directement.
        `sizeHint()` : la largeur que le widget suggère à sa mise en page.
            C'est `preferredWidth()` si elle est définie, sinon
            `minimumSizeHint()`.
        `preferredWidth()` : le seul réglage de largeur d'ensemble propre au
            widget. Il ne fait qu'alimenter `sizeHint()` : une suggestion,
            pas une contrainte.
        `buttonWidth()` et `markerWidth()` : largeur d'un bouton et largeur
            minimale d'un repère. Elles ne dimensionnent pas le widget
            directement ; elles déterminent `minimumSizeHint()`.
        `minimumWidth()`, `maximumWidth()`, `setFixedWidth()` : contraintes
            standard de `QWidget`, que la mise en page respecte toujours et
            que le widget ne modifie jamais. Pour imposer une largeur, c'est
            `setFixedWidth()` qui convient, pas `setPreferredWidth()`.
        La mise en page choisit la largeur réelle, `width()`, à partir de
        ces indications et de la politique horizontale (`Preferred` par
        défaut : ni plus étroit que `minimumSizeHint()`, ni étiré au-delà de
        `sizeHint()` sans place libre). Toute largeur au-delà du minimum va à
        l'axe : les boutons gardent `buttonWidth()`, les repères s'écartent.

    `setBinding()` relie le widget à un `QDomainBinding`, qui traduit ses
    signaux en déplacements dans un domaine externe (ex. une liste), sans code
    supplémentaire côté appelant.

    Chaque mutateur listé ci-dessus, ainsi que ceux des dimensions, de
    l'animation et de la liaison, est déclaré `@Slot(...)` : connectable
    directement à un signal Qt (ex. `QSlider.valueChanged` vers
    `setPreferredWidth()`), comme le sont les slots publics de Qt lui-même.

    Attributs statiques:
        DefaultMarkerCount: Nombre de repères par défaut (3).
        DefaultButtonWidth: Largeur par défaut d'un bouton d'action, en pixels
            (18), à la hauteur standard ; voir `buttonWidth()`.
        MinimumButtonWidth: Plancher de la largeur d'un bouton et d'un repère,
            en pixels (16), à la hauteur standard.
        RecommendedButtonWidthRange: Plage conseillée pour `setButtonWidth()`
            (16 à 24 px). 24 px est la largeur d'une flèche de `QSpinBox` du
            style windows11. Indicative : seul le plancher est imposé.
    
    Signaux:
        collapsedChanged: Signal(bool). Émis quand le widget se replie (True)
            ou se déplie (False).
        markerActivated: Signal(int). Émis quand un repère est activé, avec
            son indice.
        positionRequested: Signal(float). Émis quand un repère est activé, avec
            sa position normalisée, égale à i / (markerCount() − 1).
        triggered: Signal(Action). Émis avec l'`Action` instantanée
            (ResetToDefault ou Randomize) qui vient d'être activée.
        animationStepped: Signal(AnimationMode). Émis à chaque pas d'une
            animation en cours, avec l'`AnimationMode` actif.
        animationStateChanged: Signal(AnimationState). Émis à chaque
            changement d'`AnimationState`.
        speedFactorChanged: Signal(float). Émis quand le facteur de vitesse de
            l'animation change.

    Slots:
        activateMarker(int): Active un repère, comme un clic.
        activateAction(Action): Active un bouton d'action, comme un clic.
        setPreferredWidth(int): Définit `preferredWidth()`.
        setButtonWidth(int): Définit `buttonWidth()` souhaitée.
        setMarkerWidth(int): Définit `markerWidth()` souhaitée.
        startAnimation(AnimationMode) -> bool: Démarre une animation.
        stopAnimation(): Arrête l'animation en cours.
        setStepInterval(float): Définit `stepInterval()`.
        setSpeedFactor(float): Définit `speedFactor()`.
        setSpeedFactorStep(float): Définit `speedFactorStep()`.
        setSpeedFactorRange(float, float): Définit `speedFactorRange()`.
        setBinding(QDomainBinding): Attache ou détache un `QDomainBinding`.
        setCollapsible(bool): Définit `isCollapsible()`.
        setCollapsed(bool): Replie ou déplie le widget.
        setCollapseButtonPosition(CollapseButtonPosition): Définit le côté
            du bouton de repliement.
        addFollower(QDomainExplorerBox): Ajoute une suiveuse.
        removeFollower(QDomainExplorerBox): Retire une suiveuse.
    """

    # ------------------------------------------------------ internal enumerations

    class AnimationMode(Enum):
        """Mode de parcours automatique de l'axe.

        Chaque mode part de la position courante du domaine et avance d'une
        position à chaque pas.

        Attributs:
            Wrap: Vers la droite ; après la dernière position, reprend à la
                première.
            Bounce: Vers la droite puis vers la gauche, en changeant de sens à
                chaque extrémité. Le sens est conservé d'une animation à la
                suivante.
        """

        Wrap = auto()
        Bounce = auto()

        def action(self) -> QDomainExplorerBox.Action | None:
            """Renvoie le bouton qui déclenche ce mode.

            Retourne:
                L'`Action` associée, ou None si aucun bouton ne déclenche ce mode.
            """
            return next((a for a in QDomainExplorerBox.Action if a.animationMode() is self), None)

    class AnimationState(Enum):
        """État de l'animation en cours.

        Attributs:
            Idle: Aucune animation en cours.
            Running: Une animation est en cours.
        """

        Idle = auto()
        Running = auto()

    class Action(Enum):
        """Boutons d'action, dans l'ordre d'affichage.

        Les actions instantanées (sans `animationMode()`) s'affichent à gauche
        de l'axe, les animations à droite.

        Attributs:
            ResetToDefault: Restaure la position par défaut : celle du
                `QDomainBinding` (voir `QDomainBinding.resetToDefault()`) ou,
                sans binding, le premier repère.
            Randomize: Choisit une position au hasard.
            AnimWrap: Démarre ou arrête une animation en mode `AnimationMode.Wrap`.
            AnimBounce: Démarre ou arrête une animation en mode `AnimationMode.Bounce`.
        """

        ResetToDefault = auto()
        Randomize = auto()
        AnimWrap = auto()
        AnimBounce = auto()

        def animationMode(self) -> QDomainExplorerBox.AnimationMode | None:
            """Renvoie le mode d'animation déclenché par ce bouton.

            Retourne:
                L'`AnimationMode` correspondant, ou None si l'action est
                instantanée plutôt que de démarrer une animation.
            """
            match self:
                case QDomainExplorerBox.Action.AnimWrap:
                    return QDomainExplorerBox.AnimationMode.Wrap
                case QDomainExplorerBox.Action.AnimBounce:
                    return QDomainExplorerBox.AnimationMode.Bounce
                case _:
                    return None

    class CollapseButtonPosition(Enum):
        """Côté du bouton de repliement (voir `setCollapsible()`).

        Attributs:
            Left: À l'extrême gauche du widget (par défaut).
            Right: À l'extrême droite du widget.
        """

        Left = auto()
        Right = auto()

    # ------------------------------------------------------------------ signals

    collapsedChanged = Signal(bool)
    markerActivated = Signal(int)
    positionRequested = Signal(float)
    triggered = Signal(Action)
    animationStepped = Signal(AnimationMode)
    animationStateChanged = Signal(AnimationState)
    speedFactorChanged = Signal(float)

    # ------------------------------------------------------- static information

    DefaultMarkerCount: Final[int] = 3
    DefaultButtonWidth: Final[int] = 18
    MinimumButtonWidth: Final[int] = 16
    RecommendedButtonWidthRange: Final[tuple[int, int]] = (16, 24)

    # --------------------------------------------------------------------------

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise le widget avec ses valeurs par défaut.

        Args:
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self.__markerCount: int = self.DefaultMarkerCount
        self.__markerVisible: list[bool] = [True] * self.__markerCount
        self.__markerEnabled: list[bool] = [True] * self.__markerCount
        self.__markerToolTips: list[str] = []
        self.__actionVisible: dict[QDomainExplorerBox.Action, bool] = dict.fromkeys(QDomainExplorerBox.Action, True)
        self.__actionEnabled: dict[QDomainExplorerBox.Action, bool] = dict.fromkeys(QDomainExplorerBox.Action, True)
        self.__actionToolTips: dict[QDomainExplorerBox.Action, str] = self.__defaultToolTips()
        self.__preferredWidth: int | None = None
        self.__buttonWidth: int | None = None
        self.__markerWidth: int | None = None
        self.__binding: QDomainBinding[object, Any] | None = None
        self.__collapsible: bool = True
        self.__collapsed: bool = False
        self.__collapseButtonPosition: QDomainExplorerBox.CollapseButtonPosition = (
            QDomainExplorerBox.CollapseButtonPosition.Left)

        self.__hover: _QTarget | None = None
        self.__pressed: _QTarget | None = None
        self.__pressedByKey: bool = False
        self.__focus: _QTarget | None = None
        self.__lastInGroup: dict[int, _QTarget] = {}  # focus memory, per focus group (see _groupIndex)
        self.__animatedAction: QDomainExplorerBox.Action | None = None
        self.__cursorFrom: float = 0.0   # normalized positions the cursor glides between
        self.__cursorTo: float = 0.0
        self.__ownIndex: int = 0         # domain position followed without a binding (marker index)
        self.__ownDirection: int = 1

        self.__engine: QDomainExplorerBox._AnimationEngine = QDomainExplorerBox._AnimationEngine(self)
        self.__engine.stepped.connect(self.__advanceAnimation)
        self.__engine.frameRequested.connect(self.update)
        self.__engine.stateChanged.connect(self.__relayEngineState)
        self.__engine.speedFactorChanged.connect(self.speedFactorChanged)

        self.__leader: QDomainExplorerBox | None = None
        self.__followers: list[QDomainExplorerBox] = []
        self.__followerLinks: dict[QDomainExplorerBox, Callable[..., None]] = {}  # destroyed → forget
        self.__relayState: QDomainExplorerBox.AnimationState = QDomainExplorerBox.AnimationState.Idle
        self.markerActivated.connect(self.__relayMarker)
        self.triggered.connect(self.__relayAction)
        self.speedFactorChanged.connect(self.__relaySpeedFactor)
        self.collapsedChanged.connect(self.__relayCollapsed)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setMouseTracking(True)

    # ============================================================== API markers

    def markerCount(self) -> int:
        """Renvoie le nombre de repères affichés sur l'axe.

        Retourne:
            Le nombre de repères, toujours ≥ 2.
        """
        return self.__markerCount

    @Slot(int)
    def setMarkerCount(self, count: int) -> None:
        """Définit le nombre de repères de l'axe.

        Les repères sont répartis uniformément : le repère i se trouve à la
        position i / (count − 1). L'état (visible, activable) des repères
        existants est conservé.

        Args:
            count: Nombre de repères souhaité, doit être ≥ 2. Si un
                `QDomainBinding` est attaché et que `count` dépasse
                `binding.size()`, il est ramené à cette taille.

        Raises:
            ValueError: Si `count` est inférieur à 2.
        """
        if count < 2:
            raise ValueError("markerCount must be >= 2")
        if self.__binding is not None:
            count = max(2, min(count, self.__binding.size()))
        if count == self.__markerCount:
            return
        keep = min(count, self.__markerCount)
        self.__markerVisible = self.__markerVisible[:keep] + [True] * (count - keep)
        self.__markerEnabled = self.__markerEnabled[:keep] + [True] * (count - keep)
        self.__markerCount = count
        self.__hover = self.__pressed = None
        if isinstance(self.__focus, int) and not self._isEligible(self.__focus):
            self.__refocusAfterLoss(self.__focus)
        lastMarker = self.__lastInGroup.get(self._MarkerGroup)
        if isinstance(lastMarker, int) and lastMarker >= count:
            del self.__lastInGroup[self._MarkerGroup]
        self.__ownIndex = min(self.__ownIndex, count - 1)
        self.updateGeometry()
        self.update()

    def markerPosition(self, index: int) -> float:
        """Renvoie la position normalisée d'un repère.

        Args:
            index: Indice du repère, entre 0 et markerCount() − 1.

        Retourne:
            La position normalisée, égale à index / (markerCount() − 1).
        """
        return index / (self.__markerCount - 1)

    def isMarkerVisible(self, index: int) -> bool:
        """Indique si un repère est visible.

        Args:
            index: Indice du repère.

        Retourne:
            True si le repère est visible.
        """
        return self.__markerVisible[index]

    @Slot(int, bool)
    def setMarkerVisible(self, index: int, visible: bool) -> None:
        """Affiche ou masque un repère.

        Un repère masqué conserve sa position sur l'axe, mais n'est ni dessiné
        ni activable.

        Args:
            index: Indice du repère.
            visible: True pour l'afficher, False pour le masquer.
        """
        if self.__markerVisible[index] != visible:
            self.__markerVisible[index] = visible
            self.__forgetIneligible(index)
            self.update()

    def isMarkerEnabled(self, index: int) -> bool:
        """Indique si un repère est activable.

        Args:
            index: Indice du repère.

        Retourne:
            True si le repère est activable.
        """
        return self.__markerEnabled[index]

    @Slot(int, bool)
    def setMarkerEnabled(self, index: int, enabled: bool) -> None:
        """Active ou désactive un repère.

        Args:
            index: Indice du repère.
            enabled: True pour l'activer, False pour le désactiver.
        """
        if self.__markerEnabled[index] != enabled:
            self.__markerEnabled[index] = enabled
            self.__forgetIneligible(index)
            self.update()

    def markerToolTip(self, index: int) -> str:
        """Renvoie l'infobulle d'un repère.

        Args:
            index: Indice du repère.

        Retourne:
            L'infobulle définie par `setMarkerToolTips()` pour cet index, si sa
            liste couvre actuellement tous les repères ; sinon la position
            normalisée du repère, affichée en pourcentage.
        """
        if len(self.__markerToolTips) == self.__markerCount:
            return self.__markerToolTips[index]
        return self.tr("go to {}%").format(f"{self.markerPosition(index) * 100:g}")

    @Slot(object)
    def setMarkerToolTips(self, toolTips: Sequence[str]) -> None:
        """Définit les infobulles de tous les repères.

        Utile quand la position normalisée en pourcentage n'est pas un libellé
        adapté au domaine lié (ex. une position sur 2 représentant un booléen,
        où « 0 % » / « 100 % » est peu parlant face à « Faux » / « Vrai »).

        Args:
            toolTips: Une infobulle par repère, dans l'ordre des indices. Prise
                en compte seulement si sa taille correspond à `markerCount()` au
                moment de l'affichage ; sinon les repères affichent leur
                position en pourcentage, comme si aucune infobulle n'avait été
                définie. Une liste désormais mal dimensionnée (parce que
                `setMarkerCount()` a changé depuis) n'est donc pas une erreur :
                elle est simplement ignorée jusqu'à ce qu'elle corresponde de
                nouveau, ou soit remplacée.
        """
        self.__markerToolTips = list(toolTips)

    @Slot()
    def resetMarkerToolTips(self) -> None:
        """Efface les infobulles personnalisées des repères.

        Les repères reviennent à leur infobulle par défaut (position en
        pourcentage) ; voir `markerToolTip()`.
        """
        self.__markerToolTips = []

    @Slot(int)
    def activateMarker(self, index: int) -> None:
        """Active un repère, exactement comme un clic dessus.

        Sans effet si le repère, ou le widget, est masqué ou désactivé, ou si
        `index` est hors de [0, markerCount() − 1]. Une animation en cours est
        d'abord arrêtée. Émet `markerActivated` puis `positionRequested`.

        Args:
            index: Indice du repère.
        """
        if 0 <= index < self.__markerCount:
            self._activate(index)

    # ============================================================== API buttons

    def isActionVisible(self, action: QDomainExplorerBox.Action) -> bool:
        """Indique si un bouton d'action est visible.

        Args:
            action: Action concernée.

        Retourne:
            True si le bouton est visible.
        """
        return self.__actionVisible[action]

    @Slot(Action, bool)
    def setActionVisible(self, action: QDomainExplorerBox.Action, visible: bool) -> None:
        """Affiche ou masque un bouton d'action.

        Un bouton masqué ne prend plus de largeur : `minimumSizeHint()`
        diminue d'autant. Si la mise en page impose la largeur du widget,
        c'est l'axe qui s'allonge.

        Args:
            action: Action concernée.
            visible: True pour l'afficher, False pour le masquer.
        """
        if self.__actionVisible[action] != visible:
            self.__actionVisible[action] = visible
            self.__forgetIneligible(action)
            self.updateGeometry()
            self.update()

    def isActionEnabled(self, action: QDomainExplorerBox.Action) -> bool:
        """Indique si un bouton d'action est activable.

        Args:
            action: Action concernée.

        Retourne:
            True si le bouton est activable.
        """
        return self.__actionEnabled[action]

    @Slot(Action, bool)
    def setActionEnabled(self, action: QDomainExplorerBox.Action, enabled: bool) -> None:
        """Active ou désactive un bouton d'action.

        Args:
            action: Action concernée.
            enabled: True pour l'activer, False pour le désactiver.
        """
        if self.__actionEnabled[action] != enabled:
            self.__actionEnabled[action] = enabled
            self.__forgetIneligible(action)
            self.update()

    def actionToolTip(self, action: QDomainExplorerBox.Action) -> str:
        """Renvoie l'infobulle d'un bouton d'action.

        Args:
            action: Action concernée.

        Retourne:
            Le texte de l'infobulle.
        """
        return self.__actionToolTips[action]

    @Slot(Action, str)
    def setActionToolTip(self, action: QDomainExplorerBox.Action, text: str) -> None:
        """Définit l'infobulle d'un bouton d'action.

        Args:
            action: Action concernée.
            text: Nouveau texte de l'infobulle.
        """
        self.__actionToolTips[action] = text

    @Slot()
    def resetActionToolTips(self) -> None:
        """Restaure l'infobulle par défaut de chaque bouton d'action.

        Annule tout appel antérieur à `setActionToolTip()`.
        """
        self.__actionToolTips = self.__defaultToolTips()

    @Slot(Action)
    def activateAction(self, action: QDomainExplorerBox.Action) -> None:
        """Active un bouton d'action, exactement comme un clic dessus.

        Sans effet si le bouton, ou le widget, est masqué ou désactivé. Une
        action instantanée arrête d'abord l'animation en cours, puis émet
        `triggered`. Une action d'animation arrête l'animation si c'est la
        sienne qui est en cours ; sinon elle la démarre (en basculant de mode
        si l'autre animation était en cours). Pour une pilote, « en cours »
        s'entend de l'état agrégé de ses suiveuses : voir `addFollower()`.

        Args:
            action: Action à activer.
        """
        self._activate(action)

    # ============================================================ API dimensions

    def preferredWidth(self) -> int | None:
        """Renvoie la largeur que le widget suggère à sa mise en page.

        Une suggestion, pas une contrainte : c'est la largeur qu'annonce
        `sizeHint()`. Voir la section Dimensions de la classe pour la
        distinguer des autres largeurs.

        Retourne:
            La largeur en pixels, ou None (par défaut) : `sizeHint()` vaut
            alors `minimumSizeHint()`, la largeur la plus compacte.
        """
        return self.__preferredWidth

    @Slot(int)
    def setPreferredWidth(self, width: int | None) -> None:
        """Définit la largeur que le widget suggère à sa mise en page.

        Sert à donner à l'axe plus de longueur que le strict minimum sans
        figer la largeur du widget. La valeur n'alimente que `sizeHint()` :

        * plus petite que `minimumSizeHint()`, elle y est ramenée ;
        * la mise en page reste libre d'élargir ou de rétrécir le widget,
          selon sa politique horizontale (`Preferred` par défaut) et les
          contraintes `minimumWidth()` / `maximumWidth()` ;
        * replié, le widget l'ignore ; elle s'applique de nouveau au dépliage.

        La largeur ajoutée va à l'axe : les boutons gardent `buttonWidth()`.
        Pour imposer une largeur, utiliser plutôt `setFixedWidth()`, ou
        `setMinimumWidth()` / `setMaximumWidth()` pour des bornes.

        Args:
            width: Largeur en pixels, ou None pour revenir à la largeur
                minimale (`minimumSizeHint()`).
        """
        self.__preferredWidth = width
        self.updateGeometry()

    def buttonWidth(self) -> int:
        """Renvoie la largeur effective d'un bouton d'action.

        Retourne:
            La largeur en pixels : `DefaultButtonWidth` si aucune largeur n'a
            été demandée, sinon la largeur demandée. Ne descend jamais sous
            `MinimumButtonWidth`, le minimum pour que le glyphe reste
            dessinable et cliquable. Défaut et plancher grandissent avec la
            hauteur du widget au-delà de la hauteur standard (police agrandie),
            comme les glyphes ; ils ne rapetissent jamais en deçà.
        """
        m = _QMetrics.forHeight(self.__buttonHeight())
        requested = m.defaultButtonWidth() if self.__buttonWidth is None else self.__buttonWidth
        return max(math.ceil(m.minimumGlyphWidth()), requested)

    @Slot(int)
    def setButtonWidth(self, width: int | None) -> None:
        """Définit la largeur souhaitée d'un bouton d'action.

        Args:
            width: Largeur en pixels, ou None pour `DefaultButtonWidth`. Toute
                valeur sous `MinimumButtonWidth` y est ramenée ; aucune borne
                supérieure n'est imposée, mais `RecommendedButtonWidthRange`
                donne la plage qui s'accorde avec les autres contrôles du
                style. Voir `buttonWidth()`.
        """
        self.__buttonWidth = width
        self.updateGeometry()
        self.update()

    def markerWidth(self) -> int:
        """Renvoie la largeur minimale effective d'un repère de l'axe.

        Contrairement à `buttonWidth()`, qui fixe la largeur d'un bouton, l'axe
        est continu et ses repères s'étirent pour occuper l'espace disponible :
        cette valeur ne fixe donc que le minimum en deçà duquel un repère ne
        peut pas descendre. Elle détermine `minimumSizeHint()`.

        Retourne:
            La largeur minimale en pixels. Égale à `buttonWidth()` par défaut.
        """
        requested = self.buttonWidth() if self.__markerWidth is None else self.__markerWidth
        minimum = math.ceil(_QMetrics.forHeight(self.__buttonHeight()).minimumGlyphWidth())
        return max(minimum, math.ceil(requested))

    @Slot(int)
    def setMarkerWidth(self, width: int | None) -> None:
        """Définit la largeur minimale souhaitée d'un repère de l'axe.

        Args:
            width: Largeur minimale en pixels, ou None pour l'aligner
                automatiquement sur `buttonWidth()`. Toute valeur trop petite
                est ramenée au minimum nécessaire ; voir `markerWidth()`.
        """
        self.__markerWidth = width
        self.updateGeometry()
        self.update()

    # ============================================================ API animation

    def animationState(self) -> QDomainExplorerBox.AnimationState:
        """Renvoie l'état de l'animation en cours.

        Retourne:
            L'`AnimationState` courant. Pour une pilote (voir `addFollower()`),
            l'état agrégé : Running si au moins une suiveuse anime.
        """
        if self.__followers:
            running = any(f.animationState() is QDomainExplorerBox.AnimationState.Running for f in self.__followers)
        else:
            running = self.__engine.isActive()
        return QDomainExplorerBox.AnimationState.Running if running else QDomainExplorerBox.AnimationState.Idle

    def animationMode(self) -> QDomainExplorerBox.AnimationMode | None:
        """Renvoie le mode de l'animation en cours.

        Retourne:
            L'`AnimationMode` courant, ou None si aucune animation n'est en
            cours. Pour une pilote, le mode commun aux suiveuses qui animent,
            ou None si elles animent dans des modes différents.
        """
        if self.__followers:
            modes = {f.animationMode() for f in self.__followers} - {None}
            return modes.pop() if len(modes) == 1 else None
        return self.__animatedAction.animationMode() if self.__animatedAction is not None else None

    @Slot(AnimationMode, result=bool)
    def startAnimation(self, mode: QDomainExplorerBox.AnimationMode) -> bool:
        """Démarre une animation depuis la position courante du domaine.

        Le premier pas est immédiat. Pendant l'animation, un curseur glisse
        sur l'axe de la position précédente du domaine à la nouvelle, en un
        intervalle de pas ; il reflète donc la position réelle, lue sur le
        `QDomainBinding` attaché. Sans binding, le widget suit une position
        interne sur ses propres repères : celle fixée par le dernier repère
        activé ou par la dernière action instantanée, avancée d'un repère à
        chaque pas.

        Fixe un état, comme `QAbstractButton.setChecked()` : si ce mode est
        déjà en cours, rien ne change ; si l'autre mode est en cours, il est
        arrêté (`animationStateChanged` émet Idle) avant que celui-ci ne
        démarre (Running).

        Une pilote (voir `addFollower()`) n'anime jamais elle-même : elle
        démarre ce mode chez chacune de ses suiveuses.

        Args:
            mode: Mode d'animation à démarrer.

        Retourne:
            True si l'animation est en cours au retour (chez au moins une
            suiveuse, pour une pilote), False si le bouton correspondant est
            masqué, désactivé ou si le widget lui-même est désactivé.
        """
        action = mode.action()
        if action is None or not (self.isEnabled() and self._isEligible(action)):
            return False
        if self.__followers:
            return any([f.startAnimation(mode) for f in self.followers()])  # list: start them all
        if self.__engine.isActive():
            if action is self.__animatedAction:
                return True
            self.stopAnimation()
        self.__animatedAction = action
        self.__cursorFrom = self.__cursorTo = self.__domainPosition()
        self.__engine.start()
        return True

    @Slot()
    def stopAnimation(self) -> None:
        """Arrête l'animation en cours, sans effet si aucune n'est en cours.

        Pour une pilote (voir `addFollower()`), arrête l'animation de chacune
        de ses suiveuses.
        """
        self.__engine.stop()
        for follower in self.followers():
            follower.stopAnimation()

    # =========================================================== API followers

    def leader(self) -> QDomainExplorerBox | None:
        """Renvoie la pilote que suit ce widget.

        Retourne:
            La pilote, ou None si ce widget ne suit aucune pilote (ou si elle
            a été détruite).
        """
        if self.__leader is not None and not shiboken6.isValid(self.__leader):
            self.__leader = None
        return self.__leader

    def isLeader(self) -> bool:
        """Indique si ce widget pilote au moins une suiveuse.

        Retourne:
            True si `followers()` n'est pas vide.
        """
        return bool(self.__followers)

    def isFollower(self) -> bool:
        """Indique si ce widget suit une pilote.

        Retourne:
            True si `leader()` n'est pas None.
        """
        return self.leader() is not None

    def followers(self) -> list[QDomainExplorerBox]:
        """Renvoie les suiveuses de ce widget.

        Retourne:
            Une copie de la liste des suiveuses, dans l'ordre d'ajout.
        """
        return list(self.__followers)

    @Slot('QDomainExplorerBox')
    def addFollower(self, follower: QDomainExplorerBox) -> None:
        """Fait suivre ce widget, la pilote, par un autre, la suiveuse.

        Contrôle global à sens unique : chaque geste sur la pilote (clic,
        clavier ou programmation) est rejoué chez chaque suiveuse, qui reste
        libre de ses propres gestes et n'agit jamais sur la pilote.

        * Repère : chaque suiveuse active son repère le plus proche en
          position relative (le centre de la pilote vise le centre de la
          suiveuse). Rien si ce repère y est masqué ou désactivé.
        * Action instantanée : rejouée chez chaque suiveuse, chacune tirant
          sa propre position aléatoire. Rien si l'action y est masquée ou
          désactivée.
        * Animation : la pilote n'anime jamais elle-même, elle démarre ou
          arrête l'animation de chaque suiveuse. Son bouton reflète l'état
          agrégé, comme une case « tout sélectionner » : ⏸ tant qu'au moins
          une suiveuse anime dans ce mode (l'activer les arrête), son glyphe
          sinon (l'activer les démarre toutes). `animationState()` et
          `animationMode()` sont agrégés de même.
        * Vitesse et repliement : relayés. Une suiveuse repliée par la
          pilote reste dépliable à la main.

        Les suiveuses réémettent leurs propres signaux : leurs autres
        écouteurs les reçoivent aussi. Une pilote est un pur relais : pensée
        sans `QDomainBinding`, son domaine éventuel suit les repères et
        actions instantanées, jamais les animations. Désactiver une pilote
        suspend ses commandes sans toucher ses suiveuses.

        Pas de chaîne : un widget est pilote ou suiveuse, pas les deux, et
        n'a qu'une pilote. La dernière connexion prévaut : ce widget quitte
        sa propre pilote, `follower` quitte la sienne et libère ses propres
        suiveuses. Une suiveuse détruite est retirée d'elle-même.

        Args:
            follower: Widget qui suivra celui-ci. Sans effet s'il le suit déjà.

        Raises:
            ValueError: Si `follower` est ce widget lui-même.
        """
        if follower is self:
            raise ValueError("a QDomainExplorerBox cannot follow itself")
        if follower in self.__followers:
            return
        if (leader := self.leader()) is not None:
            leader.removeFollower(self)
        for own in follower.followers():
            follower.removeFollower(own)
        if (previous := follower.leader()) is not None:
            previous.removeFollower(follower)
        if not self.__followers:
            self.__engine.stop()  # from now on, a pure relay
        self.__followers.append(follower)
        follower.__leader = self
        forget = functools.partial(self.__forgetFollower, follower)
        self.__followerLinks[follower] = forget
        follower.destroyed.connect(forget)
        follower.animationStateChanged.connect(self.__relayAnimationState)
        self.__relayAnimationState()

    @Slot('QDomainExplorerBox')
    def removeFollower(self, follower: QDomainExplorerBox) -> None:
        """Retire une suiveuse ; elle garde son état (une animation continue).

        Args:
            follower: Suiveuse à retirer. Sans effet si elle ne suit pas ce widget.
        """
        if follower not in self.__followers:
            return
        follower.destroyed.disconnect(self.__followerLinks.pop(follower))
        follower.animationStateChanged.disconnect(self.__relayAnimationState)
        follower.__leader = None
        self.__followers.remove(follower)
        self.__relayAnimationState()

    def stepInterval(self) -> float:
        """Renvoie le rythme de base de l'animation : l'intervalle entre deux
        pas à la vitesse ×1.

        L'intervalle réel est stepInterval() / speedFactor().

        Retourne:
            L'intervalle en millisecondes (500 par défaut).
        """
        return self.__engine.stepInterval()

    @Slot(float)
    def setStepInterval(self, ms: float) -> None:
        """Définit le rythme de base de l'animation, réglage du programmeur.

        Prend effet dès le pas suivant, même pendant une animation. Non relayé
        par une pilote : chaque suiveuse garde le sien.

        Args:
            ms: Intervalle entre deux pas à la vitesse ×1, en millisecondes,
                ramené à 10 ms minimum.
        """
        self.__engine.setStepInterval(ms)

    def speedFactor(self) -> float:
        """Renvoie le facteur de vitesse de l'animation, réglage de l'usager.

        Un pas a lieu toutes les stepInterval() / speedFactor() ms : à ×2,
        l'animation va deux fois plus vite que son rythme de base.

        Retourne:
            Le facteur de vitesse courant (1.0 par défaut).
        """
        return self.__engine.speedFactor()

    @Slot(float)
    def setSpeedFactor(self, factor: float) -> None:
        """Définit le facteur de vitesse de l'animation.

        Les touches +/− le multiplient ou le divisent par `speedFactorStep()`.
        Émet `speedFactorChanged` si la valeur change ; une pilote le relaie
        alors à ses suiveuses.

        Args:
            factor: Nouveau facteur de vitesse, ramené à `speedFactorRange()`.
        """
        self.__engine.setSpeedFactor(factor)

    def speedFactorStep(self) -> float:
        """Renvoie le facteur multiplicatif utilisé par les raccourcis clavier
        +/− pour ajuster la vitesse.

        Retourne:
            Le facteur, toujours > 1.0 (1.25 par défaut).
        """
        return self.__engine.speedFactorStep()

    @Slot(float)
    def setSpeedFactorStep(self, step: float) -> None:
        """Définit le facteur multiplicatif utilisé par les raccourcis clavier
        +/− pour ajuster la vitesse.

        Args:
            step: Nouveau facteur, doit être > 1.0.

        Raises:
            ValueError: Si `step` est inférieur ou égal à 1.0.
        """
        self.__engine.setSpeedFactorStep(step)

    def speedFactorRange(self) -> tuple[float, float]:
        """Renvoie les bornes autorisées pour `speedFactor()`.

        Retourne:
            Un couple (minimum, maximum), (0.1, 10.0) par défaut.
        """
        return self.__engine.speedFactorRange()

    @Slot(float, float)
    def setSpeedFactorRange(self, minimum: float, maximum: float) -> None:
        """Définit les bornes autorisées pour `speedFactor()`.

        Args:
            minimum: Borne inférieure, doit être strictement positive.
            maximum: Borne supérieure, doit être supérieure ou égale à `minimum`.

        Raises:
            ValueError: Si les bornes ne respectent pas 0 < minimum ≤ maximum.
        """
        self.__engine.setSpeedFactorRange(minimum, maximum)

    # ============================================================= API binding

    def binding(self) -> QDomainBinding[object, Any] | None:
        """Renvoie le binding actuellement attaché.

        Retourne:
            Le `QDomainBinding` attaché, ou None si aucun ne l'est.
        """
        return self.__binding

    @Slot('QDomainBinding')
    def setBinding(self, binding: QDomainBinding[object, Any] | None) -> None:
        """Attache ou détache un `QDomainBinding`.

        Le binding déjà attaché, s'il y en a un, est détaché puis détruit avant
        que le nouveau ne soit installé : un seul binding est actif à la fois.
        Le nouveau binding devient un enfant Qt de ce widget, `markerCount()`
        est initialisée à `binding.markerCountHint()`, et les infobulles des
        repères à `binding.markerToolTips()` si elle en fournit (sinon
        `resetMarkerToolTips()`). Ces infobulles ne sont fixées qu'une fois, à
        l'attachement : un `setMarkerCount()` ultérieur les invalide (retour au
        pourcentage par défaut) sans les régénérer.

        Args:
            binding: Nouveau binding à attacher, ou None pour détacher le
                binding courant sans le remplacer.
        """
        if binding is self.__binding:
            return
        if self.__binding is not None:
            self.__binding._detach(self)  # pyright: ignore[reportPrivateUsage]
            self.__binding.deleteLater()
        self.__binding = binding
        toolTips: Sequence[str] | None = None
        if binding is not None:
            binding.setParent(self)
            binding._attach(self)  # pyright: ignore[reportPrivateUsage]
            self.setMarkerCount(binding.markerCountHint())
            toolTips = binding.markerToolTips(self.markerCount())
        if toolTips is not None:
            self.setMarkerToolTips(toolTips)
        else:
            self.resetMarkerToolTips()

    # ============================================================ API collapse

    def isCollapsible(self) -> bool:
        """Indique si le widget offre un bouton de repliement.

        Retourne:
            True si le bouton de repliement est affiché. True par défaut.
        """
        return self.__collapsible

    @Slot(bool)
    def setCollapsible(self, collapsible: bool) -> None:
        """Affiche ou retire le bouton de repliement.

        Rendre le widget non repliable le déplie d'abord, s'il était replié.

        Args:
            collapsible: True pour afficher le bouton de repliement.
        """
        if collapsible == self.__collapsible:
            return
        if not collapsible:
            self.setCollapsed(False)
        self.__collapsible = collapsible
        self.__forgetIneligible(_Part.CollapseToggle)
        self.updateGeometry()
        self.update()

    def isCollapsed(self) -> bool:
        """Indique si le widget est replié.

        Retourne:
            True si seul le bouton de repliement est affiché.
        """
        return self.__collapsed

    @Slot(bool)
    def setCollapsed(self, collapsed: bool) -> None:
        """Replie ou déplie le widget, comme un clic sur son bouton de repliement.

        Replié, le widget n'affiche que ce bouton et ne prend que sa largeur.
        Il ne fait que se cacher : une animation en cours continue (le bouton
        porte alors un point de couleur d'accent), et les repères et actions
        restent activables par programmation, donc par une pilote. Sans effet
        sur un widget non repliable, comme `QAbstractButton.setChecked()` sur
        un bouton non cochable. Émet `collapsedChanged` si l'état change.

        Args:
            collapsed: True pour replier, False pour déplier.
        """
        collapsed = collapsed and self.__collapsible
        if collapsed == self.__collapsed:
            return
        self.__collapsed = collapsed
        self.__hover = self.__pressed = None
        self.__pressedByKey = False
        if collapsed and self.__focus is not None:
            self.__setFocus(_Part.CollapseToggle)
        self.updateGeometry()
        self.update()
        self.collapsedChanged.emit(collapsed)

    def collapseButtonPosition(self) -> QDomainExplorerBox.CollapseButtonPosition:
        """Renvoie le côté du bouton de repliement.

        Retourne:
            La `CollapseButtonPosition` courante, `Left` par défaut.
        """
        return self.__collapseButtonPosition

    @Slot(CollapseButtonPosition)
    def setCollapseButtonPosition(self, position: QDomainExplorerBox.CollapseButtonPosition) -> None:
        """Place le bouton de repliement à gauche ou à droite du widget.

        Le bouton s'affiche selon l'indicateur de dépliage du style courant
        (▸ replié, ▾ déplié), et forme son propre groupe de focus.

        Args:
            position: Côté du bouton.
        """
        if position is not self.__collapseButtonPosition:
            self.__collapseButtonPosition = position
            self.__hover = None
            self.update()

    # ==================================================================== size

    @override
    def sizeHint(self) -> QSize:
        """Renvoie la taille que le widget suggère à sa mise en page.

        Retourne:
            En largeur, `preferredWidth()` si elle a été définie (jamais sous
            `minimumSizeHint()`), sinon `minimumSizeHint()` ; replié, toujours
            `minimumSizeHint()`. En hauteur, celle d'un bouton du style.
        """
        minimum = self.minimumSizeHint()
        if self.__preferredWidth is None or self.__collapsed:
            return minimum
        return QSize(max(self.__preferredWidth, minimum.width()), minimum.height())

    @override
    def minimumSizeHint(self) -> QSize:
        """Renvoie la taille sous laquelle le contenu du widget ne tient plus.

        Une mise en page ne rétrécit pas le widget en deçà, sauf contrainte
        explicite (`setMaximumWidth()`, `setFixedWidth()`).

        Retourne:
            La plus petite taille permettant d'afficher tous les repères et
            boutons visibles avec leurs largeurs respectives (`markerWidth()`,
            `buttonWidth()`), plus le bouton de repliement s'il y en a un.
            Replié, la largeur de ce seul bouton.
        """
        height = self.__buttonHeight()
        m = _QMetrics.forHeight(height)
        toggle = m.toggleWidth() if self.__collapsible else 0.0
        if self.__collapsed:
            return QSize(math.ceil(m.minimumWidth(0, 0, 0.0, 0.0) + toggle), height)
        width = toggle + m.minimumWidth(self.__markerCount, len(self._visibleActions()),
                                        self.buttonWidth(), self.markerWidth())
        return QSize(math.ceil(width), height)

    # ==================================================================== events

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        """Dessine le panneau, l'axe, les repères, les boutons et le focus.

        Le panneau est celui d'un champ de saisie du style courant, comme celui
        d'un `QSpinBox` voisin. Les couleurs viennent de la palette : `Text`
        pour l'encre, `Accent` pour l'animation et le focus. Avec le style
        windows11, les glyphes viennent de sa police d'icônes ; avec tout autre
        style, ils sont tracés.

        Args:
            event: Événement de peinture fourni par Qt.
        """
        g = self._geometry()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paintPanel(p, g)
        active = self._activeTarget()
        self._paintHighlight(p, g, active)
        self._paintAxis(p, g)
        self._paintMarkerGlyph(p, g, active)
        self._paintActionGlyphs(p, g)
        self._paintCollapseToggle(p, g)
        self._paintAnimationMarker(p, g)
        self._paintFocus(p, g)

    @override
    def event(self, event: QEvent) -> bool:
        """Traite les événements Qt, dont l'affichage des infobulles.

        Args:
            event: Événement à traiter.

        Retourne:
            True si l'événement a été traité, sinon le résultat de
            l'implémentation de la classe de base.
        """
        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            target = self._targetAt(event.pos().x())
            if target is not None and self._isShown(target):
                QToolTip.showText(event.globalPos(), self._toolTipText(target), self)
            else:
                QToolTip.hideText()
            return True
        return super().event(event)

    @override
    def changeEvent(self, event: QEvent) -> None:
        """Réagit à un changement d'état du widget.

        Arrête l'animation en cours si le widget est désactivé (la sienne
        seulement : une pilote désactivée ne touche pas ses suiveuses), et
        recalcule la géométrie si la police ou le style changent.

        Args:
            event: Événement de changement fourni par Qt.
        """
        match event.type():
            case QEvent.Type.EnabledChange if not self.isEnabled():
                self.__engine.stop()
                self.__pressed = None
            case QEvent.Type.FontChange | QEvent.Type.StyleChange:
                self.updateGeometry()
            case _:
                pass
        self.update()
        super().changeEvent(event)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        """Met à jour la tranche survolée à l'entrée du curseur.

        Args:
            event: Événement fourni par Qt.
        """
        self.__setHover(event.position().x())
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        """Efface la tranche survolée à la sortie du curseur.

        Args:
            event: Événement fourni par Qt.
        """
        self.__hover = None
        self.update()
        super().leaveEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Met à jour la tranche survolée au déplacement du curseur.

        Args:
            event: Événement fourni par Qt.
        """
        self.__setHover(event.position().x())
        super().mouseMoveEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Amorce l'activation d'une tranche : elle devient pressée si elle est activable.

        Args:
            event: Événement fourni par Qt.
        """
        if event.button() is not Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        event.accept()
        target = self._targetAt(event.position().x())
        if target is not None and self._isEligible(target):
            self.__pressed = target
            self.__pressedByKey = False
            self.__setFocus(target)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Termine l'activation d'une tranche pressée.

        L'action associée n'est déclenchée que si le relâchement se produit
        sur la même tranche que l'appui.

        Args:
            event: Événement fourni par Qt.
        """
        if event.button() is not Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)
            return
        event.accept()
        pressed, self.__pressed = self.__pressed, None
        self.update()
        if pressed is None or not self.rect().contains(event.position().toPoint()):
            return
        if self._targetAt(event.position().x()) == pressed:
            self._activate(pressed)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Traite la navigation et les raccourcis clavier.

        +/− ajustent la vitesse d'animation ; Échap arrête l'animation en
        cours ; les flèches et Origine/Fin déplacent le focus ; Espace et
        Entrée activent la tranche courante, comme un clic.

        Args:
            event: Événement fourni par Qt.
        """
        key = Qt.Key(event.key())
        match key:
            case Qt.Key.Key_Plus | Qt.Key.Key_Equal:
                self.__engine.speedUp()
            case Qt.Key.Key_Minus | Qt.Key.Key_Underscore:
                self.__engine.slowDown()
            case Qt.Key.Key_Escape if self.animationState() is QDomainExplorerBox.AnimationState.Running:
                self.stopAnimation()
            case Qt.Key.Key_Space:
                if not event.isAutoRepeat() and self.__focus is not None:
                    self.__pressed = self.__focus
                    self.__pressedByKey = True
                    self.update()
            case Qt.Key.Key_Return | Qt.Key.Key_Enter:
                if not event.isAutoRepeat() and self.__focus is not None:
                    self._activate(self.__focus)
            case Qt.Key.Key_Left:
                self.__moveWithinGroup(-1)
            case Qt.Key.Key_Right:
                self.__moveWithinGroup(+1)
            case Qt.Key.Key_Home | Qt.Key.Key_End if self.__focus is not None:
                if group := self._groupOf(self.__focus):
                    self.__setFocus(group[0] if key is Qt.Key.Key_Home else group[-1])
            case _:
                super().keyPressEvent(event)  # Esc outside of an animation → parent (dialog)
                return
        event.accept()

    @override
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Termine l'activation d'une tranche pressée au clavier (touche Espace).

        Args:
            event: Événement fourni par Qt.
        """
        if (event.key() == Qt.Key.Key_Space and not event.isAutoRepeat()
                and self.__pressedByKey):
            target, self.__pressed, self.__pressedByKey = self.__pressed, None, False
            self.update()
            if target is not None:
                self._activate(target)
            event.accept()
            return
        super().keyReleaseEvent(event)

    @override
    def focusNextPrevChild(self, next: bool) -> bool:
        """Déplace le focus d'un groupe de tranches au suivant, puis hors du widget.

        Les groupes suivent l'ordre d'affichage : bouton de repliement (s'il
        est à gauche), actions instantanées, repères, animations, puis bouton
        de repliement (s'il est à droite). Replié, seul ce bouton reste.
        Chaque groupe retient sa dernière tranche focalisée.

        Args:
            next: True pour avancer (Tab), False pour reculer (Maj+Tab).

        Retourne:
            True si le focus a été déplacé à l'intérieur du widget.
        """
        if self.hasFocus() and self.__focus is not None:
            groups = self._focusGroups()
            keys = [key for key, _ in groups]
            current = self._groupIndex(self.__focus)
            if current in keys:
                at = keys.index(current)
                for key, group in (groups[at + 1:] if next else reversed(groups[:at])):
                    if group:
                        self.__setFocus(self.__remembered(key, group))
                        return True
        return super().focusNextPrevChild(next)

    @override
    def focusInEvent(self, event: QFocusEvent) -> None:
        """Place le focus sur une tranche activable à l'entrée du focus.

        Tab entre par le premier groupe non vide, Maj+Tab par le dernier ;
        chacun reprend sa dernière tranche focalisée.

        Args:
            event: Événement fourni par Qt.
        """
        nonEmpty = [(key, group) for key, group in self._focusGroups() if group]
        match event.reason():
            case Qt.FocusReason.TabFocusReason if nonEmpty:
                self.__setFocus(self.__remembered(*nonEmpty[0]))
            case Qt.FocusReason.BacktabFocusReason if nonEmpty:
                self.__setFocus(self.__remembered(*nonEmpty[-1]))
            case _ if (self.__focus is None or not self._isEligible(self.__focus)) and nonEmpty:
                self.__setFocus(nonEmpty[0][1][0])
            case _:
                pass
        self.update()
        super().focusInEvent(event)

    @override
    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Annule une activation en attente au clavier à la sortie du focus.

        Args:
            event: Événement fourni par Qt.
        """
        if self.__pressedByKey:
            self.__pressed, self.__pressedByKey = None, False
        self.update()
        super().focusOutEvent(event)

    # ============================================================ implementation
    #
    # Everything below is private: internal type and constants, then protected
    # helpers, rendering, and finally the strictly private methods.

    class _AnimationEngine(QObject):
        """Moteur d'animation : une seule horloge pilote les pas et leur progression.

        Le temps écoulé (mesuré, pas supposé) est multiplié par le facteur de
        vitesse, puis accumulé dans le compteur de pas. `stepProgress()` donne
        la fraction écoulée du pas en cours, de quoi faire glisser un curseur
        d'une position à la suivante. Changer la vitesse ne reconfigure aucun
        timer : pas et glissement restent cohérents. Le moteur ignore les
        énumérations du widget : il ne connaît que marche et arrêt.
        """

        stepped = Signal()          # a data step is due
        frameRequested = Signal()   # the rendering must be refreshed
        stateChanged = Signal()     # isActive() changed
        speedFactorChanged = Signal(float)

        FrameIntervalMs: Final[int] = 16
        MaxStepsPerFrame: Final[int] = 4

        def __init__(self, parent: QObject | None = None) -> None:
            super().__init__(parent)
            self.__active: bool = False

            self.__stepInterval: float = 500.0
            self.__speedFactor: float = 1.0
            self.__speedFactorMin: float = 0.01
            self.__speedFactorMax: float = 100.0
            self.__speedFactorStep: float = 1.25

            self.__stepAccumulator: float = 0.0  # ms

            self.__clock: QElapsedTimer = QElapsedTimer()
            self.__timer: QTimer = QTimer(self)
            self.__timer.setTimerType(Qt.TimerType.PreciseTimer)
            self.__timer.setInterval(self.FrameIntervalMs)
            self.__timer.timeout.connect(self.__emitDueSteps)

        # ----------------------------------------------------------- state

        def isActive(self) -> bool:
            return self.__active

        def start(self) -> None:
            """Démarre (ou redémarre) ; le premier pas est immédiat."""
            self.__timer.stop()
            self.__stepAccumulator = 0.0
            self.__clock.start()
            self.__timer.start()
            self.__setActive(True)
            self.stepped.emit()

        def stop(self) -> None:
            if self.__active:
                self.__timer.stop()
                self.__setActive(False)

        # ------------------------------------------------------------ parameters

        def stepInterval(self) -> float:
            return self.__stepInterval

        def setStepInterval(self, ms: float) -> None:
            self.__stepInterval = max(10.0, float(ms))

        def speedFactor(self) -> float:
            return self.__speedFactor

        def setSpeedFactor(self, factor: float) -> None:
            clamped = min(self.__speedFactorMax, max(self.__speedFactorMin, float(factor)))
            if not math.isclose(clamped, self.__speedFactor):
                self.__speedFactor = clamped
                self.speedFactorChanged.emit(clamped)

        def speedFactorRange(self) -> tuple[float, float]:
            return self.__speedFactorMin, self.__speedFactorMax

        def setSpeedFactorRange(self, minimum: float, maximum: float) -> None:
            if not 0.0 < minimum <= maximum:
                raise ValueError("0 < minimum <= maximum required")
            self.__speedFactorMin, self.__speedFactorMax = float(minimum), float(maximum)
            self.setSpeedFactor(self.__speedFactor)

        def speedFactorStep(self) -> float:
            return self.__speedFactorStep

        def setSpeedFactorStep(self, step: float) -> None:
            if step <= 1.0:
                raise ValueError("speedFactorStep must be > 1.0")
            self.__speedFactorStep = float(step)

        def speedUp(self) -> None:
            self.setSpeedFactor(self.__speedFactor * self.__speedFactorStep)

        def slowDown(self) -> None:
            self.setSpeedFactor(self.__speedFactor / self.__speedFactorStep)

        # -------------------------------------------------------------- progress

        def stepProgress(self) -> float:
            """Fraction écoulée du pas en cours, dans [0, 1]."""
            return min(1.0, self.__stepAccumulator / self.__stepInterval)

        # -------------------------------------------------------------- private

        def __setActive(self, active: bool) -> None:
            if active != self.__active:
                self.__active = active
                self.stateChanged.emit()

        @Slot()
        def __emitDueSteps(self) -> None:
            dt = float(self.__clock.restart())
            if self.__active:
                self.__stepAccumulator += dt * self.__speedFactor
                emitted = 0
                while (self.__stepAccumulator >= self.__stepInterval
                       and emitted < self.MaxStepsPerFrame):
                    self.__stepAccumulator -= self.__stepInterval
                    emitted += 1
                    self.stepped.emit()
                    if not self.__active:  # stopped by a client
                        return
                self.__stepAccumulator %= self.__stepInterval  # catch-up dropped
            self.frameRequested.emit()

    _HoverAlpha: Final[float] = 0.08
    _PressAlpha: Final[float] = 0.14
    _AnimatedAlpha: Final[float] = 0.25
    _AxisAlpha: Final[float] = 0.70
    _AxisAnimatedAlpha: Final[float] = 0.40
    _SecondaryAlpha: Final[float] = 0.45
    _MinimumSecondaryContrast: Final[float] = 0.20  # lightness gap between PlaceholderText and Base
    _ToggleGroup: Final[int] = -1
    _LeadingGroup: Final[int] = 0
    _MarkerGroup: Final[int] = 1
    _TrailingGroup: Final[int] = 2
    # Value assigned after the class, once the drawing functions (private,
    # at the end of the file) are defined: see `QDomainExplorerBox._ActionGlyphs = {...}`.
    _ActionGlyphs: ClassVar[dict[QDomainExplorerBox.Action, _QGlyphFn]]

    # ====================================================== protected helpers

    def _visibleActions(self) -> tuple[QDomainExplorerBox.Action, ...]:
        return tuple(a for a in QDomainExplorerBox.Action if self.__actionVisible[a])

    def _isShown(self, target: _QTarget) -> bool:
        if target is _Part.CollapseToggle:
            return self.__collapsible
        if isinstance(target, QDomainExplorerBox.Action):
            return self.__actionVisible[target]
        return self.__markerVisible[target]

    def _isEligible(self, target: _QTarget) -> bool:
        if target is _Part.CollapseToggle:
            return self.__collapsible
        if isinstance(target, QDomainExplorerBox.Action):
            return self.__actionVisible[target] and self.__actionEnabled[target]
        return self.__markerVisible[target] and self.__markerEnabled[target]

    @classmethod
    def _groupIndex(cls, target: _QTarget) -> int:
        """Groupe de focus d'une tranche : bouton de repliement, actions
        instantanées, repères ou animations."""
        if target is _Part.CollapseToggle:
            return cls._ToggleGroup
        if not isinstance(target, QDomainExplorerBox.Action):
            return cls._MarkerGroup
        return cls._LeadingGroup if target.animationMode() is None else cls._TrailingGroup

    def _focusGroups(self) -> list[tuple[int, list[_QTarget]]]:
        """Groupes de focus affichés, de gauche à droite : (groupe, tranches activables)."""
        groups: dict[int, list[_QTarget]] = {}
        for target in self._displayOrder():
            group = groups.setdefault(self._groupIndex(target), [])
            if self._isEligible(target):
                group.append(target)
        return list(groups.items())

    def _groupOf(self, target: _QTarget) -> list[_QTarget]:
        return dict(self._focusGroups()).get(self._groupIndex(target), [])

    def _displayOrder(self) -> list[_QTarget]:
        """Tranches affichées, de gauche à droite (masquées comprises). Replié :
        le seul bouton de repliement."""
        toggle: list[_QTarget] = [_Part.CollapseToggle] if self.__collapsible else []
        if self.__collapsed:
            return toggle
        actions = list(QDomainExplorerBox.Action)
        body: list[_QTarget] = [a for a in actions if self._groupIndex(a) == self._LeadingGroup]
        body.extend(range(self.__markerCount))
        body.extend(a for a in actions if self._groupIndex(a) == self._TrailingGroup)
        if self.__collapseButtonPosition is QDomainExplorerBox.CollapseButtonPosition.Left:
            return toggle + body
        return body + toggle

    def _geometry(self) -> _QStripGeometry:
        visible = self._visibleActions()
        return _QStripGeometry.build(
            QRectF(self.rect()), self.__markerCount,
            [a for a in visible if self._groupIndex(a) == self._LeadingGroup],
            [a for a in visible if self._groupIndex(a) == self._TrailingGroup],
            self.buttonWidth(),
            self.__collapseButtonPosition if self.__collapsible else None,
            self.__collapsed)

    def _targetAt(self, x: float) -> _QTarget | None:
        """Tranche sous l'abscisse `x`, ou None hors du panneau (widget replié)."""
        cell = self._geometry().cellUnder(x)
        return cast(_QTarget, cell.target) if cell is not None else None

    def _isAnimating(self, action: QDomainExplorerBox.Action) -> bool:
        """Le bouton d'animation `action` est-il « en cours » (affiche ⏸) ?

        Pour une pilote, vrai si au moins une suiveuse anime dans ce mode.
        """
        if (mode := action.animationMode()) is None:
            return False
        if self.__followers:
            return any(f.animationMode() is mode for f in self.__followers)
        return self.__engine.isActive() and action is self.__animatedAction

    def _animationCursor(self) -> float | None:
        """Position normalisée du curseur d'animation, ou None hors animation."""
        if not self.__engine.isActive():
            return None
        t = self.__engine.stepProgress()
        return self.__cursorFrom + (self.__cursorTo - self.__cursorFrom) * t

    def _isPressShown(self) -> bool:
        return self.__pressed is not None and (
            self.__pressedByKey or self.__hover == self.__pressed)

    def _activeTarget(self) -> _QTarget | None:
        """Tranche rehaussée par l'interaction : pressée > survolée > focus.

        Le bouton de l'animation en cours a son propre rehaussement, permanent.
        """
        if self._isPressShown():
            return self.__pressed
        if self.__hover is not None:
            return self.__hover
        return self.__focus if self.hasFocus() else None

    def _toolTipText(self, target: _QTarget) -> str:
        if target is _Part.CollapseToggle:
            text = self.tr("expand") if self.__collapsed else self.tr("collapse")
        elif isinstance(target, QDomainExplorerBox.Action):
            text = self.__actionToolTips[target]
            if self._isAnimating(target):
                return f"{text} · {self.tr('click to stop')}"
        else:
            text = self.markerToolTip(target)
        if not self._isEligible(target) or not self.isEnabled():
            text += f" ({self.tr('disabled')})"
        return text

    def _activate(self, target: _QTarget) -> None:
        """Chemin unique de toute activation : souris, clavier ou programmation."""
        if not (self.isEnabled() and self._isEligible(target)):
            return
        if target is _Part.CollapseToggle:  # display only: a running animation goes on
            self.setCollapsed(not self.__collapsed)
            return
        if isinstance(target, QDomainExplorerBox.Action) and (mode := target.animationMode()) is not None:
            if not self._isAnimating(target):
                self.startAnimation(mode)
            elif self.__followers:  # stop the followers running this mode only
                for follower in self.followers():
                    if follower.animationMode() is mode:
                        follower.stopAnimation()
            else:
                self.stopAnimation()
            return
        self.__engine.stop()  # local only: each follower stops its own when the gesture reaches it
        if isinstance(target, int):
            self.__ownIndex = target
            self.markerActivated.emit(target)
            self.positionRequested.emit(self.markerPosition(target))
        else:
            match target:
                case QDomainExplorerBox.Action.ResetToDefault:
                    self.__ownIndex = 0
                case QDomainExplorerBox.Action.Randomize:
                    self.__ownIndex = random.randrange(self.__markerCount)
                case _:
                    pass
            self.triggered.emit(target)

    # ------------------------------------------------------------- rendering

    def _color(self, role: QPalette.ColorRole, enabled: bool = True) -> QColor:
        group = (QPalette.ColorGroup.Active if enabled and self.isEnabled()
                 else QPalette.ColorGroup.Disabled)
        return self.palette().color(group, role)

    def _ink(self, enabled: bool) -> _QInk:
        color = self._color(QPalette.ColorRole.Text, enabled)
        return _QInk(color, self._secondaryInk(color, enabled), _iconFontFor(self.style()))

    def _accentInk(self) -> _QInk:
        accent = self._color(QPalette.ColorRole.Accent)
        return _QInk(accent, accent, _iconFontFor(self.style()))

    def _secondaryInk(self, ink: QColor, enabled: bool) -> QColor:
        """Encre atténuée du thème (`PlaceholderText`), ou l'encre atténuée si
        celle du thème se distingue mal du fond (ex. contraste élevé)."""
        placeholder = self._color(QPalette.ColorRole.PlaceholderText, enabled)
        base = self._color(QPalette.ColorRole.Base, enabled)
        if abs(placeholder.lightnessF() - base.lightnessF()) < self._MinimumSecondaryContrast:
            return _withAlpha(ink, self._SecondaryAlpha)
        return placeholder

    def _highlightRect(self, g: _QStripGeometry, target: _QTarget) -> QRectF | None:
        """Zone rehaussée d'une tranche (survol, appui, focus) : le motif d'un
        repère, ou le bouton entier."""
        cell = g.cellOf(target)
        if cell is None:
            return None
        m = g.metrics
        half = m.highlightHalfHeight()
        if isinstance(target, int):
            width = m.markerMotifWidth()
            return QRectF(cell.centerX() - width / 2.0, g.axisY - half, width, 2.0 * half)
        return QRectF(cell.rect.left() + 1.0, g.axisY - half, cell.rect.width() - 2.0, 2.0 * half)

    def _paintPanel(self, p: QPainter, g: _QStripGeometry) -> None:
        """Panneau de champ de saisie du style courant, comme celui d'un `QSpinBox`."""
        option = QStyleOptionFrame()
        option.initFrom(self)
        if g.collapsed:
            option.rect = g.frame.adjusted(-0.5, -0.5, 0.5, 0.5).toRect()
        option.lineWidth = self.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth, option, self)
        option.state &= ~(QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_HasFocus)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_PanelLineEdit, option, p, self)

    def _paintHighlight(self, p: QPainter, g: _QStripGeometry, active: _QTarget | None) -> None:
        """Rehaussement permanent du bouton animé, puis celui de l'interaction."""
        radius = g.metrics.cornerRadius()
        p.setPen(Qt.PenStyle.NoPen)
        for cell in g.buttons:
            action = cast(QDomainExplorerBox.Action, cell.target)
            if self._isAnimating(action) and (rect := self._highlightRect(g, action)) is not None:
                p.setBrush(_withAlpha(self._color(QPalette.ColorRole.Accent), self._AnimatedAlpha))
                p.drawRoundedRect(rect, radius, radius)
        if active is None or not self.isEnabled() or not self._isEligible(active):
            return
        if (rect := self._highlightRect(g, active)) is not None:
            alpha = self._PressAlpha if self._isPressShown() else self._HoverAlpha
            p.setBrush(_withAlpha(self._color(QPalette.ColorRole.Text), alpha))
            p.drawRoundedRect(rect, radius, radius)

    def _paintAxis(self, p: QPainter, g: _QStripGeometry) -> None:
        if g.collapsed:
            return
        m = g.metrics
        alpha = self._AxisAnimatedAlpha if self.__engine.isActive() else self._AxisAlpha
        pen = QPen(_withAlpha(self._color(QPalette.ColorRole.Text), alpha), m.pen)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        p.drawLine(QPointF(g.axisLeft, g.axisY), QPointF(g.axisRight, g.axisY))
        half = m.barHalf()
        for x in (g.axisLeft, g.axisRight):  # end stops always visible
            p.drawLine(QPointF(x, g.axisY - half), QPointF(x, g.axisY + half))

    def _paintMarkerGlyph(self, p: QPainter, g: _QStripGeometry, active: _QTarget | None) -> None:
        if not isinstance(active, int) or active >= len(g.markers) or not self._isShown(active):
            return
        _drawMarker(p, QPointF(g.markers[active].centerX(), g.axisY), g.metrics,
                    self._ink(self._isEligible(active)),
                    first=active == 0, last=active == self.__markerCount - 1)

    def _paintActionGlyphs(self, p: QPainter, g: _QStripGeometry) -> None:
        for cell in g.buttons:
            action = cast(QDomainExplorerBox.Action, cell.target)
            if self._isAnimating(action):
                _drawPause(p, cell.rect, g.metrics, self._accentInk())  # what a click does now
            else:
                self._ActionGlyphs[action](p, cell.rect, g.metrics, self._ink(self._isEligible(action)))

    def _paintCollapseToggle(self, p: QPainter, g: _QStripGeometry) -> None:
        """Indicateur de dépliage du style (▸ replié, ▾ déplié) ; replié pendant
        une animation, un point de couleur d'accent rappelle qu'elle continue."""
        if g.toggle is None:
            return
        m, c = g.metrics, g.toggle.rect.center()
        size = round(m.toggleIndicatorSize())
        option = QStyleOption()
        option.initFrom(self)
        option.rect = QRect(round(c.x() - size / 2.0), round(g.axisY - size / 2.0), size, size)
        option.state |= QStyle.StateFlag.State_Children
        if not self.__collapsed:
            option.state |= QStyle.StateFlag.State_Open
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorBranch, option, p, self)
        if self.__collapsed and self.__engine.isActive():
            radius = m.activityDotRadius()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self._color(QPalette.ColorRole.Accent))
            p.drawEllipse(QPointF(c.x(), g.axisY + m.highlightHalfHeight() - 2.0 * radius), radius, radius)

    def _paintAnimationMarker(self, p: QPainter, g: _QStripGeometry) -> None:
        if g.collapsed or (cursor := self._animationCursor()) is None:
            return
        x, half = g.positionX(cursor), g.metrics.cursorHalf()
        pen = QPen(self._color(QPalette.ColorRole.Accent), g.metrics.pen * 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(x, g.axisY - half), QPointF(x, g.axisY + half))

    def _paintFocus(self, p: QPainter, g: _QStripGeometry) -> None:
        if not self.hasFocus() or self.__focus is None:
            return
        rect = self._highlightRect(g, self.__focus)
        if rect is None:
            return
        radius = g.metrics.cornerRadius()
        p.setPen(QPen(self._color(QPalette.ColorRole.Accent), g.metrics.pen))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

    # ================================================================ private

    def __defaultToolTips(self) -> dict[QDomainExplorerBox.Action, str]:
        return {
            QDomainExplorerBox.Action.ResetToDefault: self.tr("reset"),
            QDomainExplorerBox.Action.Randomize: self.tr("randomize"),
            QDomainExplorerBox.Action.AnimWrap: self.tr("anim wrap"),
            QDomainExplorerBox.Action.AnimBounce: self.tr("anim bounce"),
        }

    def __buttonHeight(self) -> int:
        """Hauteur d'un QPushButton sans texte, selon le style courant."""
        opt = QStyleOptionButton()
        opt.initFrom(self)
        content = self.fontMetrics().size(Qt.TextFlag.TextShowMnemonic, "XXXX")
        opt.rect.setSize(content)
        return self.style().sizeFromContents(
            QStyle.ContentsType.CT_PushButton, opt, content, self).height()

    def __remembered(self, groupIndex: int, group: list[_QTarget]) -> _QTarget:
        last = self.__lastInGroup.get(groupIndex)
        return last if last is not None and last in group else group[0]

    def __setHover(self, x: float) -> None:
        target = self._targetAt(x)
        if target is not None and not self._isShown(target):
            target = None  # hidden marker: inert slice
        if target != self.__hover:
            self.__hover = target
            self.update()

    def __setFocus(self, target: _QTarget) -> None:
        self.__focus = target
        self.__lastInGroup[self._groupIndex(target)] = target
        self.setAccessibleName(self.tr("Navigation: {}").format(self._toolTipText(target)))
        self.update()

    def __moveWithinGroup(self, step: int) -> None:
        """Flèches : déplacement dans le groupe courant, sans boucler."""
        if self.__focus is None:
            return
        group = self._groupOf(self.__focus)
        if self.__focus not in group:
            return
        i = group.index(self.__focus) + step
        if 0 <= i < len(group):
            self.__setFocus(group[i])

    def __refocusAfterLoss(self, lost: _QTarget) -> None:
        """Repli du focus : même groupe d'abord, puis les autres dans l'ordre d'affichage."""
        groups = self._focusGroups()
        same = self._groupIndex(lost)
        candidates = ([t for key, g in groups if key == same for t in g]
                      + [t for key, g in groups if key != same for t in g])
        self.__focus = candidates[0] if candidates else None

    def __forgetIneligible(self, target: _QTarget) -> None:
        if self._isEligible(target):
            return
        if target == self.__animatedAction:
            self.stopAnimation()
        if target == self.__pressed:
            self.__pressed, self.__pressedByKey = None, False
        if target == self.__hover and not self._isShown(target):
            self.__hover = None
        if target == self.__focus:
            self.__refocusAfterLoss(target)

    def __domainPosition(self) -> float:
        """Position normalisée courante du domaine : celle du binding, sinon la position interne."""
        if self.__binding is not None:
            size = self.__binding.size()
            if size <= 1:
                return 0.0
            return min(max(self.__binding.index(), 0), size - 1) / (size - 1)
        return self.markerPosition(self.__ownIndex)

    def __advanceOwnIndex(self, mode: QDomainExplorerBox.AnimationMode) -> None:
        n = self.__markerCount
        match mode:
            case QDomainExplorerBox.AnimationMode.Wrap:
                self.__ownIndex = (self.__ownIndex + 1) % n
            case QDomainExplorerBox.AnimationMode.Bounce:
                if not 0 <= self.__ownIndex + self.__ownDirection < n:
                    self.__ownDirection = -self.__ownDirection
                self.__ownIndex += self.__ownDirection

    @Slot()
    def __advanceAnimation(self) -> None:
        if (mode := self.animationMode()) is None:
            return
        if self.__binding is None:
            self.__advanceOwnIndex(mode)
        self.animationStepped.emit(mode)  # a binding moves its domain here, synchronously
        position = self.__domainPosition()
        # A step backwards while wrapping is the return to the start: jump, do not glide across.
        wrapped = mode is QDomainExplorerBox.AnimationMode.Wrap and position < self.__cursorTo
        self.__cursorFrom = position if wrapped else self.__cursorTo
        self.__cursorTo = position

    @Slot(int)
    def __relayMarker(self, index: int) -> None:
        last = self.__markerCount - 1
        for follower in self.followers():
            follower.activateMarker(round(index / last * (follower.markerCount() - 1)))

    @Slot(Action)
    def __relayAction(self, action: QDomainExplorerBox.Action) -> None:
        for follower in self.followers():
            follower.activateAction(action)

    @Slot(float)
    def __relaySpeedFactor(self, factor: float) -> None:
        for follower in self.followers():
            follower.setSpeedFactor(factor)

    @Slot(bool)
    def __relayCollapsed(self, collapsed: bool) -> None:
        for follower in self.followers():
            follower.setCollapsed(collapsed)

    def __forgetFollower(self, follower: QDomainExplorerBox, *_: object) -> None:
        """Retrait d'une suiveuse en cours de destruction : sans appel vers elle."""
        if shiboken6.isValid(self) and follower in self.__followers:  # the leader may be gone first
            self.__followers.remove(follower)
            self.__followerLinks.pop(follower, None)
            self.__relayAnimationState()

    @Slot()
    def __relayAnimationState(self) -> None:
        """Recalcule l'état agrégé d'une pilote ; émet `animationStateChanged` s'il change."""
        state = self.animationState() if self.__followers else QDomainExplorerBox.AnimationState.Idle
        if state is not self.__relayState:
            self.__relayState = state
            self.animationStateChanged.emit(state)
        self.update()

    @Slot()
    def __relayEngineState(self) -> None:
        state = self.animationState()
        if state is QDomainExplorerBox.AnimationState.Idle:
            self.__animatedAction = None
        self.animationStateChanged.emit(state)
        self.update()


class QDomainBinding[T, V = int](QObject):
    """Relie un `QDomainExplorerBox` à un domaine externe de positions indexées.

    Un domaine est une séquence de positions numérotées de 0 à size() − 1 (ex.
    les lignes d'une liste, la valeur d'un compteur). Une fois attaché à un
    widget via `QDomainExplorerBox.setBinding()`, le binding traduit chaque
    signal du widget en un déplacement dans le domaine : activer un repère
    positionne le domaine proportionnellement, les boutons d'action
    réinitialisent le domaine ou en tirent une position au hasard, et une
    animation en cours l'avance à chaque pas depuis sa position courante.
    L'aller-retour conserve son sens d'une animation à la suivante : arrêter
    puis relancer reprend là où l'animation s'était arrêtée.

    Un binding se construit indépendamment de tout widget, puis s'attache par
    `QDomainExplorerBox.setBinding()`.

    Paramètres de type :
        T : type de l'élément lié (ex. `QSlider`).
        V : type de la valeur que porte une position (ex. `float`). `int` par
            défaut : la valeur est alors l'index lui-même.

    Index et valeur :
        Le binding parle deux vocabulaires. L'index est celui du widget : une
        position entière du domaine, de 0 à size() − 1. La valeur est celui
        de l'élément lié : ce qu'il contient à cette position (ex. le réel
        d'un curseur). Deux conversions relient les deux, `valueFromIndex()`
        et `indexFromValue()`, à l'image de
        `QStyle.sliderValueFromPosition()` et `sliderPositionFromValue()`.
        Sans surcharge, la valeur est l'index : c'est le cas d'un domaine
        sans valeur propre (lignes d'une liste, onglets, groupe de boutons).

    Valeur par défaut :
        Rôle : désigner où `Action.ResetToDefault` ramène le domaine.
        États : non définie (état initial) ou définie. Non définie, elle
            vaut la valeur de la première position, relue à chaque usage :
            elle suit donc le domaine s'il change. Définie, elle est mémorisée
            telle quelle, sans arrondi ni bornage.
        Seule la valeur est mémorisée. L'index par défaut en est toujours
            déduit, au moment de la lecture : il reste juste si la plage ou
            la précision de l'élément lié change. Si la valeur mémorisée
            tombe entre deux positions ou hors de la plage, `defaultIndex()`
            donne la position valide la plus proche et `defaultValue()`
            garde la valeur demandée.
        `setDefaultIndex()` est une commodité : elle mémorise la valeur de
            la position donnée, à cet instant. Si la plage change ensuite, le
            défaut reste cette valeur, pas cette position.
        Accesseurs : `defaultValue()`, `defaultIndex()`.
        Mutateurs (slots Qt) : `setDefaultValue()`, `unsetDefaultValue()`,
            `setDefaultIndex()`.
        Action : `resetToDefault()` déplace le domaine à sa position par
            défaut. C'est ce que fait `Action.ResetToDefault`.

    Sous-classer :
        À surcharger obligatoirement (elles lèvent `NotImplementedError`
        sinon) : `index()`, `setIndex()` et `size()`.
        À surcharger ensemble si une position porte une valeur autre que son
        index : `valueFromIndex()` et `indexFromValue()`, en fixant `V`.
        Surchargeables au besoin : `resetToDefault()`, `randomIndex()`,
        `markerCountHint()` et `markerToolTips()`.
        `QCallbackDomainBinding` fournit une implémentation prête à l'emploi,
        par fonctions de rappel, quand une sous-classe n'est pas nécessaire.

    Signaux:
        defaultValueChanged: Signal(object). Émis quand `defaultValue()`
            change par un de ses mutateurs, avec la nouvelle valeur (de type
            `V`). N'est pas émis quand une valeur non définie suit un
            changement du domaine.

    Slots:
        setIndex(int): Déplace le domaine lié à une position donnée.
        setDefaultValue(V): Définit la valeur par défaut.
        unsetDefaultValue(): Rend la valeur par défaut non définie.
        setDefaultIndex(int): Définit la valeur par défaut par sa position.
        resetToDefault(): Déplace le domaine à sa position par défaut.
    """

    defaultValueChanged = Signal(object)

    def __init__(self, element: T, *, defaultValue: V | None = None, parent: QObject | None = None) -> None:
        """Initialise le binding pour un élément donné.

        Args:
            element: Élément externe lié, conservé pour référence (voir `element()`).
            defaultValue: Valeur par défaut du domaine (voir
                `setDefaultValue()`), ou None pour la laisser non définie.
            parent: Parent Qt, ou None. Remplacé par le widget lors de
                l'attachement (voir `QDomainExplorerBox.setBinding()`).
        """
        super().__init__(parent)
        self.__element: T = element
        self.__defaultValue: V | None = defaultValue
        self.__widget: QDomainExplorerBox | None = None
        self.__bounceDirection: int = 1

    def element(self) -> T:
        """Renvoie l'élément externe lié.

        Retourne:
            L'élément passé au constructeur.
        """
        return self.__element

    def widget(self) -> QDomainExplorerBox | None:
        """Renvoie le widget auquel ce binding est attaché.

        Retourne:
            Le `QDomainExplorerBox` attaché, ou None si ce binding n'est
            attaché à aucun widget.
        """
        return self.__widget

    def index(self) -> int:
        """Renvoie la position actuelle dans le domaine lié.

        À surcharger dans une sous-classe.

        Retourne:
            La position courante, un entier entre 0 et size() − 1. Une valeur
            négative signifie que l'élément lié n'est à aucune position (ex.
            une liste sans ligne courante) : une animation part alors de la
            première.

        Raises:
            NotImplementedError: Si la sous-classe ne surcharge pas cette méthode.
        """
        raise NotImplementedError

    @Slot(int)
    def setIndex(self, index: int) -> None:
        """Déplace le domaine lié à une position donnée.

        À surcharger dans une sous-classe.

        Args:
            index: Nouvelle position, un entier entre 0 et size() − 1.

        Raises:
            NotImplementedError: Si la sous-classe ne surcharge pas cette méthode.
        """
        raise NotImplementedError

    def size(self) -> int:
        """Renvoie le nombre de positions du domaine lié.

        À surcharger dans une sous-classe. Réévaluée à chaque usage : peut
        varier dans le temps (ex. une liste dont le contenu change).

        Retourne:
            Le nombre de positions du domaine.

        Raises:
            NotImplementedError: Si la sous-classe ne surcharge pas cette méthode.
        """
        raise NotImplementedError

    # ============================================================== API default

    def valueFromIndex(self, index: int) -> V:
        """Renvoie la valeur que porte une position du domaine.

        Implémentation par défaut, surchargeable avec `indexFromValue()`, sa
        réciproque : les deux se surchargent ensemble.

        Args:
            index: Position dans le domaine. Une position hors de
                [0, size() − 1] n'est pas une erreur : la valeur renvoyée
                prolonge alors le domaine, quand cela a un sens.

        Retourne:
            La valeur à cette position. L'index lui-même par défaut.
        """
        return cast(V, index)

    def indexFromValue(self, value: V) -> int:
        """Renvoie la position du domaine la plus proche d'une valeur.

        Implémentation par défaut, surchargeable avec `valueFromIndex()`, sa
        réciproque. Pour toute position i du domaine,
        `indexFromValue(valueFromIndex(i))` vaut i. L'inverse n'est pas
        garanti : une valeur entre deux positions est arrondie.

        Args:
            value: Valeur dans le vocabulaire de l'élément lié.

        Retourne:
            La position la plus proche. Elle n'a pas à être bornée à
            [0, size() − 1] : `defaultIndex()` s'en charge. La valeur
            elle-même par défaut.
        """
        return cast(int, value)

    def defaultValue(self) -> V:
        """Renvoie la valeur par défaut du domaine.

        Retourne:
            La valeur définie par `setDefaultValue()` ou `setDefaultIndex()`,
            telle quelle. Si elle n'est pas définie, la valeur de la première
            position, `valueFromIndex(0)`, relue à chaque appel.
        """
        if self.__defaultValue is None:
            return self.valueFromIndex(0)
        return self.__defaultValue

    @Slot(object)
    def setDefaultValue(self, value: V) -> None:
        """Définit la valeur par défaut du domaine.

        La valeur est mémorisée telle quelle : ni arrondie à une position, ni
        bornée à la plage courante. Elle reste donc celle demandée si
        l'élément lié change de plage ou de précision. Émet
        `defaultValueChanged` si `defaultValue()` change.

        Args:
            value: Valeur par défaut, dans le vocabulaire de l'élément lié.
        """
        self.__storeDefaultValue(value)

    @Slot()
    def unsetDefaultValue(self) -> None:
        """Rend la valeur par défaut non définie.

        Le défaut redevient la première position du domaine, quelle que soit
        sa valeur du moment (voir `defaultValue()`). Émet
        `defaultValueChanged` si `defaultValue()` change.
        """
        self.__storeDefaultValue(None)

    def defaultIndex(self) -> int:
        """Renvoie la position par défaut du domaine.

        Jamais mémorisée : déduite de `defaultValue()` à chaque appel.

        Retourne:
            La position la plus proche de la valeur par défaut, bornée à
            [0, size() − 1]. `0` si la valeur par défaut n'est pas définie
            ou si le domaine est vide.
        """
        if self.__defaultValue is None:
            return 0
        return max(0, min(self.indexFromValue(self.__defaultValue), self.size() - 1))

    @Slot(int)
    def setDefaultIndex(self, index: int) -> None:
        """Définit la valeur par défaut par sa position dans le domaine.

        Équivaut à `setDefaultValue(valueFromIndex(index))` : c'est la valeur
        de cette position, lue maintenant, qui est mémorisée. Si la plage de
        l'élément lié change ensuite, le défaut reste cette valeur.

        Args:
            index: Position dans le domaine.
        """
        self.setDefaultValue(self.valueFromIndex(index))

    @Slot()
    def resetToDefault(self) -> None:
        """Déplace le domaine à sa position par défaut.

        Appelée par `Action.ResetToDefault`. Sans effet sur un domaine vide.
        Implémentation par défaut, surchargeable : elle fait
        `setIndex(defaultIndex())`. Une sous-classe dont l'élément lié
        accepte des valeurs entre deux positions peut y restaurer
        `defaultValue()` exactement.
        """
        if self.size() > 0:
            self.setIndex(self.defaultIndex())

    # =============================================================== API hints

    def randomIndex(self) -> int:
        """Renvoie la position choisie par `Action.Randomize`.

        Implémentation par défaut, surchargeable.

        Retourne:
            Une position tirée uniformément entre 0 et size() − 1, ou 0 si le
            domaine est vide.
        """
        n = self.size()
        return random.randrange(n) if n > 0 else 0

    def markerCountHint(self) -> int:
        """Renvoie le nombre de repères suggéré pour ce domaine.

        Appliqué inconditionnellement à `markerCount()` lors de l'attachement
        par `QDomainExplorerBox.setBinding()` ; un `setMarkerCount()` explicite
        ultérieur reprend la main. Implémentation par défaut, surchargeable.

        Retourne:
            La taille du domaine si elle est petite, sinon
            `QDomainExplorerBox.DefaultMarkerCount`. Toujours ≥ 2.
        """
        return max(2, min(self.size(), QDomainExplorerBox.DefaultMarkerCount))

    def markerToolTips(self, markerCount: int) -> Sequence[str] | None:
        """Renvoie les infobulles suggérées pour les repères, une par repère.

        Appliquée une seule fois, à l'attachement par
        `QDomainExplorerBox.setBinding()`. Un `setMarkerCount()` explicite
        ultérieur les invalide sans les régénérer : les repères reviennent au
        pourcentage par défaut (voir `QDomainExplorerBox.markerToolTip()`).
        Implémentation par défaut, surchargeable.

        Args:
            markerCount: Nombre de repères pour lequel fournir une infobulle
                chacun (déjà celui résultant de `markerCountHint()`).

        Retourne:
            None par défaut : le widget garde son pourcentage. Une séquence de
            `markerCount` infobulles sinon.
        """
        return None

    def _genericMarkerToolTips(self, markerCount: int) -> list[str]:
        """Infobulles génériques (premier/milieu/dernier), indépendantes du
        contenu du domaine lié.

        Utiles quand ce contenu peut changer d'ordre ou de valeur : l'infobulle
        est fixée à l'attachement et ne suivrait pas (ex. le texte d'un
        `QComboBox`).
        """
        if markerCount <= 1:
            return [self.tr("go to first")]
        return [
            self.tr("go to first") if i == 0
            else self.tr("go to last") if i == markerCount - 1
            else self.tr("go to middle")
            for i in range(markerCount)
        ]

    def _attach(self, widget: QDomainExplorerBox) -> None:
        """Réservée à `QDomainExplorerBox.setBinding()`."""
        self.__widget = widget
        widget.positionRequested.connect(self.__moveToPosition)
        widget.triggered.connect(self.__runAction)
        widget.animationStepped.connect(self.__stepIndex)

    def _detach(self, widget: QDomainExplorerBox) -> None:
        """Réservée à `QDomainExplorerBox.setBinding()`."""
        widget.positionRequested.disconnect(self.__moveToPosition)
        widget.triggered.disconnect(self.__runAction)
        widget.animationStepped.disconnect(self.__stepIndex)
        self.__widget = None

    def __storeDefaultValue(self, value: V | None) -> None:
        previous = self.defaultValue()
        self.__defaultValue = value
        current = self.defaultValue()
        if current != previous:
            self.defaultValueChanged.emit(current)

    @Slot(float)
    def __moveToPosition(self, t: float) -> None:
        n = self.size()
        if n <= 0:
            return
        self.setIndex(round(t * (n - 1)))

    @Slot(QDomainExplorerBox.Action)
    def __runAction(self, action: QDomainExplorerBox.Action) -> None:
        match action:
            case QDomainExplorerBox.Action.ResetToDefault:
                self.resetToDefault()
            case QDomainExplorerBox.Action.Randomize:
                self.setIndex(self.randomIndex())
            case _:
                pass  # any additional instantaneous actions: ignored here

    @Slot(QDomainExplorerBox.AnimationMode)
    def __stepIndex(self, mode: QDomainExplorerBox.AnimationMode) -> None:
        n = self.size()
        if n <= 0:
            return
        row = self.index()
        match mode:
            case QDomainExplorerBox.AnimationMode.Wrap:
                row = (row + 1) % n
            case QDomainExplorerBox.AnimationMode.Bounce:
                if n > 1:
                    if not 0 <= row + self.__bounceDirection < n:
                        self.__bounceDirection = -self.__bounceDirection
                    row += self.__bounceDirection
                # n == 1: only one valid position, the bounce just stays there (nothing to do).
        self.setIndex(row)


class QCallbackDomainBinding[T, V = int](QDomainBinding[T, V]):
    """Implémentation de `QDomainBinding` par fonctions de rappel.

    Relie un élément externe sans écrire de sous-classe : chaque méthode à
    surcharger de `QDomainBinding` devient un argument du constructeur. Une
    méthode liée de l'élément convient souvent telle quelle (ex.
    `listWidget.currentRow`), sans fonction intermédiaire.

    Trois fonctions sont obligatoires. Elles décrivent le domaine en
    positions :

    * `index` : la position actuelle ;
    * `setIndex` : déplacer le domaine à une position ;
    * `size` : le nombre de positions.

    Elles suffisent à tout faire. La valeur d'une position est alors son
    index, et la valeur par défaut est un entier :

    ```python
    rows = QListWidget()
    rows.addItems(["Low", "Medium", "High"])
    binding = QCallbackDomainBinding(
        rows, index=rows.currentRow, setIndex=rows.setCurrentRow, size=rows.count,
        defaultValue=1)                 # reset goes back to "Medium"
    explorer.setBinding(binding)
    ```

    Deux fonctions sont optionnelles, et vont toujours ensemble. Elles
    donnent à chaque position une valeur propre, dans le vocabulaire de
    l'appelant :

    * `valueFromIndex` : la valeur que porte une position ;
    * `indexFromValue` : la position la plus proche d'une valeur.

    La valeur par défaut s'exprime alors dans ce vocabulaire, et `V` devient
    le type de ces valeurs :

    ```python
    zooms = [0.5, 1.0, 2.0, 4.0]
    combo = QComboBox()
    combo.addItems([f"×{zoom:g}" for zoom in zooms])
    binding = QCallbackDomainBinding(
        combo, index=combo.currentIndex, setIndex=combo.setCurrentIndex, size=combo.count,
        valueFromIndex=zooms.__getitem__, indexFromValue=zooms.index,
        defaultValue=1.0)               # reset goes back to ×1
    binding.defaultIndex()              # 1
    ```

    La valeur par défaut suit les règles de `QDomainBinding` : mémorisée
    telle quelle, modifiable ensuite par `setDefaultValue()`,
    `setDefaultIndex()` et `unsetDefaultValue()`. Elle n'est jamais une
    fonction de rappel : un défaut qui doit changer se redéfinit par ces
    mutateurs.

    Une dernière fonction optionnelle, `randomIndex`, remplace le tirage
    uniforme de `Action.Randomize`.
    """

    def __init__(
        self,
        element: T,
        *,
        index: Callable[[], int],
        setIndex: Callable[[int], None],
        size: Callable[[], int],
        valueFromIndex: Callable[[int], V] | None = None,
        indexFromValue: Callable[[V], int] | None = None,
        defaultValue: V | None = None,
        randomIndex: Callable[[], int] | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Initialise le binding avec les accesseurs de l'élément lié.

        Args:
            element: Élément externe lié, conservé pour référence (voir `element()`).
            index: Fonction renvoyant la position actuelle du domaine.
            setIndex: Fonction déplaçant le domaine à une position donnée.
            size: Fonction renvoyant le nombre de positions du domaine.
            valueFromIndex: Fonction renvoyant la valeur d'une position (voir
                `valueFromIndex()`), ou None si la valeur est l'index.
            indexFromValue: Fonction renvoyant la position la plus proche
                d'une valeur (voir `indexFromValue()`), ou None si la valeur
                est l'index.
            defaultValue: Valeur par défaut du domaine (voir
                `setDefaultValue()`), ou None pour la laisser non définie.
                Un entier, la position, sans les deux conversions.
            randomIndex: Fonction renvoyant une position aléatoire (voir
                `randomIndex()`), ou None pour un tirage uniforme par défaut.
            parent: Parent Qt, ou None.

        Raises:
            ValueError: Si une seule des deux conversions est fournie.
        """
        super().__init__(element, defaultValue=defaultValue, parent=parent)
        if (valueFromIndex is None) != (indexFromValue is None):
            raise ValueError("valueFromIndex and indexFromValue must be given together")
        self.__index: Callable[[], int] = index
        self.__setIndex: Callable[[int], None] = setIndex
        self.__size: Callable[[], int] = size
        self.__valueFromIndex: Callable[[int], V] | None = valueFromIndex
        self.__indexFromValue: Callable[[V], int] | None = indexFromValue
        self.__randomIndex: Callable[[], int] | None = randomIndex

    @override
    def index(self) -> int:
        return self.__index()

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        self.__setIndex(index)

    @override
    def size(self) -> int:
        return self.__size()

    @override
    def valueFromIndex(self, index: int) -> V:
        return super().valueFromIndex(index) if self.__valueFromIndex is None else self.__valueFromIndex(index)

    @override
    def indexFromValue(self, value: V) -> int:
        return super().indexFromValue(value) if self.__indexFromValue is None else self.__indexFromValue(value)

    @override
    def randomIndex(self) -> int:
        return super().randomIndex() if self.__randomIndex is None else self.__randomIndex()


class QSliderDomainBinding(QDomainBinding[QAbstractSlider, int]):
    """Implémentation de `QDomainBinding` pour `QAbstractSlider` et ses dérivés
    concrets (`QSlider`, `QDial`, `QScrollBar`).

    Le domaine correspond directement à la plage de l'élément lié :
    `index()`/`setIndex()` délèguent à `value()`/`setValue()`, `size()` à
    `maximum() − minimum() + 1`. Contrairement à `QDoubleSpinBoxDomainBinding`,
    aucune discrétisation par pas n'est nécessaire : un `QAbstractSlider`
    avance déjà par entiers consécutifs.

    La valeur d'une position est celle du curseur : `minimum() + index`. La
    valeur par défaut se donne donc comme une valeur du curseur.
    """

    @override
    def index(self) -> int:
        return self.indexFromValue(self.element().value())

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        self.element().setValue(self.valueFromIndex(index))

    @override
    def size(self) -> int:
        return self.element().maximum() - self.element().minimum() + 1

    @override
    def valueFromIndex(self, index: int) -> int:
        return self.element().minimum() + index

    @override
    def indexFromValue(self, value: int) -> int:
        return value - self.element().minimum()


class QButtonDomainBinding(QDomainBinding[QAbstractButton, bool]):
    """Implémentation de `QDomainBinding` pour un `QAbstractButton` cochable
    (`QCheckBox`, `QRadioButton`, ou tout `QPushButton`/`QToolButton` rendu
    cochable via `setCheckable(True)`).

    Domaine de taille fixe 2 : `index()` vaut 0 (non coché) ou 1 (coché). Si
    l'élément lié n'est pas cochable, `setIndex()` n'a aucun effet, comme
    `setChecked()` lui-même dans ce cas.

    La valeur d'une position est l'état coché, un booléen. La valeur par
    défaut se donne donc comme `True` ou `False`.
    """

    @override
    def index(self) -> int:
        return self.indexFromValue(self.element().isChecked())

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        self.element().setChecked(self.valueFromIndex(index))

    @override
    def size(self) -> int:
        return 2

    @override
    def valueFromIndex(self, index: int) -> bool:
        return bool(index)

    @override
    def indexFromValue(self, value: bool) -> int:
        return int(value)

    @override
    def markerToolTips(self, markerCount: int) -> Sequence[str] | None:
        return [self.tr("unchecked"), self.tr("checked")]


class QComboBoxDomainBinding(QDomainBinding[QComboBox]):
    """Implémentation de `QDomainBinding` pour `QComboBox`.

    Les infobulles des repères restent génériques (premier/milieu/dernier)
    plutôt que le texte des items. Ce texte peut changer d'ordre ou de valeur
    après coup. L'infobulle est fixée à l'attachement : elle ne suivrait pas
    et deviendrait trompeuse.

    La valeur d'une position est son index : la valeur par défaut se donne
    comme une position.
    """

    @override
    def index(self) -> int:
        return self.element().currentIndex()

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        self.element().setCurrentIndex(index)

    @override
    def size(self) -> int:
        return self.element().count()

    @override
    def markerToolTips(self, markerCount: int) -> Sequence[str] | None:
        return self._genericMarkerToolTips(markerCount)


class QListViewDomainBinding(QDomainBinding[QListView]):
    """Implémentation de `QDomainBinding` pour `QListView` (et `QListWidget`,
    qui en hérite directement).

    Passe par la couche modèle (`model()`), commune aux deux : `QListWidget`
    l'utilise déjà en interne, même si son API `currentRow()`/`setCurrentRow()`
    le masque. Sans modèle assigné, le domaine est vide (`size() == 0`).

    Ne couvre volontairement pas `QTableView`/`QTreeView` (ni leurs variantes
    *Widget*). Un domaine 2D ou hiérarchique ne se réduit à un index 0..n−1
    que par un choix de linéarisation arbitraire, probablement trompeur.

    La valeur d'une position est son index : la valeur par défaut se donne
    comme une position.
    """

    @override
    def index(self) -> int:
        return self.element().currentIndex().row()

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        # model() is actually Optional: the PySide6 stubs omit it, but
        # QAbstractItemView.model() does return None with no model assigned (verified
        # at runtime), hence this guard despite what pyright infers.
        model = self.element().model()
        if model is not None:  # pyright: ignore[reportUnnecessaryComparison]
            self.element().setCurrentIndex(model.index(index, 0))

    @override
    def size(self) -> int:
        model = self.element().model()
        return model.rowCount() if model is not None else 0  # pyright: ignore[reportUnnecessaryComparison]


class QSpinBoxDomainBinding(QDomainBinding[QSpinBox, int]):
    """Implémentation de `QDomainBinding` pour `QSpinBox`.

    La valeur d'une position est celle du compteur : `minimum() + index`. La
    valeur par défaut se donne donc comme une valeur du compteur.
    """

    @override
    def index(self) -> int:
        return self.indexFromValue(self.element().value())

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        self.element().setValue(self.valueFromIndex(index))

    @override
    def size(self) -> int:
        return self.element().maximum() - self.element().minimum() + 1

    @override
    def valueFromIndex(self, index: int) -> int:
        return self.element().minimum() + index

    @override
    def indexFromValue(self, value: int) -> int:
        return value - self.element().minimum()


class QDoubleSpinBoxDomainBinding(QDomainBinding[QDoubleSpinBox, float]):
    """Implémentation de `QDomainBinding` pour `QDoubleSpinBox`.

    `QDoubleSpinBox` n'a pas de position entière native : le domaine est
    discrétisé par un pas. Par défaut, c'est `singleStep()`, le pas des
    flèches haut/bas. Ce n'est pas `decimals()`, la précision affichée, qui
    donnerait un domaine démesuré (ex. 2 décimales sur une plage 0–100 :
    10 001 positions). Un autre pas peut être fourni au constructeur, par
    exemple `10 ** -element.decimals()` pour suivre la précision affichée.

    Positions :
        La position i porte la valeur `minimum() + i × pas`, sans jamais
        dépasser `maximum()`. La dernière position est toujours le maximum :
        si la plage n'est pas un multiple du pas, le dernier intervalle est
        plus court, comme avec les flèches du compteur (ex. sur [0, 1] au pas
        de 0.3 : 0, 0.3, 0.6, 0.9 et 1).
        Une valeur entre deux positions appartient à la plus proche. À
        mi-chemin, c'est la suivante, selon la règle d'arrondi du compteur
        lui-même. Les calculs se font sur l'écriture décimale des nombres : au
        pas de 0.1, la valeur 0.25 est bien à mi-chemin.
        Sans pas utilisable (`singleStep()` nul), le domaine est vide :
        `size()` vaut 0 et aucun geste n'a d'effet.

    Valeur par défaut :
        Elle se donne comme un réel. Le pas du domaine est en général plus
        grossier que la précision du compteur : une valeur par défaut peut
        tomber entre deux positions (ex. 0.25 au pas de 0.1). C'est le seul
        binding dans ce cas. Il restaure alors la valeur exacte :
        `resetToDefault()` passe par `setValue()`, que le compteur arrondit
        et borne lui-même. `defaultIndex()` renvoie la position la plus
        proche.
    """

    def __init__(self, element: QDoubleSpinBox, *, step: float | None = None,
                 defaultValue: float | None = None, parent: QObject | None = None) -> None:
        """Initialise le binding pour un `QDoubleSpinBox`.

        Args:
            element: Compteur lié.
            step: Pas de discrétisation du domaine, strictement positif, ou
                None pour suivre `singleStep()` du compteur.
            defaultValue: Valeur par défaut du domaine (voir
                `setDefaultValue()`), ou None pour la laisser non définie.
            parent: Parent Qt, ou None.

        Raises:
            ValueError: Si `step` n'est pas un nombre fini strictement positif.
        """
        super().__init__(element, defaultValue=defaultValue, parent=parent)
        if step is not None and not (math.isfinite(step) and step > 0.0):
            raise ValueError("step must be a finite, strictly positive number")
        self.__step: float | None = step

    @override
    def index(self) -> int:
        return self.indexFromValue(self.element().value())

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        if self.size() > 0:
            self.element().setValue(self.valueFromIndex(index))

    @override
    def size(self) -> int:
        steps = self.__stepsTo(self.element().maximum())
        return 0 if steps is None else int(steps.to_integral_value(rounding=ROUND_CEILING)) + 1

    @override
    def valueFromIndex(self, index: int) -> float:
        element = self.element()
        step = self.__usableStep()
        if step is None:
            return element.minimum()
        return min(float(_decimalOf(element.minimum()) + index * step), element.maximum())

    @override
    def indexFromValue(self, value: float) -> int:
        if math.isnan(value):
            return 0
        if value >= self.element().maximum():
            return max(0, self.size() - 1)
        if value <= self.element().minimum():
            return 0
        steps = self.__stepsTo(value)
        return 0 if steps is None else int(steps.to_integral_value(rounding=ROUND_HALF_UP))

    @override
    @Slot()
    def resetToDefault(self) -> None:
        if self.size() > 0:
            self.element().setValue(self.defaultValue())

    def __usableStep(self) -> Decimal | None:
        """Le pas du domaine, ou None s'il ne permet pas de discrétiser la plage."""
        step = self.__step if self.__step is not None else self.element().singleStep()
        return _decimalOf(step) if math.isfinite(step) and step > 0.0 else None

    def __stepsTo(self, value: float) -> Decimal | None:
        """La distance du minimum à `value`, en pas ; None sans pas utilisable."""
        step = self.__usableStep()
        return None if step is None else (_decimalOf(value) - _decimalOf(self.element().minimum())) / step


class _QCurrentIndexElement(Protocol):
    """Forme structurelle requise par `QCurrentIndexDomainBinding` : partagée
    par `QTabBar`, `QTabWidget` et `QToolBox`, qui n'ont pourtant pas
    d'ancêtre Qt commun au-delà de `QWidget`.
    """

    def currentIndex(self) -> int: ...
    def setCurrentIndex(self, index: int) -> None: ...
    def count(self) -> int: ...


class QCurrentIndexDomainBinding[T: _QCurrentIndexElement](QDomainBinding[T]):
    """Implémentation de `QDomainBinding` pour tout élément exposant
    `currentIndex()`/`setCurrentIndex()`/`count()`, notamment `QTabBar`,
    `QTabWidget` et `QToolBox`. Ces classes n'ont pas d'ancêtre Qt commun :
    la forme attendue est donc un `Protocol` structurel, pas un type nominal.

    Infobulles génériques (premier/milieu/dernier) plutôt que le texte des
    pages. `QTabBar`/`QTabWidget` l'exposent via `tabText()`, `QToolBox` via
    `itemText()`. Ces deux noms diffèrent : le `Protocol` ne peut pas les
    décrire par une forme unique.

    La valeur d'une position est son index : la valeur par défaut se donne
    comme une position.
    """

    @override
    def index(self) -> int:
        return self.element().currentIndex()

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        self.element().setCurrentIndex(index)

    @override
    def size(self) -> int:
        return self.element().count()

    @override
    def markerToolTips(self, markerCount: int) -> Sequence[str] | None:
        return self._genericMarkerToolTips(markerCount)


class QButtonGroupDomainBinding(QDomainBinding[QButtonGroup]):
    """Implémentation de `QDomainBinding` pour `QButtonGroup` : généralise le
    choix exclusif entre boutons à N boutons (`QButtonDomainBinding`
    n'en gère que 2).

    L'index d'un bouton est sa position dans `buttons()`, soit l'ordre d'ajout
    au groupe. Ce n'est pas son `id()` Qt : il vaut souvent -1, ou l'appelant
    le choisit librement. Il donnerait un ordre moins fiable pour parcourir
    le domaine par Wrap/Bounce.

    Sans bouton coché, `index()` vaut -1, comme `QComboBox.currentIndex()`
    sans sélection : une animation part alors du premier bouton. `setIndex()`
    ignore une position hors de [0, size() − 1].

    La valeur d'une position est son index : la valeur par défaut se donne
    comme une position.
    """

    @override
    def index(self) -> int:
        checked = self.element().checkedButton()
        return self.element().buttons().index(checked) if checked is not None else -1

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        buttons = self.element().buttons()
        if 0 <= index < len(buttons):
            buttons[index].setChecked(True)

    @override
    def size(self) -> int:
        return len(self.element().buttons())






type _QGlyphFn = Callable[[QPainter, QRectF, "_QMetrics", "_QInk"], None]
class _Part(Enum):
    """Tranches du widget qui ne sont ni un repère ni une `Action`."""

    CollapseToggle = auto()


type _QTarget = int | QDomainExplorerBox.Action | _Part  # int = marker index


def _withAlpha(color: QColor, alpha: float) -> QColor:
    c = QColor(color)
    c.setAlphaF(c.alphaF() * alpha)
    return c


# ----------------------------------------------------------------- glyphs
#
# Each glyph has two renderings: a character of the icon font that the
# windows11 style uses for its own arrows (so that the chevrons match those of
# a neighbouring QSpinBox), or an equivalent QPainter stroke drawing with any
# other style. The wrap loop has no font equivalent and is always drawn.

_FluentStyle: Final[str] = "windows11"
_FluentFamily: Final[str] = "Segoe Fluent Icons"
_ChevronChars: Final[dict[tuple[int, int], str]] = {
    (0, -1): "", (0, 1): "", (-1, 0): "", (1, 0): "",
}
_ShuffleChar: Final[str] = ""
_SwitchChar: Final[str] = ""
_PauseChar: Final[str] = ""


@dataclass(frozen=True, slots=True)
class _QInk:
    """Couleurs et mode de rendu d'un glyphe."""

    color: QColor
    secondary: QColor     # attenuated stroke (return line of the wrap loop)
    iconFont: str | None  # icon font family, or None for the QPainter rendering


@functools.cache
def _isFontInstalled(family: str) -> bool:
    return family in QFontDatabase.families()


def _iconFontFor(style: QStyle) -> str | None:
    """Police d'icônes à utiliser avec ce style, ou None pour le rendu QPainter."""
    if style.name().lower() != _FluentStyle or not _isFontInstalled(_FluentFamily):
        return None
    return _FluentFamily


def _drawChar(p: QPainter, center: QPointF, char: str, color: QColor, family: str, px: float) -> None:
    font = QFont(family)
    font.setPixelSize(max(1, round(px)))
    p.setFont(font)
    p.setPen(color)
    p.drawText(QRectF(center.x() - px, center.y() - px, 2.0 * px, 2.0 * px),
               Qt.AlignmentFlag.AlignCenter, char)


def _strokePen(color: QColor, width: float, join: Qt.PenJoinStyle = Qt.PenJoinStyle.RoundJoin) -> QPen:
    pen = QPen(color, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap if join is Qt.PenJoinStyle.RoundJoin else Qt.PenCapStyle.FlatCap)
    pen.setJoinStyle(join)
    return pen


def _line(p: QPainter, color: QColor, width: float, a: QPointF, b: QPointF) -> None:
    p.setPen(_strokePen(color, width))
    p.drawLine(a, b)


def _strokeChevron(p: QPainter, tip: QPointF, dx: float, dy: float, depth: float, half: float,
                   color: QColor, width: float) -> None:
    """Chevron ouvert tracé, pointe `tip` orientée selon le vecteur unitaire (dx, dy)."""
    bx, by = tip.x() - dx * depth, tip.y() - dy * depth
    px, py = -dy * half, dx * half
    path = QPainterPath(QPointF(bx + px, by + py))
    path.lineTo(tip)
    path.lineTo(QPointF(bx - px, by - py))
    p.setPen(_strokePen(color, width))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(path)


def _chevron(p: QPainter, center: QPointF, dx: int, dy: int, m: _QMetrics, ink: _QInk) -> None:
    """Chevron de taille canonique, centré sur `center`, orienté selon (dx, dy)."""
    if ink.iconFont is not None:
        _drawChar(p, center, _ChevronChars[(dx, dy)], ink.color, ink.iconFont, m.chevronPx())
        return
    depth = m.chevronDepth()
    tip = QPointF(center.x() + dx * depth / 2.0, center.y() + dy * depth / 2.0)
    _strokeChevron(p, tip, dx, dy, depth, m.chevronHalf(), ink.color, m.pen)


def _drawConvergence(p: QPainter, c: QPointF, ux: int, uy: int, m: _QMetrics, ink: _QInk,
                     before: bool = True, after: bool = True) -> None:
    """Motif commun au reset (˅—˄) et au repère (›|‹) : deux chevrons qui
    convergent, le long de (ux, uy), vers une barre perpendiculaire.

    `before` / `after` : chevron du côté négatif / positif de la barre.
    """
    bar, offset = m.barHalf(), m.chevronOffset()
    _line(p, ink.color, m.pen, QPointF(c.x() + uy * bar, c.y() - ux * bar),
          QPointF(c.x() - uy * bar, c.y() + ux * bar))
    if before:
        _chevron(p, QPointF(c.x() - ux * offset, c.y() - uy * offset), ux, uy, m, ink)
    if after:
        _chevron(p, QPointF(c.x() + ux * offset, c.y() + uy * offset), -ux, -uy, m, ink)


def _drawMarker(p: QPainter, c: QPointF, m: _QMetrics, ink: _QInk, first: bool, last: bool) -> None:
    """›|‹ sur l'axe. Aux extrémités, un seul chevron, tourné vers la butée."""
    _drawConvergence(p, c, 1, 0, m, ink, before=not first, after=not last)


def _drawReset(p: QPainter, rect: QRectF, m: _QMetrics, ink: _QInk) -> None:
    """˅—˄ : converger vers la valeur par défaut."""
    _drawConvergence(p, rect.center(), 0, 1, m, ink)


def _drawRandomize(p: QPainter, rect: QRectF, m: _QMetrics, ink: _QInk) -> None:
    """Deux trajectoires croisées (lecture aléatoire)."""
    c = rect.center()
    if ink.iconFont is not None:
        _drawChar(p, c, _ShuffleChar, ink.color, ink.iconFont, m.iconPx())
        return
    s = m.iconHalf()
    for sign in (1, -1):
        a = QPointF(c.x() - s, c.y() + sign * s * 0.7)
        tip = QPointF(c.x() + s, c.y() - sign * s * 0.7)
        _line(p, ink.color, m.pen, a, tip)
        vx, vy = tip.x() - a.x(), tip.y() - a.y()
        norm = math.hypot(vx, vy)
        _strokeChevron(p, tip, vx / norm, vy / norm, m.chevronDepth(), m.chevronHalf() * 0.8, ink.color, m.pen)


def _drawBounce(p: QPainter, rect: QRectF, m: _QMetrics, ink: _QInk) -> None:
    """⇄ : aller vers la droite, revenir vers la gauche."""
    c = rect.center()
    if ink.iconFont is not None:
        _drawChar(p, c, _SwitchChar, ink.color, ink.iconFont, m.iconPx())
        return
    s, dy = m.iconHalf(), m.iconHalf() * 0.45
    for y, direction in ((c.y() - dy, 1), (c.y() + dy, -1)):
        _line(p, ink.color, m.pen, QPointF(c.x() - s, y), QPointF(c.x() + s, y))
        _strokeChevron(p, QPointF(c.x() + direction * s, y), direction, 0, m.chevronDepth(),
                       m.chevronHalf() * 0.8, ink.color, m.pen)


def _drawWrap(p: QPainter, rect: QRectF, m: _QMetrics, ink: _QInk) -> None:
    """Boucle en équerre : → en haut, retour atténué par le bas, qui ne remonte qu'à gauche."""
    c, s = rect.center(), m.iconHalf()
    top, bottom = c.y() - s * 0.45, c.y() + s * 0.75
    _line(p, ink.color, m.pen, QPointF(c.x() - s, top), QPointF(c.x() + s, top))
    _strokeChevron(p, QPointF(c.x() + s, top), 1, 0, s * 0.55, s * 0.5, ink.color, m.pen)
    back = QPainterPath(QPointF(c.x() + s, bottom))
    back.lineTo(c.x() - s, bottom)
    back.lineTo(c.x() - s, top + m.pen / 2.0)
    p.setPen(_strokePen(ink.secondary, m.pen, Qt.PenJoinStyle.MiterJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(back)


def _drawPause(p: QPainter, rect: QRectF, m: _QMetrics, ink: _QInk) -> None:
    """⏸ : affiché par le bouton de l'animation en cours, qu'un clic arrête."""
    c = rect.center()
    if ink.iconFont is not None:
        _drawChar(p, c, _PauseChar, ink.color, ink.iconFont, m.pausePx())
        return
    s = m.iconHalf()
    width, gap = s * 0.55, s * 0.45
    p.setPen(_strokePen(ink.color, m.pen))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for x in (c.x() - gap - width, c.x() + gap):
        p.drawRoundedRect(QRectF(x, c.y() - s * 0.85, width, s * 1.7), m.pen, m.pen)


QDomainExplorerBox._ActionGlyphs = {  # pyright: ignore[reportPrivateUsage]
    QDomainExplorerBox.Action.ResetToDefault: _drawReset,
    QDomainExplorerBox.Action.Randomize: _drawRandomize,
    QDomainExplorerBox.Action.AnimWrap: _drawWrap,
    QDomainExplorerBox.Action.AnimBounce: _drawBounce,
}


# -----------------------------------------------------------------------------
#     internal utilities (pure geometry: panel, n-marker axis, buttons)
# -----------------------------------------------------------------------------
#
# Placed here, at the end of the file, and not as inner classes of QDomainExplorerBox:
# `_QStripGeometry.build()` builds `_QMetrics`/`_QCell`, and `QDomainExplorerBox`
# builds `_QMetrics`/`_QStripGeometry`. A class used from SEVERAL different
# classes is simpler to reference at module level. `_AnimationEngine` above is
# the opposite case: it belongs to `QDomainExplorerBox` alone and is therefore
# nested inside it. A double underscore (`__Metrics`) would have triggered Python's
# name-mangling here (any `__spam` identifier written literally in ONE class
# body is rewritten to `_ThatClass__spam`, including a bare reference to a
# module-level name) on its very first bare use (`_QMetrics.forHeight(...)`) from
# `QDomainExplorerBox`'s or `_QStripGeometry`'s own methods. Hence a single
# underscore.


@dataclass(frozen=True, slots=True)
class _QMetrics:
    """Dimensions dérivées de la hauteur du widget.

    Les glyphes sont dessinés pour `ReferenceHeight`, la hauteur d'un bouton
    du style windows11 à la police par défaut ; `scale` est le rapport entre
    la hauteur réelle et celle-ci.
    """

    ReferenceHeight: ClassVar[float] = 26.0

    height: float
    padding: float
    scale: float
    pen: float    # stroke thickness

    @staticmethod
    def forHeight(height: float) -> _QMetrics:
        scale = height / _QMetrics.ReferenceHeight
        return _QMetrics(
            height=height,
            padding=max(2.0, round(height * 0.12)),
            scale=scale,
            pen=max(1.0, round(scale * 2.0) / 2.0),
        )

    def chevronPx(self) -> float:
        """Taille de police d'un chevron, celle des flèches d'un spin box."""
        return 8.0 * self.scale

    def iconPx(self) -> float:
        return 11.0 * self.scale

    def pausePx(self) -> float:
        return 10.0 * self.scale

    def chevronDepth(self) -> float:
        return 2.0 * self.scale

    def chevronHalf(self) -> float:
        return 2.8 * self.scale

    def chevronOffset(self) -> float:
        """Distance entre la barre du motif ˅—˄ / ›|‹ et le centre de chaque chevron."""
        return 4.0 * self.scale

    def barHalf(self) -> float:
        return 4.5 * self.scale

    def iconHalf(self) -> float:
        return 4.5 * self.scale

    def cursorHalf(self) -> float:
        return 6.0 * self.scale

    def highlightHalfHeight(self) -> float:
        return 9.0 * self.scale

    def cornerRadius(self) -> float:
        return 3.0 * self.scale

    def toggleWidth(self) -> float:
        """Largeur du bouton de repliement : son indicateur et une marge."""
        return 14.0 * self.scale

    def toggleIndicatorSize(self) -> float:
        return 10.0 * self.scale

    def activityDotRadius(self) -> float:
        return 1.5 * self.scale

    def markerMotifWidth(self) -> float:
        """Largeur du motif ›|‹ d'un repère, zone rehaussée comprise."""
        return 16.0 * self.scale

    def scaledWidth(self, width: int) -> int:
        """Largeur donnée à la hauteur standard, agrandie avec le widget, jamais réduite."""
        return math.ceil(width * max(1.0, self.scale))

    def defaultButtonWidth(self) -> int:
        return self.scaledWidth(QDomainExplorerBox.DefaultButtonWidth)

    def minimumGlyphWidth(self) -> float:
        """Largeur minimale d'une tranche (repère ou bouton) pour que son glyphe
        et sa zone rehaussée restent dessinables et distinctement cliquables.

        Plancher commun de `buttonWidth()`/`setButtonWidth()` et
        `markerWidth()`/`setMarkerWidth()` sur `QDomainExplorerBox` : toute largeur
        demandée plus petite y est ramenée à ce minimum. Il couvre le motif ›|‹
        d'un repère (`markerMotifWidth()`).
        """
        return max(float(self.scaledWidth(QDomainExplorerBox.MinimumButtonWidth)), self.markerMotifWidth())

    def minimumWidth(self, markerCount: int, buttonCount: int, buttonWidth: float, markerWidth: float) -> float:
        return 2.0 * self.padding + 1.0 + markerCount * markerWidth + buttonCount * buttonWidth

    def axisEndMargin(self) -> float:
        """Espace entre un repère d'extrémité et le bord de la zone de l'axe :
        la moitié du motif ›|‹, pour que sa zone rehaussée ne déborde pas sur
        le bouton voisin.
        """
        return self.markerMotifWidth() / 2.0


@dataclass(frozen=True, slots=True)
class _QCell:
    """Tranche cliquable : un repère de l'axe ou un bouton."""

    target: Hashable
    rect: QRectF  # slice within the content area (glyph, focus)
    band: QRectF  # full-height slice, extended to the edges (background, hit-test)

    def centerX(self) -> float:
        return self.rect.center().x()


@dataclass(frozen=True, slots=True)
class _QStripGeometry:
    frame: QRectF
    content: QRectF
    metrics: _QMetrics
    axisY: float
    axisLeft: float   # center of the first marker
    axisRight: float  # center of the last marker
    markers: tuple[_QCell, ...]  # all markers, hidden ones included (fixed width w / n)
    leading: tuple[_QCell, ...]  # visible buttons left of the axis
    trailing: tuple[_QCell, ...]  # visible buttons right of the axis
    toggle: _QCell | None  # collapse button, if any
    collapsed: bool  # only the collapse button is laid out

    @classmethod
    def build(cls, rect: QRectF, markerCount: int, leadingKeys: Sequence[Hashable],
              trailingKeys: Sequence[Hashable], buttonWidth: float,
              toggleSide: QDomainExplorerBox.CollapseButtonPosition | None = None,
              collapsed: bool = False) -> _QStripGeometry:
        m = _QMetrics.forHeight(rect.height())
        frame = rect.adjusted(0.5, 0.5, -0.5, -0.5)
        content = frame.adjusted(m.padding, m.padding, -m.padding, -m.padding)
        top, h = content.top(), content.height()
        axisY = content.center().y()

        # The collapse button takes its width off one side of the content; the
        # rest of the layout ignores it, its edges (`bodyLeft`, `bodyRight`)
        # standing in for those of the frame.
        toggle: _QCell | None = None
        bodyLeft, bodyRight = frame.left(), frame.right()
        if toggleSide is not None:
            width = m.toggleWidth()
            if toggleSide is QDomainExplorerBox.CollapseButtonPosition.Left:
                r = QRectF(content.left(), top, width, h)
                bodyLeft = r.right()
                toggle = _QCell(_Part.CollapseToggle, r, QRectF(frame.left(), frame.top(), bodyLeft - frame.left(), frame.height()))
                content = content.adjusted(width, 0.0, 0.0, 0.0)
            else:
                r = QRectF(content.right() - width, top, width, h)
                bodyRight = r.left()
                toggle = _QCell(_Part.CollapseToggle, r, QRectF(bodyRight, frame.top(), frame.right() - bodyRight, frame.height()))
                content = content.adjusted(0.0, 0.0, -width, 0.0)
        if collapsed and toggle is not None:
            # A layout may give more width than sizeHint(): the panel shrinks to
            # the button, against its side, and the remaining width stays inert.
            width = 2.0 * m.padding + m.toggleWidth()
            left = frame.left() if toggleSide is QDomainExplorerBox.CollapseButtonPosition.Left else frame.right() - width
            frame = QRectF(left, frame.top(), width, frame.height())
            r = QRectF(left + m.padding, top, m.toggleWidth(), h)
            toggle = _QCell(_Part.CollapseToggle, r, frame)
            return cls(frame=frame, content=r, metrics=m, axisY=axisY, axisLeft=0.0, axisRight=0.0,
                       markers=(), leading=(), trailing=(), toggle=toggle, collapsed=True)

        nl, nt = len(leadingKeys), len(trailingKeys)
        axisRegionLeft = content.left() + nl * buttonWidth
        axisRegionRight = content.right() - nt * buttonWidth
        leftBoundary = axisRegionLeft if nl else bodyLeft
        rightBoundary = axisRegionRight if nt else bodyRight

        # Markers are POINTS regularly spaced along the axis. Both end stops touch
        # the edges of the axis region (save for `axisEndMargin()`). Centering them
        # in a full-width slice, like the inner markers, would leave a
        # disproportionate gap outside.
        endMargin = min(m.axisEndMargin(), (axisRegionRight - axisRegionLeft) / (2.0 * markerCount))
        axisLeft = axisRegionLeft + endMargin
        axisRight = axisRegionRight - endMargin
        step = (axisRight - axisLeft) / (markerCount - 1)  # spacing between two markers
        half = step / 2.0

        markers: list[_QCell] = []
        for i in range(markerCount):
            cx = axisLeft + i * step
            r = QRectF(cx - half, top, step, h)
            x0 = leftBoundary if i == 0 else r.left()
            x1 = rightBoundary if i == markerCount - 1 else r.right()
            markers.append(_QCell(i, r, QRectF(x0, frame.top(), x1 - x0, frame.height())))

        def buttonCells(keys: Sequence[Hashable], left: float, x0First: float, x1Last: float) -> tuple[_QCell, ...]:
            cells: list[_QCell] = []
            for j, key in enumerate(keys):
                r = QRectF(left + j * buttonWidth, top, buttonWidth, h)
                x0 = x0First if j == 0 else r.left()
                x1 = x1Last if j == len(keys) - 1 else r.right()
                cells.append(_QCell(key, r, QRectF(x0, frame.top(), x1 - x0, frame.height())))
            return tuple(cells)

        leading = buttonCells(leadingKeys, content.left(), bodyLeft, leftBoundary)
        trailing = buttonCells(trailingKeys, content.right() - nt * buttonWidth, rightBoundary, bodyRight)

        return cls(
            frame=frame,
            content=content,
            metrics=m,
            axisY=axisY,
            axisLeft=axisLeft,
            axisRight=axisRight,
            markers=tuple(markers),
            leading=leading,
            trailing=trailing,
            toggle=toggle,
            collapsed=False,
        )

    @property
    def buttons(self) -> tuple[_QCell, ...]:
        """Boutons visibles, de gauche à droite."""
        return self.leading + self.trailing

    def positionX(self, t: float) -> float:
        """Abscisse d'une position normalisée [0, 1] sur l'axe."""
        return self.axisLeft + t * (self.axisRight - self.axisLeft)

    def cells(self) -> tuple[_QCell, ...]:
        """Toutes les tranches, de gauche à droite."""
        body = self.leading + self.markers + self.trailing
        if self.toggle is None:
            return body
        return (self.toggle,) + body if self.toggle.band.left() <= self.frame.left() else body + (self.toggle,)

    def cellUnder(self, x: float) -> _QCell | None:
        """Tranche sous l'abscisse `x`, ou None hors du panneau (widget replié)."""
        cell = self.cellAt(x)
        return cell if self.frame.left() <= x <= self.frame.right() else None

    def cellAt(self, x: float) -> _QCell:
        cells = self.cells()
        for cell in cells:
            if cell.band.left() <= x < cell.band.right():
                return cell
        return cells[0] if x < self.frame.center().x() else cells[-1]

    def cellOf(self, target: Hashable) -> _QCell | None:
        return next((c for c in self.cells() if c.target == target), None)


def _decimalOf(x: float) -> Decimal:
    """Le nombre décimal qu'écrit `x` : 0.1 donne exactement 1/10, pas son approximation binaire."""
    return Decimal(repr(x))
