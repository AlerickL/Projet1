"""Notion 2.5 : un champ de flèches, le champ électrique d'un dipôle.

Contexte : le dipôle de la notion 2.4, vu cette fois par son champ
électrique. En chaque point du plan, le champ a une direction et une
intensité. On le représente par une flèche en chaque point d'une grille :
un champ de flèches. PyQtGraph n'a pas de fonction pour ce graphique, comme
le `quiver` de matplotlib (vérifié) : on le construit avec une courbe faite
de segments indépendants (`connect="pairs"`), un seul élément graphique
pour des centaines de flèches. numpy calcule tous les segments d'un coup.

Étapes couvertes : le récapitulatif du graphique et de sa zone visible, les
charges (`TargetItem`), le champ calculé sur une grille, des flèches
proportionnelles (le piège), des hampes de longueur fixe, les pointes
tournées par une matrice de rotation, cinq classes d'intensité, l'intensité
en couleur avec sa légende, le potentiel
en fond avec ses équipotentielles, puis des charges qu'on déplace à la
souris.

Chaque étape est une méthode de `QTopicVectorFieldTab` : elle lit et
modifie directement `self.plotWidget`.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QRectF, Slot
from PySide6.QtWidgets import QWidget

from ..common.doc_urls import numpyDocUrl, numpyPageUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetPlotItem
from .topic_2_4_heatmap import potentialGrid

_PlotDataItemPage = "api_reference/graphicsItems/plotdataitem"
_TargetItemPage = "api_reference/graphicsItems/targetitem"
_ImageItemPage = "api_reference/graphicsItems/imageitem"


def electricField(x: float | np.ndarray, y: float | np.ndarray,
                  charges: list[list[float]]) -> tuple[float | np.ndarray, float | np.ndarray]:
    """Le champ (ex, ey) en (x, y) : la somme des k·q·(x − xᵢ, y − yᵢ)/r³ des charges [x, y, q], avec k = 1.

    `x` et `y` sont des réels, ou des tableaux de réels de même forme ; ex
    et ey ont cette forme.
    """
    ex = 0.0
    ey = 0.0
    for chargeX, chargeY, q in charges:
        dx = x - chargeX
        dy = y - chargeY
        distance = np.maximum(np.hypot(dx, dy), 0.2)
        ex = ex + q * dx / distance ** 3
        ey = ey + q * dy / distance ** 3
    return ex, ey


def pairs(starts: np.ndarray, ends: np.ndarray) -> np.ndarray:
    """Les bouts de n segments, alternés départ, arrivée : `starts` et `ends` de forme (n,), le résultat (2n,)."""
    return np.column_stack((starts, ends)).flatten()


def unitVectors(ex: np.ndarray, ey: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """La direction du champ, en vecteurs de longueur 1 : deux tableaux (ux, uy) de la forme de `ex`.

    `ex` et `ey` sont des tableaux de réels de forme (n,). Un champ nul donne
    une direction nulle, sans division par zéro.
    """
    norm = np.maximum(np.hypot(ex, ey), 1e-9)
    return ex / norm, ey / norm


def shaftSegments(x: np.ndarray, y: np.ndarray, ux: np.ndarray, uy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Les hampes, longues de 0,35 dans la direction (ux, uy).

    Les quatre entrées sont des tableaux de réels de forme (n,) : le pied de
    chaque flèche et la direction du champ en ce point. Rend les x et les y
    des bouts, deux tableaux de forme (2n,), alternés pied, bout.
    """
    tipX = x + 0.35 * ux
    tipY = y + 0.35 * uy
    return pairs(x, tipX), pairs(y, tipY)


def headSegments(x: np.ndarray, y: np.ndarray, ux: np.ndarray, uy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Les deux barbes de chaque pointe : la direction tournée de ±150°, longues de 0,12.

    Mêmes entrées que `shaftSegments`. Rend les x et les y des bouts, deux
    tableaux de forme (4n,), alternés bout de la hampe, bout d'une barbe.
    """
    tipX = x + 0.35 * ux
    tipY = y + 0.35 * uy
    xs = []
    ys = []
    for angle in [150, -150]:
        theta = np.radians(angle)
        barbX = tipX + 0.12 * (np.cos(theta) * ux - np.sin(theta) * uy)
        barbY = tipY + 0.12 * (np.sin(theta) * ux + np.cos(theta) * uy)
        xs.append(pairs(tipX, barbX))
        ys.append(pairs(tipY, barbY))
    return np.concatenate(xs), np.concatenate(ys)


def arrowSegments(x: np.ndarray, y: np.ndarray, ex: np.ndarray, ey: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Hampes et pointes ensemble : les bouts de `shaftSegments`, puis ceux de `headSegments`, de forme (6n,)."""
    ux, uy = unitVectors(ex, ey)
    shaftX, shaftY = shaftSegments(x, y, ux, uy)
    headX, headY = headSegments(x, y, ux, uy)
    return np.concatenate((shaftX, headX)), np.concatenate((shaftY, headY))


def strengthClass(intensity: np.ndarray) -> np.ndarray:
    """La classe d'intensité, de 0 à 4 : le nombre de seuils que l'intensité atteint.

    `intensity` est un tableau de réels ; rend un tableau d'entiers de même forme.
    """
    classes = 0
    for threshold in [0.03, 0.1, 0.3, 1.0]:
        classes = classes + (intensity >= threshold)
    return classes


class QTopicVectorFieldTab(QWidget):
    """Onglet de la notion 2.5 : le champ électrique d'un dipôle, en flèches.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        plotWidget: Le widget du graphique, créé une seule fois.
        charges, chargeItems: Les charges [x, y, q] et leurs cibles.
        x, y, ex, ey: Le pied de chaque flèche et le champ en ce point, des
            tableaux de forme (221,), ou None.
        arrows: La courbe unique des flèches, avant le passage à la couleur.
        arrowGroups: Les cinq courbes de flèches, une par classe d'intensité.
        background, isocurves: Le potentiel en fond et ses équipotentielles.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Champ de vecteurs"
    TabToolTip = "Un champ de flèches : une seule courbe de segments, intensité en couleur, charges mobiles"
    RecommendedPanelWidth = 640
    Objective = (
        "Représenter un champ de vecteurs par une flèche en chaque point d'une grille, le "
        "construire avec une seule courbe de segments, montrer l'intensité par la couleur, puis "
        "déplacer les charges à la souris."
    )
    KeyConcepts = [
        "Un champ de vecteurs associe une direction et une intensité à chaque point du plan.",
        "PyQtGraph n'a pas de champ de flèches tout fait : on le construit.",
        "Une courbe dont les points se relient deux par deux dessine des centaines de segments "
        "indépendants : toutes les flèches en un seul élément graphique.",
        "Des flèches proportionnelles à l'intensité deviennent illisibles. Une longueur fixe "
        "montre la direction, une couleur montre l'intensité.",
        "Une courbe n'a qu'un stylo : une couleur par classe d'intensité demande une courbe par "
        "classe.",
        "Le champ coupe les équipotentielles à angle droit.",
    ]
    KeyApis = [
        "ViewBox.setRange", "TargetItem", "QGraphicsItem.setZValue", "PlotDataItem.setData",
        "ColorMap.map", "IsocurveItem.setData", "ImageItem.setImage", "TargetItem.sigPositionChanged",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.charges: list[list[float]] = []
        self.chargeItems: list[pg.TargetItem] = []
        self.x: np.ndarray | None = None
        self.y: np.ndarray | None = None
        self.ex: np.ndarray | None = None
        self.ey: np.ndarray | None = None
        self.arrows: pg.PlotDataItem | None = None
        self.arrowGroups: list[pg.PlotDataItem] = []
        self.background: pg.ImageItem | None = None
        self.isocurves: list[pg.IsocurveItem] = []

        self.createPlotWidget()

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )
        createSplitterLayout(self, self.plotWidget, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Ramène le graphique à son état d'origine (voir plot_reset.py) et oublie le champ."""
        resetPlotItem(self.plotWidget.getPlotItem())
        self.charges = []
        self.chargeItems = []
        self.x = None
        self.y = None
        self.ex = None
        self.ey = None
        self.arrows = None
        self.arrowGroups = []
        self.background = None
        self.isocurves = []

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidget(self) -> None:
        """Crée le widget du graphique, vide."""
        self.plotWidget = pg.PlotWidget()

    def setUpPlot(self) -> None:
        """Titre, axes, échelle égale et zone visible fixe, d'un seul appel, comme aux notions 1.1 et 1.7."""
        self.plotWidget.setTitle("Champ électrique d'un dipôle")
        self.plotWidget.setLabel("bottom", "x")
        self.plotWidget.setLabel("left", "y")
        self.plotWidget.setAspectLocked(True)
        self.plotWidget.setRange(xRange=(-4.3, 4.3), yRange=(-3.3, 3.3), padding=0)

    def addCharges(self) -> None:
        """Les deux charges [x, y, q] de la notion 2.4, montrées par des cibles."""
        self.charges = [[-1.0, 0.0, 1.0], [1.0, 0.0, -1.0]]
        self.chargeItems = []
        for x, y, q in self.charges:
            if q > 0:
                color = "r"
            else:
                color = "b"
            target = pg.TargetItem(pos=(x, y), size=16, movable=False, pen=pg.mkPen("w", width=2),
                                   brush=pg.mkBrush(color))
            target.setZValue(10)
            self.plotWidget.addItem(target)
            self.chargeItems.append(target)

    def computeField(self) -> None:
        """Le champ sur une grille de 17 × 13 points, une flèche tous les 0,5, en tableaux à une dimension."""
        gridX, gridY = np.meshgrid(np.linspace(-4, 4, 17), np.linspace(-3, 3, 13), indexing="ij")
        self.x = gridX.flatten()
        self.y = gridY.flatten()
        self.ex, self.ey = electricField(self.x, self.y, self.charges)

    def drawProportionalArrows(self) -> None:
        """Des hampes longues de 0,3 fois le champ, toutes dans une seule courbe."""
        xs = pairs(self.x, self.x + 0.3 * self.ex)
        ys = pairs(self.y, self.y + 0.3 * self.ey)
        self.arrows = self.plotWidget.plot(xs, ys, connect="pairs", pen="w")

    def drawFixedShafts(self) -> None:
        """Des hampes de longueur fixe : seule la direction compte."""
        ux, uy = unitVectors(self.ex, self.ey)
        xs, ys = shaftSegments(self.x, self.y, ux, uy)
        self.arrows.setData(xs, ys)

    def drawArrowHeads(self) -> None:
        """Les hampes et leurs pointes, toujours dans la même courbe."""
        xs, ys = arrowSegments(self.x, self.y, self.ex, self.ey)
        self.arrows.setData(xs, ys)

    def drawColoredArrows(self) -> None:
        """Donne à la courbe de chaque classe d'intensité les flèches de cette classe."""
        classes = strengthClass(np.hypot(self.ex, self.ey))
        for classIndex in range(5):
            chosen = classes == classIndex
            xs, ys = arrowSegments(self.x[chosen], self.y[chosen], self.ex[chosen], self.ey[chosen])
            self.arrowGroups[classIndex].setData(xs, ys)

    def colorByStrength(self) -> None:
        """Retire la courbe blanche ; cinq courbes vides et nommées, de violet sombre (faible) à jaune (fort)."""
        self.plotWidget.removeItem(self.arrows)
        self.plotWidget.addLegend(offset=(10, 10), brush=(0, 0, 0, 200))
        colorMap = pg.colormap.get("plasma")
        names = ["moins de 0,03", "0,03 à 0,1", "0,1 à 0,3", "0,3 à 1", "1 et plus"]
        self.arrowGroups = []
        for classIndex in range(5):
            color = colorMap.map(0.15 + 0.85 * classIndex / 4, mode="qcolor")
            curve = self.plotWidget.plot(pen=pg.mkPen(color, width=1.5), connect="pairs", name=names[classIndex])
            self.arrowGroups.append(curve)

    def _classesOnly(self) -> None:
        """Les classes sont une fonction : rien ne change à l'écran à cette étape."""

    def potentialImage(self) -> np.ndarray:
        """Le potentiel de la notion 2.4, sur une grille fine : un tableau de réels de forme (81, 61)."""
        return potentialGrid(np.linspace(-4, 4, 81), np.linspace(-3, 3, 61), self.charges)

    def addBackground(self) -> None:
        """Le potentiel en fond gris, derrière les flèches, et cinq équipotentielles vertes."""
        potential = self.potentialImage()
        self.background = pg.ImageItem(potential, levels=(-5, 5))
        self.background.setRect(QRectF(-4.05, -3.05, 8.1, 6.1))
        self.background.setZValue(-1)
        self.plotWidget.addItem(self.background)
        self.isocurves = []
        for level in [-0.5, -0.2, 0, 0.2, 0.5]:
            isocurve = pg.IsocurveItem(level=level, pen=pg.mkPen((0, 200, 120), width=1))
            isocurve.setData(potential)
            isocurve.setParentItem(self.background)
            self.isocurves.append(isocurve)

    def makeChargesMovable(self) -> None:
        """Rend les cibles mobiles, et relie leur déplacement au slot qui redessine tout."""
        for target in self.chargeItems:
            target.movable = True
            target.sigPositionChanged.connect(self.updateField)

    @Slot()
    def updateField(self) -> None:
        """Relit la position des charges, puis recalcule le champ, les flèches et le fond."""
        for index in range(len(self.charges)):
            position = self.chargeItems[index].pos()
            self.charges[index][0] = position.x()
            self.charges[index][1] = position.y()
        self.ex, self.ey = electricField(self.x, self.y, self.charges)
        self.drawColoredArrows()
        potential = self.potentialImage()
        self.background.setImage(potential, levels=(-5, 5))
        for isocurve in self.isocurves:
            isocurve.setData(potential)

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : graphique, axes, échelle égale, zone visible",
                explanation=(
                    "Rien de nouveau : le graphique, son titre et ses axes (notion 1.1), puis "
                    "l'échelle égale sur les deux axes (notion 1.7). La zone visible est imposée, "
                    "comme à la notion 1.2 : quand les charges bougeront, le cadre restera fixe. "
                    "Avec l'échelle égale, <code>setRange(xRange=…, yRange=…)</code> donne les deux "
                    "intervalles d'un seul appel (notion 1.7) : <code>setXRange()</code> puis "
                    "<code>setYRange()</code> se contrediraient."
                ),
                run=self.setUpPlot,
                codeSource=(self.createPlotWidget, self.setUpPlot),
                references=[("ViewBox.setRange", pyqtgraphDocUrl("api_reference/graphicsItems/viewbox",
                                                                 "ViewBox.setRange"))],
            ),
            QStepWalkthrough.Step(
                title="Les charges",
                explanation=(
                    "Les charges du dipôle de la notion 2.4, des listes <code>[x, y, q]</code>. "
                    "Chacune est montrée par une cible, le <code>pg.TargetItem</code> de la "
                    "notion 1.3 : rouge si la charge est positive, bleue sinon. "
                    "<code>movable=False</code> l'empêche pour l'instant de bouger à la souris. "
                    "<code>self.chargeItems</code> garde les cibles, dans l'ordre des charges."
                    "<br><br>Les éléments graphiques se dessinent par ordre de "
                    "<code>setZValue(valeur)</code> : un élément de valeur plus grande passe "
                    "par-dessus. À valeur égale, le dernier ajouté passe par-dessus. Les cibles "
                    "reçoivent 10 : les flèches, ajoutées ensuite, ne les couvriront pas."
                ),
                run=self.addCharges,
                references=[
                    ("TargetItem", pyqtgraphDocUrl(_TargetItemPage, "TargetItem")),
                    ("QGraphicsItem.setZValue", qtDocUrl("QtWidgets", "QGraphicsItem", "setZValue")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le champ, sur une grille",
                explanation=(
                    "Une charge q crée un champ électrique d'intensité E = k·|q|/r² : E en N/C, "
                    "r la distance à la charge en mètres, k = 8,99 × 10⁹ N·m²/C². Le champ est "
                    "dirigé selon la droite qui joint la charge au point : il s'éloigne d'une "
                    "charge positive et va vers une charge négative. Le champ de plusieurs "
                    "charges est la somme de leurs champs. Comme en 2.4, k = 1."
                    "<br><br>Dans <code>electricField()</code>, (dx, dy) va de la charge au "
                    "point, et sa longueur est r. Diviser par r donne la direction, un vecteur de "
                    "longueur 1. Diviser encore par r² donne l'intensité. D'où la division par "
                    "<code>distance ** 3</code>. La distance est comptée au moins 0,2, comme en "
                    "2.4. La fonction reçoit des tableaux de points, comme "
                    "<code>chargePotential()</code>."
                    "<br><br><code>np.meshgrid()</code> (notion 2.4) construit la grille. Les "
                    "flèches n'ont pas besoin de sa forme en rangées et colonnes : "
                    "<code>flatten()</code> (notion 1.6) la range en tableaux à une dimension. "
                    "<code>self.x</code> et <code>self.y</code> gardent le pied des 221 flèches, "
                    "<code>self.ex</code> et <code>self.ey</code> le champ en chacun."
                    "<br><br><i>Pour l'exemple</i> : 17 × 13 points, une flèche tous les 0,5. Rien "
                    "n'est encore affiché."
                ),
                run=self.computeField,
                codeSource=(electricField, self.computeField),
                references=[("numpy.meshgrid", numpyDocUrl("meshgrid"))],
            ),
            QStepWalkthrough.Step(
                title="Des flèches proportionnelles : le piège",
                explanation=(
                    "PyQtGraph n'a pas de fonction toute faite pour un champ de flèches. On le "
                    "construit avec ce qu'il a : une courbe."
                    "<br><br>Toutes les hampes forment une seule courbe. "
                    "<code>connect=\"pairs\"</code> relie les points deux par deux : le premier "
                    "au deuxième, le troisième au quatrième, et ainsi de suite, sans relier une "
                    "paire à la suivante. <code>pairs(départs, arrivées)</code> range les bouts "
                    "dans cet ordre. <code>np.column_stack()</code> place les deux tableaux côte "
                    "à côte, en deux colonnes ; <code>flatten()</code> les lit rangée par rangée : "
                    "départ, arrivée, départ, arrivée."
                    "<br><br>Première idée : en chaque point, une hampe longue de 0,3 fois le "
                    "champ. Le résultat est illisible : l'intensité varie trop. Près des charges, "
                    "les hampes sont démesurées ; au loin, elles sont minuscules."
                ),
                run=self.drawProportionalArrows,
                codeSource=(pairs, self.drawProportionalArrows),
                references=[
                    ("PlotDataItem", pyqtgraphDocUrl(_PlotDataItemPage, "PlotDataItem")),
                    ("numpy.column_stack", numpyDocUrl("column_stack")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une longueur fixe : shaftSegments()",
                explanation=(
                    "La correction : toutes les hampes mesurent 0,35. "
                    "<code>unitVectors()</code> divise (ex, ey) par sa norme : il reste la "
                    "direction seule, (ux, uy), un vecteur de longueur 1. "
                    "<code>np.maximum(…, 1e-9)</code> évite une division par zéro si le champ est "
                    "nul. <code>shaftSegments()</code> pose au bout de chaque pied une hampe de "
                    "0,35 dans cette direction, pour toutes les flèches à la fois, puis range les "
                    "bouts par <code>pairs()</code>."
                    "<br><br><code>setData()</code> remplace les points de la courbe existante "
                    "(notion 1.3). Il garde les réglages qu'il ne reçoit pas, dont "
                    "<code>connect=\"pairs\"</code> (notion 1.6). Le motif paraît : le champ "
                    "sort de +q, s'incurve et entre dans −q."
                ),
                run=self.drawFixedShafts,
                codeSource=(unitVectors, shaftSegments, self.drawFixedShafts),
                references=[("PlotDataItem.setData", pyqtgraphDocUrl(_PlotDataItemPage, "PlotDataItem.setData"))],
            ),
            QStepWalkthrough.Step(
                title="Les pointes : headSegments()",
                explanation=(
                    "Une pointe, ce sont deux barbes, deux petits segments partis du bout de la "
                    "hampe. Chaque barbe suit la direction du champ, tournée de 150° ou de −150°, "
                    "et mesure 0,12."
                    "<br><br><code>headSegments()</code> retrouve le bout de chaque hampe, comme "
                    "<code>shaftSegments()</code>. Puis, pour chaque angle θ, il tourne la "
                    "direction (ux, uy) par la matrice de rotation de la notion 2.2, "
                    "(cos θ, −sin θ ; sin θ, cos θ), écrite composante par composante : "
                    "(cos θ·ux − sin θ·uy, sin θ·ux + cos θ·uy). Le calcul vaut pour les 221 "
                    "flèches d'un coup. <code>np.radians()</code> convertit l'angle en radians."
                    "<br><br>Chaque tour de boucle ajoute aux listes <code>xs</code> et "
                    "<code>ys</code> les bouts d'une barbe de chaque flèche. "
                    "<code>np.concatenate()</code> met ensuite bout à bout les tableaux d'une "
                    "liste. <code>arrowSegments()</code> calcule la direction une seule fois, "
                    "puis réunit hampes et pointes : toujours un seul élément graphique, pour 221 "
                    "flèches."
                ),
                run=self.drawArrowHeads,
                codeSource=(headSegments, arrowSegments, self.drawArrowHeads),
                references=[("numpy.concatenate", numpyDocUrl("concatenate"))],
            ),
            QStepWalkthrough.Step(
                title="Cinq classes d'intensité",
                explanation=(
                    "Une courbe n'a qu'un stylo, donc qu'une couleur. Pour colorer les flèches "
                    "selon l'intensité du champ, on les répartit en cinq classes, et chaque "
                    "classe aura sa courbe."
                    "<br><br><code>strengthClass()</code> compte les seuils que l'intensité "
                    "atteint : 0 sous 0,03, puis 1, 2, 3, et 4 à partir de 1. Chaque seuil vaut "
                    "environ trois fois le précédent. <code>intensity >= threshold</code> rend un "
                    "tableau de booléens, et un booléen compte 1 pour vrai, 0 pour faux : la "
                    "somme <code>classes</code> compte les seuils atteints, flèche par flèche. "
                    "Rien ne change encore à l'écran."
                ),
                run=self._classesOnly,
                codeSource=(strengthClass,),
                references=[],
            ),
            QStepWalkthrough.Step(
                title="L'intensité en couleur",
                explanation=(
                    "<code>colorByStrength()</code> retire la courbe blanche, puis crée cinq "
                    "courbes vides, une par classe, réglées pour <code>connect=\"pairs\"</code>. "
                    "<code>pg.colormap.get(\"plasma\")</code> est une palette du violet sombre "
                    "au jaune. <code>colorMap.map(valeur, mode=\"qcolor\")</code> reçoit une "
                    "valeur entre 0 et 1 et rend la couleur de la palette à cette place, une "
                    "couleur Qt (<code>QColor</code>) que <code>pg.mkPen()</code> accepte. Les "
                    "valeurs commencent à 0,15 et non à 0 : le bas de la palette, presque noir, "
                    "se verrait mal sur le fond. Chaque courbe porte le nom de sa classe : la "
                    "légende (notion 1.1) dit quelle couleur vaut quelle intensité. Son pinceau, "
                    "<code>brush</code>, lui donne un fond presque opaque : elle restera lisible "
                    "sur le fond gris de l'étape « Le potentiel en fond »."
                    "<br><br>À gauche, les flèches ont disparu avec la courbe blanche : les cinq "
                    "courbes sont encore vides. Seule la légende paraît."
                ),
                run=self.colorByStrength,
                references=[
                    ("ColorMap.map", pyqtgraphDocUrl("api_reference/colormap", "ColorMap.map")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Trier les flèches par classe",
                explanation=(
                    "<code>drawColoredArrows()</code> donne à chaque courbe ses flèches. "
                    "<code>classes == classIndex</code> rend un tableau de booléens, vrai pour "
                    "les flèches de la classe. <code>self.x[chosen]</code> ne garde que les cases "
                    "où il est vrai : c'est l'<b>indexation par booléens</b> de numpy. Une classe "
                    "peut être vide : sa courbe reçoit alors des tableaux vides."
                    "<br><br>Les flèches reparaissent, en couleur. Les jaunes, les plus fortes, "
                    "entourent les charges et l'espace entre elles."
                ),
                run=self.drawColoredArrows,
                references=[
                    ("Indexation par booléens", numpyPageUrl("user/basics.indexing", "boolean-array-indexing")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le potentiel en fond",
                explanation=(
                    "Le potentiel de la notion 2.4, calculé par <code>potentialGrid()</code> sur "
                    "une grille plus fine. La fonction est importée de son fichier, comme en 1.5 : "
                    "<code>from .topic_2_4_heatmap import potentialGrid</code>. Sans palette, l'image est en "
                    "gris : claire pour un potentiel élevé, sombre pour un potentiel bas. Les "
                    "niveaux, de −5 à 5, gardent des gris moyens, sur lesquels les flèches "
                    "restent lisibles. <code>levels=(-5, 5)</code>, passé au constructeur, fait "
                    "comme <code>setLevels()</code> en 2.4. <code>setRect()</code> étire l'image "
                    "comme en 2.4 : le pas de la grille vaut ici 0,1, et le rectangle déborde d'un "
                    "demi-pas, 0,05, de chaque côté, de −4,05 à 4,05 en x et de −3,05 à 3,05 en y. "
                    "<code>setZValue(-1)</code> place l'image derrière les "
                    "flèches."
                    "<br><br>Cinq équipotentielles vertes, enfants de l'image comme en 2.4. "
                    "Cette fois, chacune est créée vide : <code>setData(tableau)</code> lui donne "
                    "ensuite le tableau du potentiel. Le slot de l'étape suivante rappellera ce "
                    "geste."
                    "<br><br>Les flèches coupent les équipotentielles à angle droit, et vont du "
                    "clair vers le sombre : le champ descend le potentiel."
                ),
                run=self.addBackground,
                codeSource=(self.potentialImage, self.addBackground),
                references=[
                    ("ImageItem", pyqtgraphDocUrl(_ImageItemPage, "ImageItem")),
                    ("IsocurveItem.setData", pyqtgraphDocUrl("api_reference/graphicsItems/isocurveitem",
                                                             "IsocurveItem.setData")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : déplacer les charges",
                explanation=(
                    "<code>makeChargesMovable()</code> rend chaque cible mobile, comme celles de "
                    "la notion 2.3 : son attribut <code>movable</code> reçoit <code>True</code>. "
                    "Il relie aussi son signal <code>sigPositionChanged</code> au slot "
                    "<code>updateField()</code>."
                    "<br><br>Le slot relit la position de chaque cible par <code>pos()</code> et "
                    "la recopie dans sa charge. Puis il recalcule le champ, redessine les "
                    "flèches, et redonne le potentiel au fond par <code>setImage()</code> et aux "
                    "équipotentielles par <code>setData()</code>. <code>setImage()</code> "
                    "recalculerait les niveaux de l'image : <code>levels</code> les redonne."
                    "<br><br>Rapprocher les deux charges, puis les éloigner : les "
                    "équipotentielles suivent, et le champ les coupe toujours à angle droit."
                ),
                run=self.makeChargesMovable,
                codeSource=(self.makeChargesMovable, self.updateField),
                references=[
                    ("TargetItem", pyqtgraphDocUrl(_TargetItemPage, "TargetItem")),
                    ("ImageItem.setImage", pyqtgraphDocUrl(_ImageItemPage, "ImageItem.setImage")),
                ],
            ),
        ]
