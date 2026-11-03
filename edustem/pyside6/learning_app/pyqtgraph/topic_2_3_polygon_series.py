"""Notion 2.3 : une série de polygones, un quadrillage transformé par une matrice.

Contexte : une matrice 2 × 2 transforme tout le plan. Un quadrillage de
carrés le montre : chaque carré devient un parallélogramme, et tous ont la
même aire, celle du carré multipliée par la valeur absolue du déterminant.
Les seize carrés forment une série : on veut les transformer, les cacher
et les nommer ensemble, mais aussi en lire ou en changer un seul.

PyQtGraph ne gère pas de série de polygones : il n'a ni élément qui
regroupe des polygones de Qt, ni entrée de légende pour eux. Qt fournit le
regroupement (un parent et ses enfants) ; la légende demande un élément
témoin et deux lignes de gestion. La notion le dit.

Étapes couvertes : un récapitulatif (graphique, échelle égale, légende),
la série sous un parent (`setParentItem`), une matrice appliquée au parent
(`QTransform`), une entrée de légende pour la série (élément témoin), la
série cachée par la légende (`visibleChanged`), les sommets transformés
calculés avec numpy, le déterminant, un sommet changé seul (`polygon()`,
`setPolygon()`), puis deux cibles mobiles qui règlent les colonnes de la
matrice.

Chaque étape est une méthode de `QTopicPolygonSeriesTab` : elle lit et
modifie directement `self.plotWidget`.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QPointF, Slot
from PySide6.QtGui import QPolygonF, QTransform
from PySide6.QtWidgets import QGraphicsItemGroup, QGraphicsPolygonItem, QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetPlotItem


class QTopicPolygonSeriesTab(QWidget):
    """Onglet de la notion 2.3 : un quadrillage de seize carrés, transformé par une matrice.

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
        legend: La légende du graphique, ou None avant son étape.
        series: Le parent des seize carrés, ou None avant son étape.
        matrix: La matrice A, un tableau de réels de forme (2, 2), ou None.
        legendSample: L'élément témoin de la légende, ou None.
        outline: Le contour jaune, image calculée du carré unité, ou None.
        handles: Les deux cibles des colonnes de A, vide avant leur étape.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Séries de polygones"
    TabToolTip = "Seize polygones sous un parent : une matrice, une étiquette, un sommet à la fois"
    RecommendedPanelWidth = 640
    Objective = (
        "Gérer une série de polygones : les ranger sous un parent qui les transforme, les cache et "
        "les nomme ensemble, puis changer tout un polygone ou un seul sommet. Le prétexte : une "
        "matrice qui transforme un quadrillage."
    )
    KeyConcepts = [
        "Une série de polygones se range sous un parent : le parent transmet à ses enfants sa "
        "position, sa transformation et sa visibilité.",
        "Les colonnes d'une matrice 2 × 2 sont les images des vecteurs (1, 0) et (0, 1).",
        "Transformer l'affichage ne change pas les sommets : pour les connaître, on les calcule.",
        "La légende ne connaît que les éléments de PyQtGraph : une série de Qt y entre par un "
        "élément témoin.",
        "Un polygone se change en entier, ou un sommet à la fois, sur la copie que rend "
        "<code>polygon()</code>.",
        "La valeur absolue du déterminant est le facteur d'aire de la transformation.",
    ]
    KeyApis = [
        "QGraphicsItem.setParentItem", "QGraphicsItemGroup", "QTransform", "LegendItem.addItem",
        "QGraphicsObject.visibleChanged", "QGraphicsPolygonItem.polygon", "TargetItem",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.legend: pg.LegendItem | None = None
        self.series: QGraphicsItemGroup | None = None
        self.matrix: np.ndarray | None = None
        self.legendSample: pg.PlotDataItem | None = None
        self.outline: QGraphicsPolygonItem | None = None
        self.handles: list[pg.TargetItem] = []

        self.createPlotWidget()
        self.readout = QReadoutLabel()

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.plotWidget, 1)
        contentLayout.addWidget(self.readout)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Ramène le graphique à son état d'origine (voir plot_reset.py) et vide la lecture."""
        resetPlotItem(self.plotWidget.getPlotItem())
        self.readout.clear()
        self.legend = None
        self.series = None
        self.matrix = None
        self.legendSample = None
        self.outline = None
        self.handles = []

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidget(self) -> None:
        """Crée le widget du graphique, vide."""
        self.plotWidget = pg.PlotWidget()

    def setUpPlot(self) -> None:
        """Titre, axes, grille, zone visible imposée, échelle égale, et la légende, gardée."""
        self.plotWidget.setTitle("Une matrice transforme le plan")
        self.plotWidget.setLabel("bottom", "x")
        self.plotWidget.setLabel("left", "y")
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)
        self.plotWidget.setXRange(-6, 6, padding=0)
        self.plotWidget.setYRange(-4, 4, padding=0)
        self.plotWidget.setAspectLocked(True)
        self.legend = self.plotWidget.addLegend(offset=(10, 10))

    def createSeries(self) -> None:
        """Seize carrés de côté 1, en damier, tous enfants d'un même parent."""
        self.series = QGraphicsItemGroup()
        self.plotWidget.addItem(self.series)
        brushes = [pg.mkBrush(70, 130, 230, 170), pg.mkBrush(230, 150, 40, 170)]
        for row in range(4):
            for column in range(4):
                x = column - 2
                y = row - 2
                square = QGraphicsPolygonItem(QPolygonF([QPointF(x, y), QPointF(x + 1, y),
                                                         QPointF(x + 1, y + 1), QPointF(x, y + 1)]))
                square.setPen(pg.mkPen("w", width=1))
                square.setBrush(brushes[(row + column) % 2])
                square.setParentItem(self.series)

    def shearSeries(self) -> None:
        """Un cisaillement, la matrice A, appliqué au parent : toute la série se transforme."""
        self.matrix = np.array([[1.0, 1.0],
                                [0.0, 1.0]])
        self.series.setTransform(QTransform(self.matrix[0, 0], self.matrix[1, 0],
                                          self.matrix[0, 1], self.matrix[1, 1], 0, 0))

    def labelSeries(self) -> None:
        """Une seule entrée de légende pour la série, par un élément témoin jamais tracé."""
        self.legendSample = pg.PlotDataItem(pen=pg.mkPen("w"), fillLevel=0, fillBrush=(70, 130, 230, 170))
        self.legend.addItem(self.legendSample, "Carrés transformés (16)")

    def connectLegendSample(self) -> None:
        """Relie la visibilité de l'élément témoin au slot qui montre ou cache la série."""
        self.legendSample.visibleChanged.connect(self.updateSeriesVisibility)

    @Slot()
    def updateSeriesVisibility(self) -> None:
        """Montre ou cache toute la série, comme le témoin de la légende."""
        self.series.setVisible(self.legendSample.isVisible())

    def computeImage(self) -> None:
        """L'image du carré unité par A, calculée avec numpy, en contour jaune."""
        corners = np.array([[0.0, 1.0, 1.0, 0.0],
                            [0.0, 0.0, 1.0, 1.0]])
        image = self.matrix @ corners
        points = [QPointF(x, y) for x, y in zip(image[0, :], image[1, :])]
        self.outline = QGraphicsPolygonItem(QPolygonF(points))
        self.outline.setPen(pg.mkPen("y", width=3))
        self.plotWidget.addItem(self.outline)

    def measureArea(self) -> None:
        """Le déterminant de A, et l'aire de chaque carré transformé, dans la lecture."""
        determinant = np.linalg.det(self.matrix)
        text = f"det A = {determinant:.2f} : chaque carré a maintenant une aire de {abs(determinant):.2f}"
        self.readout.setText(text.replace(".", ","))

    def moveOneVertex(self) -> None:
        """Le sommet d'indice 1 du contour, l'image de (1, 0), déplacé seul en (1,5 ; −0,5)."""
        polygon = self.outline.polygon()
        polygon[1] = QPointF(1.5, -0.5)
        self.outline.setPolygon(polygon)

    def addColumnHandles(self) -> None:
        """Deux cibles mobiles, rouge et verte, au bout des colonnes de A, reliées au slot qui met tout à jour."""
        self.handles = []
        colors = ["r", "g"]
        for column in range(2):
            handle = pg.TargetItem(pos=(self.matrix[0, column], self.matrix[1, column]), size=16,
                                   movable=True, pen=pg.mkPen(colors[column], width=2))
            handle.sigPositionChanged.connect(self.updateMatrix)
            self.plotWidget.addItem(handle)
            self.handles.append(handle)

    @Slot()
    def updateMatrix(self) -> None:
        """Relit les colonnes de A sur les cibles, puis met à jour la série, le contour et la lecture."""
        first = self.handles[0].pos()
        second = self.handles[1].pos()
        self.matrix = np.array([[first.x(), second.x()],
                                [first.y(), second.y()]])
        self.series.setTransform(QTransform(first.x(), first.y(), second.x(), second.y(), 0, 0))
        polygon = self.outline.polygon()
        polygon[1] = first
        polygon[2] = first + second
        polygon[3] = second
        self.outline.setPolygon(polygon)
        self.measureArea()

    def _exploreMatrix(self) -> None:
        """Ajoute les cibles, puis appelle le slot une première fois."""
        self.addColumnHandles()
        self.updateMatrix()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        polygonItemUrl = qtDocUrl("QtWidgets", "QGraphicsPolygonItem")
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : graphique, échelle égale, légende",
                explanation=(
                    "Rien de nouveau : les gestes de la notion 1.1 pour le graphique, ceux de la "
                    "notion 1.2 pour la zone visible, et l'échelle égale de la notion 1.7. Comme "
                    "en 2.2, la zone visible est imposée avant de verrouiller les proportions. "
                    "<code>addLegend()</code> rend la légende qu'il crée : "
                    "<code>self.legend</code> la garde, pour y inscrire une entrée à la main plus "
                    "loin."
                ),
                run=self.setUpPlot,
                codeSource=(self.createPlotWidget, self.setUpPlot),
                references=[
                    ("PlotItem.addLegend", pyqtgraphDocUrl("api_reference/graphicsItems/plotitem",
                                                           "PlotItem.addLegend")),
                    ("ViewBox.setAspectLocked", pyqtgraphDocUrl("api_reference/graphicsItems/viewbox",
                                                                "ViewBox.setAspectLocked")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une série sous un parent",
                explanation=(
                    "Qt regroupe des éléments graphiques sous un parent : un geste sur le parent "
                    "vaut pour tous. PyQtGraph n'a pas d'élément qui gère une série de polygones ; "
                    "le parent de Qt en tient lieu. Ici, seize carrés, chacun un "
                    "<code>QGraphicsPolygonItem</code> (notion 2.1). Ajoutés un à un par "
                    "<code>addItem()</code>, ils seraient seize éléments indépendants : pour les "
                    "tourner, les cacher ou les retirer, seize appels."
                    "<br><br><code>setParentItem(parent)</code>, hérité de "
                    "<code>QGraphicsItem</code> et rencontré à la notion 1.7 pour la barre "
                    "d'échelle, fait d'un élément l'<b>enfant</b> d'un autre :"
                    "<ul>"
                    "<li>l'enfant est affiché avec son parent : seul le parent est ajouté au "
                    "graphique ;</li>"
                    "<li>ses coordonnées se comptent dans le repère du parent ;</li>"
                    "<li>ce que le parent subit, l'enfant le subit : sa position, sa "
                    "transformation, sa visibilité, son retrait.</li>"
                    "</ul>"
                    "Le parent est ici un <code>QGraphicsItemGroup</code>, du module "
                    "<code>PySide6.QtWidgets</code> : un élément de Qt sans dessin propre, fait "
                    "pour regrouper. <code>self.series</code> le garde."
                    "<br><br><i>Pour l'exemple</i> : les carrés vont de −2 à 2 sur chaque axe, et "
                    "<code>(row + column) % 2</code> alterne les deux pinceaux, en damier."
                ),
                run=self.createSeries,
                references=[
                    ("QGraphicsItem.setParentItem", qtDocUrl("QtWidgets", "QGraphicsItem", "setParentItem")),
                    ("QGraphicsItemGroup", qtDocUrl("QtWidgets", "QGraphicsItemGroup")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le parent transforme toute la série",
                explanation=(
                    "Une transformation du parent vaut pour tous ses enfants : "
                    "<code>setTransform()</code> (notion 2.2), appelé une seule fois sur le "
                    "parent, transforme les seize carrés. <code>setTransform(QTransform())</code>, "
                    "la matrice identité, les ramènerait en carrés. <code>setVisible(False)</code> "
                    "sur le parent les cacherait tous."
                    "<br><br>Ici, la matrice A = (1, 1 ; 0, 1), écrite rangée par rangée comme en "
                    "2.2, est un <b>cisaillement</b> : x′ = x + y et "
                    "y′ = y. Chaque horizontale glisse d'autant plus qu'elle est haute, et les "
                    "carrés deviennent des parallélogrammes. <code>self.matrix</code> la garde "
                    "dans un tableau numpy de forme (2, 2)."
                    "<br><br><code>QTransform(m11, m12, m21, m22, dx, dy)</code> construit une "
                    "matrice de Qt (notion 2.2) à partir de ses nombres. Piège : Qt les range par "
                    "images de vecteurs. (m11, m12) est l'image de (1, 0), la première colonne "
                    "de A ; (m21, m22) est l'image de (0, 1), la seconde colonne. D'où l'ordre "
                    "<code>A[0, 0], A[1, 0], A[0, 1], A[1, 1]</code>. dx et dy, nuls ici, "
                    "déplaceraient en plus la figure."
                ),
                run=self.shearSeries,
                references=[
                    ("QTransform", qtDocUrl("QtGui", "QTransform", "__init__")),
                    ("QGraphicsItem.setTransform", qtDocUrl("QtWidgets", "QGraphicsItem", "setTransform")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une entrée de légende pour la série",
                explanation=(
                    "La légende n'inscrit d'elle-même que les éléments de PyQtGraph nommés "
                    "(<code>name</code>, notion 1.1). Les carrés sont des éléments de Qt, et la "
                    "série ne doit avoir qu'une entrée. PyQtGraph s'arrête là : la série demande "
                    "un peu de gestion, écrite ici."
                    "<br><br><code>self.legend.addItem(élément, nom)</code> inscrit un élément "
                    "choisi. On lui donne un <b>élément témoin</b> : un <code>PlotDataItem</code> "
                    "vide, jamais ajouté au graphique. La légende ne lit que son stylo et son "
                    "remplissage (<code>fillLevel</code> et <code>fillBrush</code>, notion 1.6) "
                    "pour dessiner l'échantillon. La légende montre une entrée, avec un "
                    "échantillon bleu."
                ),
                run=self.labelSeries,
                references=[
                    ("LegendItem.addItem", pyqtgraphDocUrl("api_reference/graphicsItems/legenditem",
                                                           "LegendItem.addItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Cacher la série par la légende",
                explanation=(
                    "Un clic sur l'échantillon de la légende cache l'élément témoin (notion 1.2), "
                    "pas la série. Tout élément de PyQtGraph émet le signal "
                    "<code>visibleChanged</code> de Qt quand il est montré ou caché. Ce signal "
                    "appartient à <code>QGraphicsObject</code>, la classe de Qt dont héritent "
                    "les éléments graphiques de PyQtGraph. "
                    "<code>connectLegendSample()</code> le relie au slot "
                    "<code>updateSeriesVisibility()</code>, qui donne à la série la visibilité du "
                    "témoin, par son parent."
                    "<br><br><i>Essai</i> : cliquer l'échantillon de la légende, deux fois. La "
                    "série disparaît, puis revient."
                ),
                run=self.connectLegendSample,
                codeSource=(self.connectLegendSample, self.updateSeriesVisibility),
                references=[
                    ("QGraphicsObject.visibleChanged", qtDocUrl("QtWidgets", "QGraphicsObject", "visibleChanged")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Les sommets transformés, calculés",
                explanation=(
                    "Le parent transforme l'affichage, mais les sommets des carrés ne changent "
                    "pas : ils restent ceux des carrés. Pour connaître les coordonnées "
                    "transformées, on les calcule."
                    "<br><br><code>corners</code> range les quatre sommets du carré unité dans un "
                    "tableau de forme (2, 4) : une colonne par sommet, x en haut, y en bas. "
                    "<code>self.matrix @ corners</code> multiplie A par chaque colonne d'un coup : "
                    "<code>@</code> est le produit matriciel de numpy. Le résultat a la même "
                    "forme, une colonne par sommet transformé. Ses deux rangées, réunies par "
                    "<code>zip()</code>, donnent les <code>QPointF</code> du polygone (notion "
                    "2.1). Le <b>contour</b> jaune recouvre exactement le carré transformé de "
                    "l'origine. Il n'est pas rempli : sans <code>setBrush()</code>, le pinceau "
                    "d'un polygone de Qt est vide. <code>self.outline</code> le garde : la suite le change, un "
                    "sommet à la fois."
                ),
                run=self.computeImage,
                references=[("numpy.matmul", numpyDocUrl("matmul"))],
            ),
            QStepWalkthrough.Step(
                title="Le déterminant mesure l'aire",
                explanation=(
                    "Le <b>déterminant</b> de A = (a, b ; c, d) vaut ad − bc, et "
                    "<code>np.linalg.det()</code> le calcule. Une figure transformée par A voit "
                    "son aire multipliée par |det A|. Le cisaillement a un déterminant de 1 : il "
                    "déforme les carrés sans changer leur aire. La lecture (notion 1.5) l'écrit."
                ),
                run=self.measureArea,
                references=[("numpy.linalg.det", numpyDocUrl("linalg.det"))],
            ),
            QStepWalkthrough.Step(
                title="Changer un seul sommet",
                explanation=(
                    "La notion 2.1 changeait tout un polygone d'un coup, par "
                    "<code>setPolygon()</code>. Pour un seul sommet, on passe par ses sommets "
                    "actuels. <code>polygon()</code> les rend dans un <code>QPolygonF</code>. "
                    "C'est une copie : la modifier ne change pas encore la figure. "
                    "<code>polygon[1] = QPointF(…)</code> remplace le sommet d'indice 1 de la "
                    "copie, puis <code>setPolygon()</code> rend la copie à l'élément. Oublier "
                    "ce dernier appel ne déplace rien."
                    "<br><br>Le sommet d'indice 1 est l'image de (1, 0). Déplacé seul, il "
                    "déforme le contour jaune, qui n'est plus un parallélogramme. Une matrice "
                    "déplace tous les sommets ensemble : aucune ne donne cette figure à partir du "
                    "carré."
                ),
                run=self.moveOneVertex,
                references=[
                    ("QGraphicsPolygonItem.polygon", qtDocUrl("QtWidgets", "QGraphicsPolygonItem", "polygon")),
                    ("QGraphicsPolygonItem.setPolygon", qtDocUrl("QtWidgets", "QGraphicsPolygonItem",
                                                                 "setPolygon")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : les colonnes de la matrice",
                explanation=(
                    "Deux cibles (<code>TargetItem</code>, notion 1.3) se posent au bout des "
                    "colonnes de A : la rouge sur l'image de (1, 0), la verte sur l'image de "
                    "(0, 1). <code>colors[column]</code> donne à chacune sa couleur. Avec "
                    "<code>movable=True</code>, la souris les fait glisser. Une cible émet "
                    "<code>sigPositionChanged</code> à chaque déplacement, relié au slot "
                    "<code>updateMatrix()</code>."
                    "<br><br>Le slot relit les deux positions par <code>pos()</code>, refait A, "
                    "puis met tout à jour :"
                    "<ul>"
                    "<li>la série, par une nouvelle matrice donnée au parent ;</li>"
                    "<li>le contour jaune, un sommet à la fois : les sommets 1 et 3 sont les "
                    "colonnes, le sommet 2 leur somme, et le sommet 0 reste à l'origine ;</li>"
                    "<li>le déterminant, dans la lecture, par <code>measureArea()</code>, la "
                    "méthode de l'étape du déterminant.</li>"
                    "</ul>"
                    "Deux <code>QPointF</code> s'additionnent par <code>+</code>. Le guide "
                    "appelle le slot une fois à l'arrivée sur l'étape : le contour redevient un "
                    "parallélogramme."
                    "<br><br>Écarter les deux cibles : l'aire grandit. Les aligner : le "
                    "déterminant tombe à 0, et les carrés s'aplatissent sur une droite. Les "
                    "croiser : il devient négatif, la figure est retournée comme dans un miroir."
                ),
                run=self._exploreMatrix,
                codeSource=(self.addColumnHandles, self.updateMatrix),
                references=[
                    ("TargetItem", pyqtgraphDocUrl("api_reference/graphicsItems/targetitem", "TargetItem")),
                    ("QGraphicsPolygonItem", polygonItemUrl),
                ],
            ),
        ]
