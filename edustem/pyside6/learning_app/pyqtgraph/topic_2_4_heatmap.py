"""Notion 2.4 : une carte de chaleur, le potentiel électrique d'un dipôle.

Contexte : deux charges opposées, +q en (−1, 0) et −q en (1, 0), créent un
potentiel électrique V défini en chaque point du plan : une valeur par
point. Une carte de chaleur le montre par la couleur de chaque pixel. Les
unités sont réduites (k = 1, charges en multiples de q, distances sans
unité) : seule la forme compte.

Étapes couvertes : un graphique dans une grille (`GraphicsLayoutWidget`,
comme en 1.5), le potentiel calculé d'un coup sur une grille de points
(`np.meshgrid`), son
affichage en image (`ImageItem`) placée par un `QRectF`, une palette
divergente, la barre de couleurs (`ColorBarItem`), les équipotentielles
(`IsocurveItem`), les charges, puis la souris : sa position dans la scène
Qt, en pixels, convertie en coordonnées des données, et le potentiel lu
sous elle.

Chaque étape est une méthode de `QTopicHeatMapTab` : elle lit et modifie
directement `self.plotItem`.
"""

from __future__ import annotations


import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import SIGNAL, QPointF, QRectF, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import removeLayoutItems, resetPlotItem

_ImageItemPage = "api_reference/graphicsItems/imageitem"
_ViewBoxPage = "api_reference/graphicsItems/viewbox"


def chargePotential(x: float | np.ndarray, y: float | np.ndarray, charges: list[list[float]]) -> float | np.ndarray:
    """Le potentiel en (x, y) : la somme des k·q/r de chaque charge [x, y, q], avec k = 1.

    `x` et `y` sont des réels, ou des tableaux de réels de même forme ; le
    résultat a cette forme. Tout près d'une charge, k·q/r grandit sans
    limite : la distance est donc comptée au moins 0,2.
    """
    potential = 0.0
    for chargeX, chargeY, q in charges:
        distance = np.maximum(np.hypot(x - chargeX, y - chargeY), 0.2)
        potential = potential + q / distance
    return potential


def potentialGrid(xs: np.ndarray, ys: np.ndarray, charges: list[list[float]]) -> np.ndarray:
    """Le potentiel en chaque point de la grille.

    `xs` est de forme (n,), `ys` de forme (m,). Rend un tableau de réels de
    forme (n, m) : potential[i, j] vaut V en (xs[i], ys[j]).
    """
    gridX, gridY = np.meshgrid(xs, ys, indexing="ij")
    return chargePotential(gridX, gridY, charges)


class QTopicHeatMapTab(QWidget):
    """Onglet de la notion 2.4 : le potentiel d'un dipôle, en carte de chaleur.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        layoutWidget, plotItem: La grille de graphiques et son graphique,
            créés une seule fois.
        readout: La lecture sous la grille (outil présenté en 1.5).
        charges, xs, ys, potential: Les charges, la grille de points et le
            potentiel calculé, ou None avant leur étape.
        image: L'image du potentiel, ou None.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Carte de chaleur"
    TabToolTip = "Un potentiel en image : palette, barre de couleurs, équipotentielles, lecture à la souris"
    RecommendedPanelWidth = 640
    Objective = (
        "Montrer une grandeur définie en chaque point du plan comme une image en couleurs : le "
        "potentiel électrique d'un dipôle, ses équipotentielles, et sa valeur lue sous la souris."
    )
    KeyConcepts = [
        "Une grandeur du plan se calcule sur une grille de points et se range dans un tableau à "
        "deux dimensions.",
        "Une image est un tableau : chaque case devient un pixel, placé ensuite dans les "
        "coordonnées du graphique.",
        "Une palette associe une couleur à chaque valeur. Une palette divergente distingue le "
        "positif du négatif.",
        "Une équipotentielle relie les points de même potentiel.",
        "La souris se lit en pixels de la scène Qt, puis se convertit en coordonnées des données.",
    ]
    KeyApis = [
        "GraphicsLayoutWidget", "ImageItem", "ImageItem.setRect", "ImageItem.setColorMap",
        "ColorBarItem", "IsocurveItem", "QGraphicsScene", "GraphicsScene.sigMouseMoved",
        "ViewBox.mapSceneToView",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.charges: list[list[float]] | None = None
        self.xs: np.ndarray | None = None
        self.ys: np.ndarray | None = None
        self.potential: np.ndarray | None = None
        self.image: pg.ImageItem | None = None

        self.createLayoutWidget()
        self.readout = QReadoutLabel()

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.layoutWidget, 1)
        contentLayout.addWidget(self.readout)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Vide le graphique et la grille, déconnecte la souris et vide la lecture."""
        # Seule cette notion connecte le signal de la souris de la scène : tout est déconnecté.
        scene = self.layoutWidget.scene()
        if scene.receivers(SIGNAL("sigMouseMoved(PyObject)")) > 0:
            scene.sigMouseMoved.disconnect()
        resetPlotItem(self.plotItem)
        removeLayoutItems(self.layoutWidget, keep=(self.plotItem,))
        self.readout.clear()
        self.charges = None
        self.xs = None
        self.ys = None
        self.potential = None
        self.image = None

    # -- Étapes ------------------------------------------------------------------------------------

    def createLayoutWidget(self) -> None:
        """Crée la grille de graphiques, et son graphique dans la première cellule."""
        self.layoutWidget = pg.GraphicsLayoutWidget()
        self.plotItem = self.layoutWidget.addPlot(row=0, col=0)

    def setUpPlot(self) -> None:
        """Titre, axes sans unité et échelle égale."""
        self.plotItem.setTitle("Potentiel électrique d'un dipôle")
        self.plotItem.setLabel("bottom", "x")
        self.plotItem.setLabel("left", "y")
        self.plotItem.setAspectLocked(True)

    def _formulasOnly(self) -> None:
        """Les formules sont des fonctions : rien n'est calculé ni tracé à cette étape."""

    def computePotential(self) -> None:
        """Les deux charges, puis le potentiel sur une grille de 161 × 121 points."""
        self.charges = [[-1.0, 0.0, 1.0], [1.0, 0.0, -1.0]]
        self.xs = np.linspace(-4, 4, 161)
        self.ys = np.linspace(-3, 3, 121)
        self.potential = potentialGrid(self.xs, self.ys, self.charges)

    def showImage(self) -> None:
        """Le tableau du potentiel en image, étirée sur la zone de la grille."""
        self.image = pg.ImageItem(self.potential)
        step = 0.05
        self.image.setRect(QRectF(-4 - step / 2, -3 - step / 2, 8 + step, 6 + step))
        self.plotItem.addItem(self.image)

    def applyColorMap(self) -> None:
        """Une palette divergente : bleu pour le négatif, blanc pour 0, rouge pour le positif."""
        self.image.setColorMap(pg.colormap.get("CET-D1"))
        self.image.setLevels((-1.5, 1.5))

    def addColorBar(self) -> None:
        """La barre de couleurs, dans la deuxième cellule de la grille."""
        colorBar = pg.ColorBarItem(values=(-1.5, 1.5), colorMap=pg.colormap.get("CET-D1"),
                                   label="Potentiel V")
        colorBar.setImageItem(self.image)
        self.layoutWidget.addItem(colorBar, row=0, col=1)

    def addEquipotentials(self) -> None:
        """Sept équipotentielles, de −1 à 1, en gris sombre, attachées à l'image."""
        for level in [-1, -0.5, -0.25, 0, 0.25, 0.5, 1]:
            isocurve = pg.IsocurveItem(data=self.potential, level=level, pen=pg.mkPen((40, 40, 40), width=2))
            isocurve.setParentItem(self.image)

    def addCharges(self) -> None:
        """Chaque charge : un point rouge si elle est positive, bleu sinon, et son nom."""
        for x, y, q in self.charges:
            if q > 0:
                color = "r"
                name = "+q"
            else:
                color = "b"
                name = "−q"
            self.plotItem.plot([x], [y], pen=None, symbol="o", symbolSize=14, symbolBrush=color)
            label = pg.TextItem(name, color="w", anchor=(0.5, 1.4))
            label.setPos(x, y)
            self.plotItem.addItem(label)

    def followMouseInScene(self) -> None:
        """Relie le mouvement de la souris au slot qui écrit sa position dans la scène."""
        self.layoutWidget.scene().sigMouseMoved.connect(self.showScenePosition)
        self.readout.setText("Promener la souris sur le graphique.")

    @Slot(object)
    def showScenePosition(self, position: QPointF) -> None:
        """Écrit la position de la souris dans la scène, en pixels."""
        self.readout.setText(f"Scène : x = {position.x():.0f} px, y = {position.y():.0f} px")

    def followMouseInData(self) -> None:
        """Remplace le slot de la souris par celui qui écrit sa position en coordonnées des données."""
        mouseMoved = self.layoutWidget.scene().sigMouseMoved
        mouseMoved.disconnect(self.showScenePosition)
        mouseMoved.connect(self.showDataPosition)

    @Slot(object)
    def showDataPosition(self, position: QPointF) -> None:
        """Convertit la position de la souris en coordonnées des données, puis l'écrit."""
        point = self.plotItem.getViewBox().mapSceneToView(position)
        text = f"Données : x = {point.x():.2f} ; y = {point.y():.2f}"
        self.readout.setText(text.replace(".", ","))

    def followMouseForPotential(self) -> None:
        """Remplace le slot de la souris par celui qui écrit aussi le potentiel."""
        mouseMoved = self.layoutWidget.scene().sigMouseMoved
        mouseMoved.disconnect(self.showDataPosition)
        mouseMoved.connect(self.showPotential)

    @Slot(object)
    def showPotential(self, position: QPointF) -> None:
        """Écrit les coordonnées du point sous la souris et le potentiel en ce point."""
        point = self.plotItem.getViewBox().mapSceneToView(position)
        potential = chargePotential(point.x(), point.y(), self.charges)
        text = f"x = {point.x():.2f} ; y = {point.y():.2f} : V = {potential:.3f}"
        self.readout.setText(text.replace(".", ","))

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : un graphique dans une grille",
                explanation=(
                    "Rien de nouveau : les gestes de la notion 1.5. "
                    "<code>pg.GraphicsLayoutWidget</code> est un widget qui range des graphiques "
                    "dans une <b>grille de graphiques</b>, et <code>addPlot(row=0, col=0)</code> y crée le graphique "
                    "dans la première cellule. La deuxième cellule recevra la barre de couleurs. "
                    "L'échelle égale (notion 1.7) garde au plan ses proportions. Les distances "
                    "sont sans unité : les axes n'en portent pas."
                ),
                run=self.setUpPlot,
                codeSource=(self.createLayoutWidget, self.setUpPlot),
                references=[
                    ("GraphicsLayoutWidget", pyqtgraphDocUrl("api_reference/widgets/graphicslayoutwidget",
                                                             "GraphicsLayoutWidget")),
                    ("ViewBox.setAspectLocked", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setAspectLocked")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le potentiel en un point",
                explanation=(
                    "Une charge q crée autour d'elle un potentiel électrique V = k·q/r : V en "
                    "volts, q en coulombs, r la distance à la charge en mètres, et "
                    "k = 8,99 × 10⁹ N·m²/C². Le potentiel de plusieurs charges est la somme de "
                    "leurs potentiels. Le <b>dipôle</b> : une charge +q en (−1, 0) et une charge "
                    "−q en (1, 0)."
                    "<br><br>Ici, k = 1, les charges sont des multiples de q et les distances "
                    "sont sans unité : seule la forme compte. Chaque charge est une liste "
                    "<code>[x, y, q]</code>."
                    "<br><br><code>chargePotential(x, y, charges)</code> rend le potentiel en un "
                    "point, ou en tout un tableau de points d'un coup. Sa boucle parcourt les "
                    "charges, chacune en trois variables, <code>chargeX</code>, <code>chargeY</code> "
                    "et <code>q</code>. "
                    "<code>np.hypot(dx, dy)</code> rend √(dx² + dy²), la distance."
                    "<br><br>Près d'une charge, k·q/r grandit sans limite : la distance est "
                    "comptée au moins 0,2, une approximation qui suffit ici. "
                    "<code>max()</code> de Python rend le plus grand élément d'une suite : il ne "
                    "compare pas deux tableaux case par case. <code>np.maximum(a, b)</code> le "
                    "fait, et garde dans chaque case la plus grande des deux valeurs. Rien n'est "
                    "encore calculé."
                ),
                run=self._formulasOnly,
                codeSource=(chargePotential,),
                references=[("numpy.maximum", numpyDocUrl("maximum"))],
            ),
            QStepWalkthrough.Step(
                title="Le potentiel sur une grille de points",
                explanation=(
                    "<code>potentialGrid()</code> construit une <b>grille de points</b>, "
                    "à ne pas confondre avec la grille de graphiques : un tableau des points où "
                    "calculer. Elle la construit par "
                    "<code>np.meshgrid(xs, ys, indexing=\"ij\")</code>. Elle rend deux tableaux "
                    "de forme (161, 121) : <code>gridX[i, j]</code> vaut <code>xs[i]</code>, et "
                    "<code>gridY[i, j]</code> vaut <code>ys[j]</code>. Chaque case porte ainsi "
                    "les coordonnées d'un point. Avec <code>indexing=\"ij\"</code>, le premier "
                    "indice suit x. Le potentiel se calcule ensuite sur toute la grille d'un "
                    "appel : <code>potential[i, j]</code> est le potentiel en "
                    "(<code>xs[i]</code>, <code>ys[j]</code>)."
                    "<br><br><i>Pour l'exemple</i> : la grille va de −4 à 4 en x et de −3 à 3 en y, un "
                    "point tous les 0,05. Rien n'est encore affiché."
                ),
                run=self.computePotential,
                codeSource=(potentialGrid, self.computePotential),
                references=[("numpy.meshgrid", numpyDocUrl("meshgrid"))],
            ),
            QStepWalkthrough.Step(
                title="Un tableau devenu image",
                explanation=(
                    "<code>pg.ImageItem(tableau)</code> est l'élément graphique d'une image : "
                    "chaque case d'un tableau à deux dimensions devient un pixel. Le premier "
                    "indice va vers la droite, le second vers le haut. Sans palette, l'image est "
                    "en niveaux de gris : clair pour une valeur haute, sombre pour une basse."
                    "<br><br>Par défaut, un pixel mesure une unité des axes : l'image irait de 0 "
                    "à 161 en x. <code>setRect()</code> reçoit un rectangle "
                    "<code>QRectF(x, y, largeur, hauteur)</code>, en unités des axes, et y étire "
                    "l'image. (x, y) est le coin aux plus petites valeurs : en bas à gauche, "
                    "puisque y monte. Chaque pixel est centré sur son point de grille : le rectangle "
                    "déborde donc d'un demi-pas (<code>step / 2</code>) de chaque côté."
                    "<br><br>À gauche, le potentiel en niveaux de gris : clair autour de +q, à "
                    "gauche, sombre autour de −q, à droite."
                ),
                run=self.showImage,
                references=[
                    ("ImageItem", pyqtgraphDocUrl(_ImageItemPage, "ImageItem")),
                    ("ImageItem.setRect", pyqtgraphDocUrl(_ImageItemPage, "ImageItem.setRect")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une palette de couleurs",
                explanation=(
                    "Une <b>palette</b> associe une couleur à chaque valeur. "
                    "<code>pg.colormap.get(nom)</code> rend la palette de ce nom, et "
                    "<code>setColorMap()</code> la donne à l'image. <code>\"CET-D1\"</code> est "
                    "une palette <b>divergente</b> : bleu, blanc, rouge. Elle convient à une "
                    "grandeur qui change de signe. <code>pg.colormap.listMaps()</code> rend la "
                    "liste des noms disponibles, dont celui-ci."
                    "<br><br><code>setLevels((-1.5, 1.5))</code> fixe les valeurs des deux bouts "
                    "de la palette. Symétriques, ils font tomber 0 sur le blanc. Au-delà, la "
                    "couleur sature : près des charges, le potentiel dépasse 1,5."
                    "<br><br>Une image dont chaque couleur dit une valeur, comme celle-ci, "
                    "s'appelle une <b>carte de chaleur</b> : c'est le sujet de la notion."
                ),
                run=self.applyColorMap,
                references=[
                    ("colormap.get", pyqtgraphDocUrl("api_reference/colormap", "colormap.get")),
                    ("ImageItem.setColorMap", pyqtgraphDocUrl(_ImageItemPage, "ImageItem.setColorMap")),
                    ("ImageItem.setLevels", pyqtgraphDocUrl(_ImageItemPage, "ImageItem.setLevels")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La barre de couleurs",
                explanation=(
                    "<code>pg.ColorBarItem</code> est la <b>barre de couleurs</b> : une règle qui "
                    "montre quelle valeur porte chaque couleur. Elle reçoit les valeurs de ses "
                    "deux bouts (<code>values</code>), la palette et un titre. "
                    "<code>setImageItem()</code> la lie à l'image : l'image prend alors la "
                    "palette et les valeurs de la barre, qui l'emportent sur celles de l'étape "
                    "précédente. Elles sont ici les mêmes, et l'image ne change pas. Sans barre, "
                    "l'étape précédente suffit. "
                    "<code>addItem(élément, row=0, col=1)</code> la range dans la deuxième "
                    "cellule de la grille de graphiques."
                    "<br><br>La barre réagit à la souris : ses deux bouts, en haut et en bas de "
                    "la bande de couleurs, se saisissent et se font glisser. L'étape « À vous » "
                    "s'en servira."
                ),
                run=self.addColorBar,
                references=[("ColorBarItem", pyqtgraphDocUrl("api_reference/graphicsItems/colorbaritem",
                                                             "ColorBarItem"))],
            ),
            QStepWalkthrough.Step(
                title="Les équipotentielles",
                explanation=(
                    "Une <b>équipotentielle</b> relie les points de même potentiel. "
                    "<code>pg.IsocurveItem</code> trace la courbe où le tableau "
                    "<code>data</code> vaut <code>level</code>, ici pour sept niveaux, avec un "
                    "stylo gris sombre, lisible sur le bleu comme sur le rouge. Le niveau 0 est "
                    "la droite x = 0, à égale distance des deux charges."
                    "<br><br>La courbe est calculée en indices du tableau : de 0 à 161 en x. "
                    "<code>addItem()</code> la placerait donc là, loin de l'image. "
                    "<code>setParentItem(self.image)</code> (notion 2.3) en fait plutôt un enfant "
                    "de l'image : il suit le placement de son parent, ici le rectangle de "
                    "<code>setRect()</code>, et s'affiche avec lui."
                ),
                run=self.addEquipotentials,
                references=[
                    ("IsocurveItem", pyqtgraphDocUrl("api_reference/graphicsItems/isocurveitem", "IsocurveItem")),
                    ("QGraphicsItem.setParentItem", qtDocUrl("QtWidgets", "QGraphicsItem", "setParentItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Les charges",
                explanation=(
                    "Une boucle sur <code>self.charges</code>, comme dans "
                    "<code>chargePotential()</code>. Une charge positive est "
                    "un point rouge nommé « +q », une négative un point bleu nommé « −q ». Les "
                    "gestes sont ceux des notions 1.2 (un point par <code>plot()</code>) et 2.2 "
                    "(<code>TextItem</code>, son ancre et <code>setPos()</code>). L'ancre "
                    "(0,5 ; 1,4) sort du cadre du texte : une fraction plus grande que 1 pose le "
                    "texte encore plus haut, ici 0,4 hauteur de texte au-dessus du point."
                ),
                run=self.addCharges,
                references=[("TextItem", pyqtgraphDocUrl("api_reference/graphicsItems/textitem", "TextItem"))],
            ),
            QStepWalkthrough.Step(
                title="La scène et la souris",
                explanation=(
                    "Tout élément d'un graphique 2D vit dans une <b>scène Qt</b> "
                    "(<code>QGraphicsScene</code>, du module <code>PySide6.QtWidgets</code>) : "
                    "l'espace que le widget dessine, mesuré en pixels. À ne pas confondre avec la "
                    "scène 3D du chapitre 3. <code>scene()</code> rend la scène du widget. "
                    "PyQtGraph lui ajoute le signal <code>sigMouseMoved</code>, émis à chaque "
                    "mouvement de la souris avec sa position dans la scène, un "
                    "<code>QPointF</code>."
                    "<br><br><code>followMouseInScene()</code> connecte ce signal au slot "
                    "<code>showScenePosition()</code>, qui écrit la position en pixels dans la "
                    "lecture (notion 1.5)."
                    "<br><br><i>Essai</i> : promener la souris. x croît vers la droite, y vers le "
                    "bas, depuis le coin du widget."
                ),
                run=self.followMouseInScene,
                codeSource=(self.followMouseInScene, self.showScenePosition),
                references=[
                    ("QGraphicsScene", qtDocUrl("QtWidgets", "QGraphicsScene")),
                    ("GraphicsScene", pyqtgraphDocUrl("api_reference/graphicsscene/graphicsscene",
                                                      "GraphicsScene")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Des pixels aux données",
                explanation=(
                    "Des pixels ne disent rien du potentiel : il faut la position en coordonnées "
                    "des données. <code>getViewBox()</code> rend la zone visible du graphique "
                    "(notion 1.7). Sa méthode <code>mapSceneToView(position)</code> reçoit une "
                    "position de la scène et rend le <code>QPointF</code> correspondant dans les "
                    "coordonnées des axes."
                    "<br><br><code>followMouseInData()</code> déconnecte d'abord le slot de "
                    "l'étape précédente : <code>disconnect(slot)</code> retire cette connexion (notion 1.8). "
                    "Puis il connecte le slot <code>showDataPosition()</code>."
                    "<br><br><i>Essai</i> : promener la souris. La lecture donne x et y comme les "
                    "axes, y croissant vers le haut."
                ),
                run=self.followMouseInData,
                codeSource=(self.followMouseInData, self.showDataPosition),
                references=[("ViewBox.mapSceneToView", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.mapSceneToView"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : lire le potentiel",
                explanation=(
                    "<code>followMouseForPotential()</code> remplace encore le slot, cette fois "
                    "par <code>showPotential()</code>. Celui-ci convertit la position comme à "
                    "l'étape précédente, puis calcule le potentiel en ce point par "
                    "<code>chargePotential()</code>."
                    "<br><br>Promener la souris le long d'une équipotentielle : V ne change pas. "
                    "Sur la droite x = 0, V vaut 0. Puis faire glisser l'un des bouts de la barre "
                    "de couleurs : la palette se resserre sur les faibles valeurs, et l'image "
                    "suit."
                ),
                run=self.followMouseForPotential,
                codeSource=(self.followMouseForPotential, self.showPotential),
                references=[("ColorBarItem", pyqtgraphDocUrl("api_reference/graphicsItems/colorbaritem",
                                                             "ColorBarItem"))],
            ),
        ]
