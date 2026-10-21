"""Notion 1.1 : les bases d'un graphique de courbes.

Contexte : trois mobiles se déplacent en ligne droite à vitesse constante
(mouvement rectiligne uniforme). Leur position en fonction du temps est une
droite : un exemple naturel pour un premier graphique à plusieurs courbes.

Étapes couvertes : le widget du graphique et le graphique qu'il contient,
le titre, les titres des axes, la grille, la légende, puis trois courbes :
une lettre de couleur, la construction explicite (`PlotDataItem` et
`addItem()`), un stylo en tirets. La dernière étape fait explorer le
graphique à la souris, sans code.

Chaque étape est une méthode de `QTopicLinesTab` : elle lit et modifie
directement `self.plotWidget`.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetPlotItem

_PlotItemPage = "api_reference/graphicsItems/plotitem"


class QTopicLinesTab(QWidget):
    """Onglet de la notion 1.1 : un graphique de plusieurs courbes.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        plotWidget: Le widget du graphique, créé une seule fois. PyQtGraph
            retient lui-même les courbes et la légende : rien d'autre n'est
            gardé sur `self`.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Courbes"
    TabToolTip = "Les bases : titre, axes, grille, légende et plusieurs courbes"
    RecommendedPanelWidth = 620
    Objective = (
        "Créer un graphique PyQtGraph, le titrer, préparer sa légende, puis y tracer plusieurs "
        "courbes à partir de tableaux numpy."
    )
    KeyConcepts = [
        "Le widget du graphique (<code>PlotWidget</code>) est un widget Qt ordinaire. Il contient "
        "le graphique (<code>PlotItem</code>) et relaie ses méthodes.",
        "Les données sont des tableaux numpy. Une opération entre un tableau et un nombre "
        "s'applique à chaque élément.",
        "Une légende créée avant les courbes inscrit d'elle-même chaque courbe nommée.",
        "Deux façons équivalentes d'ajouter une courbe : le raccourci <code>plot()</code>, ou la "
        "construction explicite de l'élément graphique qu'il produit.",
        "Le stylo décrit le trait : couleur, épaisseur, style.",
    ]
    KeyApis = [
        "PlotWidget", "PlotItem", "PlotItem.setTitle", "PlotItem.setLabel", "PlotItem.showGrid",
        "PlotItem.addLegend", "PlotItem.plot", "PlotDataItem", "PlotItem.addItem", "mkPen",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.createPlotWidget()

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )
        createSplitterLayout(self, self.plotWidget, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Ramène le graphique à son état d'origine (voir plot_reset.py)."""
        resetPlotItem(self.plotWidget.getPlotItem())

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidget(self) -> None:
        """Crée le widget du graphique, vide."""
        self.plotWidget = pg.PlotWidget()

    def _plotAlreadyCreated(self) -> None:
        """Le widget est créé avec la page : rien à faire."""

    def setPlotTitle(self) -> None:
        """Le titre, au-dessus du graphique."""
        self.plotWidget.setTitle("Mouvement rectiligne uniforme de trois mobiles")

    def setAxisLabels(self) -> None:
        """Les titres des axes, avec leur unité."""
        self.plotWidget.setLabel("bottom", "Temps", units="s")
        self.plotWidget.setLabel("left", "Position", units="m")

    def showPlotGrid(self) -> None:
        """Une grille de repère, à 30 % d'opacité."""
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)

    def prepareLegend(self) -> None:
        """La légende, accrochée en haut à droite, prête à recevoir les courbes."""
        self.plotWidget.addLegend(offset=(-10, 10))

    def plotFirstCurve(self) -> None:
        """Le mobile A, à 2 m/s, tracé en rouge par plot()."""
        time = np.array([0, 1, 2, 3, 4, 5])
        positionA = 2 * time  # chaque élément est multiplié par 2
        self.plotWidget.plot(time, positionA, pen="r", name="Mobile A (2 m/s)")

    def addSecondCurve(self) -> None:
        """Le mobile B, à 3 m/s, construit explicitement puis ajouté."""
        time = np.array([0, 1, 2, 3, 4, 5])
        positionB = 3 * time
        curve = pg.PlotDataItem(time, positionB, pen="g", name="Mobile B (3 m/s)")
        self.plotWidget.addItem(curve)

    def plotDashedCurve(self) -> None:
        """Le mobile C, qui revient vers l'origine, tracé en tirets cyan de 2 pixels."""
        time = np.array([0, 1, 2, 3, 4, 5])
        positionC = 10 - 2 * time
        dashedPen = pg.mkPen("c", width=2, style=Qt.PenStyle.DashLine)
        self.plotWidget.plot(time, positionC, pen=dashedPen, name="Mobile C (-2 m/s)")

    def _exploreWithMouse(self) -> None:
        """Rien à exécuter : l'étudiant manipule le graphique à la souris."""

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Créer le graphique",
                explanation=(
                    "Première notion du guide : pas de récapitulatif, il n'y a encore rien à reprendre. "
                    "L'essentiel de cette étape : le widget du graphique, et le graphique qu'il "
                    "contient. Les imports et l'usage hors du guide se relisent au besoin."
                    "<br><br>Les classes employées par ce guide viennent de trois modules :"
                    "<pre>import numpy as np\n"
                    "import pyqtgraph as pg\n"
                    "from PySide6.QtCore import Qt</pre>"
                    "<code>np</code> est numpy, pour les tableaux de données. <code>pg</code> est "
                    "PyQtGraph, la bibliothèque des graphiques. <code>Qt</code> est l'espace de "
                    "noms des constantes de Qt, comme <code>Qt.PenStyle.DashLine</code>."
                    "<br><br>Le <b>widget du graphique</b> (<code>pg.PlotWidget</code>) est un "
                    "widget Qt ordinaire. Il est créé une seule fois, avec la page, puis le guide "
                    "le place dans la zone de contenu, à gauche, comme on placerait tout widget "
                    "dans un layout. Il contient le <b>graphique</b> (<code>PlotItem</code>) : "
                    "les axes, la grille, le titre et tout ce qui sera tracé. Le widget relaie "
                    "les méthodes du graphique : <code>self.plotWidget.setTitle()</code> appelle "
                    "le <code>setTitle()</code> du graphique. Pour l'instant, le graphique est "
                    "vide, ses deux axes vont de 0 à 1."
                    "<br><br>Hors de ce guide, le même code fonctionne dans toute application "
                    "Qt : une <code>QApplication</code>, une fenêtre, et le widget du graphique "
                    "placé dans la fenêtre comme tout widget, dans un layout."
                ),
                run=self._plotAlreadyCreated,
                codeSource=(self.createPlotWidget,),
                references=[
                    ("PlotWidget", pyqtgraphDocUrl("api_reference/widgets/plotwidget", "PlotWidget")),
                    ("PlotItem", pyqtgraphDocUrl(_PlotItemPage, "PlotItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Ajouter un titre",
                explanation="<code>setTitle(texte)</code> écrit le titre au-dessus du graphique.",
                run=self.setPlotTitle,
                references=[("PlotItem.setTitle", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.setTitle"))],
            ),
            QStepWalkthrough.Step(
                title="Titres des axes",
                explanation=(
                    "<code>setLabel()</code> reçoit le nom de l'axe (<code>\"bottom\"</code> en "
                    "bas, <code>\"left\"</code> à gauche), un texte et une unité "
                    "(<code>units</code>). L'unité s'écrit entre parenthèses après le texte."
                    "<br><br>Quand les valeurs d'un axe atteignent 1000 ou restent sous 1, "
                    "PyQtGraph ajoute un préfixe à l'unité : km pour des milliers de mètres, mm "
                    "pour des millièmes. Ici, les positions iront de 0 à 15 m : aucun préfixe ne "
                    "paraîtra."
                ),
                run=self.setAxisLabels,
                references=[("PlotItem.setLabel", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.setLabel"))],
            ),
            QStepWalkthrough.Step(
                title="Afficher la grille",
                explanation=(
                    "<code>showGrid()</code> ajoute des lignes de repère, en x et en y. Le "
                    "paramètre <code>alpha</code> règle leur opacité, de 0 (invisible) à 1 "
                    "(opaque) : 0,3 garde une grille discrète."
                ),
                run=self.showPlotGrid,
                references=[("PlotItem.showGrid", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.showGrid"))],
            ),
            QStepWalkthrough.Step(
                title="Préparer la légende",
                explanation=(
                    "<code>addLegend()</code> crée la <b>légende</b>, vide pour l'instant. Créée "
                    "avant les courbes, elle inscrit d'elle-même chaque courbe qui porte un nom. "
                    "C'est l'ordre habituel : la légende d'abord, les courbes ensuite."
                    "<br><br><code>offset=(-10, 10)</code> l'accroche à 10 pixels du bord droit "
                    "et du bord du haut. Un nombre négatif compte depuis la droite. En haut à "
                    "droite, elle laisse libre le début des courbes."
                    "<br><br>À gauche, rien ne paraît encore : la légende n'a aucune courbe à inscrire."
                ),
                run=self.prepareLegend,
                references=[
                    ("PlotItem.addLegend", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.addLegend")),
                    ("LegendItem", pyqtgraphDocUrl("api_reference/graphicsItems/legenditem", "LegendItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Tracer la première courbe",
                explanation=(
                    "<code>plot(x, y, pen=…, name=…)</code> trace la <b>courbe</b> : les "
                    "points (x, y) reliés par un trait. <code>pen</code> est le stylo du trait. "
                    "Une lettre suffit pour une couleur simple, et le trait a alors 1 pixel "
                    "d'épaisseur :"
                    "<ul>"
                    "<li><code>\"r\"</code> rouge, <code>\"g\"</code> vert, <code>\"b\"</code> "
                    "bleu ;</li>"
                    "<li><code>\"c\"</code> cyan, <code>\"m\"</code> magenta, <code>\"y\"</code> "
                    "jaune ;</li>"
                    "<li><code>\"k\"</code> noir, <code>\"w\"</code> blanc.</li>"
                    "</ul>"
                    "Le nom (<code>name</code>) paraît aussitôt dans la légende."
                    "<br><br>Ici, les données sont des tableaux numpy (<code>np.array</code>). "
                    "<code>2 * time</code> multiplie chaque élément du tableau par 2 : la "
                    "position à chaque seconde, pour une vitesse de 2 m/s."
                ),
                run=self.plotFirstCurve,
                references=[
                    ("numpy.array", numpyDocUrl("array")),
                    ("PlotItem.plot", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.plot")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Deuxième courbe : la construction explicite",
                explanation=(
                    "<code>plot()</code> n'est qu'un raccourci. Il construit un "
                    "<code>pg.PlotDataItem</code>, l'élément graphique d'une courbe, puis "
                    "l'ajoute au graphique avec <code>addItem()</code>. Cette étape fait les deux "
                    "gestes elle-même. Le résultat est identique, légende comprise."
                    "<br><br>Quand préférer l'une ou l'autre ? <code>plot()</code> suffit pour "
                    "tracer. La construction explicite sert quand l'élément existe avant d'être "
                    "montré : on le crée, on le règle, puis on l'ajoute, ou on le retire et le "
                    "rajoute plus tard. C'est aussi la seule écriture pour les éléments qui "
                    "n'ont pas de raccourci, comme l'étiquette d'information de la notion 1.3."
                ),
                run=self.addSecondCurve,
                references=[
                    ("PlotDataItem", pyqtgraphDocUrl("api_reference/graphicsItems/plotdataitem",
                                                     "PlotDataItem")),
                    ("PlotItem.addItem", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.addItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Troisième courbe, en tirets",
                explanation=(
                    "Pour régler plus que la couleur, <code>pg.mkPen(couleur, width=…, "
                    "style=…)</code> construit un stylo. <code>width</code> est l'épaisseur en "
                    "pixels. <code>style</code> est une constante de <code>Qt.PenStyle</code>, "
                    "ici des tirets (<code>DashLine</code>). Ce mobile part de 10 m et revient "
                    "vers l'origine : <code>10 - 2 * time</code>."
                ),
                run=self.plotDashedCurve,
                references=[
                    ("mkPen", pyqtgraphDocUrl("api_reference/functions", "mkPen")),
                    ("Qt.PenStyle", qtDocUrl("QtCore", "Qt", "PenStyle")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : explorer le graphique à la souris",
                explanation=(
                    "Le graphique réagit déjà à la souris, sans aucun code de plus :"
                    "<ul>"
                    "<li>la molette agrandit ou réduit autour du pointeur ;</li>"
                    "<li>glisser avec le bouton gauche déplace les données ;</li>"
                    "<li>après un changement, un petit bouton « A » paraît dans le coin inférieur "
                    "gauche quand la souris survole le graphique : il revient à l'ajustement "
                    "automatique, qui montre toutes les données ;</li>"
                    "<li>le clic droit ouvre un menu de réglages du graphique.</li>"
                    "</ul>"
                    "Essayer chacun de ces gestes, puis revenir à la zone visible complète par « A »."
                ),
                run=self._exploreWithMouse,
                codeSource=(),
                references=[("PlotWidget", pyqtgraphDocUrl("api_reference/widgets/plotwidget", "PlotWidget"))],
            ),
        ]
