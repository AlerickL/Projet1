"""Notion 1.2 : les nuages de points et les barres d'erreur.

Contexte : trois équipes chronomètrent la chute d'une bille et notent la
distance parcourue à différents instants. Les mesures sont simulées. Ce
sont des mesures individuelles : un nuage de points les représente mieux
qu'une courbe qui les relierait à tort. Chaque mesure a une incertitude,
montrée par une barre d'erreur.

Étapes couvertes : un récapitulatif de la notion 1.1, l'axe et la grille,
la zone visible, deux nuages par `plot()`, un troisième par la classe
dédiée `ScatterPlotItem`, ses barres d'erreur (`ErrorBarItem`), la chute
attendue, une mesure douteuse, puis montrer ou cacher un élément
graphique. Trois cases à cocher montrent ou cachent ensuite chaque équipe.

Chaque étape est une méthode de `QTopicScatterTab` : elle lit et modifie
directement `self.plotWidget`.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetPlotItem

_PlotItemPage = "api_reference/graphicsItems/plotitem"
_ViewBoxPage = "api_reference/graphicsItems/viewbox"
_ScatterPage = "api_reference/graphicsItems/scatterplotitem"


class QTopicScatterTab(QWidget):
    """Onglet de la notion 1.2 : nuages de points et barres d'erreur.

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
        team1Check, team2Check, team3Check: Les cases à cocher des équipes.
        team1, team2, team3: Les nuages de points des trois équipes, ou None
            avant leur étape.
        team3Errors: Les barres d'erreur de l'équipe 3, ou None.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Nuages de points"
    TabToolTip = "Nuages de points, grille et zone visible, barres d'erreur, montrer ou cacher"
    RecommendedPanelWidth = 620
    Objective = (
        "Représenter des mesures par des nuages de points, avec leurs barres d'erreur, les "
        "comparer à une courbe attendue, et montrer ou cacher chaque élément graphique."
    )
    KeyConcepts = [
        "Un nuage de points n'a pas de trait entre ses points : chaque mesure reste isolée.",
        "La grille suit les graduations des axes : régler leur espacement règle la grille.",
        "Le graphique contient une zone visible, ajustée aux données sauf si on l'impose.",
        "Une barre d'erreur montre l'intervalle où se trouve probablement la vraie valeur.",
        "Une couleur s'écrit aussi par ses composantes rouge, vert, bleu, de 0 à 255.",
        "Un élément graphique caché reste dans le graphique : on peut le montrer de nouveau.",
    ]
    KeyApis = [
        "PlotItem.getAxis", "AxisItem.setTickSpacing", "ViewBox", "ViewBox.setXRange",
        "ScatterPlotItem", "mkBrush", "ErrorBarItem", "ScatterPlotItem.setBrush",
        "QGraphicsItem.setVisible",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.team1: pg.PlotDataItem | None = None
        self.team2: pg.PlotDataItem | None = None
        self.team3: pg.ScatterPlotItem | None = None
        self.team3Errors: pg.ErrorBarItem | None = None

        self.createPlotWidget()
        self.controls = QControlPanel()
        self.team1Check = self.controls.addCheckBox("Équipe 1", checked=True)
        self.team2Check = self.controls.addCheckBox("Équipe 2", checked=True)
        self.team3Check = self.controls.addCheckBox("Équipe 3", checked=False)

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
        self.team1 = None
        self.team2 = None
        self.team3 = None
        self.team3Errors = None

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidget(self) -> None:
        """Crée le widget du graphique, vide."""
        self.plotWidget = pg.PlotWidget()

    def setUpPlot(self) -> None:
        """Titre, axes et légende, comme à la notion 1.1."""
        self.plotWidget.setTitle("Chute d'une bille : distance parcourue, mesurée par trois équipes")
        self.plotWidget.setLabel("bottom", "Temps", units="s")
        self.plotWidget.setLabel("left", "Distance parcourue", units="m")
        self.plotWidget.addLegend(offset=(10, 10))

    def setGridSpacing(self) -> None:
        """Une grille dont l'espacement est choisi, axe par axe."""
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)
        self.plotWidget.getAxis("bottom").setTickSpacing(major=0.2, minor=0.1)
        self.plotWidget.getAxis("left").setTickSpacing(major=1, minor=0.5)

    def setViewRange(self) -> None:
        """Une zone visible imposée, qui inclut l'origine."""
        self.plotWidget.setXRange(0, 1.4, padding=0)
        self.plotWidget.setYRange(0, 8, padding=0)

    def plotFirstTeam(self) -> None:
        """Les mesures de l'équipe 1 : des cercles rouges, sans trait."""
        time = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
        distance = np.array([0.25, 0.75, 1.9, 3.0, 5.3, 7.0])
        self.team1 = self.plotWidget.plot(time, distance, pen=None, symbol="o", symbolSize=10,
                                          symbolBrush="r", name="Équipe 1")

    def plotSecondTeam(self) -> None:
        """Les mesures de l'équipe 2 : des triangles verts."""
        time = np.array([0.3, 0.5, 0.7, 0.9, 1.1])
        distance = np.array([0.5, 1.4, 2.6, 4.3, 6.2])
        self.team2 = self.plotWidget.plot(time, distance, pen=None, symbol="t", symbolSize=12,
                                          symbolBrush="g", name="Équipe 2")

    def addThirdTeam(self) -> None:
        """Les mesures de l'équipe 3, des losanges orangés, par la classe dédiée ScatterPlotItem."""
        time = np.array([0.25, 0.65, 0.85, 1.05])
        distance = np.array([0.3, 2.1, 2.4, 5.6])
        self.team3 = pg.ScatterPlotItem(time, distance, symbol="d", size=12,
                                        brush=pg.mkBrush((240, 170, 0)), name="Équipe 3")
        self.plotWidget.addItem(self.team3)

    def addErrorBars(self) -> None:
        """Les barres d'erreur de l'équipe 3 : l'incertitude de chaque mesure, en mètres."""
        time = np.array([0.25, 0.65, 0.85, 1.05])
        distance = np.array([0.3, 2.1, 2.4, 5.6])
        uncertainty = np.array([0.1, 0.25, 0.3, 0.4])
        self.team3Errors = pg.ErrorBarItem(x=time, y=distance, top=uncertainty, bottom=uncertainty,
                                           beam=0.03, pen=pg.mkPen((240, 170, 0)))
        self.plotWidget.addItem(self.team3Errors)

    def plotExpectedFall(self) -> None:
        """La chute attendue, d = ½·g·t², en tirets blancs."""
        time = np.linspace(0, 1.4, 50)
        distance = 0.5 * 9.8 * time ** 2
        dashedPen = pg.mkPen("w", width=1, style=Qt.PenStyle.DashLine)
        self.plotWidget.plot(time, distance, pen=dashedPen, name="Chute attendue")

    def markDoubtfulMeasurement(self) -> None:
        """La troisième mesure de l'équipe 3, loin de la chute attendue, en rouge."""
        orange = pg.mkBrush((240, 170, 0))
        self.team3.setBrush([orange, orange, pg.mkBrush("r"), orange])

    def hideThirdTeam(self) -> None:
        """Cache l'équipe 3 et ses barres d'erreur."""
        self.team3.setVisible(False)
        self.team3Errors.setVisible(False)

    def connectControls(self) -> None:
        """Relie les trois cases à cocher au slot qui montre ou cache les équipes."""
        self.team1Check.toggled.connect(self.updateTeamsVisibility)
        self.team2Check.toggled.connect(self.updateTeamsVisibility)
        self.team3Check.toggled.connect(self.updateTeamsVisibility)

    @Slot()
    def updateTeamsVisibility(self) -> None:
        """Montre chaque équipe dont la case est cochée, cache les autres."""
        self.team1.setVisible(self.team1Check.isChecked())
        self.team2.setVisible(self.team2Check.isChecked())
        self.team3.setVisible(self.team3Check.isChecked())
        self.team3Errors.setVisible(self.team3Check.isChecked())

    def _exploreTeams(self) -> None:
        """Connecte les cases à cocher, puis les révèle."""
        self.connectControls()
        self.controls.reveal()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : graphique, titre, axes, légende",
                explanation=(
                    "Rien de nouveau : les gestes de la notion 1.1, regroupés en une étape. Le "
                    "widget du graphique est créé avec la page, puis reçoit son titre, les "
                    "titres des axes et la légende. <code>offset=(10, 10)</code> accroche cette "
                    "fois la légende en haut à gauche : un nombre positif compte depuis la "
                    "gauche. Les données monteront vers la droite et laisseront ce coin libre."
                ),
                run=self.setUpPlot,
                codeSource=(self.createPlotWidget, self.setUpPlot),
                references=[
                    ("PlotItem.setLabel", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.setLabel")),
                    ("PlotItem.addLegend", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.addLegend")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La grille, plus en détail",
                explanation=(
                    "<code>getAxis(nom)</code> reçoit le nom d'un axe (<code>\"bottom\"</code>, "
                    "<code>\"left\"</code>) et rend cet axe, un <code>AxisItem</code> : la règle "
                    "graduée de ce côté du graphique. La grille suit toujours les graduations "
                    "de son axe. <code>setTickSpacing()</code> fixe l'écart entre deux "
                    "graduations principales (<code>major</code>) et secondaires "
                    "(<code>minor</code>), en unités de l'axe. Il règle donc aussi la densité de "
                    "la grille : une ligne tous les 0,1 s en x, tous les 0,5 m en y."
                ),
                run=self.setGridSpacing,
                references=[
                    ("PlotItem.getAxis", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.getAxis")),
                    ("AxisItem.setTickSpacing", pyqtgraphDocUrl("api_reference/graphicsItems/axisitem",
                                                                "AxisItem.setTickSpacing")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une zone visible imposée",
                explanation=(
                    "Le graphique contient une <b>zone visible</b> (<code>ViewBox</code>) : la "
                    "région des données qu'il montre, entre les axes. Par défaut, elle s'ajuste "
                    "aux données. <code>setXRange(début, fin)</code> et "
                    "<code>setYRange(début, fin)</code> l'imposent plutôt. <code>padding=0</code> "
                    "retire la petite marge que PyQtGraph ajoute autour. Le widget relaie ces "
                    "méthodes de la zone visible, comme celles du graphique."
                    "<br><br><i>Pour l'exemple</i> : de 0 à 1,4 s et de 0 à 8 m, pour garder l'origine "
                    "dans la zone visible."
                ),
                run=self.setViewRange,
                references=[
                    ("ViewBox", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox")),
                    ("ViewBox.setXRange", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setXRange")),
                    ("ViewBox.setYRange", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setYRange")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Premier nuage de points",
                explanation=(
                    "<code>plot()</code> avec <code>pen=None</code> ne trace aucun trait : il ne "
                    "reste que des points, un <b>nuage de points</b>. Trois paramètres décrivent "
                    "les points : <code>symbol</code> leur forme (<code>\"o\"</code>, un "
                    "cercle), <code>symbolSize</code> leur diamètre en pixels, et "
                    "<code>symbolBrush</code> leur pinceau, c'est-à-dire leur couleur de "
                    "remplissage. <code>plot()</code> rend l'élément graphique créé : "
                    "<code>self.team1</code> le garde pour la fin de la notion."
                ),
                run=self.plotFirstTeam,
                references=[
                    ("PlotItem.plot", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.plot")),
                    ("PlotDataItem", pyqtgraphDocUrl("api_reference/graphicsItems/plotdataitem",
                                                     "PlotDataItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Deuxième nuage, une autre forme",
                explanation=(
                    "<code>symbol</code> accepte plusieurs formes, entre autres :"
                    "<ul>"
                    "<li><code>\"o\"</code> un cercle, <code>\"s\"</code> un carré ;</li>"
                    "<li><code>\"t\"</code> un triangle, <code>\"d\"</code> un losange ;</li>"
                    "<li><code>\"+\"</code> une croix droite, <code>\"x\"</code> une croix "
                    "oblique.</li>"
                    "</ul>"
                    "Une forme par équipe reste lisible même imprimée en noir et blanc."
                ),
                run=self.plotSecondTeam,
                references=[("PlotDataItem", pyqtgraphDocUrl("api_reference/graphicsItems/plotdataitem",
                                                             "PlotDataItem"))],
            ),
            QStepWalkthrough.Step(
                title="Troisième nuage : la classe dédiée",
                explanation=(
                    "<code>pg.ScatterPlotItem</code> est l'élément graphique d'un nuage de "
                    "points. Construit directement, il se règle point par point, ce que montrera "
                    "l'étape de la mesure douteuse. Un nuage n'a que des points : ses "
                    "paramètres se nomment donc sans préfixe. <code>symbol</code> garde son "
                    "nom ; <code>size</code> et <code>brush</code> remplacent "
                    "<code>symbolSize</code> et <code>symbolBrush</code>."
                    "<br><br><code>pg.mkBrush()</code> construit un pinceau. Il reçoit ici une "
                    "couleur écrite par un tuple de nombres de 0 à 255 : rouge, vert, bleu. "
                    "<code>(240, 170, 0)</code> est un orangé. Un quatrième nombre, facultatif, "
                    "donne l'opacité (notion 1.3). Ce tuple sert dès qu'une lettre ne suffit "
                    "plus."
                ),
                run=self.addThirdTeam,
                references=[
                    ("ScatterPlotItem", pyqtgraphDocUrl(_ScatterPage, "ScatterPlotItem")),
                    ("mkBrush", pyqtgraphDocUrl("api_reference/functions", "mkBrush")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Les barres d'erreur",
                explanation=(
                    "Une mesure n'est jamais exacte. <code>pg.ErrorBarItem</code> trace, pour "
                    "chaque point (<code>x</code>, <code>y</code>), une barre verticale. "
                    "<code>top</code> et <code>bottom</code> sont des longueurs, en mètres : la "
                    "barre va de y − bottom à y + top. C'est l'intervalle où se trouve "
                    "probablement la vraie valeur. <code>beam</code> est la largeur du petit "
                    "trait aux extrémités, en unités de l'axe x."
                    "<br><br>Seule l'équipe 3 reçoit ses barres, pour garder le graphique "
                    "lisible : c'est elle qui a une mesure à juger. Les barres d'erreur ne "
                    "paraissent pas dans la légende."
                ),
                run=self.addErrorBars,
                references=[("ErrorBarItem", pyqtgraphDocUrl("api_reference/graphicsItems/errorbaritem",
                                                             "ErrorBarItem"))],
            ),
            QStepWalkthrough.Step(
                title="La chute attendue",
                explanation=(
                    "Une bille lâchée sans vitesse parcourt la distance d = ½·g·t², avec d en "
                    "mètres, t en secondes et g = 9,8 m/s², l'accélération de la pesanteur. On "
                    "néglige ici la résistance de l'air."
                    "<br><br><code>np.linspace(0, 1.4, 50)</code> rend 50 instants également "
                    "espacés de 0 à 1,4 s. <code>time ** 2</code> élève chaque instant au carré. "
                    "La courbe se trace en tirets, avec les gestes de la notion 1.1."
                ),
                run=self.plotExpectedFall,
                references=[
                    ("numpy.linspace", numpyDocUrl("linspace")),
                    ("mkPen", pyqtgraphDocUrl("api_reference/functions", "mkPen")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une mesure douteuse",
                explanation=(
                    "La troisième mesure de l'équipe 3, à 0,85 s, est loin de la chute "
                    "attendue : 2,4 m au lieu d'environ 3,5 m, bien plus que son incertitude de "
                    "0,3 m. <code>setBrush()</code> reçoit ici une liste : un pinceau par point, "
                    "dans l'ordre des données. Seul le point douteux devient rouge. La légende "
                    "garde l'orangé."
                ),
                run=self.markDoubtfulMeasurement,
                references=[("ScatterPlotItem.setBrush", pyqtgraphDocUrl(_ScatterPage,
                                                                         "ScatterPlotItem.setBrush"))],
            ),
            QStepWalkthrough.Step(
                title="Montrer ou cacher un élément",
                explanation=(
                    "Tout élément graphique a <code>setVisible(visible)</code>, hérité de "
                    "<code>QGraphicsItem</code> de Qt. Il reçoit <code>True</code> ou "
                    "<code>False</code>. Un élément caché reste dans le graphique : "
                    "<code>setVisible(True)</code> le montre de nouveau. Dans la légende, un œil "
                    "barré remplace l'échantillon d'un élément caché."
                    "<br><br>Un clic sur l'échantillon d'une entrée de la légende cache aussi "
                    "l'élément. Mais il ne cache pas les barres d'erreur, qui ne sont pas dans "
                    "la légende."
                ),
                run=self.hideThirdTeam,
                references=[("QGraphicsItem.setVisible", qtDocUrl("QtWidgets", "QGraphicsItem", "setVisible"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : montrer ou cacher chaque équipe",
                explanation=(
                    "Trois cases à cocher paraissent sous le graphique : "
                    "<code>team1Check</code>, <code>team2Check</code> et "
                    "<code>team3Check</code>, la troisième décochée au départ, comme l'équipe 3 "
                    "est cachée. <code>connectControls()</code> relie leur signal "
                    "<code>toggled</code> au slot <code>updateTeamsVisibility()</code>. Celui-ci lit "
                    "chaque case par <code>isChecked()</code> et montre ou cache le nuage de "
                    "l'équipe, et ses barres d'erreur pour l'équipe 3. Comme tout slot de ce "
                    "guide, il porte le décorateur <code>@Slot(…)</code>, qui déclare les "
                    "arguments qu'il reçoit (page « Prérequis », en bas de l'arbre). Le signal "
                    "transmet l'état de la case, mais <code>@Slot()</code> ne déclare aucun "
                    "paramètre : PySide6 accepte un slot qui reçoit moins d'arguments que le "
                    "signal n'en transmet."
                    "<br><br>Comme dans toute étape « À vous », les contrôles sont créés avec la "
                    "page de la notion, cachés jusqu'ici. À l'arrivée sur l'étape, le guide "
                    "appelle la fonction affichée qui les relie, ici <code>connectControls()</code>, "
                    "puis les montre. « Comment se servir du guide », dans l'introduction, le dit "
                    "pour tout le guide."
                    "<br><br>Comparer la mesure douteuse à l'équipe 1 seule, puis à l'équipe 2 "
                    "seule."
                ),
                run=self._exploreTeams,
                codeSource=(self.connectControls, self.updateTeamsVisibility),
                references=[("QGraphicsItem.setVisible", qtDocUrl("QtWidgets", "QGraphicsItem", "setVisible"))],
            ),
        ]
