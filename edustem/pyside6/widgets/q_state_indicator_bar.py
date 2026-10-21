from __future__ import annotations

import html
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Final, override

from PySide6.QtCore import (
    Signal, Slot, Qt, QCoreApplication, QEvent, QPoint, QPointF, QRect, QRectF, QSize, QSizeF, QTimer,
)
from PySide6.QtGui import (
    QBrush, QColor, QFontMetrics, QHelpEvent, QHideEvent, QIcon, QLinearGradient, QMouseEvent, QPainter,
    QPainterPath, QPaintEvent, QPalette, QPen, QPixmap, QPolygonF, QRadialGradient, QShowEvent, QTransform, qGray,
)
from PySide6.QtWidgets import QSizePolicy, QStyle, QStyleOptionButton, QToolTip, QWidget


class QStateIndicatorBar(QWidget):
    """Rangée de petits repères, chacun coloré selon l'état d'une source
    externe.

    Le widget ne connaît pas la source et ne l'interroge jamais : le code
    appelant pousse chaque nouvel état par `setState()` ou `setStates()`, au
    moment qu'il choisit.

    Indicateurs. Le widget porte un nombre quelconque d'indicateurs, repérés
    par leur index. Chacun a cinq constituants : un nom, un jeu d'états
    possibles, un état courant, une forme et une activation propre. Ils
    s'ajoutent par `addIndicator()`, `insertIndicator()` ou, en nombre, par
    `addIndicators()`. Ils se retirent par `removeIndicator()` ou `clear()`.
    `indexOf()` retrouve un indicateur par son nom, et `stateIndexOf()` un
    de ses états par son nom.

    Portée des réglages. Chaque constituant d'un indicateur se règle à trois
    portées, toujours nommées de la même façon.

    - Un indicateur : `setIndicatorX(index, valeur)`.
    - Une valeur par indicateur : `setIndicatorXs(liste)`.
    - La même valeur pour tous : `setAllIndicatorXs(valeur)`.

    Seul le nom n'a pas la troisième portée : donner le même nom à tous
    n'aurait pas de sens.

    L'état courant fait exception par ses noms courts, qui répondent aux
    signaux : `setState()`, `setStates()` et `clearStates()`.

    États. Les états possibles d'un indicateur forment un `QStateSet`. Le
    widget en garde une copie : `indicatorStateSet()` rend une copie, et
    `setIndicatorStateSet()` en prend une, comme `palette()` et
    `setPalette()`. L'état courant est le rang dans ce jeu, ou `NoState`
    quand la source n'a encore rien fourni. Un indicateur sans état est
    dessiné vide.

    Texte. Le nom d'un indicateur s'affiche à côté de son repère selon
    `textMode()` : jamais, toujours, ou seulement quand la place le permet.
    Dans ce dernier mode, le widget accepte de rétrécir jusqu'aux repères
    seuls, et les noms reparaissent tous ensemble dès qu'ils tiennent. Un
    nom vide n'affiche rien.

    Infobulle. Le survol d'un indicateur, repère ou texte, affiche son nom
    en gras et le nom de son état courant. Dessous vient la liste de ses
    états possibles, chacun précédé d'une puce de sa couleur, l'état courant
    en gras. La puce a la forme du repère quand la police de l'infobulle la
    fournit ; sinon c'est un pavé de couleur. Le texte, en HTML, vient de
    `toolTipText()`, qu'une sous-classe peut redéfinir. Hors de tout
    indicateur, l'infobulle ordinaire du widget (`toolTip()`) s'applique.

    Apparence. Le repère a la taille de l'indicateur d'un bouton radio du
    style courant, et les écarts viennent du même style. Son rendu combine
    trois réglages indépendants.

    - La forme (`Shape`) se choisit pour chaque indicateur. Elle distingue
      des familles d'indicateurs autrement que par la couleur.
    - Le biseau (`bevel()`) ne touche que le contour : trait uni, bord en
      relief ou bord en creux.
    - Le fini (`finish()`) ne touche que la surface : unie, avec un reflet
      de verre, ou avec un point de lumière.

    Le biseau et le fini valent pour tout le widget. Ils se calculent à
    partir de la seule couleur de l'état, éclairée d'en haut à gauche. Le
    contour est une teinte grisée de cette couleur : plus sombre qu'elle, ou
    plus claire si la couleur est elle-même très sombre. Un indicateur sans
    état reste une forme vide, sans biseau ni fini.

    Images. Un état peut porter une image à la place du dessin
    (`QStateSet.State.setIcon()`). Elle est toujours ajustée au carré du
    repère, proportions gardées. Un indicateur désactivé montre la variante
    désactivée de l'image. Selon `QStateSet.State.imageMode()`, l'image est
    le repère entier, avec sa propre silhouette et sans biseau, ou bien elle
    remplit la forme de l'indicateur, biseau compris. Le fini s'applique
    dans les deux cas, limité aux pixels opaques de l'image dans le premier.

    Clignotement. Un état marqué clignotant (`QStateSet.State.setBlinking()`)
    alterne entre sa couleur et une couleur d'alternance. Celle-ci est
    donnée par l'état, ou sinon calculée en assombrissant sa couleur selon
    `blinkDarkening()`. Une image alterne de même avec son image
    d'alternance, ou sinon avec elle-même assombrie. Tous les indicateurs
    clignotent à l'unisson, à la période `blinkPeriod()`, d'un coup ou en
    fondu selon `blinkTransition()`. `setBlinkEnabled()` coupe tout
    clignotement. Un indicateur désactivé ne clignote pas. Le minuteur
    interne ne tourne que si le widget est visible et qu'un indicateur doit
    clignoter ; il ne sert qu'à l'affichage.

    Clignotement et réglage du système. Les systèmes d'exploitation offrent
    un réglage d'accessibilité qui demande aux applications de réduire les
    animations : « Effets d'animation » sous Windows, « Réduire les
    animations » sous macOS. Une personne que le mouvement ou le clignotement
    à l'écran gêne, ou met en danger, l'active pour ne plus y être exposée.

    Le widget ne consulte pas ce réglage : il clignote même quand la personne
    l'a activé. Qt ne donne pas de moyen de le lire qui vaille pour tous les
    systèmes. `QStyleHints.accessibility()` ne renseigne que sur le
    contraste, pas sur le mouvement.

    C'est donc à l'application de respecter ce réglage. Elle le lit par le
    moyen propre à son système, ou l'offre dans ses propres préférences,
    puis appelle `setBlinkEnabled(False)`. Les états clignotants s'affichent
    alors fixes, dans leur couleur.

    Deux protections ne dépendent pas de cette démarche. La période ne
    descend jamais sous `MinimumBlinkPeriod`, soit trois clignotements par
    seconde au plus. Et le clignotement n'est jamais seul à porter
    l'information : le nom de l'état reste dans l'infobulle et dans
    `summaryText()`.

    Chaque repère distinct est dessiné une seule fois, puis réutilisé : un
    changement d'état fréquent ne recalcule aucun dégradé.

    Activation. Un indicateur désactivé garde sa couleur, mais atténuée, et
    son texte prend l'aspect désactivé de la palette. `setEnabled()`
    désactive tout le widget ; `setIndicatorEnabled()` désactive un seul
    indicateur. Un indicateur est dessiné activé seulement si le widget et
    lui-même le sont.

    Disposition. Les indicateurs se suivent sur une rangée ou sur une
    colonne, selon `orientation()`, séparés par `spacing()`. Le repère se
    place avant, après, au-dessus ou au-dessous de son texte, selon
    `markerPosition()`, à la distance `textSpacing()`. Ces deux écarts
    valent pour tout le widget, et l'écart entre deux indicateurs n'est
    jamais plus petit que celui entre un repère et son texte. Quand le widget est plus grand que son contenu,
    `alignment()` y place le bloc des indicateurs. Le tout s'inverse en
    disposition de droite à gauche.

    Interaction. Le widget ne change jamais un état de lui-même. Un clic
    gauche sur un indicateur activé, repère ou texte, est seulement signalé
    par `indicatorClicked`.

    Accessibilité. `summaryText()` donne en texte brut l'état de tous les
    indicateurs. Le widget le recopie dans `accessibleDescription()` à
    chaque changement : il ne faut donc pas y écrire soi-même.

    Signaux:
        stateChanged: Signal(int, int). Émis quand l'état courant d'un
            indicateur change réellement, quelle qu'en soit la cause. Porte
            l'index de l'indicateur, puis son nouvel état.
        statesChanged: Signal(). Émis une seule fois après tout appel qui a
            changé au moins un état, donc après les `stateChanged` de cet
            appel. Convient à qui recalcule un résumé de l'ensemble.
        indicatorClicked: Signal(int). Émis quand l'utilisateur clique sur
            un indicateur activé. Porte l'index de l'indicateur.

    Slots:
        setState(int, int): Définit l'état courant d'un indicateur.
        setStates(list): Définit l'état courant de chaque indicateur.
        clearStates(): Remet tous les indicateurs sans état.
        addIndicator(str, QStateSet): Ajoute un indicateur.
        insertIndicator(int, str, QStateSet): Insère un indicateur.
        addIndicators(list, QStateSet): Ajoute plusieurs indicateurs.
        removeIndicator(int): Retire un indicateur.
        clear(): Retire tous les indicateurs.
        setIndicatorName(int, str): Renomme un indicateur.
        setIndicatorNames(list): Renomme chaque indicateur.
        setIndicatorStateSet(int, QStateSet): Redéfinit les états possibles
            d'un indicateur.
        setIndicatorStateSets(list): Redéfinit ceux de chaque indicateur.
        setAllIndicatorStateSets(QStateSet): Redéfinit ceux de tous.
        setIndicatorShape(int, Shape): Définit la forme d'un repère.
        setIndicatorShapes(list): Définit la forme de chaque repère.
        setAllIndicatorShapes(Shape): Définit la forme de tous les repères.
        setIndicatorEnabled(int, bool): Active ou désactive un indicateur.
        setIndicatorsEnabled(list): Active ou désactive chaque indicateur.
        setAllIndicatorsEnabled(bool): Active ou désactive tous les
            indicateurs.
        setTextMode(TextMode): Définit l'affichage des noms.
        setOrientation(Qt.Orientation): Rangée ou colonne.
        setAlignment(Qt.AlignmentFlag): Place le bloc dans le widget.
        setMarkerPosition(MarkerPosition): Place le repère et son texte.
        setSpacing(int): Définit l'écart entre deux indicateurs.
        setTextSpacing(int): Définit l'écart entre un repère et son texte.
        setBevel(Bevel): Définit le contour des repères.
        setFinish(Finish): Définit la surface des repères.
        setBlinkEnabled(bool): Autorise ou coupe le clignotement.
        setBlinkPeriod(int): Définit la durée d'un cycle de clignotement.
        setBlinkTransition(BlinkTransition): Clignotement net ou en fondu.
        setBlinkDarkening(int): Définit l'assombrissement de l'alternance.
    """

    class Shape(Enum):
        """Forme d'un repère, inscrite dans le carré d'un repère de bouton
        radio.

        Attributs:
            Circular: Disque.
            Rectangular: Carré aux coins à peine arrondis.
            Diamond: Losange, pointes sur les quatre côtés.
            TriangleUp: Triangle, pointe en haut.
            TriangleDown: Triangle, pointe en bas.
        """

        Circular = 0
        Rectangular = 1
        Diamond = 2
        TriangleUp = 3
        TriangleDown = 4

    class Bevel(Enum):
        """Contour d'un repère.

        Attributs:
            Flat: Trait uni.
            Raised: Bord en relief, clair en haut à gauche.
            Sunken: Bord en creux, sombre en haut à gauche.
        """

        Flat = 0
        Raised = 1
        Sunken = 2

    class Finish(Enum):
        """Surface d'un repère.

        Attributs:
            Matte: Couleur unie, sans effet.
            Glossy: Reflet clair sur la moitié haute, façon verre.
            Specular: Petit point de lumière, entouré d'un halo diffus.
        """

        Matte = 0
        Glossy = 1
        Specular = 2

    class MarkerPosition(Enum):
        """Position du repère par rapport à son texte.

        Attributs:
            BeforeText: Repère du côté où la lecture commence.
            AfterText: Repère du côté où la lecture finit.
            AboveText: Repère centré au-dessus du texte.
            BelowText: Repère centré au-dessous du texte.
        """

        BeforeText = 0
        AfterText = 1
        AboveText = 2
        BelowText = 3

    class TextMode(Enum):
        """Affichage du nom des indicateurs à côté de leur repère.

        Attributs:
            Hidden: Jamais. Le widget a la taille des repères seuls.
            Visible: Toujours. Le widget ne rétrécit pas sous cette taille.
            Collapsible: Quand la place le permet. La taille préférée compte
                les noms, la taille minimale les repères seuls. Les noms
                s'affichent tous ou aucun.
        """

        Hidden = 0
        Visible = 1
        Collapsible = 2

    class BlinkTransition(Enum):
        """Passage d'une couleur à l'autre pendant le clignotement.

        Attributs:
            Step: D'un coup, à chaque demi-période.
            Fade: En fondu, par quelques paliers.
        """

        Step = 0
        Fade = 1

    NoState: Final[int] = -1
    MinimumBlinkPeriod: Final[int] = 334

    stateChanged = Signal(int, int)
    statesChanged = Signal()
    indicatorClicked = Signal(int)

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        """Initialise un widget sans indicateur.

        Args:
            orientation: Valeur initiale de `orientation()`.
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self.__indicators: list[QStateIndicatorBar._Indicator] = []
        self.__orientation: Qt.Orientation = orientation
        self.__alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        self.__markerPosition: QStateIndicatorBar.MarkerPosition = self.MarkerPosition.BeforeText
        self.__spacing: int = -1
        self.__textSpacing: int = -1
        self.__textMode: QStateIndicatorBar.TextMode = self.TextMode.Visible
        self.__bevel: QStateIndicatorBar.Bevel = self.Bevel.Flat
        self.__finish: QStateIndicatorBar.Finish = self.Finish.Matte
        self.__blinkEnabled: bool = True
        self.__blinkPeriod: int = 1000
        self.__blinkTransition: QStateIndicatorBar.BlinkTransition = self.BlinkTransition.Step
        self.__blinkDarkening: int = 250
        self.__blinkTick: int = 0
        self.__blinkTimer: QTimer = QTimer(self)
        self.__blinkTimer.timeout.connect(self._advanceBlink)
        self.__pressedIndex: int = -1
        self.__markerCache: dict[tuple[object, ...], QPixmap] = {}

        self.__applySizePolicy()

    # ============================================================== indicators

    def count(self) -> int:
        """Renvoie le nombre d'indicateurs.

        Retourne:
            Le nombre d'indicateurs.
        """
        return len(self.__indicators)

    @Slot(str, object, result=int)
    def addIndicator(self, name: str, stateSet: QStateSet, state: int = NoState,
                     shape: Shape = Shape.Circular) -> int:
        """Ajoute un indicateur à la fin.

        Args:
            name: Nom de l'indicateur.
            stateSet: États possibles de l'indicateur.
            state: État courant initial.
            shape: Forme du repère.

        Retourne:
            L'index du nouvel indicateur.

        Lève:
            TypeError, ValueError: Mêmes cas que `insertIndicator()`.
        """
        return self.insertIndicator(len(self.__indicators), name, stateSet, state, shape)

    @Slot(int, str, object, result=int)
    def insertIndicator(self, index: int, name: str, stateSet: QStateSet, state: int = NoState,
                        shape: Shape = Shape.Circular) -> int:
        """Insère un indicateur à la position donnée.

        Aucun signal d'état n'est émis : l'indicateur naît avec son état
        initial.

        Args:
            index: Position d'insertion, ramenée dans `0..count()`.
            name: Nom de l'indicateur.
            stateSet: États possibles de l'indicateur. Le jeu est copié : le
                même `QStateSet` peut servir à plusieurs indicateurs.
            state: État courant initial.
            shape: Forme du repère.

        Retourne:
            L'index réel du nouvel indicateur.

        Lève:
            TypeError: Si `name` n'est pas une chaîne, si `stateSet` n'est
                pas un `QStateSet`, ou si `shape` n'est pas une `Shape`.
            ValueError: Si `state` ne désigne ni un état possible ni
                `NoState`.
        """
        _checkNames([name])
        self.__checkDefinition(stateSet, state, shape)

        index = max(0, min(index, len(self.__indicators)))
        self.__indicators.insert(index, self._Indicator(name, stateSet.copy(), state, True, shape))
        self.__indicatorsChanged()
        return index

    @Slot(list, object, result=list)
    def addIndicators(self, names: Sequence[str], stateSet: QStateSet, state: int = NoState,
                      shape: Shape = Shape.Circular) -> list[int]:
        """Ajoute à la fin plusieurs indicateurs semblables, un par nom.

        Les arguments sont validés en entier avant tout ajout : en cas
        d'erreur, aucun indicateur n'est créé.

        Args:
            names: Nom de chaque indicateur à créer. Une liste vide ne crée
                rien.
            stateSet: États possibles, communs à tous. Chaque indicateur en
                reçoit sa propre copie.
            state: État courant initial, commun à tous.
            shape: Forme des repères.

        Retourne:
            L'index de chaque indicateur créé, dans l'ordre de `names`.

        Lève:
            TypeError: Si `names` est une chaîne seule ou contient autre
                chose que des chaînes, si `stateSet` n'est pas un
                `QStateSet`, ou si `shape` n'est pas une `Shape`.
            ValueError: Si `state` ne désigne ni un état possible ni
                `NoState`.
        """
        _checkNames(names)
        self.__checkDefinition(stateSet, state, shape)

        first = len(self.__indicators)
        for name in names:
            self.__indicators.append(self._Indicator(name, stateSet.copy(), state, True, shape))
        if names:
            self.__indicatorsChanged()
        return list(range(first, len(self.__indicators)))

    @Slot(int)
    def removeIndicator(self, index: int) -> None:
        """Retire un indicateur. Les suivants reculent d'un index.

        Args:
            index: Index de l'indicateur.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        self._checkIndex(index)
        del self.__indicators[index]
        self.__indicatorsChanged()

    @Slot()
    def clear(self) -> None:
        """Retire tous les indicateurs."""
        if self.__indicators:
            self.__indicators.clear()
            self.__indicatorsChanged()

    def indexOf(self, name: str) -> int:
        """Renvoie l'index de l'indicateur qui porte un nom.

        Args:
            name: Nom cherché, casse comprise.

        Retourne:
            L'index du premier indicateur de ce nom, ou -1.
        """
        for index, indicator in enumerate(self.__indicators):
            if indicator.name == name:
                return index
        return -1

    # ------------------------------------------------------------------- name

    def indicatorName(self, index: int) -> str:
        """Renvoie le nom d'un indicateur.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Le nom de l'indicateur.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        return self._indicator(index).name

    @Slot(int, str)
    def setIndicatorName(self, index: int, name: str) -> None:
        """Renomme un indicateur.

        Args:
            index: Index de l'indicateur.
            name: Nouveau nom.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
            TypeError: Si `name` n'est pas une chaîne.
        """
        indicator = self._indicator(index)
        _checkNames([name])
        if indicator.name != name:
            indicator.name = name
            self.__indicatorsChanged()

    def indicatorNames(self) -> list[str]:
        """Renvoie le nom de tous les indicateurs.

        Retourne:
            Un nom par indicateur, dans l'ordre des index.
        """
        return [indicator.name for indicator in self.__indicators]

    @Slot(list)
    def setIndicatorNames(self, names: Sequence[str]) -> None:
        """Renomme chaque indicateur en un appel.

        Args:
            names: Un nom par indicateur, dans l'ordre des index.

        Lève:
            TypeError: Si `names` est une chaîne seule ou contient autre
                chose que des chaînes.
            ValueError: Si la liste n'a pas `count()` éléments.
        """
        _checkNames(names)
        if len(names) != len(self.__indicators):
            raise ValueError(f"expected {len(self.__indicators)} names, got {len(names)}")
        if list(names) != self.indicatorNames():
            for indicator, name in zip(self.__indicators, names):
                indicator.name = name
            self.__indicatorsChanged()

    # -------------------------------------------------------------- state set

    def indicatorStateSet(self, index: int) -> QStateSet:
        """Renvoie les états possibles d'un indicateur.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Une copie du jeu. La modifier ne change pas l'indicateur : il
            faut la redonner par `setIndicatorStateSet()`.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        return self._indicator(index).stateSet.copy()

    @Slot(int, object)
    def setIndicatorStateSet(self, index: int, stateSet: QStateSet) -> None:
        """Redéfinit les états possibles d'un indicateur.

        L'état courant est conservé s'il désigne encore un état possible.
        Sinon il revient à `NoState`, et les signaux d'état sont émis.

        Args:
            index: Index de l'indicateur.
            stateSet: Nouveaux états possibles. Le jeu est copié.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
            TypeError: Si `stateSet` n'est pas un `QStateSet`.
        """
        self._checkIndex(index)
        _checkStateSet(stateSet)
        self.__finishStateChanges(self.__applyStateSet(index, stateSet), repaint=True)

    def indicatorStateSets(self) -> list[QStateSet]:
        """Renvoie les états possibles de tous les indicateurs.

        Retourne:
            Une copie de jeu par indicateur, dans l'ordre des index.
        """
        return [indicator.stateSet.copy() for indicator in self.__indicators]

    @Slot(list)
    def setIndicatorStateSets(self, stateSets: Sequence[QStateSet]) -> None:
        """Redéfinit les états possibles de chaque indicateur en un appel.

        La liste est validée en entier avant tout changement. Chaque état
        courant est conservé s'il désigne encore un état possible ; sinon il
        revient à `NoState`.

        Args:
            stateSets: Un jeu par indicateur, dans l'ordre des index. Copiés.

        Lève:
            TypeError: Si un élément n'est pas un `QStateSet`.
            ValueError: Si la liste n'a pas `count()` éléments.
        """
        _checkCount(stateSets, len(self.__indicators), "state sets")
        for stateSet in stateSets:
            _checkStateSet(stateSet)
        # A list, not a generator: every indicator must be updated, whatever the first results.
        changes = [self.__applyStateSet(index, stateSet) for index, stateSet in enumerate(stateSets)]
        self.__finishStateChanges(any(changes), repaint=True)

    @Slot(object)
    def setAllIndicatorStateSets(self, stateSet: QStateSet) -> None:
        """Redéfinit les états possibles de tous les indicateurs actuels.

        Chaque état courant est conservé s'il désigne encore un état
        possible. Sinon il revient à `NoState`.

        Args:
            stateSet: Nouveaux états possibles, communs à tous.

        Lève:
            TypeError: Si `stateSet` n'est pas un `QStateSet`.
        """
        _checkStateSet(stateSet)
        # A list, not a generator: every indicator must be updated, whatever the first results.
        changes = [self.__applyStateSet(index, stateSet) for index in range(len(self.__indicators))]
        self.__finishStateChanges(any(changes), repaint=True)

    def indicatorStateNames(self, index: int) -> list[str]:
        """Renvoie le nom de chaque état possible d'un indicateur.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Un nom par état possible, dans l'ordre du jeu.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        return self._indicator(index).stateSet.names()

    def stateIndexOf(self, index: int, stateName: str) -> int:
        """Renvoie le rang d'un état possible d'un indicateur, d'après son
        nom.

        Le résultat se passe tel quel à `setState()` : un nom inconnu donne
        `NoState`.

        Args:
            index: Index de l'indicateur.
            stateName: Nom d'état cherché, casse comprise.

        Retourne:
            Le rang du premier état de ce nom, ou `NoState`.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        return self._indicator(index).stateSet.indexOf(stateName)

    # ------------------------------------------------------------------ shape

    def indicatorShape(self, index: int) -> Shape:
        """Renvoie la forme du repère d'un indicateur.

        Args:
            index: Index de l'indicateur.

        Retourne:
            La forme, par défaut `Shape.Circular`.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        return self._indicator(index).shape

    @Slot(int, Shape)
    def setIndicatorShape(self, index: int, shape: Shape) -> None:
        """Définit la forme du repère d'un indicateur.

        Toutes les formes occupent le même carré : la taille du widget ne
        change pas.

        Args:
            index: Index de l'indicateur.
            shape: Nouvelle forme.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        indicator = self._indicator(index)
        if indicator.shape != shape:
            indicator.shape = shape
            self.update()

    def indicatorShapes(self) -> list[Shape]:
        """Renvoie la forme du repère de tous les indicateurs.

        Retourne:
            Une forme par indicateur, dans l'ordre des index.
        """
        return [indicator.shape for indicator in self.__indicators]

    @Slot(list)
    def setIndicatorShapes(self, shapes: Sequence[Shape]) -> None:
        """Définit la forme du repère de chaque indicateur en un appel.

        Args:
            shapes: Une forme par indicateur, dans l'ordre des index.

        Lève:
            TypeError: Si un élément n'est pas une `Shape`.
            ValueError: Si la liste n'a pas `count()` éléments.
        """
        _checkCount(shapes, len(self.__indicators), "shapes")
        for shape in shapes:
            if not isinstance(shape, self.Shape):
                raise TypeError(f"expected a QStateIndicatorBar.Shape, got {type(shape).__name__}")
        for indicator, shape in zip(self.__indicators, shapes):
            indicator.shape = shape
        self.update()

    @Slot(Shape)
    def setAllIndicatorShapes(self, shape: Shape) -> None:
        """Définit la forme du repère de tous les indicateurs actuels.

        Un indicateur ajouté ensuite reçoit la forme donnée à sa création.

        Args:
            shape: Nouvelle forme.
        """
        for indicator in self.__indicators:
            indicator.shape = shape
        self.update()

    # ---------------------------------------------------------------- enabled

    def isIndicatorEnabled(self, index: int) -> bool:
        """Indique si un indicateur est activé.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Le réglage propre à l'indicateur, sans égard à l'état activé du
            widget lui-même.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        return self._indicator(index).enabled

    @Slot(int, bool)
    def setIndicatorEnabled(self, index: int, enabled: bool) -> None:
        """Active ou désactive un seul indicateur.

        Un indicateur désactivé garde son état et continue de le recevoir.
        Son dessin change, il ne clignote plus et ne signale plus le clic.

        Args:
            index: Index de l'indicateur.
            enabled: True pour l'activer.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        indicator = self._indicator(index)
        if indicator.enabled != enabled:
            indicator.enabled = enabled
            self.__updateBlinkTimer()
            self.update()

    def areIndicatorsEnabled(self) -> list[bool]:
        """Indique, pour chaque indicateur, s'il est activé.

        Retourne:
            Le réglage propre à chaque indicateur, dans l'ordre des index.
        """
        return [indicator.enabled for indicator in self.__indicators]

    @Slot(list)
    def setIndicatorsEnabled(self, enabled: Sequence[bool]) -> None:
        """Active ou désactive chaque indicateur en un appel.

        Args:
            enabled: Un booléen par indicateur, dans l'ordre des index.

        Lève:
            TypeError: Si `enabled` est un booléen seul, ou contient autre
                chose que des booléens. Pour une même valeur donnée à tous,
                voir `setAllIndicatorsEnabled()`.
            ValueError: Si la liste n'a pas `count()` éléments.
        """
        if isinstance(enabled, bool):
            raise TypeError("expected one boolean per indicator, got a single boolean")
        _checkCount(enabled, len(self.__indicators), "booleans")
        for value in enabled:
            if not isinstance(value, bool):
                raise TypeError(f"expected every value to be a boolean, got {type(value).__name__}")
        for indicator, value in zip(self.__indicators, enabled):
            indicator.enabled = value
        self.__updateBlinkTimer()
        self.update()

    @Slot(bool)
    def setAllIndicatorsEnabled(self, enabled: bool) -> None:
        """Active ou désactive chacun des indicateurs actuels.

        Contrairement à `setEnabled()`, le widget lui-même reste activé :
        c'est le réglage propre à chaque indicateur qui change.

        Args:
            enabled: True pour les activer.
        """
        for indicator in self.__indicators:
            indicator.enabled = enabled
        self.__updateBlinkTimer()
        self.update()

    # =================================================================== state

    def state(self, index: int) -> int:
        """Renvoie l'état courant d'un indicateur.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Le rang de l'état courant dans le jeu, ou `NoState`.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        return self._indicator(index).state

    @Slot(int, int)
    def setState(self, index: int, state: int) -> None:
        """Définit l'état courant d'un indicateur.

        Args:
            index: Index de l'indicateur.
            state: Rang d'un état possible, ou `NoState`.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
            ValueError: Si `state` ne désigne ni un état possible ni
                `NoState`.
        """
        _checkState(state, self._indicator(index).stateSet.count())
        self.__finishStateChanges(self.__applyState(index, state))

    def states(self) -> list[int]:
        """Renvoie l'état courant de tous les indicateurs.

        Retourne:
            Un état par indicateur, dans l'ordre des index.
        """
        return [indicator.state for indicator in self.__indicators]

    @Slot(list)
    def setStates(self, states: Sequence[int]) -> None:
        """Définit l'état courant de chaque indicateur en un appel.

        La liste est validée en entier avant tout changement : en cas
        d'erreur, aucun état n'est modifié. `stateChanged` est émis pour
        chaque indicateur qui change, puis `statesChanged` une seule fois.

        Args:
            states: Un état par indicateur, dans l'ordre des index.

        Lève:
            ValueError: Si la liste n'a pas `count()` éléments, ou si un état
                ne désigne ni un état possible ni `NoState`.
        """
        if len(states) != len(self.__indicators):
            raise ValueError(f"expected {len(self.__indicators)} states, got {len(states)}")
        for indicator, state in zip(self.__indicators, states):
            _checkState(state, indicator.stateSet.count())
        # A list, not a generator: every indicator must be updated, whatever the first results.
        changes = [self.__applyState(index, state) for index, state in enumerate(states)]
        self.__finishStateChanges(any(changes))

    @Slot()
    def clearStates(self) -> None:
        """Remet tous les indicateurs sans état (`NoState`)."""
        changes = [self.__applyState(index, self.NoState) for index in range(len(self.__indicators))]
        self.__finishStateChanges(any(changes))

    def stateName(self, index: int) -> str:
        """Renvoie le nom de l'état courant d'un indicateur.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Le nom de l'état courant, ou une chaîne vide sans état.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        current = self._indicator(index).currentState()
        return "" if current is None else current.name()

    def summaryText(self) -> str:
        """Renvoie en texte brut l'état de tous les indicateurs.

        C'est le texte donné aux lecteurs d'écran : le widget le recopie
        dans `accessibleDescription()` à chaque changement.

        Retourne:
            Une entrée par indicateur, séparées par des virgules : son nom
            et le nom de son état courant, ou un seul des deux si l'autre
            est vide. Un indicateur sans nom ni état est omis.
        """
        entries: list[str] = []
        for index, indicator in enumerate(self.__indicators):
            stateName = self.stateName(index)
            if indicator.name and stateName:
                entries.append(self.tr("{name}: {state}").format(name=indicator.name, state=stateName))
            elif indicator.name or stateName:
                entries.append(indicator.name or stateName)
        return self.tr(", ").join(entries)

    # ================================================================== layout

    def orientation(self) -> Qt.Orientation:
        """Renvoie la disposition des indicateurs.

        Retourne:
            `Horizontal` pour une rangée, `Vertical` pour une colonne.
        """
        return self.__orientation

    @Slot(Qt.Orientation)
    def setOrientation(self, orientation: Qt.Orientation) -> None:
        """Dispose les indicateurs sur une rangée ou sur une colonne.

        Args:
            orientation: `Horizontal` pour une rangée, `Vertical` pour une
                colonne.
        """
        if self.__orientation != orientation:
            self.__orientation = orientation
            self.__applySizePolicy()
            self.__refreshGeometry()

    def alignment(self) -> Qt.AlignmentFlag:
        """Renvoie l'alignement du bloc des indicateurs dans le widget.

        Retourne:
            L'alignement, par défaut à gauche et centré verticalement.
        """
        return self.__alignment

    @Slot(Qt.AlignmentFlag)
    def setAlignment(self, alignment: Qt.AlignmentFlag) -> None:
        """Place le bloc des indicateurs dans le widget.

        N'a d'effet visible que si le widget est plus grand que son contenu.
        Sans composante horizontale, le bloc va du côté où la lecture
        commence. Sans composante verticale, il va en haut.

        Args:
            alignment: Combinaison d'une composante horizontale et d'une
                composante verticale.
        """
        if self.__alignment != alignment:
            self.__alignment = alignment
            self.update()

    def markerPosition(self) -> MarkerPosition:
        """Renvoie la position du repère par rapport à son texte.

        Retourne:
            La position, par défaut `MarkerPosition.BeforeText`.
        """
        return self.__markerPosition

    @Slot(MarkerPosition)
    def setMarkerPosition(self, position: MarkerPosition) -> None:
        """Place le repère par rapport à son texte, pour tous les indicateurs.

        Les repères restent alignés entre eux le long de la rangée ou de la
        colonne, même si certains indicateurs n'affichent pas de texte.

        Args:
            position: Nouvelle position.
        """
        if self.__markerPosition != position:
            self.__markerPosition = position
            self.__refreshGeometry()

    def spacing(self) -> int:
        """Renvoie l'écart demandé entre deux indicateurs.

        Retourne:
            L'écart en pixels, ou -1 quand il est laissé au style courant.
        """
        return self.__spacing

    @Slot(int)
    def setSpacing(self, spacing: int) -> None:
        """Définit l'écart entre deux indicateurs voisins.

        L'écart appliqué n'est jamais plus petit que celui qui sépare un
        repère de son texte (`textSpacing()`) : un texte resterait sinon
        plus près du repère voisin que du sien. La valeur demandée est
        conservée, et reprend effet si `textSpacing()` diminue.

        Args:
            spacing: Écart en pixels. Une valeur négative rend le choix au
                style courant.
        """
        spacing = max(-1, spacing)
        if self.__spacing != spacing:
            self.__spacing = spacing
            self.__refreshGeometry()

    def textSpacing(self) -> int:
        """Renvoie l'écart demandé entre un repère et son texte.

        Retourne:
            L'écart en pixels, ou -1 quand il est laissé au style courant.
        """
        return self.__textSpacing

    @Slot(int)
    def setTextSpacing(self, spacing: int) -> None:
        """Définit l'écart entre un repère et son texte, pour tous les
        indicateurs.

        Cet écart est aussi le plus petit écart possible entre deux
        indicateurs : voir `setSpacing()`.

        Args:
            spacing: Écart en pixels. Une valeur négative rend le choix au
                style courant, qui donne celui d'un bouton radio.
        """
        spacing = max(-1, spacing)
        if self.__textSpacing != spacing:
            self.__textSpacing = spacing
            self.__refreshGeometry()

    def textMode(self) -> TextMode:
        """Renvoie l'affichage du nom des indicateurs.

        Retourne:
            Le mode, par défaut `TextMode.Visible`.
        """
        return self.__textMode

    @Slot(TextMode)
    def setTextMode(self, mode: TextMode) -> None:
        """Définit l'affichage du nom des indicateurs à côté de leur repère.

        Le mode fixe aussi la politique de taille du widget : en
        `TextMode.Collapsible`, il accepte de rétrécir sous sa taille
        préférée.

        Args:
            mode: Nouveau mode.
        """
        if self.__textMode != mode:
            self.__textMode = mode
            self.__applySizePolicy()
            self.__refreshGeometry()

    def isTextShown(self) -> bool:
        """Indique si les noms sont affichés en ce moment.

        Retourne:
            True en `TextMode.Visible`, False en `TextMode.Hidden`. En
            `TextMode.Collapsible`, True si tous les noms tiennent dans la
            taille actuelle du widget.
        """
        if self.__textMode != self.TextMode.Collapsible:
            return self.__textMode == self.TextMode.Visible
        metrics = self.__metrics()
        needed = self.__contentSize(self.__itemSizes(metrics, True), metrics)
        available = self.contentsRect().size()
        return needed.width() <= available.width() and needed.height() <= available.height()

    # ================================================================ rendering

    def bevel(self) -> Bevel:
        """Renvoie le contour des repères.

        Retourne:
            Le contour, par défaut `Bevel.Flat`.
        """
        return self.__bevel

    @Slot(Bevel)
    def setBevel(self, bevel: Bevel) -> None:
        """Définit le contour des repères, pour tous les indicateurs.

        Args:
            bevel: Nouveau contour.
        """
        if self.__bevel != bevel:
            self.__bevel = bevel
            self.__markerCache.clear()
            self.update()

    def finish(self) -> Finish:
        """Renvoie la surface des repères.

        Retourne:
            La surface, par défaut `Finish.Matte`.
        """
        return self.__finish

    @Slot(Finish)
    def setFinish(self, finish: Finish) -> None:
        """Définit la surface des repères, pour tous les indicateurs.

        Args:
            finish: Nouvelle surface.
        """
        if self.__finish != finish:
            self.__finish = finish
            self.__markerCache.clear()
            self.update()

    def isBlinkEnabled(self) -> bool:
        """Indique si le clignotement est autorisé.

        Retourne:
            True si les états clignotants clignotent, ce qui est le défaut.
        """
        return self.__blinkEnabled

    @Slot(bool)
    def setBlinkEnabled(self, enabled: bool) -> None:
        """Autorise ou coupe tout clignotement.

        Coupé, un état clignotant s'affiche fixe, dans sa couleur. Sert à
        figer l'affichage, et surtout à respecter le réglage du système qui
        demande de réduire les animations. Le widget ne lit pas ce réglage
        lui-même : c'est à l'application d'appeler cette méthode (voir la
        documentation de la classe).

        Args:
            enabled: True pour autoriser le clignotement.
        """
        if self.__blinkEnabled != enabled:
            self.__blinkEnabled = enabled
            self.__updateBlinkTimer()
            self.update()

    def blinkPeriod(self) -> int:
        """Renvoie la durée d'un cycle complet de clignotement.

        Retourne:
            La durée en millisecondes, 1000 par défaut : la couleur de
            l'état, puis la couleur d'alternance.
        """
        return self.__blinkPeriod

    @Slot(int)
    def setBlinkPeriod(self, period: int) -> None:
        """Définit la durée d'un cycle complet de clignotement.

        Args:
            period: Durée en millisecondes. Une valeur sous
                `MinimumBlinkPeriod` y est ramenée : au-delà de trois
                clignotements par seconde, un affichage peut déclencher une
                crise chez une personne épileptique photosensible.
        """
        period = max(self.MinimumBlinkPeriod, period)
        if self.__blinkPeriod != period:
            self.__blinkPeriod = period
            self.__updateBlinkTimer()

    def blinkTransition(self) -> BlinkTransition:
        """Renvoie le passage d'une couleur à l'autre pendant le
        clignotement.

        Retourne:
            Le passage, par défaut `BlinkTransition.Step`.
        """
        return self.__blinkTransition

    @Slot(BlinkTransition)
    def setBlinkTransition(self, transition: BlinkTransition) -> None:
        """Définit le passage d'une couleur à l'autre pendant le
        clignotement.

        Args:
            transition: Nouveau passage.
        """
        if self.__blinkTransition != transition:
            self.__blinkTransition = transition
            self.__blinkTick = 0
            self.__updateBlinkTimer()
            self.update()

    def blinkDarkening(self) -> int:
        """Renvoie l'assombrissement qui calcule la couleur d'alternance d'un
        état qui n'en donne pas.

        Retourne:
            Le facteur, selon la convention de `QColor.darker()` : 100 ne
            change rien, 200 divise la clarté par deux. 250 par défaut.
        """
        return self.__blinkDarkening

    @Slot(int)
    def setBlinkDarkening(self, factor: int) -> None:
        """Définit l'assombrissement qui calcule la couleur d'alternance.

        Il vaut pour tous les états clignotants sans couleur d'alternance
        propre, et pour une image sans image d'alternance.

        Args:
            factor: Facteur selon la convention de `QColor.darker()`. Une
                valeur sous 100 y est ramenée.
        """
        factor = max(100, factor)
        if self.__blinkDarkening != factor:
            self.__blinkDarkening = factor
            self.__markerCache.clear()
            self.update()

    # ================================================================= geometry

    def indicatorRect(self, index: int) -> QRect:
        """Renvoie la zone occupée par un indicateur, repère et texte.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Le rectangle, en coordonnées du widget.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        self._checkIndex(index)
        return self.__layoutItems()[index].item

    def markerRect(self, index: int) -> QRect:
        """Renvoie la zone du repère d'un indicateur.

        Sert à superposer une annotation au repère, ou à l'animer.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Le carré du repère, en coordonnées du widget. Il a la taille de
            l'indicateur d'un bouton radio, quelle que soit la forme.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        self._checkIndex(index)
        return self.__layoutItems()[index].indicator

    def textRect(self, index: int) -> QRect:
        """Renvoie la zone du texte d'un indicateur.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Le rectangle du texte, en coordonnées du widget. Un rectangle
            vide si le texte n'est pas affiché : nom vide, `TextMode.Hidden`,
            ou noms repliés en `TextMode.Collapsible`.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        self._checkIndex(index)
        return self.__layoutItems()[index].text

    def indicatorAt(self, position: QPoint) -> int:
        """Renvoie l'indicateur situé à une position.

        Args:
            position: Position, en coordonnées du widget.

        Retourne:
            L'index de l'indicateur dont la zone contient la position, ou -1.
        """
        for index, geometry in enumerate(self.__layoutItems()):
            if geometry.item.contains(position):
                return index
        return -1

    def toolTipText(self, index: int) -> str:
        """Renvoie le texte de l'infobulle d'un indicateur.

        Point d'extension : une sous-classe peut le redéfinir pour composer
        un autre texte, brut ou HTML. Une chaîne vide n'affiche aucune
        infobulle.

        Args:
            index: Index de l'indicateur.

        Retourne:
            Un fragment HTML. Sa première ligne porte le nom de l'indicateur
            en gras et le nom de son état courant, ou un seul des deux si
            l'autre est vide. Les lignes suivantes listent les états
            possibles, chacun avec une puce de sa couleur, l'état courant en
            gras. Les noms sont échappés. Une chaîne vide si l'indicateur
            n'a ni nom ni état possible.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        indicator = self._indicator(index)
        name = f"<b>{html.escape(indicator.name)}</b>" if indicator.name else ""
        stateName = html.escape(self.stateName(index))
        if name and stateName:
            title = self.tr("{name}: {state}").format(name=name, state=stateName)
        else:
            title = name or stateName

        lines = [title] if title else []
        for rank, state in enumerate(indicator.stateSet.states()):
            label = html.escape(state.name())
            if rank == indicator.state:
                label = f"<b>{label}</b>"
            lines.append(f"{self._stateBullet(state.color(), indicator.shape)}&nbsp;{label}")
        if not lines:
            return ""
        return f'<div style="white-space: nowrap;">{"<br>".join(lines)}</div>'

    @override
    def sizeHint(self) -> QSize:
        """Renvoie la taille par défaut du widget.

        Retourne:
            La taille exacte des indicateurs, écarts et marges compris. Les
            noms sont comptés, sauf en `TextMode.Hidden`.
        """
        return self.__hintSize(self.__textMode != self.TextMode.Hidden)

    @override
    def minimumSizeHint(self) -> QSize:
        """Renvoie la taille minimale du widget.

        Retourne:
            La taille des indicateurs. Les noms ne sont comptés qu'en
            `TextMode.Visible` : rien n'est élidé, et en
            `TextMode.Collapsible` les noms se replient tous.
        """
        return self.__hintSize(self.__textMode == self.TextMode.Visible)

    # ================================================================== events

    @override
    def event(self, event: QEvent) -> bool:
        """Affiche l'infobulle de l'indicateur survolé.

        Args:
            event: Événement fourni par Qt.

        Retourne:
            True si l'événement a été traité.
        """
        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            index = self.indicatorAt(event.pos())
            if index >= 0:
                text = self.toolTipText(index)
                if text:
                    # The rect makes Qt hide the tip as soon as the cursor leaves this indicator.
                    QToolTip.showText(event.globalPos(), text, self, self.indicatorRect(index))
                else:
                    QToolTip.hideText()
                    event.ignore()
                return True
        return super().event(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Retient l'indicateur sur lequel le bouton gauche s'enfonce.

        Args:
            event: Événement fourni par Qt.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.__pressedIndex = self.__clickableIndexAt(event.position().toPoint())
        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Signale le clic si le bouton gauche se relâche sur l'indicateur
        où il s'était enfoncé.

        Args:
            event: Événement fourni par Qt.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            pressed = self.__pressedIndex
            self.__pressedIndex = -1
            if pressed >= 0 and pressed == self.__clickableIndexAt(event.position().toPoint()):
                self.indicatorClicked.emit(pressed)
        super().mouseReleaseEvent(event)

    @override
    def showEvent(self, event: QShowEvent) -> None:
        """Relance le clignotement quand le widget redevient visible.

        Args:
            event: Événement fourni par Qt.
        """
        super().showEvent(event)
        self.__updateBlinkTimer()

    @override
    def hideEvent(self, event: QHideEvent) -> None:
        """Arrête le clignotement quand le widget n'est plus visible.

        Args:
            event: Événement fourni par Qt.
        """
        super().hideEvent(event)
        self.__updateBlinkTimer()

    @override
    def changeEvent(self, event: QEvent) -> None:
        """Suit les changements de style, de police, de sens de lecture, de
        palette et d'activation.

        Args:
            event: Événement fourni par Qt.
        """
        super().changeEvent(event)
        if event.type() in (QEvent.Type.StyleChange, QEvent.Type.PaletteChange):
            self.__markerCache.clear()
        if event.type() in (QEvent.Type.StyleChange, QEvent.Type.FontChange, QEvent.Type.LayoutDirectionChange):
            self.__refreshGeometry()
        if event.type() == QEvent.Type.EnabledChange:
            self.__updateBlinkTimer()

    @override
    def paintEvent(self, _: QPaintEvent) -> None:
        """Dessine chaque indicateur : son repère, puis son texte.

        Args:
            _: Événement de peinture fourni par Qt (non utilisé).
        """
        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            for indicator, geometry in zip(self.__indicators, self.__layoutItems()):
                enabled = self.isEnabled() and indicator.enabled
                palette = QPalette(self.palette())
                palette.setCurrentColorGroup(QPalette.ColorGroup.Normal if enabled else QPalette.ColorGroup.Disabled)

                marker = geometry.indicator
                painter.drawPixmap(marker.topLeft(), self.__markerPixmap(indicator, palette, enabled, marker.size()))

                if not geometry.text.isEmpty():
                    self.style().drawItemText(
                        painter, geometry.text, Qt.AlignmentFlag.AlignCenter, palette, enabled, indicator.name,
                        QPalette.ColorRole.WindowText,
                    )

    # ========================================================== implementation

    @dataclass
    class _Indicator:
        name: str
        stateSet: QStateSet
        state: int
        enabled: bool
        shape: QStateIndicatorBar.Shape

        def currentState(self) -> QStateSet.State | None:
            return None if self.state < 0 else self.stateSet._stateAt(self.state)  # pyright: ignore[reportPrivateUsage]

    @dataclass(frozen=True)
    class _Geometry:
        item: QRect
        indicator: QRect
        text: QRect

    @dataclass(frozen=True)
    class _Metrics:
        indicatorSize: QSize
        labelSpacing: int
        itemSpacing: int

    _FrameContrast: Final[float] = 0.65  # Frame color between the background (0) and the text color (1).
    _DisabledDesaturation: Final[float] = 0.6  # Blend toward gray when disabled (0: none, 1: full gray).
    _DisabledFade: Final[float] = 0.5  # Blend toward the window background when disabled.
    _DisabledHighlight: Final[float] = 0.5  # Strength of the white highlights when disabled.
    _BevelWidth: Final[float] = 0.12  # Width of a raised or sunken contour, as a fraction of the marker size.
    _BevelLight: Final[float] = 0.65  # Blend of the lit edge toward white.
    _BevelShade: Final[float] = 0.6  # Blend of the shaded edge toward black.
    _BevelLightest: Final[float] = 88.0  # Highest L* allowed for the lit edge.
    _BevelDarkest: Final[float] = 14.0  # Lowest L* allowed for the shaded edge.
    _BevelClamp: Final[float] = 0.22  # Blend away from the extreme, for an edge beyond those limits.
    _BulletContrast: Final[float] = 18.0  # Smallest L* gap between a tooltip bullet and the tooltip background.
    _GlossScale: Final[float] = 0.78  # Size of the glossy reflection, relative to a non circular shape.
    # (position along the halo radius, white opacity out of 255)
    _SpecularFalloff: Final[tuple[tuple[float, float], ...]] = (
        (0.0, 255), (0.1, 240), (0.28, 100), (0.6, 32), (1.0, 0),
    )
    _FadeSteps: Final[int] = 6  # Levels between the two colors of a fading blink: few, so that markers stay cached.

    def _checkIndex(self, index: int) -> None:
        """Lève `IndexError` si `index` ne désigne aucun indicateur.

        Args:
            index: Index à vérifier.
        """
        if not 0 <= index < len(self.__indicators):
            raise IndexError(f"indicator index {index} out of range (count: {len(self.__indicators)})")

    def _indicator(self, index: int) -> QStateIndicatorBar._Indicator:
        """Renvoie les données d'un indicateur.

        Args:
            index: Index de l'indicateur.

        Retourne:
            L'indicateur, modifiable sur place.

        Lève:
            IndexError: Si `index` ne désigne aucun indicateur.
        """
        self._checkIndex(index)
        return self.__indicators[index]

    @Slot()
    def _advanceBlink(self) -> None:
        """Avance le clignotement d'un pas. Appelé par le minuteur interne."""
        self.__blinkTick += 1
        self.update()

    def _blinkLevel(self) -> float:
        """Renvoie où en est le clignotement.

        Retourne:
            0.0 pour la couleur de l'état, 1.0 pour la couleur d'alternance,
            une valeur intermédiaire pendant un fondu.
        """
        if self.__blinkTransition == self.BlinkTransition.Step:
            return float(self.__blinkTick % 2)
        position = self.__blinkTick % (2 * self._FadeSteps)
        return min(position, 2 * self._FadeSteps - position) / self._FadeSteps

    def _frameColor(self, palette: QPalette) -> QColor:
        """Renvoie la couleur du contour d'un repère sans état.

        Elle se situe entre le fond de fenêtre et la couleur du texte, donc
        elle contraste en thème clair comme en thème sombre, et pâlit avec
        le groupe désactivé de la palette.

        Args:
            palette: Palette, déjà réglée sur le groupe à utiliser.

        Retourne:
            La couleur du contour.
        """
        return _blended(
            palette.color(QPalette.ColorRole.Window), palette.color(QPalette.ColorRole.WindowText),
            self._FrameContrast,
        )

    def _fillColor(self, indicator: QStateIndicatorBar._Indicator, palette: QPalette, enabled: bool,
                   level: float) -> QColor:
        """Renvoie la couleur de remplissage d'un repère.

        Args:
            indicator: Indicateur à dessiner.
            palette: Palette, déjà réglée sur le groupe à utiliser.
            enabled: True si l'indicateur est dessiné activé.
            level: Avancement du clignotement, de 0.0 à 1.0.

        Retourne:
            La couleur de l'état courant, tirée vers sa couleur d'alternance
            selon `level`, puis atténuée si l'indicateur est désactivé. Sans
            état, la couleur de fond des champs de saisie.
        """
        current = indicator.currentState()
        if current is None:
            return palette.color(QPalette.ColorRole.Base)
        color = current.color()
        if level > 0.0:
            alternate = current.blinkColor()
            if not alternate.isValid():
                alternate = color.darker(self.__blinkDarkening)
            color = _blended(color, alternate, level)
        if enabled:
            return color
        gray = qGray(color.rgb())
        desaturated = _blended(color, QColor(gray, gray, gray, color.alpha()), self._DisabledDesaturation)
        return _blended(desaturated, palette.color(QPalette.ColorRole.Window), self._DisabledFade)

    def _paintMarker(self, painter: QPainter, rect: QRect, indicator: QStateIndicatorBar._Indicator,
                     palette: QPalette, enabled: bool) -> None:
        """Dessine le repère d'un indicateur.

        Point d'extension : une sous-classe peut le redéfinir pour un dessin
        entièrement à elle. Le résultat est mis en cache par le widget.

        Args:
            painter: Painter actif sur une image transparente, anticrénelage
                activé.
            rect: Zone du repère.
            indicator: Indicateur à dessiner.
            palette: Palette, déjà réglée sur le groupe à utiliser.
            enabled: True si l'indicateur est dessiné activé.
        """
        area = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        level = self.__blinkLevelOf(indicator, enabled)
        color = self._fillColor(indicator, palette, enabled, level)
        shape = indicator.shape
        joined = (Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.RoundJoin)

        current = indicator.currentState()
        if current is None:
            painter.setPen(QPen(self._frameColor(palette), 1.0, *joined))
            painter.setBrush(color)
            painter.drawPath(_shapePath(shape, area))
            return

        highlight = 1.0 if enabled else self._DisabledHighlight
        framed = current.imageMode() == QStateSet.State.ImageMode.Framed
        hasImage = not current.icon().isNull()

        if hasImage and not framed:
            # The image is the whole marker: the finish only lands on its opaque pixels.
            self._paintImage(painter, rect, current, enabled, level)
            whole = QPainterPath()
            whole.addRect(area)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
            self._paintFinish(painter, whole, area, self.Shape.Rectangular, highlight)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            return

        # The contour is centered on the path: a wider one must not spill out of the marker square.
        flat = self.__bevel == self.Bevel.Flat
        contourWidth = 1.0 if flat else max(1.5, area.width() * self._BevelWidth)
        inset = (contourWidth - 1.0) / 2
        area = area.adjusted(inset, inset, -inset, -inset)
        path = _shapePath(shape, area)

        painter.setPen(Qt.PenStyle.NoPen)
        if self.__finish == self.Finish.Matte:
            painter.setBrush(color)
        else:
            # Wide enough to reach the corners of the non circular shapes.
            body = QRadialGradient(area.center(), area.width() / 2 * 1.35, _lightPoint(shape, area))
            if self.__finish == self.Finish.Glossy:
                body.setColorAt(0.0, color.lighter(120))
                body.setColorAt(1.0, color.darker(125))
            else:
                body.setColorAt(0.0, color)
                body.setColorAt(1.0, color.darker(140))
            painter.setBrush(body)
        painter.drawPath(path)

        if hasImage:
            painter.save()
            painter.setClipPath(path)
            self._paintImage(painter, rect, current, enabled, level)
            painter.restore()

        self._paintFinish(painter, path, area, shape, highlight)

        if flat:
            contour = QBrush(_edgeColor(color, _outlineTarget(color), _OutlineContrast))
        else:
            lit = _edgeColor(color, QColor(Qt.GlobalColor.white), self._BevelLight)
            shaded = _edgeColor(color, QColor(Qt.GlobalColor.black), self._BevelShade)
            # A near white lit edge, or a near black shaded one, would vanish on a window of that tone:
            # keep both away from the extremes, the lit edge still being the lighter of the two.
            if _lightness(lit) > self._BevelLightest:
                lit = _edgeColor(color, QColor(Qt.GlobalColor.black), self._BevelClamp)
            if _lightness(shaded) < self._BevelDarkest:
                shaded = _edgeColor(color, QColor(Qt.GlobalColor.white), self._BevelClamp)
            first, second = (lit, shaded) if self.__bevel == self.Bevel.Raised else (shaded, lit)
            edge = QLinearGradient(area.topLeft(), area.bottomRight())
            edge.setColorAt(0.0, first)
            edge.setColorAt(0.3, first)
            edge.setColorAt(0.7, second)
            edge.setColorAt(1.0, second)
            contour = QBrush(edge)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(contour, contourWidth, *joined))
        painter.drawPath(path)

    def _paintFinish(self, painter: QPainter, path: QPainterPath, area: QRectF, shape: QStateIndicatorBar.Shape,
                     highlight: float) -> None:
        """Dessine les reflets du fini par-dessus une surface déjà peinte.

        Args:
            painter: Painter actif.
            path: Tracé de la surface.
            area: Carré dans lequel le tracé est inscrit.
            shape: Forme du tracé, qui fixe la place de la lumière.
            highlight: Force des reflets, de 0.0 à 1.0.
        """
        center = area.center()
        painter.setPen(Qt.PenStyle.NoPen)
        if self.__finish == self.Finish.Glossy:
            if shape == self.Shape.Circular:
                gloss = QPainterPath()
                gloss.addEllipse(QRectF(
                    area.left() + area.width() * 0.2, area.top() + area.height() * 0.06,
                    area.width() * 0.6, area.height() * 0.45,
                ))
            else:
                # The upper part of a shrunk copy of the shape, cut along a curve.
                shrink = QTransform()
                shrink.translate(center.x(), center.y())
                shrink.scale(self._GlossScale, self._GlossScale)
                shrink.translate(-center.x(), -center.y())
                cut = QPainterPath()
                cut.addEllipse(QRectF(
                    area.left() - area.width() * 0.2, area.top() - area.height() * 0.45,
                    area.width() * 1.4, area.height() * 0.97,
                ))
                gloss = shrink.map(path).intersected(cut)
            bounds = gloss.boundingRect()
            shine = QLinearGradient(bounds.topLeft(), bounds.bottomLeft())
            shine.setColorAt(0.0, _white(210 * highlight))
            shine.setColorAt(1.0, _white(20 * highlight))
            painter.setBrush(shine)
            painter.drawPath(gloss)

        elif self.__finish == self.Finish.Specular:
            # A tight white core, then a long faint halo, cut by the shape itself.
            spot = QRadialGradient(_lightPoint(shape, area), area.width() / 2 * 0.95)
            for position, alpha in self._SpecularFalloff:
                spot.setColorAt(position, _white(alpha * highlight))
            painter.setBrush(spot)
            painter.drawPath(path)

    def _paintImage(self, painter: QPainter, rect: QRect, state: QStateSet.State, enabled: bool,
                    level: float) -> None:
        """Dessine l'image d'un état, ajustée au carré du repère.

        Args:
            painter: Painter actif.
            rect: Zone du repère.
            state: État dont l'image est à dessiner.
            enabled: True pour la variante activée de l'image.
            level: Avancement du clignotement, de 0.0 à 1.0.
        """
        icon = state.icon()
        darkened = 0.0
        if level > 0.0:
            alternate = state.blinkIcon()
            if alternate.isNull():
                darkened = level * (1.0 - 100.0 / self.__blinkDarkening)
            elif level >= 0.5:
                icon = alternate

        mode = QIcon.Mode.Normal if enabled else QIcon.Mode.Disabled
        pixmap = icon.pixmap(rect.size(), painter.device().devicePixelRatioF(), mode)
        if pixmap.isNull():
            return
        # QIcon never scales up: do it here, so that a small image still fills the marker.
        fitted = pixmap.deviceIndependentSize().scaled(QSizeF(rect.size()), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF(
            rect.x() + (rect.width() - fitted.width()) / 2, rect.y() + (rect.height() - fitted.height()) / 2,
            fitted.width(), fitted.height(),
        )
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
        if darkened > 0.0:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
            painter.fillRect(target, QColor(0, 0, 0, round(255 * darkened)))
        painter.restore()

    def _stateBullet(self, color: QColor, shape: QStateIndicatorBar.Shape) -> str:
        """Renvoie la puce HTML d'un état, pour l'infobulle.

        Args:
            color: Couleur de l'état.
            shape: Forme du repère de l'indicateur.

        Retourne:
            Le caractère de la forme, dans la couleur de l'état. Il reçoit un
            fond contrastant si cette couleur se confond avec le fond de
            l'infobulle. Si la police de l'infobulle n'a pas ce caractère, un
            pavé de cette couleur.
        """
        glyph = _ShapeGlyphs[shape]
        if not self._isGlyphAvailable(glyph):
            return f'<span style="background-color: {color.name()};">&nbsp;&nbsp;&nbsp;</span>'
        style = f"color: {color.name()};"
        background = QToolTip.palette().color(QPalette.ColorRole.ToolTipBase)
        if abs(_lightness(color) - _lightness(background)) < self._BulletContrast:
            style += f" background-color: {_outlineColor(color).name()};"
        return f'<span style="{style}">{glyph}</span>'

    def _isGlyphAvailable(self, glyph: str) -> bool:
        """Indique si la police de l'infobulle fournit un caractère.

        Args:
            glyph: Caractère à chercher.

        Retourne:
            True si la police le contient.
        """
        return QFontMetrics(QToolTip.font()).inFontUcs4(ord(glyph))

    def __checkDefinition(self, stateSet: QStateSet, state: int, shape: QStateIndicatorBar.Shape) -> None:
        _checkStateSet(stateSet)
        _checkState(state, stateSet.count())
        if not isinstance(shape, self.Shape):
            raise TypeError(f"expected a QStateIndicatorBar.Shape, got {type(shape).__name__}")

    def __applyState(self, index: int, state: int) -> bool:
        indicator = self.__indicators[index]
        if indicator.state == state:
            return False
        indicator.state = state
        self.stateChanged.emit(index, state)
        return True

    def __applyStateSet(self, index: int, stateSet: QStateSet) -> bool:
        indicator = self.__indicators[index]
        indicator.stateSet = stateSet.copy()
        return indicator.state >= stateSet.count() and self.__applyState(index, self.NoState)

    def __finishStateChanges(self, changed: bool, repaint: bool = False) -> None:
        if repaint:
            self.__markerCache.clear()  # keeps the cache bounded when colors are redefined over and over
        if changed or repaint:
            self.update()
            self.__syncAccessibleDescription()
            self.__updateBlinkTimer()
        if changed:
            self.statesChanged.emit()

    def __indicatorsChanged(self) -> None:
        self.__syncAccessibleDescription()
        self.__updateBlinkTimer()
        self.__refreshGeometry()

    def __syncAccessibleDescription(self) -> None:
        self.setAccessibleDescription(self.summaryText())

    def __clickableIndexAt(self, position: QPoint) -> int:
        index = self.indicatorAt(position)
        return index if index >= 0 and self.__indicators[index].enabled else -1

    def __blinks(self, indicator: QStateIndicatorBar._Indicator, enabled: bool) -> bool:
        current = indicator.currentState()
        return enabled and self.__blinkEnabled and current is not None and current.isBlinking()

    def __blinkLevelOf(self, indicator: QStateIndicatorBar._Indicator, enabled: bool) -> float:
        return self._blinkLevel() if self.__blinks(indicator, enabled) else 0.0

    def __updateBlinkTimer(self) -> None:
        needed = self.isVisible() and self.isEnabled() and any(
            self.__blinks(indicator, indicator.enabled) for indicator in self.__indicators
        )
        if needed:
            fading = self.__blinkTransition == self.BlinkTransition.Fade
            self.__blinkTimer.setInterval(self.__blinkPeriod // (2 * (self._FadeSteps if fading else 1)))
            if not self.__blinkTimer.isActive():
                self.__blinkTimer.start()
        elif self.__blinkTimer.isActive():
            # Stops on the state's own color, never on the alternate one.
            self.__blinkTimer.stop()
            self.__blinkTick = 0
            self.update()

    def __refreshGeometry(self) -> None:
        self.updateGeometry()
        self.update()

    def __applySizePolicy(self) -> None:
        if self.__textMode == self.TextMode.Collapsible:
            # May shrink below the size hint, down to the markers alone.
            policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        else:
            policy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            if self.__orientation == Qt.Orientation.Vertical:
                policy.transpose()
        self.setSizePolicy(policy)

    def __metrics(self) -> QStateIndicatorBar._Metrics:
        style = self.style()
        option = QStyleOptionButton()
        option.initFrom(self)

        indicatorSize = QSize(
            style.pixelMetric(QStyle.PixelMetric.PM_ExclusiveIndicatorWidth, option, self),
            style.pixelMetric(QStyle.PixelMetric.PM_ExclusiveIndicatorHeight, option, self),
        )
        labelSpacing = self.__textSpacing
        if labelSpacing < 0:
            labelSpacing = style.pixelMetric(QStyle.PixelMetric.PM_RadioButtonLabelSpacing, option, self)

        # Both spacing queries may answer -1 (left to the layout by the style).
        radioButton = QSizePolicy.ControlType.RadioButton
        itemSpacing = self.__spacing
        if itemSpacing < 0:
            itemSpacing = style.layoutSpacing(radioButton, radioButton, self.__orientation, option, self)
        if itemSpacing < 0:
            horizontal = self.__orientation == Qt.Orientation.Horizontal
            itemSpacing = style.pixelMetric(
                QStyle.PixelMetric.PM_LayoutHorizontalSpacing if horizontal
                else QStyle.PixelMetric.PM_LayoutVerticalSpacing,
                option, self,
            )
        if itemSpacing < 0:
            itemSpacing = indicatorSize.width() // 2
        # A text must never sit closer to the next marker than to its own.
        itemSpacing = max(itemSpacing, labelSpacing)

        return self._Metrics(indicatorSize, labelSpacing, itemSpacing)

    def __textWidth(self, indicator: QStateIndicatorBar._Indicator, withText: bool) -> int:
        if not withText or not indicator.name:
            return 0
        return self.fontMetrics().horizontalAdvance(indicator.name)

    def __isStacked(self) -> bool:
        return self.__markerPosition in (self.MarkerPosition.AboveText, self.MarkerPosition.BelowText)

    def __itemSizes(self, metrics: QStateIndicatorBar._Metrics, withText: bool) -> list[QSize]:
        marker = metrics.indicatorSize
        textHeight = self.fontMetrics().height()
        stacked = self.__isStacked()

        sizes: list[QSize] = []
        for indicator in self.__indicators:
            textWidth = self.__textWidth(indicator, withText)
            if not textWidth:
                sizes.append(QSize(marker))
            elif stacked:
                sizes.append(QSize(
                    max(marker.width(), textWidth), marker.height() + metrics.labelSpacing + textHeight,
                ))
            else:
                sizes.append(QSize(
                    marker.width() + metrics.labelSpacing + textWidth, max(marker.height(), textHeight),
                ))

        # A shared cross size keeps the markers aligned along the bar.
        if self.__orientation == Qt.Orientation.Horizontal:
            height = max((size.height() for size in sizes), default=0)
            return [QSize(size.width(), height) for size in sizes]
        width = max((size.width() for size in sizes), default=0)
        return [QSize(width, size.height()) for size in sizes]

    def __contentSize(self, sizes: list[QSize], metrics: QStateIndicatorBar._Metrics) -> QSize:
        gaps = max(0, len(sizes) - 1) * metrics.itemSpacing
        if self.__orientation == Qt.Orientation.Horizontal:
            return QSize(
                sum(size.width() for size in sizes) + gaps, max((size.height() for size in sizes), default=0),
            )
        return QSize(
            max((size.width() for size in sizes), default=0), sum(size.height() for size in sizes) + gaps,
        )

    def __hintSize(self, withText: bool) -> QSize:
        metrics = self.__metrics()
        return self.__contentSize(self.__itemSizes(metrics, withText), metrics).grownBy(self.contentsMargins())

    def __placeParts(self, item: QRect, textWidth: int, metrics: QStateIndicatorBar._Metrics) -> tuple[QRect, QRect]:
        marker = metrics.indicatorSize
        textHeight = self.fontMetrics().height()
        centeredX = item.left() + (item.width() - marker.width()) // 2
        centeredY = item.top() + (item.height() - marker.height()) // 2
        stackedTextWidth = item.width() if textWidth else 0

        position = self.__markerPosition
        if position == self.MarkerPosition.BeforeText:
            markerRect = QRect(QPoint(item.left(), centeredY), marker)
            textRect = QRect(markerRect.right() + 1 + metrics.labelSpacing, item.top(), textWidth, item.height())
        elif position == self.MarkerPosition.AfterText:
            markerRect = QRect(QPoint(item.right() + 1 - marker.width(), centeredY), marker)
            textRect = QRect(
                markerRect.left() - metrics.labelSpacing - textWidth, item.top(), textWidth, item.height(),
            )
        elif position == self.MarkerPosition.AboveText:
            markerRect = QRect(QPoint(centeredX, item.top()), marker)
            textRect = QRect(item.left(), item.bottom() + 1 - textHeight, stackedTextWidth, textHeight)
        else:
            markerRect = QRect(QPoint(centeredX, item.bottom() + 1 - marker.height()), marker)
            textRect = QRect(item.left(), item.top(), stackedTextWidth, textHeight)
        return markerRect, textRect

    def __layoutItems(self) -> list[QStateIndicatorBar._Geometry]:
        metrics = self.__metrics()
        withText = self.isTextShown()
        sizes = self.__itemSizes(metrics, withText)
        direction = self.layoutDirection()
        horizontal = self.__orientation == Qt.Orientation.Horizontal
        block = QStyle.alignedRect(
            direction, self.__alignment, self.__contentSize(sizes, metrics), self.contentsRect(),
        )

        x = block.left()
        y = block.top()
        geometries: list[QStateIndicatorBar._Geometry] = []
        for indicator, size in zip(self.__indicators, sizes):
            item = QRect(QPoint(x, y), size)
            rects = (item, *self.__placeParts(item, self.__textWidth(indicator, withText), metrics))
            # Laid out left to right, then mirrored as a whole when right to left.
            geometries.append(self._Geometry(*(QStyle.visualRect(direction, block, rect) for rect in rects)))
            if horizontal:
                x += size.width() + metrics.itemSpacing
            else:
                y += size.height() + metrics.itemSpacing
        return geometries

    def __markerPixmap(self, indicator: QStateIndicatorBar._Indicator, palette: QPalette, enabled: bool,
                       size: QSize) -> QPixmap:
        # A marker only depends on this key: each distinct one is rendered once, then reused by every paint.
        ratio = self.devicePixelRatioF()
        level = self.__blinkLevelOf(indicator, enabled)
        color = self._fillColor(indicator, palette, enabled, level)
        current = indicator.currentState()
        image: tuple[object, ...] = ()
        if current is not None and not current.icon().isNull():
            # The fill color already carries the blink level, an image does not.
            image = (current.icon().cacheKey(), current.blinkIcon().cacheKey(), current.imageMode(), level)
        key = (indicator.shape, current is None, color.rgba(), enabled, size.width(), size.height(), ratio, image)
        pixmap = self.__markerCache.get(key)
        if pixmap is None:
            pixmap = QPixmap(size * ratio)
            pixmap.setDevicePixelRatio(ratio)
            pixmap.fill(Qt.GlobalColor.transparent)
            with QPainter(pixmap) as painter:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                self._paintMarker(painter, QRect(QPoint(0, 0), size), indicator, palette, enabled)
            self.__markerCache[key] = pixmap
        return pixmap


class QStateSet:
    """Jeu d'états possibles d'un indicateur : une suite ordonnée de
    `QStateSet.State`.

    Le rang d'un état dans le jeu est la valeur passée à
    `QStateIndicatorBar.setState()`.

    Un jeu est une valeur, comme `QPalette` : il se construit, se modifie,
    se compare par `==` et se copie par `copy()`. Un widget n'en garde ni
    n'en rend jamais que des copies. Pour changer les états d'un indicateur,
    on prend son jeu, on le modifie, puis on le lui redonne.

    Construction. Un jeu se construit vide puis se remplit par `append()`,
    ou d'un coup à partir d'une suite d'états. `fromColors()` est la forme
    courte, quand chaque état se résume à une couleur et un nom.

    Jeux courants. Des méthodes statiques créent les jeux les plus
    fréquents, noms traduisibles compris : `onOff()`, `connection()`,
    `trafficLight()`, `severity()`, `activity()` et `passFail()`.

    Jeux calculés. D'autres méthodes statiques calculent les couleurs à
    partir des noms donnés : `gradient()` pour une progression entre deux
    couleurs, `categorical()` pour des catégories sans ordre.

    Exemple :
        >>> states = QStateSet.fromColors(["gray", "green"], ["Off", "On"])
        >>> states.append(QStateSet.State("Fault", "red", blinking=True))
        >>> states.count(), states.names(), states.indexOf("Fault")
        (3, ['Off', 'On', 'Fault'], 2)
        >>> states.state(2).isBlinking(), states == states.copy()
        (True, True)
        >>> [color.name() for color in QStateSet.gradient("#000000", "#ffffff", ["a", "b", "c"]).colors()]
        ['#000000', '#808080', '#ffffff']
    """

    class State:
        """Un état possible d'un indicateur.

        Un état a sept constituants. Seuls les deux premiers sont requis.

        - `name()` : son nom, affiché dans l'infobulle et le résumé.
        - `color()` : sa couleur, celle du repère et de la puce d'infobulle.
        - `isBlinking()` : s'il clignote.
        - `blinkColor()` : la couleur avec laquelle il alterne. Sans elle,
          le widget la calcule en assombrissant `color()`.
        - `icon()` : une image dessinée à la place du repère.
        - `blinkIcon()` : l'image avec laquelle `icon()` alterne. Sans elle,
          le widget assombrit `icon()`.
        - `imageMode()` : la façon dont l'image occupe le repère.

        Un état est une valeur : il se compare par `==` et se copie par
        `copy()`.
        """

        class ImageMode(Enum):
            """Façon dont l'image d'un état occupe le repère.

            Attributs:
                Standalone: L'image est le repère entier, avec sa propre
                    silhouette. La forme et le biseau ne s'appliquent pas.
                    Convient à un pictogramme détouré.
                Framed: L'image remplit la forme de l'indicateur, qui la
                    découpe et reçoit le biseau. Convient à une texture.
            """

            Standalone = 0
            Framed = 1

        def __init__(self, name: str, color: QColor | Qt.GlobalColor | str, blinking: bool = False,
                     blinkColor: QColor | Qt.GlobalColor | str | None = None, icon: QIcon | None = None,
                     blinkIcon: QIcon | None = None, imageMode: ImageMode = ImageMode.Standalone) -> None:
            """Initialise l'état.

            Args:
                name: Nom de l'état.
                color: Couleur de l'état.
                blinking: True si l'état clignote.
                blinkColor: Couleur d'alternance, ou None pour la laisser
                    calculer.
                icon: Image dessinée à la place du repère, ou None.
                blinkIcon: Image d'alternance, ou None.
                imageMode: Façon dont l'image occupe le repère.

            Lève:
                TypeError: Si `name` n'est pas une chaîne.
                ValueError: Si une couleur donnée est invalide.
            """
            self.__name: str = ""
            self.__color: QColor = QColor()
            self.__blinking: bool = False
            self.__blinkColor: QColor = QColor()
            self.__icon: QIcon = QIcon()
            self.__blinkIcon: QIcon = QIcon()
            self.__imageMode: QStateSet.State.ImageMode = imageMode

            self.setName(name)
            self.setColor(color)
            self.setBlinking(blinking)
            self.setBlinkColor(blinkColor)
            self.setIcon(icon)
            self.setBlinkIcon(blinkIcon)

        def name(self) -> str:
            """Renvoie le nom de l'état.

            Retourne:
                Le nom.
            """
            return self.__name

        def setName(self, name: str) -> None:
            """Définit le nom de l'état.

            Args:
                name: Nouveau nom.

            Lève:
                TypeError: Si `name` n'est pas une chaîne.
            """
            _checkNames([name])
            self.__name = name

        def color(self) -> QColor:
            """Renvoie la couleur de l'état.

            Retourne:
                Une copie de la couleur.
            """
            return QColor(self.__color)

        def setColor(self, color: QColor | Qt.GlobalColor | str) -> None:
            """Définit la couleur de l'état.

            Args:
                color: Nouvelle couleur. Copiée.

            Lève:
                ValueError: Si la couleur est invalide.
            """
            self.__color = _validatedColor(color)

        def isBlinking(self) -> bool:
            """Indique si l'état clignote.

            Retourne:
                True s'il clignote.
            """
            return self.__blinking

        def setBlinking(self, blinking: bool) -> None:
            """Fait clignoter l'état ou non.

            Args:
                blinking: True pour qu'il clignote.
            """
            self.__blinking = bool(blinking)

        def blinkColor(self) -> QColor:
            """Renvoie la couleur avec laquelle l'état alterne quand il
            clignote.

            Retourne:
                Une copie de la couleur d'alternance, ou une couleur
                invalide si elle est laissée au calcul du widget.
            """
            return QColor(self.__blinkColor)

        def setBlinkColor(self, color: QColor | Qt.GlobalColor | str | None) -> None:
            """Définit la couleur d'alternance du clignotement.

            Args:
                color: Nouvelle couleur, ou None pour la laisser calculer
                    par le widget (`QStateIndicatorBar.blinkDarkening()`).

            Lève:
                ValueError: Si la couleur donnée est invalide.
            """
            self.__blinkColor = QColor() if color is None else _validatedColor(color)

        def icon(self) -> QIcon:
            """Renvoie l'image dessinée à la place du repère.

            Retourne:
                L'image, ou une image nulle si l'état est dessiné.
            """
            return QIcon(self.__icon)

        def setIcon(self, icon: QIcon | None) -> None:
            """Définit l'image dessinée à la place du repère.

            Args:
                icon: Nouvelle image, ou None pour revenir au dessin.
            """
            self.__icon = QIcon() if icon is None else QIcon(icon)

        def blinkIcon(self) -> QIcon:
            """Renvoie l'image avec laquelle `icon()` alterne quand l'état
            clignote.

            Retourne:
                L'image d'alternance, ou une image nulle si le widget doit
                assombrir `icon()`.
            """
            return QIcon(self.__blinkIcon)

        def setBlinkIcon(self, icon: QIcon | None) -> None:
            """Définit l'image d'alternance du clignotement.

            Args:
                icon: Nouvelle image, ou None pour laisser le widget
                    assombrir `icon()`.
            """
            self.__blinkIcon = QIcon() if icon is None else QIcon(icon)

        def imageMode(self) -> ImageMode:
            """Renvoie la façon dont l'image occupe le repère.

            Retourne:
                Le mode, par défaut `ImageMode.Standalone`. Sans effet sans
                image.
            """
            return self.__imageMode

        def setImageMode(self, mode: ImageMode) -> None:
            """Définit la façon dont l'image occupe le repère.

            Args:
                mode: Nouveau mode.
            """
            self.__imageMode = mode

        def copy(self) -> QStateSet.State:
            """Renvoie une copie indépendante de l'état.

            Retourne:
                Un nouvel état, égal à celui-ci.
            """
            return QStateSet.State(
                self.__name, self.__color, self.__blinking,
                self.__blinkColor if self.__blinkColor.isValid() else None,
                self.__icon, self.__blinkIcon, self.__imageMode,
            )

        @override
        def __eq__(self, other: object) -> bool:
            if not isinstance(other, QStateSet.State):
                return NotImplemented
            return self._identity() == other._identity()

        @override
        def __repr__(self) -> str:
            details = f"{self.__name!r}, {self.__color.name(QColor.NameFormat.HexArgb)!r}"
            if self.__blinking:
                details += ", blinking=True"
            return f"QStateSet.State({details})"

        def _identity(self) -> tuple[object, ...]:
            """Renvoie les valeurs qui font l'égalité de deux états.

            Retourne:
                Les sept constituants. Une image y compte par sa clé de
                cache : deux copies d'une même image sont égales.
            """
            return (
                self.__name, self.__color.rgba(), self.__blinking,
                self.__blinkColor.rgba() if self.__blinkColor.isValid() else None,
                self.__icon.cacheKey(), self.__blinkIcon.cacheKey(), self.__imageMode,
            )

    def __init__(self, states: Iterable[State] = ()) -> None:
        """Initialise le jeu.

        Args:
            states: États du jeu, dans l'ordre. Copiés. Aucun par défaut.

        Lève:
            TypeError: Si un élément n'est pas un `QStateSet.State`.
        """
        self.__states: list[QStateSet.State] = []
        for state in states:
            self.append(state)

    # ================================================================== content

    def count(self) -> int:
        """Renvoie le nombre d'états du jeu.

        Retourne:
            Le nombre d'états.
        """
        return len(self.__states)

    def isEmpty(self) -> bool:
        """Indique si le jeu n'a aucun état.

        Retourne:
            True si le jeu est vide.
        """
        return not self.__states

    def state(self, index: int) -> State:
        """Renvoie un état du jeu.

        Args:
            index: Rang de l'état.

        Retourne:
            Une copie de l'état. La modifier ne change pas le jeu : il faut
            la redonner par `replace()`.

        Lève:
            IndexError: Si `index` ne désigne aucun état du jeu.
        """
        return self._stateAt(index).copy()

    def states(self) -> list[State]:
        """Renvoie tous les états du jeu.

        Retourne:
            Une copie de chaque état, dans l'ordre.
        """
        return [state.copy() for state in self.__states]

    def names(self) -> list[str]:
        """Renvoie le nom de chaque état.

        Retourne:
            Un nom par état, dans l'ordre.
        """
        return [state.name() for state in self.__states]

    def colors(self) -> list[QColor]:
        """Renvoie la couleur de chaque état.

        Retourne:
            Une copie de couleur par état, dans l'ordre.
        """
        return [state.color() for state in self.__states]

    def indexOf(self, name: str) -> int:
        """Renvoie le rang de l'état qui porte un nom.

        Args:
            name: Nom cherché, casse comprise.

        Retourne:
            Le rang du premier état de ce nom, ou -1.
        """
        for index, state in enumerate(self.__states):
            if state.name() == name:
                return index
        return -1

    # ================================================================== edition

    def append(self, state: State) -> None:
        """Ajoute un état à la fin du jeu.

        Args:
            state: État à ajouter. Copié.

        Lève:
            TypeError: Si `state` n'est pas un `QStateSet.State`.
        """
        self.insert(len(self.__states), state)

    def insert(self, index: int, state: State) -> None:
        """Insère un état dans le jeu. Les suivants avancent d'un rang.

        Args:
            index: Rang d'insertion, ramené dans `0..count()`.
            state: État à insérer. Copié.

        Lève:
            TypeError: Si `state` n'est pas un `QStateSet.State`.
        """
        _checkStateType(state)
        self.__states.insert(max(0, min(index, len(self.__states))), state.copy())

    def replace(self, index: int, state: State) -> None:
        """Remplace un état du jeu.

        Args:
            index: Rang de l'état à remplacer.
            state: Nouvel état. Copié.

        Lève:
            IndexError: Si `index` ne désigne aucun état du jeu.
            TypeError: Si `state` n'est pas un `QStateSet.State`.
        """
        self._stateAt(index)
        _checkStateType(state)
        self.__states[index] = state.copy()

    def removeAt(self, index: int) -> None:
        """Retire un état du jeu. Les suivants reculent d'un rang.

        Args:
            index: Rang de l'état à retirer.

        Lève:
            IndexError: Si `index` ne désigne aucun état du jeu.
        """
        self._stateAt(index)
        del self.__states[index]

    def clear(self) -> None:
        """Retire tous les états du jeu."""
        self.__states.clear()

    def copy(self) -> QStateSet:
        """Renvoie une copie indépendante du jeu.

        Retourne:
            Un nouveau jeu, égal à celui-ci.
        """
        return QStateSet(self.__states)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QStateSet):
            return NotImplemented
        return self.__states == other.__states

    @override
    def __repr__(self) -> str:
        return f"QStateSet({self.__states!r})"

    # ============================================================== common sets

    @staticmethod
    def fromColors(colors: Sequence[QColor | Qt.GlobalColor | str], names: Sequence[str]) -> QStateSet:
        """Crée un jeu d'états simples, chacun fait d'une couleur et d'un
        nom.

        Args:
            colors: Couleur de chaque état.
            names: Nom de chaque état, de même longueur que `colors`.

        Retourne:
            Le jeu, d'autant d'états que de noms.

        Lève:
            TypeError: Si `names` est une chaîne seule ou contient autre
                chose que des chaînes.
            ValueError: Si les deux listes n'ont pas la même longueur, ou si
                une couleur est invalide.
        """
        _checkNames(names)
        if len(colors) != len(names):
            raise ValueError(f"colors and names must have the same length ({len(colors)} != {len(names)})")
        return QStateSet(QStateSet.State(name, color) for name, color in zip(names, colors))

    @staticmethod
    def onOff() -> QStateSet:
        """Crée le jeu d'un élément éteint ou allumé.

        Retourne:
            Deux états : Off (gris), On (vert).
        """
        return QStateSet.fromColors([_Gray, _Green], [_translated("Off"), _translated("On")])

    @staticmethod
    def connection() -> QStateSet:
        """Crée le jeu d'une liaison.

        Retourne:
            Deux états : Offline (gris), Online (bleu).
        """
        return QStateSet.fromColors([_Gray, _Blue], [_translated("Offline"), _translated("Online")])

    @staticmethod
    def trafficLight() -> QStateSet:
        """Crée le jeu d'un feu de circulation.

        Retourne:
            Trois états : Stop (rouge), Caution (ambre), Go (vert).
        """
        return QStateSet.fromColors(
            [_Red, _Amber, _Green], [_translated("Stop"), _translated("Caution"), _translated("Go")],
        )

    @staticmethod
    def severity() -> QStateSet:
        """Crée le jeu d'un niveau de gravité croissant.

        Retourne:
            Quatre états : Ok (vert), Warning (ambre), Error (rouge),
            Critical (rouge sombre, clignotant).
        """
        states = QStateSet.fromColors(
            [_Green, _Amber, _Red], [_translated("Ok"), _translated("Warning"), _translated("Error")],
        )
        states.append(QStateSet.State(_translated("Critical"), _DarkRed, blinking=True))
        return states

    @staticmethod
    def activity() -> QStateSet:
        """Crée le jeu d'un appareil qui démarre et s'arrête.

        Retourne:
            Trois états : Stopped (rouge), Starting (ambre), Running (vert).
        """
        return QStateSet.fromColors(
            [_Red, _Amber, _Green], [_translated("Stopped"), _translated("Starting"), _translated("Running")],
        )

    @staticmethod
    def passFail() -> QStateSet:
        """Crée le jeu d'un résultat de vérification.

        Retourne:
            Deux états : Fail (rouge), Pass (vert).
        """
        return QStateSet.fromColors([_Red, _Green], [_translated("Fail"), _translated("Pass")])

    # ============================================================ computed sets

    @staticmethod
    def gradient(start: QColor | Qt.GlobalColor | str, end: QColor | Qt.GlobalColor | str,
                 names: Sequence[str]) -> QStateSet:
        """Crée un jeu dont les couleurs progressent d'une couleur à une
        autre.

        Convient à une grandeur ordonnée : niveau, température, charge. Les
        couleurs sont réparties également en teinte, saturation et clarté
        (HSL). La teinte suit le plus court chemin sur le cercle des
        couleurs. Une extrémité grise n'a pas de teinte : elle prend celle
        de l'autre extrémité.

        Args:
            start: Couleur du premier état.
            end: Couleur du dernier état.
            names: Nom de chaque état. Leur nombre fixe le nombre de
                couleurs. Un seul nom reçoit `start`.

        Retourne:
            Le jeu, d'autant d'états que de noms.

        Lève:
            TypeError: Si `names` est une chaîne seule ou contient autre
                chose que des chaînes.
            ValueError: Si `start` ou `end` est une couleur invalide.
        """
        _checkNames(names)
        first = _validatedColor(start)
        last = _validatedColor(end)
        firstHue, firstSaturation, firstLightness, firstAlpha = first.getHslF()
        lastHue, lastSaturation, lastLightness, lastAlpha = last.getHslF()
        # An achromatic color reports a hue of -1.
        if firstHue < 0:
            firstHue = max(lastHue, 0.0)
        if lastHue < 0:
            lastHue = firstHue
        turn = lastHue - firstHue
        if turn > 0.5:
            turn -= 1.0
        elif turn < -0.5:
            turn += 1.0

        colors: list[QColor] = []
        for position in range(len(names)):
            amount = position / (len(names) - 1) if len(names) > 1 else 0.0
            colors.append(QColor.fromHslF(
                (firstHue + turn * amount) % 1.0,
                firstSaturation + (lastSaturation - firstSaturation) * amount,
                firstLightness + (lastLightness - firstLightness) * amount,
                firstAlpha + (lastAlpha - firstAlpha) * amount,
            ).toRgb())
        # The round trip through HSL may shift a channel by one: both ends stay exactly as given.
        if colors:
            colors[0] = first
        if len(colors) > 1:
            colors[-1] = last
        return QStateSet.fromColors(colors, names)

    @staticmethod
    def categorical(names: Sequence[str], saturation: float = 0.65, lightness: float = 0.45) -> QStateSet:
        """Crée un jeu de couleurs bien distinctes, sans ordre entre elles.

        Convient à des catégories : modes, zones, équipes. Les teintes sont
        réparties également autour du cercle des couleurs, à partir du
        rouge.

        Args:
            names: Nom de chaque état. Leur nombre fixe le nombre de
                couleurs.
            saturation: Saturation HSL commune, de 0.0 à 1.0.
            lightness: Clarté HSL commune, de 0.0 à 1.0.

        Retourne:
            Le jeu, d'autant d'états que de noms.

        Lève:
            TypeError: Si `names` est une chaîne seule ou contient autre
                chose que des chaînes.
            ValueError: Si `saturation` ou `lightness` sort de 0.0 à 1.0.
        """
        _checkNames(names)
        if not (0.0 <= saturation <= 1.0 and 0.0 <= lightness <= 1.0):
            raise ValueError(f"saturation and lightness must be within 0.0 and 1.0 ({saturation}, {lightness})")
        colors = [
            QColor.fromHslF(position / len(names), saturation, lightness).toRgb() for position in range(len(names))
        ]
        return QStateSet.fromColors(colors, names)

    # ========================================================== implementation

    def _stateAt(self, index: int) -> State:
        """Renvoie un état du jeu sans le copier.

        Réservé au widget, qui lit ses propres jeux à chaque peinture.

        Args:
            index: Rang de l'état.

        Retourne:
            L'état lui-même, à ne pas modifier.

        Lève:
            IndexError: Si `index` ne désigne aucun état du jeu.
        """
        if not 0 <= index < len(self.__states):
            raise IndexError(f"state {index} out of range (state count: {len(self.__states)})")
        return self.__states[index]


_Gray: Final[str] = "#9e9e9e"
_Green: Final[str] = "#2e7d32"
_Blue: Final[str] = "#1565c0"
_Amber: Final[str] = "#f9a825"
_Red: Final[str] = "#c62828"
_DarkRed: Final[str] = "#7f0000"

_OutlineLightnessThreshold: Final[float] = 33.0  # Below this L*, a darker outline would not show: lighten instead.
_OutlineContrast: Final[float] = 0.45  # Blend of the outline toward black or white.
_CornerRadius: Final[float] = 0.14  # Corner radius of the rectangular shape, as a fraction of its size.

# Position of the light inside each shape, from its center, as fractions of its half size.
# Toward the top left, but pulled in where the shape is narrow there.
_LightOffsets: Final[dict[QStateIndicatorBar.Shape, tuple[float, float]]] = {
    QStateIndicatorBar.Shape.Circular: (-0.35, -0.35),
    QStateIndicatorBar.Shape.Rectangular: (-0.42, -0.42),
    QStateIndicatorBar.Shape.Diamond: (-0.24, -0.24),
    QStateIndicatorBar.Shape.TriangleUp: (-0.2, 0.2),
    QStateIndicatorBar.Shape.TriangleDown: (-0.3, -0.5),
}

# Characters drawing each shape, for the colored bullets of the tooltip.
_ShapeGlyphs: Final[dict[QStateIndicatorBar.Shape, str]] = {
    QStateIndicatorBar.Shape.Circular: "●",
    QStateIndicatorBar.Shape.Rectangular: "■",
    QStateIndicatorBar.Shape.Diamond: "◆",
    QStateIndicatorBar.Shape.TriangleUp: "▲",
    QStateIndicatorBar.Shape.TriangleDown: "▼",
}


def _validatedColor(color: QColor | Qt.GlobalColor | str) -> QColor:
    """Renvoie une copie validée d'une couleur.

    Args:
        color: Couleur, sous l'une des formes que `QColor` accepte.

    Retourne:
        La couleur, convertie en `QColor`.

    Lève:
        ValueError: Si la couleur est invalide.
    """
    result = QColor(color)
    if not result.isValid():
        raise ValueError(f"invalid color: {color!r}")
    return result


def _lightPoint(shape: QStateIndicatorBar.Shape, area: QRectF) -> QPointF:
    """Renvoie la position de la lumière dans une forme de repère.

    Args:
        shape: Forme du repère.
        area: Carré dans lequel la forme est inscrite.

    Retourne:
        Le point éclairé, vers le haut à gauche et à l'intérieur de la forme.
    """
    offset = _LightOffsets[shape]
    radius = area.width() / 2
    return area.center() + QPointF(offset[0] * radius, offset[1] * radius)


def _checkNames(names: Sequence[str]) -> None:
    """Lève `TypeError` si `names` n'est pas une suite de chaînes.

    Une chaîne seule est refusée : elle se parcourt lettre par lettre, et
    créerait un élément par lettre.

    Args:
        names: Suite à vérifier.
    """
    if isinstance(names, str):
        raise TypeError("expected a sequence of names, got a single string")
    for name in names:
        if not isinstance(name, str):
            raise TypeError(f"expected every name to be a string, got {type(name).__name__}")


def _checkCount(values: Sequence[object], expected: int, what: str) -> None:
    """Lève `ValueError` si une liste n'a pas un élément par indicateur.

    Args:
        values: Liste à vérifier.
        expected: Nombre d'indicateurs.
        what: Nom des éléments, pour le message.
    """
    if len(values) != expected:
        raise ValueError(f"expected {expected} {what}, got {len(values)}")


def _checkStateType(state: QStateSet.State) -> None:
    """Lève `TypeError` si `state` n'est pas un `QStateSet.State`.

    Args:
        state: Objet à vérifier.
    """
    if not isinstance(state, QStateSet.State):
        raise TypeError(f"expected a QStateSet.State, got {type(state).__name__}")


def _checkStateSet(stateSet: QStateSet) -> None:
    """Lève `TypeError` si `stateSet` n'est pas un `QStateSet`.

    Args:
        stateSet: Objet à vérifier.
    """
    if not isinstance(stateSet, QStateSet):
        raise TypeError(f"expected a QStateSet, got {type(stateSet).__name__}")


def _translated(text: str) -> str:
    """Renvoie la traduction d'un nom d'état des jeux courants.

    Args:
        text: Nom en anglais.

    Retourne:
        Le nom traduit, ou `text` sans traduction installée.
    """
    return QCoreApplication.translate("QStateSet", text)


def _checkState(state: int, stateCount: int) -> None:
    """Lève `ValueError` si `state` ne désigne ni un état possible ni
    `NoState`.

    Args:
        state: État à vérifier.
        stateCount: Nombre d'états possibles.
    """
    if not QStateIndicatorBar.NoState <= state < stateCount:
        raise ValueError(f"state {state} out of range (state count: {stateCount})")


def _blended(start: QColor, end: QColor, amount: float) -> QColor:
    """Renvoie le mélange linéaire de deux couleurs.

    Args:
        start: Couleur obtenue pour `amount` à 0.0.
        end: Couleur obtenue pour `amount` à 1.0.
        amount: Proportion de `end`.

    Retourne:
        La couleur mélangée, avec l'alpha de `start`.
    """
    return QColor(
        round(start.red() + (end.red() - start.red()) * amount),
        round(start.green() + (end.green() - start.green()) * amount),
        round(start.blue() + (end.blue() - start.blue()) * amount),
        start.alpha(),
    )


def _outlineColor(color: QColor) -> QColor:
    """Renvoie la couleur du contour d'un repère coloré.

    Args:
        color: Couleur de remplissage du repère.

    Le sens du contraste suit la clarté perçue de la couleur (L* de CIE, de
    0 à 100), et non sa moyenne RVB : l'œil juge un bleu pur bien plus sombre
    qu'un vert pur de même intensité.

    Retourne:
        Une teinte à demi grisée de `color`, assombrie, ou éclaircie si
        `color` est très sombre.
    """
    return _edgeColor(color, _outlineTarget(color), _OutlineContrast)


def _outlineTarget(color: QColor) -> QColor:
    """Renvoie la couleur vers laquelle tirer le contour d'un repère.

    Args:
        color: Couleur de remplissage du repère.

    Retourne:
        Le blanc si `color` est très sombre, sinon le noir.
    """
    return QColor(Qt.GlobalColor.white if _lightness(color) < _OutlineLightnessThreshold else Qt.GlobalColor.black)


def _edgeColor(color: QColor, target: QColor, amount: float) -> QColor:
    """Renvoie une teinte de bord dérivée d'une couleur de remplissage.

    Args:
        color: Couleur de remplissage du repère.
        target: Couleur vers laquelle tirer, le blanc ou le noir.
        amount: Proportion de `target`.

    Retourne:
        La couleur tirée vers `target`, puis à demi grisée.
    """
    shifted = _blended(color, target, amount)
    gray = qGray(shifted.rgb())
    return _blended(shifted, QColor(gray, gray, gray), 0.5)


def _shapePath(shape: QStateIndicatorBar.Shape, area: QRectF) -> QPainterPath:
    """Renvoie le tracé d'une forme de repère.

    Args:
        shape: Forme voulue.
        area: Carré dans lequel inscrire la forme.

    Retourne:
        Le tracé fermé de la forme.
    """
    shapes = QStateIndicatorBar.Shape
    center = area.center()
    path = QPainterPath()
    if shape == shapes.Circular:
        path.addEllipse(area)
    elif shape == shapes.Rectangular:
        radius = area.width() * _CornerRadius
        path.addRoundedRect(area, radius, radius)
    else:
        if shape == shapes.Diamond:
            points = [
                QPointF(center.x(), area.top()), QPointF(area.right(), center.y()),
                QPointF(center.x(), area.bottom()), QPointF(area.left(), center.y()),
            ]
        elif shape == shapes.TriangleUp:
            points = [QPointF(center.x(), area.top()), area.bottomRight(), area.bottomLeft()]
        else:
            points = [area.topLeft(), area.topRight(), QPointF(center.x(), area.bottom())]
        path.addPolygon(QPolygonF(points))
        path.closeSubpath()
    return path


def _lightness(color: QColor) -> float:
    """Renvoie la clarté perçue d'une couleur.

    Args:
        color: Couleur sRGB.

    Retourne:
        La clarté L* de CIE, de 0.0 (noir) à 100.0 (blanc).
    """
    def linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    luminance = (
        0.2126 * linear(color.redF()) + 0.7152 * linear(color.greenF()) + 0.0722 * linear(color.blueF())
    )
    return 116 * luminance ** (1 / 3) - 16 if luminance > 0.008856 else 903.3 * luminance


def _white(alpha: float) -> QColor:
    """Renvoie un blanc translucide.

    Args:
        alpha: Opacité, de 0 à 255.

    Retourne:
        Le blanc d'opacité `alpha`.
    """
    return QColor(255, 255, 255, round(alpha))
