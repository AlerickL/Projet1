"""Notion 2.1 : polygones et flèches, le polygone des forces.

Contexte : quatre forces s'exercent sur un même point. Mises bout à bout,
chacune partant de la pointe de la précédente, elles tracent un chemin. Si
elles s'équilibrent, ce chemin se referme en un polygone : leur somme est
nulle. Sinon, l'écart entre le départ et l'arrivée est la résultante.

Étapes couvertes : un récapitulatif des notions 1.1 et 1.7 (l'échelle égale
sur les deux axes), une flèche (une courbe et un `ArrowItem`), l'angle d'une
flèche, les quatre forces par une boucle, le chemin bout à bout, le polygone
rempli de Qt (`QPolygonF` et `QGraphicsPolygonItem`), la résultante, une
couleur selon l'équilibre, la mise à jour d'une flèche et du polygone, puis
deux sélecteurs numériques pour chercher l'équilibre soi-même.

Chaque étape est une méthode de `QTopicPolygonsTab` : elle lit et modifie
directement `self.plotWidget`.
"""

from __future__ import annotations

import math

import pyqtgraph as pg
from PySide6.QtCore import QPointF, Qt, Slot
from PySide6.QtGui import QPolygonF
from PySide6.QtWidgets import QGraphicsPolygonItem, QVBoxLayout, QWidget

from ..common.doc_urls import pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetPlotItem

_PlotItemPage = "api_reference/graphicsItems/plotitem"
_ViewBoxPage = "api_reference/graphicsItems/viewbox"
_ArrowItemPage = "api_reference/graphicsItems/arrowitem"


def forceComponents(magnitude: float, angle: float) -> tuple[float, float]:
    """Les composantes (fx, fy) d'une force, à partir de sa norme et de son angle en degrés."""
    theta = math.radians(angle)
    return magnitude * math.cos(theta), magnitude * math.sin(theta)


def tipToTailVertices(forces: list[tuple[str, float, float]]) -> tuple[list[float], list[float]]:
    """Les sommets du chemin bout à bout : l'origine, puis la pointe de chaque force à son tour."""
    xs = [0.0]
    ys = [0.0]
    for name, magnitude, angle in forces:
        fx, fy = forceComponents(magnitude, angle)
        xs.append(xs[-1] + fx)
        ys.append(ys[-1] + fy)
    return xs, ys


class QTopicPolygonsTab(QWidget):
    """Onglet de la notion 2.1 : le polygone des forces.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        plotWidget: Le widget du graphique, créé une seule fois.
        readout: La lecture sous le graphique (outil présenté en 1.5).
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        magnitudeSlider, angleSlider: Les sélecteurs numériques de la force F4.
        forces: Les forces déjà tracées (nom, norme en N, angle en degrés).
        forceLines, forceArrows: La hampe et la pointe de F3 et F4, par nom.
        path, polygon, resultantLine, resultantArrow: Les éléments graphiques
            que la mise à jour de F4 modifie, ou None avant leur étape.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Polygones et flèches"
    TabToolTip = "Le polygone des forces : flèches, polygone rempli, résultante, équilibre"
    RecommendedPanelWidth = 640
    Objective = (
        "Représenter des forces par des flèches, les mettre bout à bout dans un polygone rempli, "
        "tracer leur résultante, puis chercher l'équilibre en réglant une force."
    )
    KeyConcepts = [
        "Une flèche est une courbe de deux points, sa hampe, plus une pointe placée et orientée "
        "à part.",
        "Des forces mises bout à bout referment un polygone si, et seulement si, elles "
        "s'équilibrent.",
        "Un polygone de Qt remplit l'intérieur d'une forme fermée quelconque.",
        "Un élément graphique gardé dans un attribut se déplace, se tourne ou change de forme "
        "sans être recréé.",
    ]
    KeyApis = [
        "ArrowItem", "ArrowItem.setStyle", "QPolygonF",
        "QGraphicsPolygonItem", "QGraphicsPolygonItem.setPolygon",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.forces: list[tuple[str, float, float]] = []
        self.forceLines: dict[str, pg.PlotDataItem] = {}
        self.forceArrows: dict[str, pg.ArrowItem] = {}
        self.path: pg.PlotDataItem | None = None
        self.polygon: QGraphicsPolygonItem | None = None
        self.resultantLine: pg.PlotDataItem | None = None
        self.resultantArrow: pg.ArrowItem | None = None

        self.createPlotWidget()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.magnitudeSlider = self.controls.addSlider("F4, norme", 0, 80, 20, divisor=10, suffix="N")
        self.angleSlider = self.controls.addSlider("F4, angle", 0, 359, 270, suffix="°")

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.plotWidget, 1)
        contentLayout.addWidget(self.readout)
        contentLayout.addWidget(self.controls)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Ramène le graphique et les contrôles à leur état d'origine (voir plot_reset.py)."""
        self.controls.resetControls()
        resetPlotItem(self.plotWidget.getPlotItem())
        self.readout.clear()
        self.forces = []
        self.forceLines = {}
        self.forceArrows = {}
        self.path = None
        self.polygon = None
        self.resultantLine = None
        self.resultantArrow = None

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidget(self) -> None:
        """Crée le widget du graphique, vide."""
        self.plotWidget = pg.PlotWidget()

    def setUpPlot(self) -> None:
        """Titre, axes, grille et légende, comme à la notion 1.1 ; échelle égale, comme à la notion 1.7."""
        self.plotWidget.setTitle("Polygone des forces")
        self.plotWidget.setLabel("bottom", "Fx", units="N")
        self.plotWidget.setLabel("left", "Fy", units="N")
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)
        self.plotWidget.addLegend(offset=(-10, -10))
        self.plotWidget.setAspectLocked(True)

    def addFirstForce(self) -> None:
        """F1 : 5 N vers la droite, une hampe de l'origine à (5, 0) et une pointe en (5, 0)."""
        pen = pg.mkPen((255, 90, 90), width=2)
        self.plotWidget.plot([0, 5], [0, 0], pen=pen, name="F1")
        arrow = pg.ArrowItem(pos=(5, 0), angle=180, headLen=15, pen=pen,
                             brush=pg.mkBrush((255, 90, 90)))
        self.plotWidget.addItem(arrow)
        self.forces = [("F1", 5.0, 0.0)]

    def addSecondForce(self) -> None:
        """F2 : 4 N à 100°, ses composantes calculées par forceComponents()."""
        fx, fy = forceComponents(4.0, 100.0)
        pen = pg.mkPen((90, 200, 255), width=2)
        self.plotWidget.plot([0, fx], [0, fy], pen=pen, name="F2")
        arrow = pg.ArrowItem(pos=(fx, fy), angle=180 - 100.0, headLen=15, pen=pen,
                             brush=pg.mkBrush((90, 200, 255)))
        self.plotWidget.addItem(arrow)
        self.forces.append(("F2", 4.0, 100.0))

    def addOtherForces(self) -> None:
        """F3 et F4 par une boucle ; leur hampe et leur pointe sont gardées par nom."""
        self.forceLines = {}
        self.forceArrows = {}
        for name, magnitude, angle, color in [("F3", 3.5, 200.0, (255, 220, 90)),
                                              ("F4", 2.0, 300.0, (200, 120, 255))]:
            fx, fy = forceComponents(magnitude, angle)
            pen = pg.mkPen(color, width=2)
            self.forceLines[name] = self.plotWidget.plot([0, fx], [0, fy], pen=pen, name=name)
            self.forceArrows[name] = pg.ArrowItem(pos=(fx, fy), angle=180 - angle, headLen=15,
                                                  pen=pen, brush=pg.mkBrush(color))
            self.plotWidget.addItem(self.forceArrows[name])
            self.forces.append((name, magnitude, angle))

    def drawTipToTail(self) -> None:
        """Les quatre forces bout à bout : un chemin en tirets blancs."""
        xs, ys = tipToTailVertices(self.forces)
        dashedPen = pg.mkPen("w", width=2, style=Qt.PenStyle.DashLine)
        self.path = self.plotWidget.plot(xs, ys, pen=dashedPen)

    def fillPolygon(self) -> None:
        """Le chemin refermé en polygone, rempli d'un gris translucide."""
        xs, ys = tipToTailVertices(self.forces)
        points = [QPointF(x, y) for x, y in zip(xs, ys)]
        self.polygon = QGraphicsPolygonItem(QPolygonF(points))
        self.polygon.setPen(pg.mkPen("w", width=1))
        self.polygon.setBrush(pg.mkBrush((150, 150, 150, 100)))
        self.plotWidget.addItem(self.polygon)

    def drawResultant(self) -> None:
        """La résultante, une flèche blanche, de l'origine au dernier sommet."""
        xs, ys = tipToTailVertices(self.forces)
        rx, ry = xs[-1], ys[-1]
        angle = math.degrees(math.atan2(ry, rx))
        pen = pg.mkPen("w", width=3)
        self.resultantLine = self.plotWidget.plot([0, rx], [0, ry], pen=pen, name="Résultante")
        self.resultantArrow = pg.ArrowItem(pos=(rx, ry), angle=180 - angle, headLen=18,
                                           pen=pen, brush=pg.mkBrush("w"))
        self.plotWidget.addItem(self.resultantArrow)

    def colorByEquilibrium(self) -> None:
        """Le polygone en vert si la résultante est sous 0,3 N, en orange sinon ; la lecture le dit."""
        xs, ys = tipToTailVertices(self.forces)
        resultant = math.hypot(xs[-1], ys[-1])
        if resultant < 0.3:
            self.polygon.setBrush(pg.mkBrush((0, 200, 0, 120)))
            verdict = "équilibre atteint"
        else:
            self.polygon.setBrush(pg.mkBrush((230, 140, 0, 120)))
            verdict = "pas d'équilibre"
        text = f"Résultante : {resultant:.2f} N, {verdict}"
        self.readout.setText(text.replace(".", ","))

    def setFourthForce(self, magnitude: float, angle: float) -> None:
        """Donne à F4 une norme et un angle, puis met à jour ce qui en dépend."""
        self.forces[3] = ("F4", magnitude, angle)
        fx, fy = forceComponents(magnitude, angle)
        self.forceLines["F4"].setData([0, fx], [0, fy])
        self.forceArrows["F4"].setPos(fx, fy)
        self.forceArrows["F4"].setStyle(angle=180 - angle)

        xs, ys = tipToTailVertices(self.forces)
        self.path.setData(xs, ys)
        self.polygon.setPolygon(QPolygonF([QPointF(x, y) for x, y in zip(xs, ys)]))

        rx, ry = xs[-1], ys[-1]
        self.resultantLine.setData([0, rx], [0, ry])
        self.resultantArrow.setPos(rx, ry)
        self.resultantArrow.setStyle(angle=180 - math.degrees(math.atan2(ry, rx)))
        self.colorByEquilibrium()

    def turnFourthForce(self) -> None:
        """F4 passe de 300° à 270°, avec la même norme."""
        self.setFourthForce(2.0, 270.0)

    def connectControls(self) -> None:
        """Relie les deux sélecteurs numériques au slot qui met F4 à jour."""
        self.magnitudeSlider.valueChanged.connect(self.updateFourthForce)
        self.angleSlider.valueChanged.connect(self.updateFourthForce)

    @Slot()
    def updateFourthForce(self) -> None:
        """Lit la norme et l'angle de F4, puis met F4 à jour."""
        magnitude = self.magnitudeSlider.value() / 10
        angle = float(self.angleSlider.value())
        self.setFourthForce(magnitude, angle)

    def _exploreEquilibrium(self) -> None:
        """Connecte les sélecteurs numériques, puis les révèle."""
        self.connectControls()
        self.controls.reveal()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : graphique, légende, échelle égale",
                explanation=(
                    "Rien de nouveau : les gestes de la notion 1.1. Les axes portent les "
                    "composantes d'une force, Fx et Fy, en newtons. "
                    "<code>offset=(-10, -10)</code> accroche la légende en bas à droite : un "
                    "nombre négatif compte depuis la droite, ou depuis le bas. Les forces "
                    "laisseront ce coin libre."
                    "<br><br><code>setAspectLocked(True)</code> donne la même échelle aux deux "
                    "axes, comme pour la carte de la notion 1.7 : les angles et les longueurs des "
                    "forces seront justes à l'œil."
                ),
                run=self.setUpPlot,
                codeSource=(self.createPlotWidget, self.setUpPlot),
                references=[
                    ("PlotItem.addLegend", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.addLegend")),
                    ("ViewBox.setAspectLocked", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setAspectLocked")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une force, une flèche",
                explanation=(
                    "Une force se représente par une flèche. Sa <b>norme</b>, sa longueur, est "
                    "l'intensité de la force, en newtons. F1 vaut 5 N et pointe vers la droite : "
                    "elle va de l'origine au point (5, 0)."
                    "<br><br>Une flèche se trace en deux éléments graphiques. La <b>hampe</b>, le "
                    "trait, est une courbe de deux points tracée par <code>plot()</code>. La "
                    "<b>pointe</b> est un <code>pg.ArrowItem</code> :"
                    "<ul>"
                    "<li><code>pos</code> est la position du bout de la pointe, en unités des "
                    "axes ;</li>"
                    "<li><code>headLen</code> est sa longueur, en pixels de l'écran : la pointe "
                    "garde la même taille quand on agrandit le graphique ;</li>"
                    "<li><code>pen</code> et <code>brush</code> donnent son contour et son "
                    "remplissage ;</li>"
                    "<li><code>angle</code> l'oriente. Piège : à <code>angle=0</code>, la pointe "
                    "regarde vers la gauche, et <code>angle=180</code> la retourne vers la "
                    "droite.</li>"
                    "</ul>"
                    "<br><br><code>self.forces</code> garde chaque force tracée : son nom, sa "
                    "norme et son angle en degrés. Le chemin des étapes suivantes en aura besoin."
                    "<br><br><code>plot()</code> reçoit ici deux listes Python, et non des "
                    "tableaux numpy : pour quelques points, une liste convient aussi bien."
                ),
                run=self.addFirstForce,
                references=[
                    ("ArrowItem", pyqtgraphDocUrl(_ArrowItemPage, "ArrowItem")),
                    ("ArrowItem.setStyle", pyqtgraphDocUrl(_ArrowItemPage, "ArrowItem.setStyle")),
                ],
            ),
            QStepWalkthrough.Step(
                title="L'angle d'une flèche",
                explanation=(
                    "F2 vaut 4 N et fait un angle de 100° avec l'axe x, compté dans le sens "
                    "antihoraire. <code>forceComponents()</code> calcule ses composantes : "
                    "fx = F·cos θ et fy = F·sin θ. <code>math.radians()</code> convertit d'abord "
                    "l'angle en radians, l'unité qu'attendent <code>math.cos()</code> et "
                    "<code>math.sin()</code>. La fonction rend le tuple (fx, fy). <code>theta</code> "
                    "est l'angle θ, en radians."
                    "<br><br>Le module <code>math</code> de Python (prérequis) est importé en tête "
                    "du fichier. Il calcule sur un seul nombre, ce qui suffit ici. Sur un tableau "
                    "entier, il faut les fonctions de numpy, comme <code>np.cos()</code>, qui "
                    "agissent sur chaque élément (notion 1.3) : les notions 2.5 et 3.2 les "
                    "emploient pour cette raison."
                    "<br><br>L'angle de la pointe se compte autrement. Un <code>ArrowItem</code> "
                    "se dessine en pixels de l'écran, où l'axe y descend : son angle tourne dans "
                    "le sens horaire, à partir de la gauche. La règle de l'étape précédente se "
                    "généralise : pour une force d'angle θ, la pointe reçoit "
                    "<code>angle=180 - θ</code>. Pour F1, 180 − 0 = 180 ; pour F2, "
                    "180 − 100 = 80."
                ),
                run=self.addSecondForce,
                codeSource=(forceComponents, self.addSecondForce),
                references=[("ArrowItem", pyqtgraphDocUrl(_ArrowItemPage, "ArrowItem"))],
            ),
            QStepWalkthrough.Step(
                title="Les quatre forces, par une boucle",
                explanation=(
                    "F3 et F4 se tracent avec les mêmes gestes, répétés par une boucle. Chaque "
                    "tuple de la liste donne le nom, la norme, l'angle et la couleur d'une force. "
                    "La légende nomme les quatre forces, F1 à F4."
                    "<br><br>Deux dictionnaires, créés au début de la méthode, gardent la "
                    "hampe et la pointe de F3 et de F4, rangées sous leur nom : "
                    "<code>self.forceLines[\"F4\"]</code> retrouvera la hampe de F4 à l'étape "
                    "de la mise à jour."
                ),
                run=self.addOtherForces,
                references=[("PlotItem.plot", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.plot"))],
            ),
            QStepWalkthrough.Step(
                title="Bout à bout",
                explanation=(
                    "Un chemin en tirets s'ajoute : chaque force y part de la pointe de la "
                    "précédente. C'est la méthode du polygone. Les quatre flèches, elles, restent "
                    "en place, depuis l'origine. <code>tipToTailVertices()</code> reçoit la liste des "
                    "forces et rend deux listes, les x et les y des sommets du chemin. Elle part "
                    "de l'origine, puis ajoute les composantes de chaque force au dernier sommet "
                    "(<code>xs[-1]</code>, le dernier élément de la liste)."
                    "<br><br>Le chemin, tracé en tirets par <code>plot()</code>, ne revient pas à "
                    "l'origine : ces quatre forces ne s'équilibrent pas."
                ),
                run=self.drawTipToTail,
                codeSource=(tipToTailVertices, self.drawTipToTail),
                references=[("PlotItem.plot", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.plot"))],
            ),
            QStepWalkthrough.Step(
                title="Un polygone rempli",
                explanation=(
                    "<code>plot()</code> trace un contour, mais ne remplit pas une forme fermée "
                    "quelconque. Qt le fait. Un <code>QPolygonF</code> (module "
                    "<code>PySide6.QtGui</code>) est une liste de sommets, chacun un "
                    "<code>QPointF</code>. La compréhension de liste en fait un <code>QPointF</code> "
                    "par sommet, à partir des paires (x, y) de <code>zip(xs, ys)</code>."
                    "<br><br>Un <code>QGraphicsPolygonItem</code> (module "
                    "<code>PySide6.QtWidgets</code>) est l'élément graphique de Qt qui dessine ce "
                    "polygone. Il se referme de lui-même, du dernier sommet au premier. "
                    "<code>setPen()</code> reçoit son stylo, <code>setBrush()</code> son pinceau : "
                    "<code>pg.mkPen()</code> et <code>pg.mkBrush()</code> rendent un stylo et un "
                    "pinceau de Qt, que Qt accepte tels quels. <code>addItem()</code> l'ajoute au "
                    "graphique comme tout élément graphique."
                    "<br><br>Le côté qui referme le polygone va du dernier sommet à l'origine : "
                    "c'est l'écart que les forces ne compensent pas."
                ),
                run=self.fillPolygon,
                references=[
                    ("QPolygonF", qtDocUrl("QtGui", "QPolygonF")),
                    ("QGraphicsPolygonItem", qtDocUrl("QtWidgets", "QGraphicsPolygonItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La résultante",
                explanation=(
                    "La <b>résultante</b> est la somme des quatre forces : de l'origine au "
                    "dernier sommet du chemin, (rx, ry). Elle se trace comme une cinquième "
                    "flèche, en blanc."
                    "<br><br>Pour orienter sa pointe, il faut son angle. "
                    "<code>math.atan2(ry, rx)</code> reçoit les deux composantes, y d'abord, et "
                    "rend l'angle du vecteur en radians, de −π à π, dans le bon quadrant. "
                    "<code>math.degrees()</code> le convertit en degrés. La pointe reçoit "
                    "<code>180 - angle</code>, comme à l'étape de l'angle d'une flèche."
                ),
                run=self.drawResultant,
                references=[("ArrowItem", pyqtgraphDocUrl(_ArrowItemPage, "ArrowItem"))],
            ),
            QStepWalkthrough.Step(
                title="Une couleur selon l'équilibre",
                explanation=(
                    "<code>math.hypot(rx, ry)</code> rend la norme de la résultante, "
                    "√(rx² + ry²). Sous 0,3 N, on considère les forces en équilibre : le polygone "
                    "devient vert. Sinon, il devient orange. <code>setBrush()</code> change le "
                    "pinceau d'un polygone déjà affiché. Ici, la résultante mesure environ 2,3 N : "
                    "le polygone devient orange."
                    "<br><br>La lecture (notion 1.5) donne la norme et le verdict, avec la "
                    "virgule décimale (notion 1.3). Le titre garde son rôle : il nomme le "
                    "graphique, et ne reçoit jamais un résultat."
                ),
                run=self.colorByEquilibrium,
                references=[("QAbstractGraphicsShapeItem.setBrush", qtDocUrl("QtWidgets", "QAbstractGraphicsShapeItem",
                                                                             "setBrush"))],
            ),
            QStepWalkthrough.Step(
                title="Mettre une flèche à jour",
                explanation=(
                    "F4 tourne de 300° à 270°. Rien n'est recréé : chaque élément graphique, "
                    "gardé dans un attribut, reçoit ses nouvelles valeurs. "
                    "<code>setFourthForce()</code> fait tout le travail."
                    "<br><br>La hampe de F4 reçoit ses deux nouveaux points par "
                    "<code>setData()</code> (notion 1.3). Sa pointe se déplace par "
                    "<code>setPos(x, y)</code> et tourne par <code>setStyle(angle=…)</code>, qui "
                    "ne change que l'angle et garde la longueur, le stylo et le pinceau. "
                    "<code>setPolygon()</code> donne au polygone ses nouveaux sommets. La "
                    "résultante suit de la même façon, et <code>colorByEquilibrium()</code> "
                    "refait la couleur et la lecture."
                    "<br><br>Tournée vers le bas, F4 compense mieux F2, qui monte : la résultante "
                    "raccourcit."
                ),
                run=self.turnFourthForce,
                codeSource=(self.setFourthForce, self.turnFourthForce),
                references=[
                    ("ArrowItem.setStyle", pyqtgraphDocUrl(_ArrowItemPage, "ArrowItem.setStyle")),
                    ("QGraphicsPolygonItem.setPolygon", qtDocUrl("QtWidgets", "QGraphicsPolygonItem",
                                                                 "setPolygon")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : trouver l'équilibre",
                explanation=(
                    "Deux sélecteurs numériques paraissent sous le graphique. "
                    "<code>magnitudeSlider</code> règle la norme de F4 : il va de 0 à 80, et la "
                    "valeur lue divisée par 10 donne la norme, de 0 à 8 N par pas de 0,1 N. Il "
                    "part de 20, soit 2 N. <code>angleSlider</code> règle l'angle de F4, de 0 à "
                    "359°, et part de 270°."
                    "<br><br><code>connectControls()</code> relie le signal "
                    "<code>valueChanged</code> des deux sélecteurs au slot "
                    "<code>updateFourthForce()</code>. Celui-ci lit la norme et l'angle, puis appelle "
                    "<code>setFourthForce()</code> de l'étape précédente."
                    "<br><br>Chercher la norme et l'angle qui referment le polygone : il devient "
                    "vert."
                ),
                run=self._exploreEquilibrium,
                codeSource=(self.connectControls, self.updateFourthForce),
                references=[("QSlider", qtDocUrl("QtWidgets", "QSlider"))],
            ),
        ]
