"""Notion 1.6 : résumer des mesures répétées, deux graphiques côte à côte.

Contexte : la température d'une salle est relevée chaque heure, de 6 h à
22 h, pendant 30 jours. Les mesures sont simulées. Chaque jour diffère un
peu des autres. À gauche : les mesures, puis la moyenne de chaque heure, sa
dispersion (± un écart type) et l'incertitude sur la moyenne. À droite :
l'histogramme des mesures de l'heure analysée, comparé à une courbe en
cloche.

Étapes couvertes, une nouveauté par étape : deux graphiques côte à côte,
la température typique, 30 jours de mesures dans un tableau à deux
dimensions, les mesures individuelles, l'heure analysée, la moyenne
(`np.mean`), l'écart type (`np.std`), l'incertitude sur la moyenne, le
comptage par tranche (`np.histogram`), le tracé en marches (`stepMode`),
les mesures près de l'histogramme, la courbe en cloche. Un bouton et deux
sélecteurs numériques font ensuite explorer le tirage, le nombre de jours
et l'heure analysée.

Chaque étape est une méthode de `QTopicStatisticsTab`. Les calculs sont des
fonctions du module, montrées à leur étape.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetPlotItem

_PlotDataItemPage = "api_reference/graphicsItems/plotdataitem"


def baselineTemperature(hour: float | np.ndarray) -> float | np.ndarray:
    """La température typique de la salle, en °C : 18 °C à 6 h, 24 °C à 14 h.

    `hour` est une heure, ou un tableau d'heures de forme (n,) ; le résultat
    est un réel, ou un tableau de réels de même forme.
    """
    return 18 + 6 * np.sin((hour - 6) / 16 * np.pi)


def generateSamples(hours: np.ndarray, dayCount: int, rng: np.random.Generator) -> np.ndarray:
    """Une mesure par heure et par jour.

    `hours` est un tableau d'heures de forme (n,). Rend un tableau de réels
    de forme (n, dayCount) : samples[rangée, jour], une rangée par heure.
    """
    samples = np.zeros((hours.shape[0], dayCount))
    for row in range(hours.shape[0]):
        samples[row, :] = baselineTemperature(hours[row]) + rng.normal(0, 1.2, dayCount)
    return samples


def gatherMeasurements(hours: np.ndarray, samples: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Toutes les mesures, en deux tableaux de réels de forme (n × jours,) : leur heure, leur température.

    `hours` est de forme (n,), `samples` de forme (n, jours).
    """
    measureHours = np.repeat(hours, samples.shape[1])
    temperatures = samples.flatten()
    return measureHours, temperatures


def hourlyMeans(samples: np.ndarray) -> np.ndarray:
    """La moyenne de chaque rangée, c'est-à-dire de chaque heure.

    `samples` est de forme (n, jours) ; rend un tableau de réels de forme (n,).
    """
    means = np.zeros(samples.shape[0])
    for row in range(samples.shape[0]):
        means[row] = np.mean(samples[row, :])
    return means


def hourlyDeviations(samples: np.ndarray) -> np.ndarray:
    """L'écart type expérimental de chaque heure, qui divise par n − 1.

    `samples` est de forme (n, jours) ; rend un tableau de réels de forme (n,).
    """
    deviations = np.zeros(samples.shape[0])
    for row in range(samples.shape[0]):
        deviations[row] = np.std(samples[row, :], ddof=1)
    return deviations


def binCenters(edges: np.ndarray) -> np.ndarray:
    """Le centre de chaque tranche : `edges` est de forme (m + 1,), le résultat de forme (m,)."""
    return (edges[:-1] + edges[1:]) / 2


def bellCurve(values: np.ndarray, temperatures: np.ndarray) -> np.ndarray:
    """La courbe en cloche de même moyenne et de même écart type que `values`, à l'échelle des comptes.

    `values` et `temperatures` sont des tableaux de réels à une dimension ;
    rend un tableau de réels de la forme de `temperatures`.
    """
    mean = np.mean(values)
    sigma = np.std(values, ddof=1)
    sampleCount = values.shape[0]
    binWidth = 0.5
    height = sampleCount * binWidth / (sigma * np.sqrt(2 * np.pi))
    reducedGap = (temperatures - mean) / sigma
    return height * np.exp(-(reducedGap ** 2) / 2)


class QTopicStatisticsTab(QWidget):
    """Onglet de la notion 1.6 : moyenne, dispersion et distribution de mesures simulées.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        layoutWidget, leftPlot, rightPlot: La grille et ses deux
            graphiques, créés une seule fois.
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        regenerateButton, daysSlider, hourSlider: Le nouveau tirage, le
            nombre de jours et l'heure analysée.
        hours, rng, samples, analyzedHour: Les données, ou None avant leur
            étape.
        allPoints, analyzedPoints, meanCurve, upperBand, lowerBand,
            errorBars, histogramPoints, histogram, rightPoints, bell: Les
            éléments graphiques que l'exploration met à jour.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Statistiques"
    TabToolTip = "Moyenne, écart type, incertitude, histogramme et courbe en cloche"
    RecommendedPanelWidth = 600
    Objective = (
        "Résumer des mesures répétées : leur moyenne, leur dispersion et l'incertitude sur la "
        "moyenne, puis la distribution des mesures d'une heure, en histogramme."
    )
    KeyConcepts = [
        "Un tableau à deux dimensions range une mesure par heure et par jour.",
        "La moyenne résume des mesures répétées ; l'écart type mesure leur dispersion. Il ne "
        "diminue pas quand on mesure plus longtemps : c'est une propriété du phénomène.",
        "L'incertitude sur la moyenne, l'écart type divisé par √n, diminue avec le nombre n de "
        "mesures.",
        "Un histogramme compte les mesures par tranche, et se trace en marches.",
        "Une courbe en cloche est un modèle, comparé aux mesures.",
    ]
    KeyApis = [
        "numpy.arange", "numpy.mean", "numpy.std", "numpy.histogram", "PlotDataItem (stepMode)",
        "FillBetweenItem", "ErrorBarItem",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._clearData()

        self.createLayout()
        self.controls = QControlPanel()
        self.regenerateButton = self.controls.addButton("Nouveau tirage")
        self.daysSlider = self.controls.addSlider("Nombre de jours", 5, 100, 30, suffix="jours")
        self.hourSlider = self.controls.addSlider("Heure analysée", 6, 22, 14, suffix="h")

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.layoutWidget, 1)
        contentLayout.addWidget(self.controls)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _clearData(self) -> None:
        """Oublie les données et les éléments graphiques remplis par les étapes."""
        self.hours: np.ndarray | None = None
        self.rng: np.random.Generator | None = None
        self.samples: np.ndarray | None = None
        self.analyzedHour: int | None = None
        self.allPoints: pg.PlotDataItem | None = None
        self.analyzedPoints: pg.PlotDataItem | None = None
        self.meanCurve: pg.PlotDataItem | None = None
        self.upperBand: pg.PlotDataItem | None = None
        self.lowerBand: pg.PlotDataItem | None = None
        self.errorBars: pg.ErrorBarItem | None = None
        self.histogramPoints: pg.PlotDataItem | None = None
        self.histogram: pg.PlotDataItem | None = None
        self.rightPoints: pg.PlotDataItem | None = None
        self.bell: pg.PlotDataItem | None = None

    def _resetState(self) -> None:
        """Vide les deux graphiques et remet les contrôles à zéro."""
        self.controls.resetControls()
        resetPlotItem(self.leftPlot)
        resetPlotItem(self.rightPlot)
        self._clearData()

    # -- Étapes ------------------------------------------------------------------------------------

    def createLayout(self) -> None:
        """Crée deux graphiques côte à côte, dans les colonnes 0 et 1 de la grille."""
        self.layoutWidget = pg.GraphicsLayoutWidget()
        self.leftPlot = self.layoutWidget.addPlot(row=0, col=0)
        self.rightPlot = self.layoutWidget.addPlot(row=0, col=1)

    def setUpPlots(self) -> None:
        """Titres, axes, grilles et légendes des deux graphiques."""
        self.leftPlot.setTitle("Température par heure, 30 jours")
        self.leftPlot.setLabel("bottom", "Heure")
        self.leftPlot.setLabel("left", "Température", units="°C")
        self.leftPlot.showGrid(x=True, y=True, alpha=0.3)
        self.leftPlot.setYRange(12, 32, padding=0)
        self.leftPlot.addLegend(offset=(10, 10))
        self.rightPlot.setTitle("Distribution à 14 h")
        self.rightPlot.setLabel("bottom", "Température", units="°C")
        self.rightPlot.setLabel("left", "Nombre de jours")
        self.rightPlot.showGrid(x=True, y=True, alpha=0.3)
        self.rightPlot.addLegend(offset=(10, 10))

    def plotBaseline(self) -> None:
        """La température typique, de 6 h à 22 h, en tirets."""
        hours = np.linspace(6, 22, 100)
        temperatures = baselineTemperature(hours)
        dashedPen = pg.mkPen("w", width=1, style=Qt.PenStyle.DashLine)
        self.leftPlot.plot(hours, temperatures, pen=dashedPen, name="Température typique")

    def createSamples(self) -> None:
        """Les heures de 6 à 22, un générateur à graine fixe, et 30 jours de mesures."""
        self.hours = np.arange(6, 23)
        self.rng = np.random.default_rng(42)
        self.samples = generateSamples(self.hours, 30, self.rng)

    def plotAllMeasurements(self) -> None:
        """Toutes les mesures, en un seul nuage de petits points gris, dans le graphique des heures."""
        measureHours, temperatures = gatherMeasurements(self.hours, self.samples)
        self.allPoints = self.leftPlot.plot(measureHours, temperatures, pen=None, symbol="o", symbolSize=4,
                                            symbolBrush=(150, 150, 150), name="Mesures")

    def plotAnalyzedHour(self) -> None:
        """Les mesures de l'heure analysée, 14 h, en rouge, dans le graphique des heures."""
        self.analyzedHour = 14
        values = self.samples[self.analyzedHour - 6, :]
        self.analyzedPoints = self.leftPlot.plot(np.full(values.shape, self.analyzedHour), values, pen=None,
                                                 symbol="o", symbolSize=6, symbolBrush="r",
                                                 name="Heure analysée")

    def plotMeans(self) -> None:
        """La moyenne de chaque heure, en jaune."""
        self.meanCurve = self.leftPlot.plot(self.hours, hourlyMeans(self.samples), pen=pg.mkPen("y", width=2),
                                            name="Moyenne")

    def plotDispersion(self) -> None:
        """La bande de dispersion : la moyenne plus ou moins un écart type, remplie."""
        means = hourlyMeans(self.samples)
        deviations = hourlyDeviations(self.samples)
        self.upperBand = self.leftPlot.plot(self.hours, means + deviations, pen="c", name="± 1 écart type")
        self.lowerBand = self.leftPlot.plot(self.hours, means - deviations, pen="c")
        self.leftPlot.addItem(pg.FillBetweenItem(self.upperBand, self.lowerBand, brush=(0, 200, 200, 40)))

    def plotMeanUncertainty(self) -> None:
        """L'incertitude sur chaque moyenne, σ/√n, en barres d'erreur jaunes."""
        means = hourlyMeans(self.samples)
        uncertainty = hourlyDeviations(self.samples) / np.sqrt(self.samples.shape[1])
        self.errorBars = pg.ErrorBarItem(x=self.hours, y=means, top=uncertainty, bottom=uncertainty,
                                         beam=0.3, pen=pg.mkPen("y", width=2))
        self.leftPlot.addItem(self.errorBars)

    def countByBin(self) -> None:
        """Les mesures de 14 h comptées par tranche de 0,5 °C, en points, dans le graphique de distribution."""
        counts, edges = np.histogram(self.samples[self.analyzedHour - 6, :], bins=np.linspace(12, 30, 37))
        self.histogramPoints = self.rightPlot.plot(binCenters(edges), counts, pen=None, symbol="o",
                                                   symbolSize=6, symbolBrush=(100, 100, 220))

    def plotSteps(self) -> None:
        """Les mêmes comptes, tracés en marches remplies ; les points de l'étape précédente sont cachés."""
        counts, edges = np.histogram(self.samples[self.analyzedHour - 6, :], bins=np.linspace(12, 30, 37))
        self.histogram = self.rightPlot.plot(edges, counts, stepMode="center", fillLevel=0,
                                             fillBrush=(100, 100, 220, 150), name="Mesures par tranche")
        self.histogramPoints.setVisible(False)

    def plotRightMeasurements(self) -> None:
        """Les mesures de 14 h, en rouge, sous les marches, à la hauteur 0,3."""
        values = self.samples[self.analyzedHour - 6, :]
        self.rightPoints = self.rightPlot.plot(values, np.full(values.shape, 0.3), pen=None, symbol="o",
                                               symbolSize=5, symbolBrush="r")

    def plotBellCurve(self) -> None:
        """La courbe en cloche de même moyenne et de même écart type que les mesures de 14 h."""
        curveTemperatures = np.linspace(12, 30, 300)
        counts = bellCurve(self.samples[self.analyzedHour - 6, :], curveTemperatures)
        self.bell = self.rightPlot.plot(curveTemperatures, counts, pen=pg.mkPen("y", width=2),
                                        name="Courbe en cloche")

    def connectControls(self) -> None:
        """Relie le bouton et les deux sélecteurs numériques à leur slot."""
        self.regenerateButton.clicked.connect(self.regenerateSamples)
        self.daysSlider.valueChanged.connect(self.regenerateSamples)
        self.hourSlider.valueChanged.connect(self.setAnalyzedHour)

    @Slot()
    def regenerateSamples(self) -> None:
        """Tire de nouvelles mesures, pour le nombre de jours choisi, puis redessine."""
        self.samples = generateSamples(self.hours, self.daysSlider.value(), self.rng)
        self.redraw()

    @Slot()
    def setAnalyzedHour(self) -> None:
        """Change l'heure analysée, puis redessine."""
        self.analyzedHour = self.hourSlider.value()
        self.redraw()

    def redraw(self) -> None:
        """Met chaque élément graphique à jour, avec les gestes des étapes précédentes."""
        measureHours, temperatures = gatherMeasurements(self.hours, self.samples)
        self.allPoints.setData(measureHours, temperatures)
        values = self.samples[self.analyzedHour - 6, :]
        self.analyzedPoints.setData(np.full(values.shape, self.analyzedHour), values)
        means = hourlyMeans(self.samples)
        deviations = hourlyDeviations(self.samples)
        self.meanCurve.setData(self.hours, means)
        self.upperBand.setData(self.hours, means + deviations)
        self.lowerBand.setData(self.hours, means - deviations)
        uncertainty = deviations / np.sqrt(self.samples.shape[1])
        self.errorBars.setData(x=self.hours, y=means, top=uncertainty, bottom=uncertainty)
        self.leftPlot.setTitle(f"Température par heure, {self.samples.shape[1]} jours")
        self.rightPlot.setTitle(f"Distribution à {self.analyzedHour} h")
        counts, edges = np.histogram(values, bins=np.linspace(12, 30, 37))
        self.histogram.setData(edges, counts)
        self.rightPoints.setData(values, np.full(values.shape, 0.3))
        curveTemperatures = np.linspace(12, 30, 300)
        self.bell.setData(curveTemperatures, bellCurve(values, curveTemperatures))

    def _exploreStatistics(self) -> None:
        """Connecte les contrôles, puis les révèle."""
        self.connectControls()
        self.controls.reveal()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : deux graphiques côte à côte",
                explanation=(
                    "Rien de nouveau : une grille de graphiques, cette fois en deux colonnes "
                    "d'une même rangée (notion 1.5), puis les titres, les axes, les grilles et "
                    "les légendes (notion 1.1). Le <b>graphique des heures</b>, à gauche, montrera "
                    "les mesures heure par heure. Le <b>graphique de distribution</b>, à droite, "
                    "montrera les mesures d'une seule heure. Ces deux noms servent dans toute la "
                    "notion. La zone visible du graphique des heures est imposée de 12 "
                    "à 32 °C (notion 1.2) : les mesures dépassent rarement 28 °C, et le haut garde la "
                    "place de la légende."
                ),
                run=self.setUpPlots,
                codeSource=(self.createLayout, self.setUpPlots),
                references=[("GraphicsLayout.addPlot", pyqtgraphDocUrl("api_reference/graphicsItems/graphicslayout",
                                                                       "GraphicsLayout.addPlot"))],
            ),
            QStepWalkthrough.Step(
                title="La température typique",
                explanation=(
                    "La température de la salle monte le jour et baisse le soir. Un modèle "
                    "simple la donne à chaque heure h, de 6 h à 22 h : T(h) = 18 + "
                    "6·sin((h − 6)/16·π), en °C. Elle vaut 18 °C à 6 h et à 22 h, et 24 °C à "
                    "14 h, au milieu de la journée."
                    "<br><br><code>baselineTemperature(hour)</code> calcule ce modèle. Comme "
                    "<code>displacement()</code> à la notion 1.3, elle reçoit une heure ou un "
                    "tableau d'heures : ici 100 heures d'un coup, tracées en tirets (notion "
                    "1.1)."
                ),
                run=self.plotBaseline,
                codeSource=(baselineTemperature, self.plotBaseline),
                references=[("mkPen", pyqtgraphDocUrl("api_reference/functions", "mkPen"))],
            ),
            QStepWalkthrough.Step(
                title="30 jours de mesures",
                explanation=(
                    "<code>np.arange(6, 23)</code> rend les heures entières de 6 à 22 : comme "
                    "<code>range</code>, la borne de fin est exclue. Le générateur à graine de "
                    "la notion 1.4 ajoute à chaque mesure un bruit d'environ ±1,2 °C : chaque "
                    "jour diffère un peu du modèle."
                    "<br><br>La nouveauté de l'étape : les mesures vont dans un <b>tableau à deux "
                    "dimensions</b>, fait de rangées et de colonnes."
                    "<ul>"
                    "<li><code>np.zeros((rangées, jours))</code> le crée, rempli de zéros : 17 "
                    "rangées, une par heure, et 30 colonnes, une par jour ;</li>"
                    "<li><code>shape</code> rend sa forme, ici <code>(17, 30)</code> : "
                    "<code>shape[0]</code> est le nombre de rangées, <code>shape[1]</code> le "
                    "nombre de colonnes. Pour <code>hours</code>, à une dimension, "
                    "<code>hours.shape[0]</code> est le nombre d'heures ;</li>"
                    "<li><code>samples[rangée, jour]</code> désigne une case, et "
                    "<code>samples[rangée, :]</code> toute une rangée : les 30 jours d'une "
                    "heure.</li>"
                    "</ul>"
                    "Une boucle remplit une rangée par tour : la température typique de l'heure, "
                    "plus 30 bruits tirés d'un coup. Une seule instruction pourrait tout tirer, "
                    "mais il faudrait d'abord recopier la température typique de chaque heure "
                    "sur ses 30 colonnes : la boucle sur les rangées reste plus lisible, et "
                    "c'est un choix voulu. Rien ne change encore dans les graphiques."
                ),
                run=self.createSamples,
                codeSource=(generateSamples, self.createSamples),
                references=[
                    ("numpy.arange", numpyDocUrl("arange")),
                    ("numpy.zeros", numpyDocUrl("zeros")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Les mesures individuelles",
                explanation=(
                    "Regarder les données avant de les résumer. Un seul nuage de points les "
                    "montre toutes, s'il reçoit deux tableaux à une dimension : l'heure de chaque "
                    "mesure, et sa température. <code>gatherMeasurements()</code> les prépare. "
                    "<code>samples.flatten()</code> range toutes les cases, rangée après rangée, "
                    "dans un seul tableau. <code>samples.shape[1]</code> est le nombre de "
                    "colonnes (étape précédente), donc de jours. "
                    "<code>np.repeat(hours, samples.shape[1])</code> répète chaque heure autant "
                    "de fois, ici 30, de suite : chaque température a ainsi son heure en face "
                    "d'elle."
                    "<br><br>Dans le graphique des heures, 30 petits points gris par heure, "
                    "dispersés autour du modèle."
                ),
                run=self.plotAllMeasurements,
                codeSource=(gatherMeasurements, self.plotAllMeasurements),
                references=[
                    ("numpy.repeat", numpyDocUrl("repeat")),
                    ("numpy.ndarray.flatten", numpyDocUrl("ndarray.flatten")),
                ],
            ),
            QStepWalkthrough.Step(
                title="L'heure analysée",
                explanation=(
                    "<code>self.analyzedHour = 14</code> choisit l'heure qu'on regardera de près. "
                    "Ses mesures forment la rangée <code>self.samples[14 - 6, :]</code> : la "
                    "rangée 0 est 6 h. <code>np.full(values.shape, self.analyzedHour)</code> "
                    "rend un tableau de la forme de <code>values</code>, rempli de 14 : "
                    "l'abscisse de chaque point. Les 30 mesures de 14 h paraissent en rouge."
                ),
                run=self.plotAnalyzedHour,
                references=[("numpy.full", numpyDocUrl("full"))],
            ),
            QStepWalkthrough.Step(
                title="La moyenne",
                explanation=(
                    "<code>np.mean(tableau)</code> rend la moyenne des éléments d'un tableau. "
                    "<code>hourlyMeans()</code> l'applique à chaque rangée : la moyenne de "
                    "chaque heure, sur les 30 jours. La courbe jaune passe au milieu des points "
                    "gris, près du modèle."
                    "<br><br>La boucle est un choix voulu : <code>np.mean(samples, axis=1)</code> "
                    "ferait le même calcul d'un coup, rangée par rangée, mais la notion d'axe "
                    "demande plus d'explication que la boucle."
                ),
                run=self.plotMeans,
                codeSource=(hourlyMeans, self.plotMeans),
                references=[("numpy.mean", numpyDocUrl("mean"))],
            ),
            QStepWalkthrough.Step(
                title="La dispersion : ± un écart type",
                explanation=(
                    "L'<b>écart type</b>, noté σ, mesure la dispersion typique des mesures "
                    "autour de leur moyenne. Ici, il retrouve le bruit d'environ 1,2 °C ajouté "
                    "aux mesures. <code>np.std(tableau, ddof=1)</code> le calcule. "
                    "Pour n mesures, il fait la somme des carrés des écarts à la moyenne, la "
                    "divise, puis en prend la racine carrée : σ = √(Σ(x − moyenne)² / (n − 1)). "
                    "<code>ddof=1</code> donne cette division par n − 1 plutôt que par n : c'est "
                    "l'écart type expérimental, celui des mesures de laboratoire. La boucle suit "
                    "le même choix que pour la moyenne."
                    "<br><br>La bande cyan va de la moyenne moins σ à la moyenne plus σ, remplie "
                    "comme l'enveloppe de la notion 1.3. Environ deux mesures sur trois y "
                    "tombent, si leurs écarts suivent la courbe en cloche de l'étape « Une "
                    "courbe en cloche », plus loin : "
                    "une règle de la statistique, admise ici."
                ),
                run=self.plotDispersion,
                codeSource=(hourlyDeviations, self.plotDispersion),
                references=[("numpy.std", numpyDocUrl("std"))],
            ),
            QStepWalkthrough.Step(
                title="L'incertitude sur la moyenne",
                explanation=(
                    "La moyenne de n mesures est plus précise qu'une seule mesure. Son "
                    "<b>incertitude</b> vaut σ/√n : ici σ/√30, environ 0,2 °C. "
                    "<code>self.samples.shape[1]</code> est n, la deuxième dimension du tableau : "
                    "le nombre de jours. <code>np.sqrt()</code> en prend la racine carrée. Les "
                    "barres d'erreur jaunes (notion 1.2) la montrent sur chaque moyenne : bien "
                    "plus courtes que la bande de dispersion."
                ),
                run=self.plotMeanUncertainty,
                references=[("ErrorBarItem", pyqtgraphDocUrl("api_reference/graphicsItems/errorbaritem",
                                                             "ErrorBarItem"))],
            ),
            QStepWalkthrough.Step(
                title="Compter par tranche",
                explanation=(
                    "<code>np.histogram(valeurs, bins=bornes)</code> compte les valeurs qui "
                    "tombent dans chaque tranche. Les bornes vont de 12 à 30 °C par pas de "
                    "0,5 °C : 37 bornes, donc 36 tranches. Il rend deux tableaux, "
                    "<code>counts, edges</code> : les comptes, et les bornes. Il y a une borne "
                    "de plus que de comptes."
                    "<br><br><code>binCenters()</code> calcule le centre de chaque tranche, à "
                    "mi-chemin entre ses deux bornes. <code>edges[:-1]</code> garde toutes les "
                    "bornes sauf la dernière, <code>edges[1:]</code> toutes sauf la première, "
                    "comme le tampon de la notion 1.4 : leur somme, divisée par 2, donne les 36 "
                    "centres d'un coup. Dans le graphique de distribution, les comptes de 14 h, "
                    "un point par tranche."
                ),
                run=self.countByBin,
                codeSource=(binCenters, self.countByBin),
                references=[("numpy.histogram", numpyDocUrl("histogram"))],
            ),
            QStepWalkthrough.Step(
                title="Tracer en marches",
                explanation=(
                    "Un <b>histogramme</b> se trace en marches. "
                    "<code>stepMode=\"center\"</code> dessine une marche par tranche, d'une "
                    "borne à la suivante : il reçoit donc les bornes en x, et non les centres. "
                    "Le nom dit où se rapporte chaque compte : au centre de sa marche, entre deux "
                    "bornes. <code>fillLevel=0</code> remplit sous les marches jusqu'à zéro, avec "
                    "le pinceau <code>fillBrush</code>, un tuple avec opacité (notion 1.3)."
                    "<br><br>Les points de l'étape précédente ont servi à lire les comptes ; les "
                    "marches les remplacent. <code>setVisible(False)</code> les cache."
                ),
                run=self.plotSteps,
                references=[("PlotDataItem", pyqtgraphDocUrl(_PlotDataItemPage, "PlotDataItem"))],
            ),
            QStepWalkthrough.Step(
                title="Les mesures de 14 h près de l'histogramme",
                explanation=(
                    "Les points rouges du graphique des heures, reportés dans le graphique de "
                    "distribution : chaque mesure de 14 h est "
                    "placée à sa température, à la hauteur 0,3, sous les marches. Chaque marche "
                    "compte les points rouges qui sont sous elle."
                ),
                run=self.plotRightMeasurements,
                references=[("PlotItem.plot", pyqtgraphDocUrl("api_reference/graphicsItems/plotitem",
                                                              "PlotItem.plot"))],
            ),
            QStepWalkthrough.Step(
                title="Une courbe en cloche",
                explanation=(
                    "Un modèle à comparer : la courbe en cloche, aussi appelée <b>loi "
                    "normale</b>. C'est la forme que prennent, le plus souvent, de nombreuses "
                    "petites erreurs de mesure. Sa formule est donnée ici sans démonstration. "
                    "Pour n mesures de moyenne μ et d'écart type σ, et des tranches de "
                    "Δ = 0,5 °C, le compte attendu près de la température T vaut :"
                    "<br>compte = n·Δ / (σ·√(2π)) × e<sup>u</sup>, avec u = −½ × ((T − μ) / σ)²."
                    "<br>La cloche culmine à la moyenne, où u = 0 ; σ fixe sa largeur. Le "
                    "facteur n·Δ / (σ·√(2π)) ajuste sa hauteur pour qu'elle compte, en tout, les "
                    "n mesures."
                    "<br><br><code>bellCurve()</code> calcule ce compte attendu à 300 températures d'un "
                    "coup. Dans le code, <code>sampleCount</code> est n, le nombre de mesures "
                    "(<code>values.shape[0]</code>), et <code>binWidth</code> est Δ. Trois "
                    "temps :"
                    "<ul>"
                    "<li><code>height</code>, la hauteur n·Δ / (σ·√(2π)) ;</li>"
                    "<li><code>reducedGap</code>, l'<b>écart réduit</b> (T − μ) / σ : l'écart "
                    "de chaque température à la moyenne, compté en écarts types ;</li>"
                    "<li>le produit de la hauteur par e<sup>u</sup>, avec u = −(écart "
                    "réduit)² / 2, que <code>np.exp()</code> calcule pour chaque écart.</li>"
                    "</ul>"
                    "<br><br>Avec 30 mesures, les marches s'écartent encore nettement de la "
                    "cloche."
                ),
                run=self.plotBellCurve,
                codeSource=(bellCurve, self.plotBellCurve),
                references=[("numpy.std", numpyDocUrl("std"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : explorer",
                explanation=(
                    "Trois contrôles paraissent sous les graphiques : le bouton "
                    "<code>regenerateButton</code>, « Nouveau tirage » ; le sélecteur numérique "
                    "<code>daysSlider</code>, le nombre de jours, de 5 à 100, à 30 au départ ; "
                    "et <code>hourSlider</code>, l'heure analysée, de 6 à 22, à 14 au départ."
                    "<br><br>Le bouton et le nombre de jours sont connectés au même slot, "
                    "<code>regenerateSamples()</code>, qui tire de nouvelles mesures avec le même "
                    "générateur. L'heure est connectée à <code>setAnalyzedHour()</code>. "
                    "Les deux appellent <code>redraw()</code>, qui met chaque élément à jour par "
                    "<code>setData()</code>, avec les calculs des étapes précédentes. Les barres "
                    "d'erreur ont aussi leur <code>setData()</code>, qui reçoit les mêmes "
                    "paramètres que leur constructeur (notion 1.2). Un <code>setData()</code> "
                    "garde les réglages qu'il ne reçoit pas : le stylo, et pour l'histogramme "
                    "<code>stepMode</code> et le remplissage."
                    "<br><br>Les titres nomment ce que montre chaque graphique : le nombre de "
                    "jours, l'heure analysée. Quand ces données changent, <code>redraw()</code> "
                    "récrit le titre pour qu'il reste juste. Il n'y écrit aucun résultat "
                    "calculé, qui irait dans une étiquette d'information (notion 1.3)."
                    "<br><br>Passer à 100 jours : la bande de dispersion garde sa largeur, mais "
                    "les barres d'erreur raccourcissent, et les marches se rapprochent de la "
                    "cloche."
                ),
                run=self._exploreStatistics,
                codeSource=(self.connectControls, self.regenerateSamples, self.setAnalyzedHour, self.redraw),
                references=[("PlotDataItem.setData", pyqtgraphDocUrl(_PlotDataItemPage, "PlotDataItem.setData"))],
            ),
        ]
