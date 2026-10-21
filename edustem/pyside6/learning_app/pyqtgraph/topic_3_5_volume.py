"""Notion 3.5 : un volume 3D, le potentiel d'un dipôle dans l'espace.

Contexte : le potentiel du dipôle de la notion 2.4, cette fois en chaque
point d'un cube. Après la carte de chaleur (2.4) et la surface (3.3), le
volume montre la grandeur dans les trois dimensions : un nuage
translucide, rouge autour de la charge positive, bleu autour de la
négative. Une coupe plane en montre l'intérieur.

Étapes couvertes : un récapitulatif de la scène (notion 3.1), le potentiel
en chaque point d'un cube, un volume de couleurs (`GLVolumeItem`), son
opacité selon le potentiel, une coupe du tableau, la coupe placée dans la
scène (`GLImageItem`), dessinée d'abord (test de profondeur et ordre de
dessin), le plan XZ, le plan YZ et la
transposée, la coupe par-dessus tout, puis deux étapes « À vous » : la
coupe (aucune, son plan, sa position, son opacité, sa façon d'être
dessinée), puis la charge et l'opacité du volume.

Chaque étape est une méthode de `QTopicVolumeTab` : elle lit et modifie
directement `self.view`.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from OpenGL import GL
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, numpyPageUrl, pyqtgraphDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetGLView
from .topic_3_1_scene import createView, nameAxes

_GLPage = "api_reference/3dgraphics"


def chargePotential3D(x: np.ndarray, y: np.ndarray, z: np.ndarray, charges: list[list[float]]) -> np.ndarray:
    """Le potentiel en (x, y, z) : la somme des k·q/r des charges [x, y, z, q], avec k = 1.

    `x`, `y` et `z` sont des tableaux de réels de même forme ; le résultat a
    cette forme.
    """
    potential = 0.0
    for chargeX, chargeY, chargeZ, q in charges:
        distance = np.maximum(np.sqrt((x - chargeX) ** 2 + (y - chargeY) ** 2 + (z - chargeZ) ** 2), 0.2)
        potential = potential + q / distance
    return potential


def potentialVolume(centers: np.ndarray, charges: list[list[float]]) -> np.ndarray:
    """Le potentiel au centre de chaque case du cube.

    `centers` est de forme (n,), le même sur les trois axes. Rend un tableau
    de réels de forme (n, n, n) : potential[ix, iy, iz] en
    (centers[ix], centers[iy], centers[iz]).
    """
    gridX, gridY, gridZ = np.meshgrid(centers, centers, centers, indexing="ij")
    return chargePotential3D(gridX, gridY, gridZ, charges)


def paletteColors(values: np.ndarray) -> np.ndarray:
    """Une couleur par case, de 0 à 255 : la palette de 2.4 selon V, plafonné à ±2.

    `values` est de forme quelconque ; rend un tableau d'octets de cette forme,
    plus un dernier axe de 4 nombres (rouge, vert, bleu, opacité).
    """
    fractions = (np.clip(values, -2.0, 2.0) + 2) / 4
    return pg.colormap.get("CET-D1").map(fractions, mode="byte")


def volumeColors(potential: np.ndarray, opacity: float) -> np.ndarray:
    """Les couleurs du volume : la palette selon V, une opacité selon |V|².

    `potential` est de forme (n, n, n) ; rend un tableau d'octets de forme (n, n, n, 4).
    """
    colors = paletteColors(potential)
    clipped = np.clip(potential, -2.0, 2.0)
    colors[:, :, :, 3] = (np.abs(clipped) / 2) ** 2 * opacity * 255
    return colors


def sliceColors(values: np.ndarray, opacity: float) -> np.ndarray:
    """Les couleurs d'une coupe : la palette selon V, et la même opacité partout.

    `values` est de forme (n, m) ; rend un tableau d'octets de forme (n, m, 4).
    """
    colors = paletteColors(values)
    colors[:, :, 3] = opacity * 255
    return colors


def sliceImage(potential: np.ndarray, plane: str, index: int) -> np.ndarray:
    """La coupe du tableau dans le plan choisi, à la case `index` de l'axe perpendiculaire à ce plan.

    `potential` est de forme (n, n, n) ; rend un tableau de réels de forme (n, n).
    """
    if plane == "XY":
        return potential[:, :, index]
    if plane == "XZ":
        return potential[:, index, :]
    return potential[index, :, :].T


def placeSlice(sliceItem: gl.GLImageItem, plane: str, index: int) -> None:
    """Place l'image de la coupe dans la scène, dans son plan, au centre de la case `index`."""
    offset = -2 + 0.1 * index + 0.05
    sliceItem.resetTransform()
    sliceItem.scale(0.1, 0.1, 1)
    sliceItem.translate(-2, -2, 0)
    if plane == "XY":
        sliceItem.translate(0, 0, offset)
    elif plane == "XZ":
        sliceItem.rotate(90, 1, 0, 0)
        sliceItem.translate(0, offset, 0)
    else:
        sliceItem.rotate(-90, 0, 1, 0)
        sliceItem.translate(offset, 0, 0)


class QTopicVolumeTab(QWidget):
    """Onglet de la notion 3.5 : le potentiel d'un dipôle en volume, et une coupe.

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
        controls: Le panneau des contrôles des étapes « À vous » (plomberie).
        planeCombo, positionSlider, sliceOpacitySlider, onTopCheck,
            chargeSlider, opacitySlider: Les contrôles.
        charges, centers, potential: Les charges, les centres des cases et le
            potentiel en chaque case, ou None.
        sliceValues: La coupe du tableau, ou None avant son étape.
        volume, sliceItem: Le volume et la coupe, ou None avant leur étape.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Volume 3D"
    TabToolTip = "Le potentiel d'un dipôle en volume translucide, et une coupe qu'on déplace"
    RecommendedPanelWidth = 640
    Objective = (
        "Montrer une grandeur définie en chaque point de l'espace : le potentiel d'un dipôle en "
        "volume translucide, puis une coupe plane pour en voir l'intérieur."
    )
    KeyConcepts = [
        "Une grandeur de l'espace est un tableau à trois dimensions, calculé d'un coup sur une grille.",
        "Un volume translucide laisse voir l'intérieur : les faibles valeurs sont presque "
        "transparentes.",
        "Une coupe est un tableau à deux dimensions extrait du volume, montré comme une image "
        "placée dans la scène.",
        "Le test de profondeur cache ce qui est derrière un objet : une coupe se dessine à sa "
        "profondeur, voilée par le volume devant elle, ou par-dessus tout, nette mais sans "
        "profondeur.",
        "Les données et les axes doivent partager le même repère.",
    ]
    KeyApis = [
        "GLVolumeItem", "GLVolumeItem.setData", "GLImageItem", "GLImageItem.setData",
        "GLGraphicsItem.scale", "GLGraphicsItem.setDepthValue", "GLGraphicsItem.resetTransform",
        "GLGraphicsItem.setGLOptions",
        "GLGraphicsItem.updateGLOptions",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.charges: list[list[float]] | None = None
        self.centers: np.ndarray | None = None
        self.potential: np.ndarray | None = None
        self.sliceValues: np.ndarray | None = None
        self.volume: gl.GLVolumeItem | None = None
        self.sliceItem: gl.GLImageItem | None = None

        self.viewContainer, self.titleLabel, self.view = createView()
        self.controls = QControlPanel()
        self.planeCombo = self.controls.addComboBox("Plan de la coupe",
                                                    [("Aucune", ""), ("XY", "XY"), ("XZ", "XZ"), ("YZ", "YZ")], 2)
        self.positionSlider = self.controls.addSlider("Case de la coupe", 0, 39, 20)
        self.sliceOpacitySlider = self.controls.addSlider("Opacité de la coupe", 0, 100, 100, suffix="%")
        self.onTopCheck = self.controls.addCheckBox("Coupe par-dessus le volume", checked=True)
        self.chargeSlider = self.controls.addSlider("Charge de droite", -20, 20, -10, divisor=10, suffix="q")
        self.opacitySlider = self.controls.addSlider("Opacité du volume", 0, 100, 30, suffix="%")

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
        self.charges = None
        self.centers = None
        self.potential = None
        self.sliceValues = None
        self.volume = None
        self.sliceItem = None

    # -- Étapes ------------------------------------------------------------------------------------

    def setUpScene(self) -> None:
        """Titre, axes nommés et caméra, sans grille."""
        self.titleLabel.setText("Le potentiel d'un dipôle, dans l'espace")
        axes = gl.GLAxisItem()
        axes.setSize(2.5, 2.5, 2.5)
        self.view.addItem(axes)
        nameAxes(self.view, 2.8)
        self.view.setCameraPosition(distance=9, elevation=25, azimuth=-60)

    def computeVolume(self) -> None:
        """Les deux charges, puis le potentiel au centre de chaque case d'un cube de −2 à 2."""
        self.charges = [[-1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, -1.0]]
        self.centers = np.linspace(-1.95, 1.95, 40)
        self.potential = potentialVolume(self.centers, self.charges)

    def addVolume(self) -> None:
        """Le volume, aux couleurs de la palette, ramené sur le cube de −2 à 2 des axes."""
        self.volume = gl.GLVolumeItem(paletteColors(self.potential))
        self.volume.scale(0.1, 0.1, 0.1)
        self.volume.translate(-2, -2, -2)
        self.view.addItem(self.volume)

    def makeTranslucent(self) -> None:
        """Le volume reçoit ses couleurs translucides : opacité selon |V|²."""
        self.volume.setData(volumeColors(self.potential, 1.0))

    def takeSlice(self) -> None:
        """La coupe horizontale du tableau, à la case 20 de z."""
        self.sliceValues = self.potential[:, :, 20]

    def addSlice(self) -> None:
        """La coupe dans la scène, à z = 0,05, et le volume atténué : la coupe ne paraît pas encore."""
        self.sliceItem = gl.GLImageItem(sliceColors(self.sliceValues, 1.0))
        self.sliceItem.scale(0.1, 0.1, 1)
        self.sliceItem.translate(-2, -2, 0.05)
        self.view.addItem(self.sliceItem)
        self.volume.setData(volumeColors(self.potential, 0.3))

    def drawSliceFirst(self) -> None:
        """La coupe dessinée avant les autres éléments : elle paraît, à sa profondeur."""
        self.sliceItem.setDepthValue(-1)

    def showSlice(self, plane: str, index: int, opacity: float) -> None:
        """Donne à la coupe l'image du plan, de la case et de l'opacité choisis, puis la place."""
        self.sliceItem.setData(sliceColors(sliceImage(self.potential, plane, index), opacity))
        placeSlice(self.sliceItem, plane, index)

    def turnSlice(self) -> None:
        """La coupe passe dans le plan vertical XZ, à la case 20 de y, opaque."""
        self.showSlice("XZ", 20, 1.0)

    def turnSliceSideways(self) -> None:
        """La coupe passe dans le plan YZ, à la case 10 de x, près de +q."""
        self.showSlice("YZ", 10, 1.0)

    @Slot(bool)
    def drawSliceOnTop(self, onTop: bool) -> None:
        """Dessine la coupe par-dessus tout le volume, ou à sa profondeur (étape « Dessiner la coupe d'abord »)."""
        self.sliceItem.setGLOptions("translucent")
        if onTop:
            self.sliceItem.updateGLOptions({GL.GL_DEPTH_TEST: False})
            self.sliceItem.setDepthValue(1)
        else:
            self.sliceItem.setDepthValue(-1)

    def compareDrawings(self) -> None:
        """La coupe revient dans le plan XZ des charges, puis passe par-dessus tout le volume."""
        self.showSlice("XZ", 20, 1.0)
        self.drawSliceOnTop(True)

    def connectSliceControls(self) -> None:
        """Relie les quatre contrôles de la coupe à leurs slots."""
        self.planeCombo.currentIndexChanged.connect(self.updateSlice)
        self.positionSlider.valueChanged.connect(self.updateSlice)
        self.sliceOpacitySlider.valueChanged.connect(self.updateSlice)
        self.onTopCheck.toggled.connect(self.drawSliceOnTop)

    @Slot()
    def updateSlice(self) -> None:
        """Montre la coupe du plan, de la case et de l'opacité choisis ; « Aucune » la cache."""
        plane = self.planeCombo.currentData()
        self.sliceItem.setVisible(plane != "")
        if plane != "":
            self.showSlice(plane, self.positionSlider.value(), self.sliceOpacitySlider.value() / 100)

    def connectChargeControls(self) -> None:
        """Relie la charge et l'opacité à leurs slots."""
        self.chargeSlider.valueChanged.connect(self.updateCharge)
        self.opacitySlider.valueChanged.connect(self.updateOpacity)

    @Slot()
    def updateCharge(self) -> None:
        """Change la charge de droite, recalcule potentiel et volume, puis redessine la coupe choisie."""
        self.charges[1][3] = self.chargeSlider.value() / 10
        self.potential = potentialVolume(self.centers, self.charges)
        self.volume.setData(volumeColors(self.potential, self.opacitySlider.value() / 100))
        self.updateSlice()

    @Slot()
    def updateOpacity(self) -> None:
        """Recolore le volume avec la nouvelle opacité, sans recalculer le potentiel."""
        self.volume.setData(volumeColors(self.potential, self.opacitySlider.value() / 100))

    def _exploreSlice(self) -> None:
        """Connecte les contrôles de la coupe, puis les révèle."""
        self.connectSliceControls()
        self.controls.reveal(self.planeCombo, self.positionSlider, self.sliceOpacitySlider, self.onTopCheck)

    def _exploreCharge(self) -> None:
        """Connecte la charge et l'opacité, puis révèle leurs sélecteurs."""
        self.connectChargeControls()
        self.controls.reveal(self.chargeSlider, self.opacitySlider)

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : la scène",
                explanation=(
                    "Rien de nouveau : la vue de <code>createView()</code>, les axes nommés et la "
                    "caméra de la notion 3.1. <code>createView()</code> est affichée pour "
                    "rappel : elle s'est exécutée une seule fois, à la création de la page. Les "
                    "axes mesurent 2,5 : le cube des données ira de "
                    "−2 à 2. Pas de grille : le volume donnera lui-même la profondeur, et une "
                    "grille brouillerait sa transparence."
                ),
                run=self.setUpScene,
                codeSource=(createView, self.setUpScene),
                references=[("GLAxisItem", pyqtgraphDocUrl(f"{_GLPage}/glaxisitem", "opengl.GLAxisItem"))],
            ),
            QStepWalkthrough.Step(
                title="Le potentiel en chaque point d'un cube",
                explanation=(
                    "Le potentiel V = k·q/r de la notion 2.4, avec k = 1, mais dans l'espace : "
                    "chaque charge est une liste <code>[x, y, z, q]</code>, et la distance "
                    "compte les trois coordonnées, r = √((x − xᵢ)² + (y − yᵢ)² + (z − zᵢ)²). "
                    "<code>chargePotential3D()</code> est la version à trois coordonnées de "
                    "<code>chargePotential()</code> (notion 2.4), et <code>np.sqrt()</code> y "
                    "prend la racine carrée. Le dipôle est le même : +q en (−1, 0, 0), −q en "
                    "(1, 0, 0)."
                    "<br><br><code>potentialVolume()</code> construit la grille par "
                    "<code>np.meshgrid()</code> (notion 2.4), cette fois en trois dimensions, et "
                    "calcule d'un coup un tableau de 40 × 40 × 40, soit 64 000 valeurs : "
                    "<code>potential[ix, iy, iz]</code> est le potentiel en (<code>centers[ix]</code>, "
                    "<code>centers[iy]</code>, <code>centers[iz]</code>). Les indices s'appellent "
                    "<code>ix</code>, <code>iy</code> et <code>iz</code>, et non i, j, k : k est "
                    "déjà la constante de la formule."
                    "<br><br>Les données et les axes doivent partager le même repère. Le cube "
                    "va de −2 à 2, découpé en 40 cases de 0,1 sur chaque axe. "
                    "<code>centers</code> donne le centre de chaque case : de −1,95 à 1,95. Rien "
                    "n'est encore affiché."
                ),
                run=self.computeVolume,
                codeSource=(chargePotential3D, potentialVolume, self.computeVolume),
                references=[],
            ),
            QStepWalkthrough.Step(
                title="Un volume de couleurs",
                explanation=(
                    "<code>gl.GLVolumeItem</code> affiche un tableau de couleurs à quatre "
                    "dimensions : x, y, z, puis les quatre nombres d'une couleur (rouge, vert, "
                    "bleu, opacité). Le tableau de couleurs d'une image ou d'un volume va de 0 à "
                    "255, et non de 0 à 1 comme un tuple (notion 3.1)."
                    "<br><br><code>paletteColors()</code> construit ce tableau d'un coup. "
                    "<code>np.clip()</code> (notion 3.3) plafonne V à ±2 : près des charges, V "
                    "grandit sans limite. Elle en tire la place dans la palette, de 0 à 1, comme "
                    "en 3.3. <code>map(…, mode=\"byte\")</code> rend les couleurs en octets, de 0 "
                    "à 255, et non en réels comme le mode <code>\"float\"</code> de 3.3. Elle suit "
                    "la palette divergente de 2.4 : rouge pour V positif, bleu pour V "
                    "négatif, blanc près de 0. Chaque couleur de la palette a l'opacité 255."
                    "<br><br>Une case du volume mesure une unité. <code>scale(sx, sy, sz)</code> "
                    "multiplie les tailles d'un élément 3D le long de chaque axe : "
                    "<code>scale(0.1, 0.1, 0.1)</code> ramène la case à 0,1, puis "
                    "<code>translate(-2, -2, -2)</code> place le cube de −2 "
                    "à 2, dans le repère des axes. À gauche : un cube plein. On n'en voit que les "
                    "faces, pâles, loin des charges : l'intérieur reste caché."
                ),
                run=self.addVolume,
                codeSource=(paletteColors, self.addVolume),
                references=[
                    ("GLVolumeItem", pyqtgraphDocUrl(f"{_GLPage}/glvolumeitem", "opengl.GLVolumeItem")),
                    ("ColorMap.map", pyqtgraphDocUrl("api_reference/colormap", "ColorMap.map")),
                    ("GLGraphicsItem.scale",
                     pyqtgraphDocUrl(f"{_GLPage}/glgraphicsitem", "opengl.GLGraphicsItem.GLGraphicsItem.scale")),
                ],
            ),
            QStepWalkthrough.Step(
                title="L'opacité selon le potentiel",
                explanation=(
                    "<code>volumeColors()</code> part des couleurs de <code>paletteColors()</code>, "
                    "puis remplace leur opacité. <code>colors[:, :, :, 3]</code> désigne le "
                    "quatrième nombre, l'opacité, de toutes les cases. Il reçoit le carré de "
                    "|V|/2, multiplié par l'opacité voulue, de 0 à 1, puis par 255. "
                    "<code>np.abs()</code> rend la valeur absolue. Un faible potentiel devient "
                    "presque transparent et laisse voir l'intérieur. Le volume se dessine couche "
                    "par couche : 40 couches empilées, une par rangée de cases. Sans le carré, "
                    "ces couches de faible opacité s'accumuleraient en un brouillard blanc."
                    "<br><br><code>setData()</code> donne au volume ses nouvelles couleurs. Il "
                    "les remplace en place, sans retirer ni recréer l'élément. À gauche : deux "
                    "lobes, un rouge autour de +q, un bleu autour de −q."
                ),
                run=self.makeTranslucent,
                codeSource=(volumeColors, self.makeTranslucent),
                references=[("GLVolumeItem", pyqtgraphDocUrl(f"{_GLPage}/glvolumeitem", "opengl.GLVolumeItem"))],
            ),
            QStepWalkthrough.Step(
                title="Une coupe du tableau",
                explanation=(
                    "Une <b>coupe</b> montre ce que contient le volume dans un plan, comme la "
                    "coupe de la surface en 3.3. Dans le tableau, "
                    "<code>self.potential[:, :, 20]</code> garde toutes les cases dont le troisième "
                    "indice vaut 20 : toutes les valeurs de x et de y, à une seule hauteur. Le "
                    "résultat est un tableau à deux dimensions, de 40 × 40, comme la carte de "
                    "chaleur de 2.4. La case 20 de z est centrée en z = 0,05, tout près du plan "
                    "des deux charges. Rien n'est encore affiché."
                ),
                run=self.takeSlice,
                references=[("Indexation numpy", numpyPageUrl("user/basics.indexing"))],
            ),
            QStepWalkthrough.Step(
                title="La coupe dans la scène",
                explanation=(
                    "<code>gl.GLImageItem</code> montre une image dans la scène, à plat dans le "
                    "plan z = 0 : un pixel par case, d'une unité de côté. Comme pour "
                    "l'<code>ImageItem</code> de 2.4, le premier indice du tableau suit l'axe x "
                    "de l'image, le second son axe y. <code>sliceColors()</code> part aussi des "
                    "couleurs de <code>paletteColors()</code>, avec la même opacité pour toutes "
                    "les cases, ici 1 : opaque."
                    "<br><br>Comme pour le volume, <code>scale(0.1, 0.1, 1)</code> ramène les "
                    "pixels à 0,1 ; le 1 en z ne change rien, puisque l'image est plate. "
                    "<code>translate()</code> place ensuite l'image de −2 à 2 en x et en y, à la "
                    "hauteur z = 0,05. <code>scale()</code> vient toujours en premier : chaque "
                    "transformation s'applique après les précédentes (notion 3.2), et un "
                    "<code>scale()</code> placé après <code>translate()</code> réduirait aussi "
                    "le déplacement."
                    "<br><br>Le volume reçoit aussi une opacité de 0,3, par <code>setData()</code> "
                    "(étape 5) : moins dense, il laissera lire la coupe."
                    "<br><br>À gauche, le volume pâlit, mais la coupe ne paraît pas : on n'en voit "
                    "au mieux qu'un trait. L'étape suivante dit pourquoi."
                ),
                run=self.addSlice,
                codeSource=(sliceColors, self.addSlice),
                references=[("GLImageItem", pyqtgraphDocUrl(f"{_GLPage}/glimageitem", "opengl.GLImageItem"))],
            ),
            QStepWalkthrough.Step(
                title="Dessiner la coupe d'abord",
                explanation=(
                    "OpenGL, la bibliothèque qui dessine la 3D sous PyQtGraph, retient pour "
                    "chaque pixel de l'écran la profondeur de ce qu'il y a dessiné. Il ne dessine "
                    "plus, à ce pixel, un objet plus éloigné : c'est le <b>test de "
                    "profondeur</b>. Or le volume est dessiné couche par couche, et chaque couche "
                    "note sa profondeur, même là où elle est presque transparente. Dessinée après "
                    "lui, la coupe était cachée par les couches devant elle."
                    "<br><br><code>setDepthValue(-1)</code> fait dessiner la coupe avant les "
                    "autres éléments, qui gardent la valeur 0 : les éléments sont dessinés de la "
                    "plus petite valeur à la plus grande. Malgré son nom, cette valeur ne règle "
                    "que l'<b>ordre de dessin</b>. La profondeur du test, elle, vient de la place "
                    "de chaque objet dans l'espace."
                    "<br><br>Dessinée d'abord, la coupe note à son tour sa profondeur. Les couches "
                    "du volume devant elle se dessinent ensuite par-dessus, par transparence : "
                    "elles la voilent. Celles qui sont derrière ne se dessinent pas : le test de "
                    "profondeur les rejette, la coupe étant plus proche."
                    "<br><br>À gauche : la coupe à plat, rouge autour de +q, bleue autour de −q, "
                    "blanche entre les deux, voilée par le volume devant elle."
                ),
                run=self.drawSliceFirst,
                references=[
                    ("GLGraphicsItem.setDepthValue",
                     pyqtgraphDocUrl(f"{_GLPage}/glgraphicsitem", "opengl.GLGraphicsItem.GLGraphicsItem.setDepthValue")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le plan vertical XZ",
                explanation=(
                    "<code>sliceImage()</code> extrait la coupe du plan choisi. Pour le plan XZ, "
                    "<code>potential[:, index, :]</code> garde les cases dont le deuxième indice, "
                    "celui de y, vaut <code>index</code>. <code>placeSlice()</code> dresse "
                    "l'image dans son plan, puis la place. Elle commence par "
                    "<code>resetTransform()</code>, qui ramène l'image à sa place d'origine, "
                    "sans échelle, rotation ni déplacement : une coupe déplacée plusieurs fois "
                    "ne cumule pas les déplacements."
                    "<br><br>Le raisonnement, pas à pas. Une image se pose à plat, dans le plan "
                    "XY. Chaque transformation s'applique après les précédentes (notion 3.2). "
                    "<code>scale()</code> puis <code>translate(-2, -2, 0)</code> la réduisent et "
                    "la centrent sur l'origine, à plat. <code>rotate()</code> (notion 3.2) la "
                    "tourne ensuite autour d'un axe qui passe par l'origine, sans la décentrer : "
                    "+90° autour de X envoie son axe y vers +Z, d'où le plan XZ. Un dernier "
                    "<code>translate()</code> la pousse le long de l'axe perpendiculaire à son "
                    "plan, ici y, jusqu'à la case choisie. <code>offset</code> est le centre de "
                    "cette case : −2 est le bord du cube, 0,1 la taille d'une case et 0,05 la "
                    "demi-case, comme les centres de l'étape 3."
                    "<br><br><code>showSlice()</code> donne à la coupe sa nouvelle image par "
                    "<code>setData()</code>, puis la place. Ici, elle passe dans le plan vertical "
                    "XZ, à la case 20 de y, en y = 0,05 : le plan des deux charges, vu de face."
                    "<br><br>À cette étape, seule la branche XZ de chaque fonction s'exécute. La "
                    "branche XY refait le placement de l'étape 7 : elle servira à l'étape "
                    "« À vous », pour revenir à ce plan. La dernière branche, celle du plan YZ, "
                    "est l'objet de l'étape suivante."
                ),
                run=self.turnSlice,
                codeSource=(sliceImage, placeSlice, self.showSlice, self.turnSlice),
                references=[
                    ("GLGraphicsItem.resetTransform",
                     pyqtgraphDocUrl(f"{_GLPage}/glgraphicsitem", "opengl.GLGraphicsItem.GLGraphicsItem.resetTransform")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le plan YZ et la transposée",
                explanation=(
                    "Pour le plan YZ, <code>placeSlice()</code> tourne l'image de −90° autour de "
                    "Y. Le sens d'une rotation suit la règle de la main droite (notion 3.2) : "
                    "−90° autour de Y envoie l'axe x de l'image vers +Z. Le premier indice de "
                    "l'image suit donc z. Or le premier indice de <code>potential[index, :, :]</code> "
                    "suit y. <code>.T</code> rend le tableau transposé, dont les lignes et les "
                    "colonnes sont échangées : son premier indice suit alors z, et chaque valeur "
                    "tombe à sa place."
                    "<br><br>Ici, la coupe passe à la case 10 de x, en x = −0,95 : tout près de "
                    "+q, en (−1, 0, 0). Elle montre un disque rouge, vif au centre."
                ),
                run=self.turnSliceSideways,
                codeSource=(sliceImage, placeSlice, self.turnSliceSideways),
                references=[("numpy.ndarray.T", numpyDocUrl("ndarray.T"))],
            ),
            QStepWalkthrough.Step(
                title="Par-dessus tout",
                explanation=(
                    "Depuis l'étape 8, la coupe est dessinée à sa profondeur. Le volume devant "
                    "elle la voile ; ce qui est derrière, elle le cache. L'image est fidèle à "
                    "l'espace : on voit où la coupe traverse les lobes. Mais au fond d'un lobe "
                    "épais, elle se lit mal."
                    "<br><br>L'autre façon : désactiver le test de profondeur pour la coupe seule, "
                    "et la dessiner en dernier. Elle couvre alors le volume partout, même là où "
                    "il est devant elle. Ses couleurs restent nettes, mais la profondeur se "
                    "perd : la coupe semble flotter devant le volume, et cache même les axes."
                    "<br><br><code>drawSliceOnTop()</code> le fait en trois appels :"
                    "<ul>"
                    "<li><code>setGLOptions(\"translucent\")</code> donne à la coupe le réglage "
                    "d'OpenGL qu'elle a par défaut : test de profondeur et transparence. Il sert "
                    "dans les deux cas : avec <code>False</code>, c'est lui qui rétablit le "
                    "test ;</li>"
                    "<li><code>updateGLOptions()</code> change un seul de ces réglages. Il reçoit "
                    "un dictionnaire : la clé <code>GL.GL_DEPTH_TEST</code> nomme le test de "
                    "profondeur, et la valeur <code>False</code> le désactive. La clé vient du "
                    "module <code>GL</code> de PyOpenGL, installé avec la 3D de PyQtGraph et "
                    "importé par <code>from OpenGL import GL</code> ;</li>"
                    "<li><code>setDepthValue(1)</code> fait dessiner la coupe après le volume, "
                    "qui garde la valeur 0 : un ordre de dessin, comme à l'étape 8.</li>"
                    "</ul>"
                    "Avec <code>False</code>, <code>drawSliceOnTop()</code> revient à la "
                    "première façon. Le choix dépend de la question. Où la coupe traverse-t-elle "
                    "les lobes ? À sa profondeur. Que vaut le potentiel dans ce plan ? "
                    "Par-dessus tout."
                    "<br><br><i>Pour l'exemple</i> : <code>compareDrawings()</code> ramène d'abord "
                    "la coupe dans le plan XZ des charges, à la case 20 : la vue de l'étape 9, "
                    "dessinée à sa profondeur. Revenir à l'étape 9 pour comparer les deux "
                    "façons."
                ),
                run=self.compareDrawings,
                codeSource=(self.drawSliceOnTop, self.compareDrawings),
                references=[
                    ("GLGraphicsItem.setGLOptions",
                     pyqtgraphDocUrl(f"{_GLPage}/glgraphicsitem", "opengl.GLGraphicsItem.GLGraphicsItem.setGLOptions")),
                    ("GLGraphicsItem.updateGLOptions",
                     pyqtgraphDocUrl(f"{_GLPage}/glgraphicsitem", "opengl.GLGraphicsItem.GLGraphicsItem.updateGLOptions")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : la coupe",
                explanation=(
                    "Deux étapes « À vous » ferment la notion, chacune avec ses contrôles : la "
                    "coupe ici, puis la charge et l'opacité du volume."
                    "<br><br>Quatre contrôles paraissent sous la vue :"
                    "<ul>"
                    "<li><code>planeCombo</code>, une liste déroulante, choisit le plan. Chaque "
                    "choix porte un texte, lu par <code>currentData()</code> : XY, XZ, YZ, ou un "
                    "texte vide pour « Aucune ». Elle part de XZ ;</li>"
                    "<li><code>positionSlider</code> choisit la case de la coupe le long de l'axe "
                    "perpendiculaire à son plan, de 0 à 39, et part de 20 ;</li>"
                    "<li><code>sliceOpacitySlider</code> règle l'opacité de la coupe, de 0 à "
                    "100 %, et part de 100 % ;</li>"
                    "<li><code>onTopCheck</code>, une case à cocher, choisit la façon de dessiner "
                    "la coupe. Cochée au départ, comme l'étape précédente l'a laissée.</li>"
                    "</ul>"
                    "Le guide appelle <code>connectSliceControls()</code> en arrivant à cette "
                    "étape. Elle relie les trois premiers contrôles au slot "
                    "<code>updateSlice()</code>. Pour « Aucune », il cache la coupe par "
                    "<code>setVisible(False)</code> ; sinon, il la montre et appelle "
                    "<code>showSlice()</code>. La case est reliée directement à "
                    "<code>drawSliceOnTop()</code> : son signal <code>toggled</code> transmet "
                    "l'état de la case, que le slot reçoit. La coupe est mise à jour en place, "
                    "sans être recréée."
                    "<br><br>Promener une coupe XY de bas en haut : les lobes s'élargissent "
                    "puis rétrécissent, et sont les plus vifs au plan des charges. Baisser "
                    "l'opacité de la coupe, case cochée : le volume reparaît entier à travers "
                    "elle. Décocher la case : la moitié du volume située derrière la coupe "
                    "disparaît, rejetée par le test de profondeur, même quand la coupe est "
                    "presque transparente. Choisir « Aucune » pour revoir le volume seul."
                ),
                run=self._exploreSlice,
                codeSource=(self.connectSliceControls, self.updateSlice, self.drawSliceOnTop),
                references=[("GLImageItem", pyqtgraphDocUrl(f"{_GLPage}/glimageitem", "opengl.GLImageItem"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : la charge et l'opacité",
                explanation=(
                    "Deux sélecteurs numériques de plus. <code>chargeSlider</code> règle la charge "
                    "de droite, comme en 3.3 : il va de −20 à 20 et se lit divisé par 10 ; il "
                    "part de −10, soit −1. <code>opacitySlider</code> règle l'opacité du volume, "
                    "de 0 à 100 %, et part de 30 %."
                    "<br><br>Le guide appelle <code>connectChargeControls()</code>, qui relie "
                    "chacun à son slot. <code>updateCharge()</code> change la charge, "
                    "recalcule le potentiel et le volume, puis appelle "
                    "<code>updateSlice()</code> (étape précédente) : la coupe suit les "
                    "contrôles de la coupe. Le calcul, fait d'un coup par numpy, prend moins d'un "
                    "centième de seconde. <code>updateOpacity()</code> ne recalcule "
                    "que les couleurs du volume, pas le potentiel."
                    "<br><br>À +1, les deux charges ont le même signe : le potentiel est positif "
                    "partout, et tout le cube rougit, plus vif autour des charges. À 0, il ne reste "
                    "qu'un lobe."
                ),
                run=self._exploreCharge,
                codeSource=(self.connectChargeControls, self.updateCharge, self.updateOpacity),
                references=[("GLVolumeItem", pyqtgraphDocUrl(f"{_GLPage}/glvolumeitem", "opengl.GLVolumeItem"))],
            ),
        ]
