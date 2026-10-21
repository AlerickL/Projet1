"""Notion 3.3 : une surface 3D, le potentiel d'un dipôle en relief.

Contexte : le potentiel électrique du dipôle de la notion 2.4, cette fois en
relief. La hauteur de la surface au-dessus de chaque point (x, y) est le
potentiel en ce point : un pic sur la charge positive, un creux sur la
charge négative. Une surface z = f(x, y) est le graphique 3D le plus
courant.

Étapes couvertes : un récapitulatif de la scène (notion 3.1), le calcul des
hauteurs sur une grille, la surface éclairée (`GLSurfacePlotItem`), ses
couleurs selon la hauteur (une palette appliquée à tout un tableau), une
coupe le long de l'axe x, puis deux sélecteurs numériques : la charge de
droite et la position de la coupe.

Chaque étape est une méthode de `QTopicSurfaceTab` : elle lit et modifie
directement `self.view`.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetGLView
from .topic_2_4_heatmap import potentialGrid
from .topic_3_1_scene import createView, nameAxes

_GLPage = "api_reference/3dgraphics"


def heightGrid(xs: np.ndarray, ys: np.ndarray, charges: list[list[float]]) -> np.ndarray:
    """La hauteur en chaque point : le potentiel, plafonné à ±3.

    `xs` est de forme (n,), `ys` de forme (m,). Rend un tableau de réels de
    forme (n, m) : heights[i, j] est la hauteur en (xs[i], ys[j]).
    """
    return np.clip(potentialGrid(xs, ys, charges), -3.0, 3.0)


def heightColors(heights: np.ndarray) -> np.ndarray:
    """Une couleur par point, de 0 à 1 : la palette CET-D1, de −3 (bleu) à 3 (rouge).

    `heights` est de forme (n, m) ; rend un tableau de réels de forme (n, m, 4).
    """
    fractions = (heights + 3) / 6
    return pg.colormap.get("CET-D1").map(fractions, mode="float")


def cutAlongX(xs: np.ndarray, ys: np.ndarray, heights: np.ndarray, column: int) -> np.ndarray:
    """La coupe de la surface à y = ys[column], un peu au-dessus d'elle.

    `xs` est de forme (n,), `heights` de forme (n, m). Rend un tableau de
    réels de forme (n, 3) : une rangée (x, y, hauteur) par point.
    """
    return np.column_stack((xs, np.full(xs.shape, ys[column]), heights[:, column] + 0.05))


class QTopicSurfaceTab(QWidget):
    """Onglet de la notion 3.3 : le potentiel d'un dipôle, en surface.

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
        chargeSlider, cutSlider: Les sélecteurs numériques de la charge de
            droite et de la position y de la coupe.
        charges, xs, ys, heights: Les charges, la grille et les hauteurs, ou None.
        surface, cutLine: La surface et sa coupe, ou None avant leur étape.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Surface 3D"
    TabToolTip = "z = f(x, y) : une surface éclairée, colorée selon la hauteur, avec une coupe"
    RecommendedPanelWidth = 640
    Objective = (
        "Représenter une grandeur du plan en relief, par une surface : la calculer sur une "
        "grille, l'éclairer, la colorer selon la hauteur, y tracer une coupe, puis la faire "
        "changer avec la charge de droite et déplacer la coupe."
    )
    KeyConcepts = [
        "Une surface se calcule comme une carte de chaleur : une hauteur par point d'une grille.",
        "L'éclairage donne le relief. La couleur peut, en plus, montrer la hauteur.",
        "Une palette s'applique à tout un tableau d'un coup : une couleur par case.",
        "Une coupe à y fixe redonne la courbe d'un graphique 2D ordinaire.",
    ]
    KeyApis = ["GLSurfacePlotItem", "GLSurfacePlotItem.setData", "ColorMap.map", "GLLinePlotItem"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.charges: list[list[float]] | None = None
        self.xs: np.ndarray | None = None
        self.ys: np.ndarray | None = None
        self.heights: np.ndarray | None = None
        self.surface: gl.GLSurfacePlotItem | None = None
        self.cutLine: gl.GLLinePlotItem | None = None

        self.viewContainer, self.titleLabel, self.view = createView()
        self.controls = QControlPanel()
        self.chargeSlider = self.controls.addSlider("Charge de droite", -20, 20, -10, divisor=10, suffix="q")
        self.cutSlider = self.controls.addSlider("Position y de la coupe", -30, 30, 0, divisor=10)

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
        """Vide la scène, remet la caméra en place (voir plot_reset.py) et le contrôle."""
        self.controls.resetControls()
        resetGLView(self.view)
        self.titleLabel.setText("")
        self.charges = None
        self.xs = None
        self.ys = None
        self.heights = None
        self.surface = None
        self.cutLine = None

    # -- Étapes ------------------------------------------------------------------------------------

    def setUpScene(self) -> None:
        """Titre, grille descendue sous la surface, axes nommés, caméra."""
        self.titleLabel.setText("Le potentiel d'un dipôle, en relief")
        grid = gl.GLGridItem()
        grid.setSize(8, 6)
        grid.translate(0, 0, -3.2)
        self.view.addItem(grid)
        axes = gl.GLAxisItem()
        axes.setSize(5, 4, 4)
        self.view.addItem(axes)
        nameAxes(self.view, 5.3)
        self.view.setCameraPosition(distance=14, elevation=30, azimuth=-60)

    def computeHeights(self) -> None:
        """Les charges de la notion 2.4, puis les hauteurs sur une grille de 81 × 61 points."""
        self.charges = [[-1.0, 0.0, 1.0], [1.0, 0.0, -1.0]]
        self.xs = np.linspace(-4, 4, 81)
        self.ys = np.linspace(-3, 3, 61)
        self.heights = heightGrid(self.xs, self.ys, self.charges)

    def addSurface(self) -> None:
        """La surface, d'une seule couleur, éclairée."""
        self.surface = gl.GLSurfacePlotItem(x=self.xs, y=self.ys, z=self.heights,
                                            color=(0.6, 0.6, 1.0, 1.0), shader="shaded", smooth=True)
        self.view.addItem(self.surface)

    def colorByHeight(self) -> None:
        """Les couleurs selon la hauteur, données à la surface existante avec ses hauteurs."""
        self.surface.setData(z=self.heights, colors=heightColors(self.heights))

    def addCut(self) -> None:
        """La coupe à y = 0, la colonne 30 du tableau, en jaune."""
        self.cutLine = gl.GLLinePlotItem(pos=cutAlongX(self.xs, self.ys, self.heights, 30),
                                         color=(1, 1, 0, 1), width=3, antialias=True)
        self.view.addItem(self.cutLine)

    def connectControls(self) -> None:
        """Relie les deux sélecteurs numériques à leur slot."""
        self.chargeSlider.valueChanged.connect(self.updateCharge)
        self.cutSlider.valueChanged.connect(self.placeCut)

    @Slot()
    def updateCharge(self) -> None:
        """Donne sa valeur à la charge de droite, puis recalcule hauteurs, couleurs et coupe."""
        self.charges[1][2] = self.chargeSlider.value() / 10
        self.heights = heightGrid(self.xs, self.ys, self.charges)
        self.surface.setData(z=self.heights, colors=heightColors(self.heights))
        self.placeCut()

    @Slot()
    def placeCut(self) -> None:
        """Place la coupe à la colonne du y choisi : de −3 à 3 par pas de 0,1, les colonnes 0 à 60."""
        column = self.cutSlider.value() + 30
        self.cutLine.setData(pos=cutAlongX(self.xs, self.ys, self.heights, column))

    def _exploreCharge(self) -> None:
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
                    "grille est descendue sous la surface par "
                    "<code>translate()</code> (notion 3.2) : à z = 0, elle se confondrait avec "
                    "la partie plate de la surface, loin des charges."
                ),
                run=self.setUpScene,
                codeSource=(createView, self.setUpScene),
                references=[("GLGridItem", pyqtgraphDocUrl(f"{_GLPage}/glgriditem", "opengl.GLGridItem"))],
            ),
            QStepWalkthrough.Step(
                title="Les hauteurs, sur une grille",
                explanation=(
                    "Le calcul de la carte de chaleur de la notion 2.4 : les mêmes charges, la "
                    "même fonction <code>potentialGrid()</code>, importée de son fichier comme en "
                    "1.5 (<code>from .topic_2_4_heatmap import potentialGrid</code>), sur une "
                    "grille de 81 × 61 points. Comme en 2.4, k = 1 et les charges sont des "
                    "multiples de q."
                    "<br><br>Une nouveauté dans <code>heightGrid()</code> : la hauteur est "
                    "plafonnée à ±3. <code>np.clip(tableau, -3.0, 3.0)</code> ramène chaque "
                    "valeur sous −3 à −3, et chaque valeur au-dessus de 3 à 3. Tout près d'une "
                    "charge, le potentiel grandit sans limite : sans plafond, un pic immense "
                    "écraserait tout le reste du relief. Rien n'est encore affiché."
                ),
                run=self.computeHeights,
                codeSource=(heightGrid, self.computeHeights),
                references=[("numpy.clip", numpyDocUrl("clip"))],
            ),
            QStepWalkthrough.Step(
                title="La surface",
                explanation=(
                    "<code>gl.GLSurfacePlotItem</code> reçoit les x, les y et le tableau des "
                    "hauteurs : <code>z[i, j]</code> est la hauteur au-dessus de "
                    "(<code>x[i]</code>, <code>y[j]</code>). Il relie les points voisins par des "
                    "triangles, un maillage."
                    "<br><br>Une seule couleur ne montrerait pas le relief. "
                    "<code>shader=\"shaded\"</code> éclaire la surface : les pentes tournées vers "
                    "la lumière sont plus claires. <code>smooth=True</code> lisse l'éclairage "
                    "d'un triangle à l'autre."
                    "<br><br>À gauche : un pic au-dessus de +q, en (−1, 0), un creux sous −q, en "
                    "(1, 0), tronqués à ±3 par le "
                    "plafond, et une grande partie plate autour, où le potentiel est presque "
                    "nul."
                ),
                run=self.addSurface,
                references=[("GLSurfacePlotItem",
                             pyqtgraphDocUrl(f"{_GLPage}/glsurfaceplotitem", "opengl.GLSurfacePlotItem"))],
            ),
            QStepWalkthrough.Step(
                title="La couleur selon la hauteur",
                explanation=(
                    "<code>heightColors()</code> ramène d'abord chaque hauteur entre 0 et 1, "
                    "d'un coup : (h + 3) / 6 donne 0 pour −3 et 1 pour 3."
                    "<br><br>Puis la palette divergente de la notion 2.4 s'applique à tout le "
                    "tableau d'un coup : <code>colorMap.map(tableau, mode=\"float\")</code> rend "
                    "une couleur par case, quatre nombres de 0 à 1 (rouge, vert, bleu, "
                    "opacité). Le résultat est un tableau de 81 × 61 × 4."
                    "<br><br><code>setData(z=…, colors=…)</code> donne ces couleurs à la surface "
                    "existante. Piège vérifié : avec <code>colors</code> seul, la surface garde "
                    "sa couleur unique à l'écran. Il faut lui redonner aussi ses hauteurs, "
                    "<code>z</code>, même inchangées. L'éclairage s'y ajoute : on lit à la fois la valeur, par la "
                    "couleur, et la pente, par l'ombre."
                ),
                run=self.colorByHeight,
                codeSource=(heightColors, self.colorByHeight),
                references=[("ColorMap.map", pyqtgraphDocUrl("api_reference/colormap", "ColorMap.map"))],
            ),
            QStepWalkthrough.Step(
                title="Une coupe",
                explanation=(
                    "<code>ys</code> va de −3 à 3 en 61 points : <code>ys[30]</code>, le point du "
                    "milieu, vaut 0. La colonne 30 du tableau des hauteurs, "
                    "<code>heights[:, 30]</code>, est donc la droite y = 0, qui passe par les "
                    "deux charges. <code>cutAlongX()</code> range ses points en (x, y, hauteur) "
                    "par <code>np.column_stack()</code> (notion 2.5), un peu au-dessus de la "
                    "surface pour rester visibles. <code>np.full()</code> (notion 1.6) répète le "
                    "même y. Le <code>GLLinePlotItem</code> de la notion 3.2 les relie."
                    "<br><br>C'est la courbe du potentiel le long de l'axe x, le graphique 2D "
                    "qu'on tracerait avec <code>plot()</code>. Une surface contient toutes ces "
                    "coupes à la fois."
                ),
                run=self.addCut,
                codeSource=(cutAlongX, self.addCut),
                references=[("GLLinePlotItem",
                             pyqtgraphDocUrl(f"{_GLPage}/gllineplotitem", "opengl.GLLinePlotItem"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : la charge de droite et la coupe",
                explanation=(
                    "Deux sélecteurs numériques paraissent sous la vue :"
                    "<ul>"
                    "<li><code>chargeSlider</code>, la charge de droite en multiples de q. Il va "
                    "de −20 à 20 : divisé par 10, il donne la charge, de −2 à 2 par pas de 0,1. "
                    "Il part de −10, soit −1, la charge actuelle ;</li>"
                    "<li><code>cutSlider</code>, la position y de la coupe. Il va de −30 à 30 : "
                    "divisé par 10, il donne y, de −3 à 3 par pas de 0,1, le pas de la grille. "
                    "Il part de 0.</li>"
                    "</ul>"
                    "<code>connectControls()</code> relie leur signal <code>valueChanged</code> à "
                    "leur slot. <code>updateCharge()</code> change la charge, le troisième "
                    "nombre de <code>self.charges[1]</code>, puis recalcule les hauteurs et les "
                    "couleurs : <code>setData(z=…, colors=…)</code> les donne à la surface "
                    "existante. Il appelle enfin <code>placeCut()</code>, qui refait la coupe. "
                    "Celui-ci trouve la colonne du y choisi : la valeur lue plus 30, puisque la "
                    "colonne 0 est y = −3 et la colonne 30, y = 0."
                    "<br><br>À +1, les deux charges ont le même signe : deux pics. À 0, il ne "
                    "reste qu'une charge. Éloigner la coupe de y = 0 : elle ne passe plus par les "
                    "charges, et ses pics s'abaissent."
                ),
                run=self._exploreCharge,
                codeSource=(self.connectControls, self.updateCharge, self.placeCut),
                references=[("GLSurfacePlotItem",
                             pyqtgraphDocUrl(f"{_GLPage}/glsurfaceplotitem", "opengl.GLSurfacePlotItem"))],
            ),
        ]
