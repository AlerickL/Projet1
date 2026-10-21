"""Notion 2.2 : transformer un élément graphique, les pales d'une éolienne.

Contexte : une éolienne a plusieurs pales identiques, tournées autour du
moyeu. On dessine une seule pale, puis on la copie et on la tourne, avec
les outils de transformation de Qt, sans jamais recalculer ses sommets à la
main. La matrice de rotation, connue du cours d'algèbre linéaire, est
nommée : c'est elle que Qt applique.

Étapes couvertes : un récapitulatif (graphique, échelle égale, un polygone
pour le mât), une pale de référence, `setRotation()`, `setScale()`,
`setPos()`, trois pales par une boucle, la matrice derrière ces outils
(`QTransform` appliqué par `setTransform()`), un point tourné par
`QTransform.map()`, le retrait d'éléments précis (`removeItem`), une
annotation (`TextItem`), puis trois sélecteurs numériques qui règlent le
rotor.

Chaque étape est une méthode de `QTopicTransformationsTab` : elle lit et
modifie directement `self.plotWidget`.
"""

from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtCore import QPointF, Slot
from PySide6.QtGui import QPolygonF, QTransform
from PySide6.QtWidgets import QGraphicsPolygonItem, QVBoxLayout, QWidget

from ..common.doc_urls import pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetPlotItem

_PlotItemPage = "api_reference/graphicsItems/plotitem"


def createBlade() -> QGraphicsPolygonItem:
    """Une pale de 40 m, de son pied à l'origine jusqu'à son bout en (40, 0)."""
    points = [QPointF(0, 0), QPointF(5, 3.5), QPointF(40, 1.5), QPointF(40, -0.5), QPointF(5, -1.5)]
    blade = QGraphicsPolygonItem(QPolygonF(points))
    blade.setPen(pg.mkPen("w", width=1))
    blade.setBrush(pg.mkBrush((200, 200, 210)))
    return blade


class QTopicTransformationsTab(QWidget):
    """Onglet de la notion 2.2 : les pales d'une éolienne, tournées, agrandies et déplacées.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        plotWidget: Le widget du graphique, créé une seule fois.
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        angleSlider, sizeSlider, countSlider: Les sélecteurs numériques du rotor.
        referenceBlade, matrixBlade, pointBefore, pointAfter: Les éléments de
            démonstration, ou None avant leur étape.
        blades: Les pales du rotor, dans l'ordre.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Transformations"
    TabToolTip = "Tourner, agrandir et déplacer un élément graphique ; la matrice derrière"
    RecommendedPanelWidth = 640
    Objective = (
        "Tourner, agrandir et déplacer un élément graphique avec les outils de Qt, reconnaître "
        "la matrice de rotation qu'ils appliquent, et retirer un élément précis du graphique."
    )
    KeyConcepts = [
        "Un élément graphique tourne et s'agrandit autour de sa propre origine, puis sa position "
        "le place dans le graphique.",
        "Dans une zone visible, où l'axe y monte, un angle positif tourne dans le sens "
        "antihoraire.",
        "Derrière ces outils se trouve une matrice de transformation : Qt la construit et "
        "l'applique pour nous.",
        "La même matrice tourne aussi un point isolé, sans calcul à la main.",
        "Retirer un élément précis laisse le reste du graphique intact.",
    ]
    KeyApis = [
        "QGraphicsItem.setRotation", "QGraphicsItem.setScale", "QGraphicsItem.setPos", "QTransform",
        "QGraphicsItem.setTransform", "QTransform.map", "PlotItem.removeItem", "TextItem",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.referenceBlade: QGraphicsPolygonItem | None = None
        self.matrixBlade: QGraphicsPolygonItem | None = None
        self.pointBefore: pg.PlotDataItem | None = None
        self.pointAfter: pg.PlotDataItem | None = None
        self.blades: list[QGraphicsPolygonItem] = []

        self.createPlotWidget()
        self.controls = QControlPanel()
        self.angleSlider = self.controls.addSlider("Angle du rotor", 0, 359, 0, suffix="°")
        self.sizeSlider = self.controls.addSlider("Facteur d'échelle", 5, 15, 10, divisor=10)
        self.countSlider = self.controls.addSlider("Nombre de pales", 2, 6, 3)

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.plotWidget, 1)
        contentLayout.addWidget(self.controls)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Ramène le graphique et les contrôles à leur état d'origine (voir plot_reset.py)."""
        self.controls.resetControls()
        resetPlotItem(self.plotWidget.getPlotItem())
        self.referenceBlade = None
        self.matrixBlade = None
        self.pointBefore = None
        self.pointAfter = None
        self.blades = []

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidget(self) -> None:
        """Crée le widget du graphique, vide."""
        self.plotWidget = pg.PlotWidget()

    def setUpPlot(self) -> None:
        """Titre, axes, grille, zone visible imposée, échelle égale, et le mât, un polygone."""
        self.plotWidget.setTitle("Une éolienne : une pale, copiée et tournée")
        self.plotWidget.setLabel("bottom", "x", units="m")
        self.plotWidget.setLabel("left", "y", units="m")
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)
        self.plotWidget.setXRange(-110, 70, padding=0)
        self.plotWidget.setYRange(-80, 70, padding=0)
        self.plotWidget.setAspectLocked(True)
        mast = QGraphicsPolygonItem(QPolygonF([QPointF(-3, -70), QPointF(3, -70),
                                               QPointF(1.5, 0), QPointF(-1.5, 0)]))
        mast.setPen(pg.mkPen("w", width=1))
        mast.setBrush(pg.mkBrush((110, 110, 120)))
        self.plotWidget.addItem(mast)

    def addReferenceBlade(self) -> None:
        """La pale de référence, en orangé, couchée vers la droite depuis le moyeu."""
        self.referenceBlade = createBlade()
        self.referenceBlade.setBrush(pg.mkBrush((240, 170, 0)))
        self.plotWidget.addItem(self.referenceBlade)

    def rotateReferenceBlade(self) -> None:
        """La pale tourne de 30° autour de son origine, le moyeu."""
        self.referenceBlade.setRotation(30)

    def scaleReferenceBlade(self) -> None:
        """La pale s'agrandit d'un facteur 1,5 autour de la même origine."""
        self.referenceBlade.setScale(1.5)

    def moveReferenceBlade(self) -> None:
        """La pale, tournée et agrandie, est placée à l'écart du rotor."""
        self.referenceBlade.setPos(-100, -60)

    def addRotor(self) -> None:
        """Trois pales au moyeu, tournées de 0°, 120° et 240°."""
        self.blades = []
        for angle in [0, 120, 240]:
            blade = createBlade()
            blade.setRotation(angle)
            self.plotWidget.addItem(blade)
            self.blades.append(blade)

    def addMatrixBlade(self) -> None:
        """Une quatrième pale, en contour cyan, tournée par une matrice de rotation de 120°."""
        transform = QTransform().rotate(120)
        self.matrixBlade = createBlade()
        self.matrixBlade.setBrush(pg.mkBrush(None))
        self.matrixBlade.setPen(pg.mkPen("c", width=3))
        self.matrixBlade.setTransform(transform)
        self.plotWidget.addItem(self.matrixBlade)

    def rotatePoint(self) -> None:
        """Le point (30, 0), en jaune, et son image par la rotation, en cyan."""
        transform = QTransform().rotate(120)
        x, y = transform.map(30.0, 0.0)
        self.pointBefore = self.plotWidget.plot([30.0], [0.0], pen=None, symbol="o",
                                                symbolSize=12, symbolBrush="y")
        self.pointAfter = self.plotWidget.plot([x], [y], pen=None, symbol="o",
                                               symbolSize=12, symbolBrush="c")

    def removeDemonstration(self) -> None:
        """Retire la pale de référence et les éléments des deux étapes précédentes."""
        for item in [self.referenceBlade, self.matrixBlade, self.pointBefore, self.pointAfter]:
            self.plotWidget.removeItem(item)

    def annotateMast(self) -> None:
        """Un texte centré sous le pied du mât."""
        label = pg.TextItem("Mât : 70 m", color="w", anchor=(0.5, 0))
        label.setPos(0, -70)
        self.plotWidget.addItem(label)

    def connectControls(self) -> None:
        """Relie les trois sélecteurs numériques au slot qui reconstruit le rotor."""
        self.angleSlider.valueChanged.connect(self.updateRotor)
        self.sizeSlider.valueChanged.connect(self.updateRotor)
        self.countSlider.valueChanged.connect(self.updateRotor)

    @Slot()
    def updateRotor(self) -> None:
        """Retire les pales, puis en crée de nouvelles selon les trois sélecteurs."""
        angle = self.angleSlider.value()
        size = self.sizeSlider.value() / 10
        count = self.countSlider.value()
        for blade in self.blades:
            self.plotWidget.removeItem(blade)
        self.blades = []
        for index in range(count):
            blade = createBlade()
            blade.setRotation(angle + index * 360 / count)
            blade.setScale(size)
            self.plotWidget.addItem(blade)
            self.blades.append(blade)

    def _exploreRotor(self) -> None:
        """Connecte les sélecteurs numériques, puis les révèle."""
        self.connectControls()
        self.controls.reveal()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        graphicsItemUrl = qtDocUrl("QtWidgets", "QGraphicsItem")
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : graphique, échelle égale, un polygone",
                explanation=(
                    "Rien de nouveau : les gestes de la notion 1.1 pour le graphique, ceux de la "
                    "notion 1.2 pour la zone visible, et ceux de la notion 1.7 pour l'échelle "
                    "égale et le polygone. La zone visible est imposée avant de verrouiller les "
                    "proportions : elle couvre au moins ces deux plages, élargie dans un sens "
                    "pour garder l'échelle égale. Elle ne bougera plus quand les pales "
                    "changeront.<br><br>Le mât de l'éolienne est "
                    "un <code>QGraphicsPolygonItem</code> de quatre sommets, haut de 70 m. Son "
                    "sommet, le <b>moyeu</b>, est à l'origine : les pales tourneront autour de "
                    "lui."
                ),
                run=self.setUpPlot,
                codeSource=(self.createPlotWidget, self.setUpPlot),
                references=[
                    ("ViewBox.setAspectLocked", pyqtgraphDocUrl("api_reference/graphicsItems/viewbox",
                                                                "ViewBox.setAspectLocked")),
                    ("QGraphicsPolygonItem", qtDocUrl("QtWidgets", "QGraphicsPolygonItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une forme de référence : une pale",
                explanation=(
                    "<code>createBlade()</code> crée une pale de 40 m, un polygone de cinq "
                    "sommets, et la rend. Ses sommets sont donnés autour de l'origine : le pied de "
                    "la pale est en (0, 0), son bout en (40, 0). Cette origine est celle de "
                    "l'élément graphique lui-même. Tant qu'on ne le déplace pas, elle se confond "
                    "avec l'origine du graphique, le moyeu."
                    "<br><br>Cette pale de référence est peinte en orangé par "
                    "<code>setBrush()</code>. Les trois étapes suivantes la transforment sans "
                    "toucher à ses sommets."
                ),
                run=self.addReferenceBlade,
                codeSource=(createBlade, self.addReferenceBlade),
                references=[("QGraphicsPolygonItem", qtDocUrl("QtWidgets", "QGraphicsPolygonItem"))],
            ),
            QStepWalkthrough.Step(
                title="Tourner : setRotation()",
                explanation=(
                    "Tout élément graphique hérite de <code>QGraphicsItem</code>, la classe de "
                    "base de Qt. <code>setRotation(angle)</code> reçoit un angle en degrés et "
                    "tourne l'élément autour de sa propre origine. Ici, la pale pivote de 30° "
                    "autour du moyeu."
                    "<br><br>Dans une zone visible, l'axe y monte : un angle positif tourne donc "
                    "dans le sens antihoraire, comme en mathématiques. Le bout de la pale monte : "
                    "il passe de (40, 0) à environ (34,6 ; 20), en haut à droite du moyeu."
                    "<br><br>La pointe de flèche de la notion 2.1 tournait dans l'autre sens : un "
                    "<code>ArrowItem</code> se dessine en pixels de l'écran, où y descend. La "
                    "pale, elle, est dessinée dans le repère des axes, où y monte."
                ),
                run=self.rotateReferenceBlade,
                references=[("QGraphicsItem.setRotation", qtDocUrl("QtWidgets", "QGraphicsItem", "setRotation"))],
            ),
            QStepWalkthrough.Step(
                title="Agrandir : setScale()",
                explanation=(
                    "<code>setScale(facteur)</code> multiplie toutes les distances à l'origine de "
                    "l'élément par ce facteur, dans les deux directions. À 1,5, la pale passe de "
                    "40 m à 60 m. Elle s'agrandit autour de la même origine : son pied reste au "
                    "moyeu et elle garde son angle de 30°. Un facteur plus petit que 1 la "
                    "réduirait."
                ),
                run=self.scaleReferenceBlade,
                references=[("QGraphicsItem.setScale", qtDocUrl("QtWidgets", "QGraphicsItem", "setScale"))],
            ),
            QStepWalkthrough.Step(
                title="Déplacer : setPos()",
                explanation=(
                    "<code>setPos(x, y)</code> place l'origine de l'élément au point (x, y) du "
                    "graphique, en unités des axes. C'est le geste de la cible de la notion 1.3. "
                    "La pale part maintenant de (−100, −60), à l'écart du moyeu."
                    "<br><br>Ces trois réglages sont indépendants : le résultat ne dépend pas de "
                    "l'ordre des trois appels. Qt tourne et agrandit toujours l'élément autour de "
                    "sa propre origine, puis le place à sa position. "
                    "La pale déplacée garde donc ses 30° et ses 60 m."
                ),
                run=self.moveReferenceBlade,
                references=[("QGraphicsItem.setPos", qtDocUrl("QtWidgets", "QGraphicsItem", "setPos"))],
            ),
            QStepWalkthrough.Step(
                title="Trois pales, par une boucle",
                explanation=(
                    "Le rotor : trois pales neuves, créées par <code>createBlade()</code> et "
                    "tournées de 0°, 120° et 240°, un tiers de tour chacune. Elles restent au "
                    "moyeu, sans <code>setPos()</code>. <code>self.blades</code> garde les pales "
                    "dans une liste, pour l'étape « À vous »."
                    "<br><br>À gauche, la pale de référence orangée reste à l'écart, telle que "
                    "les trois étapes précédentes l'ont laissée."
                ),
                run=self.addRotor,
                references=[("QGraphicsItem.setRotation", qtDocUrl("QtWidgets", "QGraphicsItem", "setRotation"))],
            ),
            QStepWalkthrough.Step(
                title="Derrière ces outils : une matrice",
                explanation=(
                    "Qt tourne un élément par une matrice de transformation. Un "
                    "<code>QTransform</code>, du module <code>PySide6.QtGui</code>, est une telle "
                    "matrice. <code>QTransform()</code> crée la matrice identité, qui ne change "
                    "rien. <code>rotate(120)</code> en fait la matrice de rotation du cours "
                    "d'algèbre linéaire : (cos θ, −sin θ ; sin θ, cos θ), pour θ = 120°, et rend "
                    "ce même <code>QTransform</code>."
                    "<br><br><code>setTransform(transform)</code> applique la matrice à un "
                    "élément. Ici, une quatrième pale, en contour cyan et sans remplissage "
                    "(<code>pg.mkBrush(None)</code>). À gauche, elle recouvre exactement la pale "
                    "à 120° : <code>setTransform()</code> avec cette matrice a le même effet que "
                    "<code>setRotation(120)</code>."
                ),
                run=self.addMatrixBlade,
                references=[
                    ("QTransform", qtDocUrl("QtGui", "QTransform")),
                    ("QTransform.rotate", qtDocUrl("QtGui", "QTransform", "rotate")),
                    ("QGraphicsItem.setTransform", qtDocUrl("QtWidgets", "QGraphicsItem", "setTransform")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Tourner un point",
                explanation=(
                    "La même matrice tourne aussi un point isolé. <code>transform.map(x, y)</code> "
                    "reçoit les coordonnées d'un point et rend le tuple (x, y) du point "
                    "transformé. Aucun cosinus ni sinus à écrire."
                    "<br><br>À gauche, le point (30, 0), en jaune, est sur la pale à 0°. Son "
                    "image, en cyan, est (−15 ; 26) : à la même distance du moyeu, sur la pale à "
                    "120°. La notion 2.3 fera le même calcul pour tout un tableau de points "
                    "d'un coup, avec numpy."
                ),
                run=self.rotatePoint,
                references=[("QTransform.map", qtDocUrl("QtGui", "QTransform", "map"))],
            ),
            QStepWalkthrough.Step(
                title="Retirer un élément : removeItem() contre clear()",
                explanation=(
                    "<code>removeItem(élément)</code> retire du graphique cet élément précis, et "
                    "rien d'autre. Une boucle retire ici la pale de référence, la pale en contour "
                    "et les deux points : il ne reste que le mât et le rotor."
                    "<br><br><code>clear()</code>, lui, retire tous les éléments d'un coup : le "
                    "mât et le rotor seraient partis aussi."
                ),
                run=self.removeDemonstration,
                references=[
                    ("PlotItem.removeItem", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.removeItem")),
                    ("PlotItem.clear", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.clear")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Annoter : l'ancre d'un texte",
                explanation=(
                    "<code>pg.TextItem</code>, l'étiquette de la notion 1.3, sert aussi à annoter "
                    "une figure. Son texte se donne au constructeur. Il se place par "
                    "<code>setPos(x, y)</code>, en unités des axes, mais sa taille reste en "
                    "pixels de l'écran."
                    "<br><br>Nouveau : l'<b>ancre</b> (<code>anchor</code>) choisit le point du "
                    "texte qui se pose sur cette position, en fractions de sa largeur et de sa "
                    "hauteur. (0, 0), la valeur par défaut, est son coin en haut à gauche, comme "
                    "en 1.3 ; (1, 1) est son coin en bas à droite. (0,5 ; 0) est le milieu de son "
                    "bord du haut : le texte est centré sous le point."
                    "<br><br><i>Pour l'exemple</i> : le point est (0, −70), le pied du mât. Les pales, "
                    "longues de 60 m au plus, ne couvriront jamais le texte."
                ),
                run=self.annotateMast,
                references=[("TextItem", pyqtgraphDocUrl("api_reference/graphicsItems/textitem", "TextItem"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : l'angle, la taille et le nombre de pales",
                explanation=(
                    "Trois sélecteurs numériques paraissent sous le graphique. "
                    "<code>angleSlider</code> tourne tout le rotor, de 0 à 359°, et part de 0°. "
                    "<code>sizeSlider</code> va de 5 à 15 : divisé par 10, il donne le facteur "
                    "d'échelle des pales, de 0,5 à 1,5, et part de 1. <code>countSlider</code> "
                    "donne le nombre de pales, de 2 à 6, et part de 3."
                    "<br><br><code>connectControls()</code> relie leur signal "
                    "<code>valueChanged</code> au slot <code>updateRotor()</code>. Le nombre de "
                    "pales peut changer : le slot retire donc les anciennes pales par "
                    "<code>removeItem()</code>, puis en crée de nouvelles. Chacune est tournée "
                    "de <code>360 / count</code> degrés de plus que la précédente, et agrandie "
                    "par <code>setScale()</code>."
                    "<br><br>Faire tourner le rotor : chaque pale pivote autour du moyeu, son "
                    "origine. Agrandir les pales : leur pied reste au moyeu."
                ),
                run=self._exploreRotor,
                codeSource=(self.connectControls, self.updateRotor),
                references=[("QGraphicsItem", graphicsItemUrl)],
            ),
        ]
