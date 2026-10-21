"""Notion 1.5 : plusieurs graphiques dans une même figure.

Contexte : l'oscillateur amorti de la notion 1.3, avec γ = 0,3 /s. Son
déplacement en haut, son amplitude A(t) = 2·e^(−γt) en bas : l'enveloppe de
la notion 1.3. En échelle logarithmique, l'amplitude devient une droite,
dont la pente mesure la décroissance. Une troisième colonne compare
l'amplitude pour trois amortissements.

Étapes couvertes : une grille de graphiques (`GraphicsLayoutWidget`), un
récapitulatif (titres, axes, déplacement), l'amplitude, des axes liés,
l'échelle logarithmique, une cellule sur deux rangées, puis l'export en
image (`ImageExporter`), dont la taille s'écrit dans la lecture, présentée
ici. Une case à cocher et un bouton font ensuite explorer l'échelle et
l'export.

Chaque étape est une méthode de `QTopicLayoutTab`. Les fonctions de calcul
viennent de la notion 1.3.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QFileDialog, QVBoxLayout, QWidget

from ..common.doc_urls import pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import removeLayoutItems, resetPlotItem
from .topic_1_3_interaction import displacement, envelope

_PlotItemPage = "api_reference/graphicsItems/plotitem"
_GraphicsLayoutPage = "api_reference/graphicsItems/graphicslayout"


class QTopicLayoutTab(QWidget):
    """Onglet de la notion 1.5 : une figure de trois graphiques.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        layoutWidget: La grille de graphiques, créée une seule fois.
        displacementPlot, amplitudePlot: Les deux graphiques empilés de la
            première colonne, créés une seule fois.
        dampingPlot: Le graphique des trois amortissements, ou None avant
            son étape.
        readout: La lecture sous la figure (outil présenté à l'étape de
            l'export).
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        logCheck, exportButton: L'échelle logarithmique et l'export.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Mise en page"
    TabToolTip = "Une grille de graphiques : axes liés, échelle logarithmique, cellule sur deux rangées, export"
    RecommendedPanelWidth = 620
    Objective = (
        "Composer une figure de plusieurs graphiques : les disposer en grille, lier leurs axes, "
        "choisir une échelle logarithmique, puis exporter la figure en image."
    )
    KeyConcepts = [
        "Une grille de graphiques se remplit cellule par cellule : rangée et colonne.",
        "Deux graphiques aux axes liés zooment et défilent ensemble.",
        "Une décroissance exponentielle devient une droite en échelle logarithmique ; sa pente "
        "mesure la décroissance.",
        "Une cellule peut s'étendre sur plusieurs rangées ou colonnes.",
        "Une figure s'exporte en image, telle qu'elle est affichée.",
    ]
    KeyApis = [
        "GraphicsLayoutWidget", "GraphicsLayout.addPlot", "PlotItem.setXLink", "PlotItem.setLogMode",
        "ImageExporter", "ImageExporter.export",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.dampingPlot: pg.PlotItem | None = None

        self.createLayout()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.logCheck = self.controls.addCheckBox("Échelle logarithmique de l'amplitude", checked=True)
        self.exportButton = self.controls.addButton("Enregistrer l'image…")

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.layoutWidget, 1)
        contentLayout.addWidget(self.readout)
        contentLayout.addWidget(self.controls)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Vide les deux graphiques, retire le troisième, vide la lecture et remet les contrôles à zéro."""
        self.controls.resetControls()
        self.readout.clear()
        removeLayoutItems(self.layoutWidget, keep=(self.displacementPlot, self.amplitudePlot))
        resetPlotItem(self.displacementPlot)
        resetPlotItem(self.amplitudePlot)
        self.dampingPlot = None

    # -- Étapes ------------------------------------------------------------------------------------

    def createLayout(self) -> None:
        """Crée la grille et ses deux premiers graphiques, l'un sous l'autre."""
        self.layoutWidget = pg.GraphicsLayoutWidget()
        self.displacementPlot = self.layoutWidget.addPlot(row=0, col=0)
        self.amplitudePlot = self.layoutWidget.addPlot(row=1, col=0)

    def _layoutAlreadyCreated(self) -> None:
        """La grille est créée avec la page : rien à faire."""

    def plotDisplacement(self) -> None:
        """Titres, axes et grilles, puis le déplacement de la notion 1.3 en haut, pour γ = 0,3 /s."""
        self.displacementPlot.setTitle("Oscillateur amorti, γ = 0,3 /s")
        self.displacementPlot.setLabel("left", "Déplacement", units="m")
        self.displacementPlot.showGrid(x=True, y=True, alpha=0.3)
        self.amplitudePlot.setLabel("left", "Amplitude A(t)", units="m")
        self.amplitudePlot.setLabel("bottom", "Temps", units="s")
        self.amplitudePlot.showGrid(x=True, y=True, alpha=0.3)
        times = np.linspace(0, 10, 500)
        self.displacementPlot.plot(times, displacement(times, 0.3), pen=pg.mkPen("y", width=2))

    def plotAmplitude(self) -> None:
        """L'amplitude A(t) = 2·e^(−γt) en bas, pour γ = 0,3 /s."""
        times = np.linspace(0, 10, 500)
        self.amplitudePlot.plot(times, envelope(times, 0.3), pen=pg.mkPen("m", width=2))

    def linkTimeAxes(self) -> None:
        """L'axe du temps du graphique du bas, lié à celui du haut."""
        self.amplitudePlot.setXLink(self.displacementPlot)

    def useLogScale(self) -> None:
        """L'amplitude, en échelle logarithmique."""
        self.amplitudePlot.setLogMode(x=False, y=True)

    def plotThreeDampings(self) -> None:
        """Une deuxième colonne sur deux rangées : l'amplitude pour trois amortissements."""
        self.dampingPlot = self.layoutWidget.addPlot(row=0, col=1, rowspan=2)
        self.dampingPlot.setTitle("Amplitude pour trois amortissements")
        self.dampingPlot.setLabel("bottom", "Temps", units="s")
        self.dampingPlot.setLabel("left", "Amplitude A(t)", units="m")
        self.dampingPlot.showGrid(x=True, y=True, alpha=0.3)
        self.dampingPlot.setLogMode(x=False, y=True)
        self.dampingPlot.addLegend(offset=(10, -10))
        times = np.linspace(0, 10, 500)
        dampings = [0.1, 0.3, 0.8]
        colors = ["g", "m", "r"]
        names = ["γ = 0,1 /s", "γ = 0,3 /s", "γ = 0,8 /s"]
        for i in range(3):
            self.dampingPlot.plot(times, envelope(times, dampings[i]), pen=pg.mkPen(colors[i], width=2),
                                  name=names[i])

    def exportToImage(self) -> None:
        """Exporte la figure en image, sans fichier, et écrit sa taille dans la lecture."""
        exporter = ImageExporter(self.layoutWidget.ci)
        image = exporter.export(toBytes=True)
        self.readout.setText(f"Image exportée : {image.width()} × {image.height()} pixels")

    def connectControls(self) -> None:
        """Relie la case à cocher et le bouton à leur slot."""
        self.logCheck.toggled.connect(self.setAmplitudeLog)
        self.exportButton.clicked.connect(self.saveFigure)

    @Slot(bool)
    def setAmplitudeLog(self, logarithmic: bool) -> None:
        """Passe les deux graphiques de l'amplitude en échelle logarithmique, ou linéaire."""
        self.amplitudePlot.setLogMode(x=False, y=logarithmic)
        self.dampingPlot.setLogMode(x=False, y=logarithmic)

    @Slot()
    def saveFigure(self) -> None:
        """Demande un nom de fichier, puis y enregistre la figure en PNG."""
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer la figure", "oscillateur.png",
                                              "Images PNG (*.png)")
        if path:
            ImageExporter(self.layoutWidget.ci).export(path)

    def _exploreLayout(self) -> None:
        """Connecte la case à cocher et le bouton, puis les révèle."""
        self.connectControls()
        self.controls.reveal()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Une grille de graphiques",
                explanation=(
                    "Pas de récapitulatif : la notion repart d'une figure neuve, une grille de "
                    "graphiques, et non du graphique seul des notions précédentes. "
                    "<br><br><code>pg.GraphicsLayoutWidget</code> est un widget qui range des graphiques "
                    "en grille, comme un layout range des widgets. "
                    "<code>addPlot(row=…, col=…)</code> crée directement un graphique (un "
                    "<code>PlotItem</code>) dans la cellule voulue, et le rend. Il n'y a pas de "
                    "widget autour de chaque graphique : la grille est le seul widget, créé une "
                    "seule fois avec la page. À gauche, deux graphiques vides, l'un sous "
                    "l'autre, dans la première colonne."
                ),
                run=self._layoutAlreadyCreated,
                codeSource=(self.createLayout,),
                references=[
                    ("GraphicsLayoutWidget", pyqtgraphDocUrl("api_reference/widgets/graphicslayoutwidget",
                                                             "GraphicsLayoutWidget")),
                    ("GraphicsLayout.addPlot", pyqtgraphDocUrl(_GraphicsLayoutPage, "GraphicsLayout.addPlot")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Récapitulatif : titres, axes et déplacement",
                explanation=(
                    "Rien de nouveau. Chaque graphique se règle comme à la notion 1.1. Seul "
                    "celui du haut porte un titre, et seul celui du bas nomme l'axe du temps : "
                    "les deux montreront le même intervalle de temps."
                    "<br><br><code>displacement()</code>, écrite à la notion 1.3, est importée "
                    "de son fichier : <code>from .topic_1_3_interaction import displacement, "
                    "envelope</code>. Le point au début du nom désigne le dossier de "
                    "l'application : le fichier <code>topic_1_3_interaction.py</code> voisin."
                    "<br><br><i>Pour l'exemple</i> : le graphique du haut montre le déplacement, pour "
                    "γ = 0,3 /s."
                ),
                run=self.plotDisplacement,
                references=[("PlotItem.setLabel", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.setLabel"))],
            ),
            QStepWalkthrough.Step(
                title="L'amplitude",
                explanation=(
                    "En bas, l'amplitude A(t) = 2·e<sup>−γt</sup>, en mètres : la taille des "
                    "oscillations à chaque instant. C'est le bord supérieur de l'enveloppe de la "
                    "notion 1.3, calculé par <code>envelope()</code>, importée elle aussi. "
                    "Le déplacement oscille ; l'amplitude, elle, ne fait que décroître. Elle "
                    "perd la même fraction de sa valeur à chaque seconde : une décroissance "
                    "exponentielle."
                ),
                run=self.plotAmplitude,
                references=[("PlotItem.plot", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.plot"))],
            ),
            QStepWalkthrough.Step(
                title="Lier les axes du temps",
                explanation=(
                    "<code>setXLink(autre)</code> lie l'axe horizontal d'un graphique à celui "
                    "d'un autre graphique. Un zoom à la molette dans l'un, ou un glissement, est "
                    "suivi par l'autre. Les deux montrent toujours le même intervalle de "
                    "temps."
                ),
                run=self.linkTimeAxes,
                references=[("ViewBox.setXLink", pyqtgraphDocUrl("api_reference/graphicsItems/viewbox",
                                                                 "ViewBox.setXLink"))],
            ),
            QStepWalkthrough.Step(
                title="L'échelle logarithmique",
                explanation=(
                    "<code>setLogMode(x=False, y=True)</code> passe l'axe vertical en "
                    "<b>échelle logarithmique</b> : chaque graduation vaut dix fois la "
                    "précédente. L'écart entre deux puissances de 10 est une <b>décade</b>."
                    "<br><br>L'amplitude y devient une droite. À chaque seconde, elle perd la même "
                    "fraction d'elle-même : sur cet axe, elle descend donc toujours de la même "
                    "hauteur. En 10 s, elle passe de 2 m à 0,1 m, un facteur 20, soit 1,3 décade "
                    "(10<sup>1,3</sup> ≈ 20). La pente vaut environ 0,13 décade par seconde, pour "
                    "γ = 0,3 /s. "
                    "Une droite en échelle logarithmique est le moyen le plus sûr de reconnaître "
                    "une décroissance exponentielle dans des mesures."
                ),
                run=self.useLogScale,
                references=[("PlotItem.setLogMode", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.setLogMode"))],
            ),
            QStepWalkthrough.Step(
                title="Une cellule sur deux rangées",
                explanation=(
                    "<code>addPlot(row=0, col=1, rowspan=2)</code> ouvre une deuxième colonne, "
                    "dont l'unique graphique couvre les deux rangées. Il compare l'amplitude "
                    "pour trois amortissements, en échelle logarithmique. Trois droites : plus γ "
                    "est grand, plus la pente est forte. La légende s'accroche en bas à gauche, "
                    "où rien n'est tracé : <code>offset=(10, -10)</code>, un nombre négatif "
                    "comptant depuis le bas."
                    "<br><br>Les trois listes donnent, pour chaque indice <code>i</code>, "
                    "l'amortissement, la couleur et le nom de la même courbe."
                ),
                run=self.plotThreeDampings,
                references=[("GraphicsLayout.addPlot", pyqtgraphDocUrl(_GraphicsLayoutPage, "GraphicsLayout.addPlot"))],
            ),
            QStepWalkthrough.Step(
                title="Exporter la figure",
                explanation=(
                    "<code>ImageExporter</code>, du module <code>pyqtgraph.exporters</code>, "
                    "exporte en image ce qu'il reçoit. Il reçoit ici "
                    "<code>self.layoutWidget.ci</code>, abréviation de <i>central item</i> : la "
                    "grille centrale du widget, l'élément graphique qui contient les trois "
                    "graphiques. Malgré son nom, <code>export(toBytes=True)</code> rend une "
                    "image en mémoire, une <code>QImage</code> de <code>PySide6.QtGui</code>, "
                    "sans écrire de fichier."
                    "<br><br>Une vérification : sa largeur et sa hauteur, lues par "
                    "<code>width()</code> et <code>height()</code>. Ce sont celles du widget : "
                    "l'export reprend ce qui est à l'écran."
                    "<br><br>Elles s'écrivent sous la figure, dans la <b>lecture</b> "
                    "(<code>self.readout</code>). C'est un outil écrit pour ce guide, qui ne fait "
                    "partie ni de PyQtGraph ni de Qt. Une seule de ses méthodes paraît dans le "
                    "code : <code>setText(texte)</code>, qui y affiche un texte. Elle reste "
                    "cachée tant qu'elle est vide. Le titre du graphique, lui, ne change pas : "
                    "un résultat a sa place à lui."
                ),
                run=self.exportToImage,
                references=[
                    ("Exporter (guide)", pyqtgraphDocUrl("user_guide/exporting")),
                    ("QImage", qtDocUrl("QtGui", "QImage")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : axes liés, échelle et export",
                explanation=(
                    "Zoomer dans un graphique de la première colonne : l'autre suit."
                    "<br><br>Deux contrôles paraissent sous la figure. La case à cocher "
                    "<code>logCheck</code>, cochée au départ, choisit l'échelle de l'amplitude : "
                    "le slot <code>setAmplitudeLog()</code> reçoit l'état de la case, "
                    "<code>True</code> si elle est cochée, et le passe à <code>setLogMode()</code> "
                    "pour les deux graphiques de l'amplitude. Le bouton <code>exportButton</code> "
                    "appelle <code>saveFigure()</code>."
                    "<br><br><code>QFileDialog.getSaveFileName()</code> ouvre la boîte de "
                    "dialogue d'enregistrement ; son premier argument est son parent, la "
                    "page. Elle rend deux valeurs : le chemin choisi, et le "
                    "filtre de fichiers, qui ne sert pas ici (<code>_</code>). Le chemin est vide "
                    "si l'on annule. <code>export(chemin)</code> écrit alors l'image dans un "
                    "fichier PNG."
                ),
                run=self._exploreLayout,
                codeSource=(self.connectControls, self.setAmplitudeLog, self.saveFigure),
                references=[("QFileDialog", qtDocUrl("QtWidgets", "QFileDialog"))],
            ),
        ]
