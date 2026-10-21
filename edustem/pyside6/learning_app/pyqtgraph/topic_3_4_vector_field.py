"""Notion 3.4 : un champ de vecteurs en 3D, le champ magnétique d'un fil.

Contexte : un long fil vertical, sur l'axe z, est parcouru par un courant I.
Son champ magnétique tourne autour du fil et faiblit en 1/r. On y ajoute un
champ extérieur uniforme, vertical. La somme des deux s'enroule autour du
fil en montant : un champ qu'aucune coupe plane ne montre en entier. Les
unités sont réduites (μ₀/2π = 1).

PyQtGraph n'a pas de champ de flèches 3D. Comme à la notion 2.5, toutes les
hampes forment un seul élément graphique : un `GLLinePlotItem` en mode
« lines », qui relie les points deux par deux. En 3D, il accepte une
couleur par sommet.

Étapes couvertes : un récapitulatif de la scène (notion 3.1), le fil, le
la grille 3D, le champ du fil, les hampes en un seul élément, la couleur
selon l'intensité, les pointes, puis deux sélecteurs numériques pour le
courant et le champ extérieur.

Chaque étape est une méthode de `QTopicVectorField3DTab` : elle lit et
modifie directement `self.view`.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetGLView
from .topic_3_1_scene import createView, nameAxes

_GLPage = "api_reference/3dgraphics"


def gridPoints() -> np.ndarray:
    """Les points d'une grille de 7 × 7 × 5, sauf ceux du fil.

    Rend un tableau de réels de forme (240, 3) : une rangée (x, y, z) par point.
    """
    gridX, gridY, gridZ = np.meshgrid(np.linspace(-3, 3, 7), np.linspace(-3, 3, 7), np.linspace(-3, 3, 5),
                                      indexing="ij")
    points = np.column_stack((gridX.flatten(), gridY.flatten(), gridZ.flatten()))
    awayFromWire = np.hypot(points[:, 0], points[:, 1]) > 0.5
    return points[awayFromWire, :]


def fieldVectors(points: np.ndarray, current: float, external: float) -> np.ndarray:
    """Le champ en chaque point : celui du fil, I/r autour de l'axe z, plus le champ vertical.

    `points` est de forme (n, 3). Rend un tableau de réels de même forme :
    une rangée (bx, by, bz) par point.
    """
    x = points[:, 0]
    y = points[:, 1]
    r2 = np.maximum(x ** 2 + y ** 2, 0.25)
    return np.column_stack((-current * y / r2, current * x / r2, np.full(x.shape, external)))


def vectorLengths(vectors: np.ndarray) -> np.ndarray:
    """La longueur de chaque vecteur, √(bx² + by² + bz²).

    `vectors` est de forme (n, 3) ; rend un tableau de réels de forme (n,).
    """
    return np.sqrt(vectors[:, 0] ** 2 + vectors[:, 1] ** 2 + vectors[:, 2] ** 2)


def shaftSegments3D(points: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    """Les deux bouts de chaque hampe, longue de 0,6 dans la direction du champ.

    `points` et `vectors` sont de forme (n, 3). Rend un tableau de réels de
    forme (2n, 3) : le pied d'une hampe dans une rangée paire, son bout dans
    la rangée suivante.
    """
    lengths = np.maximum(vectorLengths(vectors), 1e-9)
    tips = np.zeros(points.shape)
    for column in range(3):
        tips[:, column] = points[:, column] + 0.6 * vectors[:, column] / lengths
    segments = np.zeros((2 * points.shape[0], 3))
    segments[0::2, :] = points
    segments[1::2, :] = tips
    return segments


def strengthColors(vectors: np.ndarray) -> np.ndarray:
    """Une couleur par flèche, de 0 à 1 : la palette plasma, de sombre (faible) à jaune (1,2 et plus).

    `vectors` est de forme (n, 3) ; rend un tableau de réels de forme (n, 4).
    """
    fractions = 0.15 + 0.85 * np.minimum(1.0, vectorLengths(vectors) / 1.2)
    return pg.colormap.get("plasma").map(fractions, mode="float")


class QTopicVectorField3DTab(QWidget):
    """Onglet de la notion 3.4 : le champ magnétique d'un fil, en flèches 3D.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        viewContainer, titleLabel, view: La vue 3D et son titre, créés une
            seule fois par `createView()` (notion 3.1).
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        currentSlider, externalSlider: Les sélecteurs numériques du champ.
        points, vectors: La grille et le champ en chaque point, ou None.
        shafts, tips: Les hampes et les pointes, ou None avant leur étape.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Champ de vecteurs 3D"
    TabToolTip = "Un champ de flèches 3D : hampes en un seul élément, une couleur par sommet, pointes"
    RecommendedPanelWidth = 640
    Objective = (
        "Représenter un champ de vecteurs dans l'espace : le champ magnétique d'un fil, plus un "
        "champ extérieur. Toutes les flèches en un seul élément graphique, colorées selon leur "
        "intensité, puis réglées par le courant et le champ extérieur."
    )
    KeyConcepts = [
        "Un champ de vecteurs 3D associe un vecteur (bx, by, bz) à chaque point de l'espace.",
        "Une ligne 3D en mode « lines » trace des segments indépendants : toutes les hampes "
        "d'un coup, comme en 2D.",
        "En 3D, une ligne accepte une couleur par sommet.",
        "Le champ du fil seul tourne en cercles. Le champ vertical ajouté l'enroule en montant.",
    ]
    KeyApis = ["GLLinePlotItem", "numpy.repeat", "ColorMap.map", "GLScatterPlotItem"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.points: np.ndarray | None = None
        self.vectors: np.ndarray | None = None
        self.shafts: gl.GLLinePlotItem | None = None
        self.tips: gl.GLScatterPlotItem | None = None

        self.viewContainer, self.titleLabel, self.view = createView()
        self.controls = QControlPanel()
        self.currentSlider = self.controls.addSlider("Courant I", -20, 20, 10, divisor=10)
        self.externalSlider = self.controls.addSlider("Champ extérieur", -10, 10, 3, divisor=10)

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.viewContainer, 1)
        contentLayout.addWidget(self.controls)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Vide la scène, remet la caméra en place (voir plot_reset.py) et les contrôles."""
        self.controls.resetControls()
        resetGLView(self.view)
        self.titleLabel.setText("")
        self.points = None
        self.vectors = None
        self.shafts = None
        self.tips = None

    # -- Étapes ------------------------------------------------------------------------------------

    def setUpScene(self) -> None:
        """Titre, grille descendue sous le champ, axes nommés, caméra."""
        self.titleLabel.setText("Le champ magnétique d'un fil, plus un champ vertical")
        grid = gl.GLGridItem()
        grid.setSize(8, 8)
        grid.translate(0, 0, -3.6)
        self.view.addItem(grid)
        axes = gl.GLAxisItem()
        axes.setSize(4, 4, 4)
        self.view.addItem(axes)
        nameAxes(self.view, 4.3)
        self.view.setCameraPosition(distance=16, elevation=25, azimuth=-50)

    def addWire(self) -> None:
        """Le fil, sur l'axe z, et le sens du courant."""
        wire = gl.GLLinePlotItem(pos=np.array([[0, 0, -4], [0, 0, 4]]), color=(1, 0.6, 0.2, 1), width=6)
        self.view.addItem(wire)
        self.view.addItem(gl.GLTextItem(pos=(0.5, 0.5, 3.5), text="I ↑", color=(255, 160, 60, 255)))

    def computeGrid(self) -> None:
        """Les points de la grille, hors du fil."""
        self.points = gridPoints()

    def computeField(self) -> None:
        """Le champ en chaque point de la grille, pour I = 1 et un champ extérieur de 0,3."""
        self.vectors = fieldVectors(self.points, 1.0, 0.3)

    def addShafts(self) -> None:
        """Toutes les hampes, de longueur fixe, en un seul élément graphique blanc."""
        self.shafts = gl.GLLinePlotItem(pos=shaftSegments3D(self.points, self.vectors), mode="lines",
                                        color=(1, 1, 1, 1), width=2, antialias=True)
        self.view.addItem(self.shafts)

    def colorByStrength(self) -> None:
        """Une couleur par flèche selon l'intensité, donnée aux deux bouts de sa hampe."""
        colors = strengthColors(self.vectors)
        self.shafts.setData(color=np.repeat(colors, 2, axis=0))

    def addTips(self) -> None:
        """Les pointes : un point au bout de chaque hampe, de la couleur de sa flèche."""
        tipPositions = shaftSegments3D(self.points, self.vectors)[1::2, :]
        self.tips = gl.GLScatterPlotItem(pos=tipPositions, color=strengthColors(self.vectors), size=7)
        self.view.addItem(self.tips)

    def connectControls(self) -> None:
        """Relie les deux sélecteurs numériques au slot qui recalcule le champ."""
        self.currentSlider.valueChanged.connect(self.updateField)
        self.externalSlider.valueChanged.connect(self.updateField)

    @Slot()
    def updateField(self) -> None:
        """Recalcule le champ, puis donne aux hampes et aux pointes leurs positions et couleurs."""
        current = self.currentSlider.value() / 10
        external = self.externalSlider.value() / 10
        self.vectors = fieldVectors(self.points, current, external)
        segments = shaftSegments3D(self.points, self.vectors)
        colors = strengthColors(self.vectors)
        self.shafts.setData(pos=segments, color=np.repeat(colors, 2, axis=0))
        self.tips.setData(pos=segments[1::2, :], color=colors)

    def _exploreField(self) -> None:
        """Connecte les sélecteurs numériques, puis les révèle."""
        self.connectControls()
        self.controls.reveal()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : la scène",
                explanation=(
                    "Rien de nouveau : la vue de <code>createView()</code>, les axes nommés et la "
                    "caméra de la notion 3.1. <code>createView()</code> est affichée pour "
                    "rappel : elle s'est exécutée une seule fois, à la création de la page. La "
                    "grille est descendue par "
                    "<code>translate()</code> (notion 3.2), pour ne pas se mêler aux flèches les "
                    "plus basses."
                ),
                run=self.setUpScene,
                codeSource=(createView, self.setUpScene),
                references=[("GLGridItem", pyqtgraphDocUrl(f"{_GLPage}/glgriditem", "opengl.GLGridItem"))],
            ),
            QStepWalkthrough.Step(
                title="Le fil",
                explanation=(
                    "Le fil est une ligne 3D de deux points sur l'axe Z, de z = −4 à z = 4 : un "
                    "<code>GLLinePlotItem</code> (notion 3.2), épais et orange. Un "
                    "<code>GLTextItem</code> indique le sens du courant I : vers le haut."
                ),
                run=self.addWire,
                references=[("GLLinePlotItem",
                             pyqtgraphDocUrl(f"{_GLPage}/gllineplotitem", "opengl.GLLinePlotItem"))],
            ),
            QStepWalkthrough.Step(
                title="Une grille 3D",
                explanation=(
                    "<code>gridPoints()</code> construit la grille par "
                    "<code>np.meshgrid()</code> (notion 2.4), cette fois en trois dimensions : "
                    "7 × 7 × 5 points, de −3 à 3. <code>flatten()</code> (notion 1.6) range "
                    "chaque tableau à une dimension, et <code>np.column_stack()</code> (notion "
                    "2.5) les place en trois colonnes : une rangée (x, y, z) par point. "
                    "<code>points[:, 0]</code> est la colonne des x, toutes les rangées."
                    "<br><br>Le fil passera sur l'axe z : les points à moins de 0,5 de cet axe "
                    "sont retirés, par un tableau de booléens (notion 2.5). Il en reste 240. "
                    "Rien n'est encore dessiné."
                ),
                run=self.computeGrid,
                codeSource=(gridPoints, self.computeGrid),
                references=[("numpy.meshgrid", numpyDocUrl("meshgrid"))],
            ),
            QStepWalkthrough.Step(
                title="Le champ du fil",
                explanation=(
                    "Un long fil parcouru par un courant I crée un champ magnétique "
                    "B = μ₀·I/(2π·r) : B en teslas, I en ampères, r la distance au fil en "
                    "mètres, et μ₀ = 4π × 10⁻⁷ T·m/A. Le champ tourne autour du fil. Son sens "
                    "suit la règle de la main droite : le pouce dans le sens du courant, les "
                    "doigts s'enroulent dans le sens du champ, ici antihoraire vu d'en haut."
                    "<br><br>Ici, μ₀/(2π) = 1, donc B = I/r ; I et B sont en unités réduites : "
                    "seule la forme compte. Dans <code>fieldVectors()</code>, le vecteur "
                    "(−y, x) est le vecteur (x, y) tourné de 90° : il est perpendiculaire au "
                    "rayon, donc tangent au cercle autour du fil, et sa longueur est r. Multiplié "
                    "par I/r², il a la longueur I/r. Tout près du fil, r² est compté au moins "
                    "0,25. Le champ extérieur, le même partout, vertical, s'ajoute en z. Il "
                    "viendrait, par exemple, d'un grand aimant placé loin du fil."
                    "<br><br><code>fieldVectors()</code> calcule le champ en chaque point d'un "
                    "coup : un tableau de même forme que <code>points</code>, une rangée "
                    "(bx, by, bz) par point."
                    "<br><br><i>Pour l'exemple</i> : I = 1, et un champ extérieur de 0,3 dans l'unité de "
                    "B. Rien n'est encore dessiné."
                ),
                run=self.computeField,
                codeSource=(fieldVectors, self.computeField),
                references=[("numpy.column_stack", numpyDocUrl("column_stack"))],
            ),
            QStepWalkthrough.Step(
                title="Les hampes, en un seul élément",
                explanation=(
                    "Comme à la notion 2.5 : des hampes de longueur fixe, pour lire la "
                    "direction. <code>vectorLengths()</code> rend la longueur de chaque vecteur, "
                    "√(bx² + by² + bz²), calculée sur ses trois colonnes : une longueur par "
                    "rangée. <code>shaftSegments3D()</code>, la version 3D de "
                    "<code>shaftSegments()</code> (notion 2.5), divise chaque vecteur par sa "
                    "longueur, puis le ramène à 0,6."
                    "<br><br>Une boucle traite les trois colonnes l'une après l'autre. Chaque "
                    "colonne a la forme (240,), comme <code>lengths</code> : la division se fait "
                    "case par case. Diviser d'un coup tout le tableau, de forme (240, 3), par "
                    "<code>lengths</code>, de forme (240,), échouerait : numpy n'associe pas ces "
                    "deux formes sans une écriture de plus, que ce guide n'emploie pas."
                    "<br><br>Les bouts s'alternent dans <code>segments</code> : "
                    "<code>segments[0::2, :]</code> désigne une rangée sur deux à partir de la "
                    "première, et reçoit les pieds ; <code>segments[1::2, :]</code> une rangée sur "
                    "deux à partir de la deuxième, et reçoit les bouts."
                    "<br><br><code>mode=\"lines\"</code> relie les points deux par deux, comme "
                    "<code>connect=\"pairs\"</code> en 2D : chaque paire est une hampe. Un seul "
                    "élément graphique pour 240 hampes. Sans pointe, leur sens ne se lit pas "
                    "encore."
                ),
                run=self.addShafts,
                codeSource=(vectorLengths, shaftSegments3D, self.addShafts),
                references=[
                    ("numpy.sqrt", numpyDocUrl("sqrt")),
                    ("GLLinePlotItem", pyqtgraphDocUrl(f"{_GLPage}/gllineplotitem", "opengl.GLLinePlotItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="L'intensité en couleur",
                explanation=(
                    "En 2D, une courbe n'avait qu'une couleur. En 3D, "
                    "<code>GLLinePlotItem</code> accepte un tableau de couleurs, une par sommet. "
                    "<code>strengthColors()</code> rend une couleur par flèche, de la palette "
                    "<code>\"plasma\"</code> de la notion 2.5, par un seul appel de "
                    "<code>map()</code> sur tout le tableau. La place dans la palette vaut "
                    "0,15 + 0,85 × |B| / 1,2, plafonnée à 1 par <code>np.minimum()</code> : un "
                    "champ de 1,2 ou plus est jaune. "
                    "Le 0,15 évite le bas de la palette, presque noir, qui disparaîtrait sur le "
                    "fond noir de la vue."
                    "<br><br>Chaque hampe a deux sommets. <code>np.repeat()</code> (notion 1.6) "
                    "répète ici des rangées. Un <b>axe</b> d'un tableau est l'une de ses "
                    "dimensions, numérotée depuis 0 : l'axe 0 est celui des rangées, l'axe 1 "
                    "celui des colonnes. Avec <code>axis=0</code>, chaque rangée de couleur "
                    "paraît deux fois de suite, une pour chaque bout d'une hampe. "
                    "<code>setData(color=…)</code> les donne à la ligne existante."
                    "<br><br>Les flèches proches du fil sont jaunes : le champ y est le plus "
                    "fort."
                ),
                run=self.colorByStrength,
                codeSource=(strengthColors, self.colorByStrength),
                references=[
                    ("numpy.repeat", numpyDocUrl("repeat")),
                    ("ColorMap.map", pyqtgraphDocUrl("api_reference/colormap", "ColorMap.map")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Les pointes",
                explanation=(
                    "Une pointe en cône, comme la flèche du vent de la notion 3.2, demanderait "
                    "une rotation différente pour chacune des 240 flèches. Un point au bout de "
                    "chaque hampe suffit à indiquer le sens. <code>[1::2, :]</code> garde une "
                    "rangée sur deux à partir de la deuxième, et toutes ses colonnes : les bouts "
                    "des hampes. "
                    "<code>GLScatterPlotItem</code> (notion 3.1) accepte lui aussi une couleur "
                    "par point."
                    "<br><br>Le sens se lit maintenant : tourner la caméra. Les flèches tournent "
                    "autour du fil en montant, sous l'effet du champ vertical."
                ),
                run=self.addTips,
                references=[("GLScatterPlotItem",
                             pyqtgraphDocUrl(f"{_GLPage}/glscatterplotitem", "opengl.GLScatterPlotItem"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : le courant et le champ extérieur",
                explanation=(
                    "Deux sélecteurs numériques paraissent sous la vue. "
                    "<code>currentSlider</code> va de −20 à 20 : divisé par 10, il donne le "
                    "courant I, de −2 à 2. Il part de 10, soit 1. <code>externalSlider</code> va "
                    "de −10 à 10 : divisé par 10, il donne le champ extérieur, de −1 à 1. Il part "
                    "de 3, soit 0,3."
                    "<br><br><code>connectControls()</code> relie leur signal "
                    "<code>valueChanged</code> au slot <code>updateField()</code>. Celui-ci "
                    "recalcule le champ, puis donne aux hampes et aux pointes leurs nouvelles "
                    "positions et couleurs par <code>setData()</code>."
                    "<br><br>Inverser le courant inverse le sens de rotation. Annuler le champ "
                    "extérieur donne des cercles plats autour du fil. Annuler le courant ne "
                    "laisse que le champ vertical, uniforme. Annuler les deux rend le champ "
                    "nul : les hampes se réduisent à leur pied, et il ne reste que les pointes, "
                    "des points sans direction."
                ),
                run=self._exploreField,
                codeSource=(self.connectControls, self.updateField),
                references=[("GLLinePlotItem",
                             pyqtgraphDocUrl(f"{_GLPage}/gllineplotitem", "opengl.GLLinePlotItem"))],
            ),
        ]
