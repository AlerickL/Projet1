"""Notion 1.8 : réagir aux signaux d'un graphique, en échelle logarithmique.

Contexte : un filtre passe-bas RC, mesuré au laboratoire. Un générateur
envoie une tension sinusoïdale de fréquence f à l'entrée ; un oscilloscope
mesure l'amplitude de la sortie, aux bornes du condensateur. Le gain
G = Vs/Ve suit G = 1/√(1 + (f/fc)²), avec fc = 1/(2πRC), R = 1,5 kΩ et
C = 100 nF. Note de conception, jamais affichée : les mesures ont été
simulées avec fc = 1000 Hz (C = 106 nF) et un bruit de 2 %.

Étapes couvertes : les mesures, la courbe théorique, les deux axes en
échelle logarithmique, chacun à son tour, le piège des exposants, puis les
signaux. Une étape fait la synthèse formelle des signaux déjà vus. Les
« À vous » ajoutent chacune un signal ou une stratégie : la coupure à la
souris, avec un compteur d'appels qui rend les signaux visibles ; la zone
visible et ses arguments (`sigRangeChanged`) ; un bouton et son slot ; une
bande qui réagit en direct, puis au relâchement (`LinearRegionItem`) ; un
signal émis par le code ; la souris seule (`sigDragged`) et trois façons de
traiter l'écho. Un inventaire des signaux de PyQtGraph ferme la notion.

Chaque étape est une méthode de `QTopicSignalsTab`. Les fonctions de calcul,
`lowPassGain()`, `cutoffFrequency()` et `frequencyText()`, sont écrites au
niveau du module.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QSignalBlocker, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetPlotItem

_PlotItemPage = "api_reference/graphicsItems/plotitem"
_ViewBoxPage = "api_reference/graphicsItems/viewbox"
_InfiniteLinePage = "api_reference/graphicsItems/infiniteline"
_RegionPage = "api_reference/graphicsItems/linearregionitem"

# The inventory of the last step: one row per signal, grouped by family.
_InventoryHtml = (
    "<table border='1' cellspacing='0' cellpadding='3'>"
    "<tr><th>Classe</th><th>Signal</th><th>Émis quand…</th><th>Arguments</th><th>Par le code ?</th>"
    "<th>Dans ce guide</th></tr>"
    "<tr><td colspan='6'><b>La zone visible</b> (<code>ViewBox</code>)</td></tr>"
    "<tr><td><code>ViewBox</code></td><td><code>sigRangeChanged</code></td><td>l'étendue change</td>"
    "<td>la zone visible, les étendues, les axes changés</td><td>oui</td><td>1.8</td></tr>"
    "<tr><td><code>ViewBox</code></td><td><code>sigXRangeChanged</code>, "
    "<code>sigYRangeChanged</code></td><td>l'étendue d'un seul axe change</td><td>la zone visible, "
    "l'intervalle de l'axe</td><td>oui</td><td>—</td></tr>"
    "<tr><td><code>ViewBox</code></td><td><code>sigRangeChangedManually</code></td><td>la souris "
    "change l'étendue</td><td>les axes que la souris peut changer</td><td>non</td><td>1.7</td></tr>"
    "<tr><td><code>ViewBox</code></td><td><code>sigResized</code></td><td>la zone visible change de "
    "taille, en pixels</td><td>la zone visible</td><td>oui, en changeant la taille du widget</td>"
    "<td>—</td></tr>"
    "<tr><td colspan='6'><b>Les éléments graphiques</b></td></tr>"
    "<tr><td><code>PlotDataItem</code></td><td><code>sigPointsClicked</code>, "
    "<code>sigPointsHovered</code></td><td>un clic sur des points, la souris sur des points</td>"
    "<td>la courbe, les points, l'évènement</td><td>non</td><td>1.3</td></tr>"
    "<tr><td><code>PlotDataItem</code></td><td><code>sigPlotChanged</code></td><td>les données "
    "changent</td><td>la courbe</td><td>oui, <code>setData()</code></td><td>—</td></tr>"
    "<tr><td><code>ScatterPlotItem</code></td><td><code>sigClicked</code>, <code>sigHovered</code>"
    "</td><td>un clic sur des points, la souris sur des points</td><td>le nuage, les points, "
    "l'évènement</td><td>non</td><td>—</td></tr>"
    "<tr><td><code>InfiniteLine</code></td><td><code>sigPositionChanged</code></td><td>la ligne "
    "bouge</td><td>la ligne</td><td>oui, <code>setValue()</code></td><td>1.3</td></tr>"
    "<tr><td><code>InfiniteLine</code></td><td><code>sigDragged</code></td><td>la souris fait "
    "glisser la ligne</td><td>la ligne</td><td>non</td><td>1.8</td></tr>"
    "<tr><td><code>InfiniteLine</code></td><td><code>sigPositionChangeFinished</code></td><td>la "
    "souris lâche la ligne</td><td>la ligne</td><td>non</td><td>—</td></tr>"
    "<tr><td><code>TargetItem</code></td><td><code>sigPositionChanged</code></td><td>la cible "
    "bouge</td><td>la cible</td><td>oui, <code>setPos()</code></td><td>plus loin : 2.5</td></tr>"
    "<tr><td><code>LinearRegionItem</code></td><td><code>sigRegionChanged</code></td><td>la bande "
    "bouge</td><td>la bande</td><td>oui, <code>setRegion()</code></td><td>1.8</td></tr>"
    "<tr><td><code>LinearRegionItem</code></td><td><code>sigRegionChangeFinished</code></td><td>la "
    "souris lâche la bande</td><td>la bande</td><td>oui, <code>setRegion()</code></td><td>1.8</td>"
    "</tr>"
    "<tr><td><code>LegendItem</code></td><td><code>sigSampleClicked</code></td><td>un clic sur "
    "l'échantillon d'une entrée</td><td>l'élément de l'entrée</td><td>non</td><td>—</td></tr>"
    "<tr><td colspan='6'><b>La scène</b>, qui reçoit toute la souris</td></tr>"
    "<tr><td><code>GraphicsScene</code></td><td><code>sigMouseMoved</code></td><td>la souris "
    "bouge</td><td>la position, en pixels de la scène</td><td>non</td><td>plus loin : 2.4</td></tr>"
    "<tr><td colspan='6'><b>Hérités de Qt</b>, sans préfixe <code>sig</code>, sur tout élément "
    "graphique</td></tr>"
    "<tr><td><code>QGraphicsObject</code></td><td><code>visibleChanged</code>, "
    "<code>xChanged</code>, <code>yChanged</code>…</td><td>la visibilité ou la position change</td>"
    "<td>aucun</td><td>oui, <code>setVisible()</code>, <code>setPos()</code></td><td>plus loin : "
    "2.3</td></tr>"
    "</table>"
)


def lowPassGain(frequency: float | np.ndarray, cutoff: float) -> float | np.ndarray:
    """Le gain G = 1/√(1 + (f/fc)²) d'un filtre passe-bas RC, sans unité.

    `frequency` est une fréquence en hertz, ou un tableau de fréquences ; le
    résultat est un réel, ou un tableau de réels de même forme.
    """
    return 1 / np.sqrt(1 + (frequency / cutoff) ** 2)


def cutoffFrequency(resistance: float, capacitance: float) -> float:
    """La fréquence de coupure fc = 1/(2πRC), en hertz ; R en ohms, C en farads."""
    return 1 / (2 * np.pi * resistance * capacitance)


def frequencyText(frequency: float) -> str:
    """Une fréquence en texte : en Hz sous 1 kHz, en kHz au-delà, avec une décimale sous 10 kHz."""
    if frequency < 1000:
        return f"{frequency:.0f} Hz"
    if frequency < 10000:
        return f"{frequency / 1000:.1f} kHz"
    return f"{frequency / 1000:.0f} kHz"


class QTopicSignalsTab(QWidget):
    """Onglet de la notion 1.8 : la réponse d'un filtre RC, et les signaux du graphique.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        plotWidget: Le widget du graphique, créé une seule fois.
        readout: La lecture sous le graphique (outil présenté en 1.5), qui
            montre le compteur d'appels.
        controls: Le panneau des contrôles des étapes « À vous » (plomberie).
        frequencyLogCheck, gainLogCheck: L'échelle de chaque axe.
        showAllButton: Le bouton « Tout voir ».
        resistanceSlider: La résistance R, en demi-kΩ.
        echoCombo: La façon de traiter l'écho entre la ligne et le sélecteur.
        measuredFrequencies, measuredGains, frequencies: Les tableaux des
            mesures et de la théorie, ou None avant leur étape.
        callCounts: Le nombre d'appels de chaque slot, par son nom.
        measurements, theoryCurve, cutoffLine, rangeLabel, band, slopeLabel:
            Les éléments graphiques que les signaux modifient, ou None avant
            leur étape.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Réagir aux signaux"
    TabToolTip = "Un filtre RC en échelle logarithmique, et les signaux du graphique : qui, quand, avec quoi"
    RecommendedPanelWidth = 660
    Objective = (
        "Choisir l'échelle de chaque axe. Puis faire réagir un graphique à ses signaux : savoir "
        "ce que chacun transmet, s'il vient de la souris ou du code, et s'il est émis en direct "
        "ou à la fin d'un geste."
    )
    KeyConcepts = [
        "Chaque axe passe en échelle logarithmique indépendamment de l'autre. En double échelle "
        "logarithmique, une loi de puissance, G proportionnel à une puissance de f, devient une "
        "droite.",
        "En échelle logarithmique, la zone visible compte en exposants : une position, une "
        "étendue. PyQtGraph convertit les courbes, pas les éléments ajoutés un à un.",
        "Un signal a un émetteur, un moment et des arguments. Le slot relié reçoit ceux qu'il "
        "déclare.",
        "Certains signaux sont émis par la souris seule, d'autres aussi par le code ; certains en "
        "direct, d'autres à la fin du geste. Le bon choix évite le travail inutile.",
        "Deux commandes reliées dans les deux sens se renvoient leurs changements : un écho, "
        "qu'on coupe.",
    ]
    KeyApis = [
        "PlotItem.setLogMode", "numpy.logspace", "InfiniteLine.value", "ViewBox.sigRangeChanged",
        "ViewBox.autoRange", "LinearRegionItem", "LinearRegionItem.sigRegionChanged",
        "LinearRegionItem.sigRegionChangeFinished", "numpy.polyfit", "InfiniteLine.sigDragged",
        "QSignalBlocker",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.measuredFrequencies: np.ndarray | None = None
        self.measuredGains: np.ndarray | None = None
        self.frequencies: np.ndarray | None = None
        self.callCounts: dict[str, int] = {}
        self.measurements: pg.PlotDataItem | None = None
        self.theoryCurve: pg.PlotDataItem | None = None
        self.cutoffLine: pg.InfiniteLine | None = None
        self.rangeLabel: pg.TextItem | None = None
        self.band: pg.LinearRegionItem | None = None
        self.slopeLabel: pg.TextItem | None = None

        self.createPlotWidget()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.frequencyLogCheck = self.controls.addCheckBox("Fréquence en échelle logarithmique", checked=True)
        self.gainLogCheck = self.controls.addCheckBox("Gain en échelle logarithmique", checked=True)
        self.showAllButton = self.controls.addButton("Tout voir")
        self.resistanceSlider = self.controls.addSlider("Résistance R", 1, 20, 3, divisor=2, suffix="kΩ")
        self.echoCombo = self.controls.addComboBox(
            "Contre l'écho", [("rien", "none"), ("déconnexion ciblée", "disconnect"),
                              ("QSignalBlocker", "blocker")], currentIndex=1)

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
        """Vide le graphique et la lecture, et remet les contrôles à zéro, cases réactivées."""
        self.controls.resetControls()
        self.frequencyLogCheck.setEnabled(True)
        self.gainLogCheck.setEnabled(True)
        self.readout.clear()
        if self.rangeLabel is not None:
            self.plotWidget.getViewBox().sigRangeChanged.disconnect(self.showVisibleRange)
            self.plotWidget.scene().removeItem(self.rangeLabel)
        resetPlotItem(self.plotWidget.getPlotItem())
        self.measuredFrequencies = None
        self.measuredGains = None
        self.frequencies = None
        self.callCounts = {}
        self.measurements = None
        self.theoryCurve = None
        self.cutoffLine = None
        self.rangeLabel = None
        self.band = None
        self.slopeLabel = None

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidget(self) -> None:
        """Crée le widget du graphique, vide."""
        self.plotWidget = pg.PlotWidget()

    def setUpPlot(self) -> None:
        """Titre, axes, grille et légende, puis les treize mesures de l'oscilloscope, en points rouges."""
        self.plotWidget.setTitle("Filtre passe-bas RC : le gain en fonction de la fréquence")
        self.plotWidget.setLabel("bottom", "Fréquence", units="Hz")
        self.plotWidget.setLabel("left", "Gain Vs/Ve")
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)
        self.plotWidget.addLegend(offset=(-10, 10))
        self.measuredFrequencies = np.array([10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000,
                                             50000, 100000])
        self.measuredGains = np.array([1.04, 0.949, 1.01, 0.984, 0.972, 0.891, 0.679, 0.445, 0.193, 0.106,
                                       0.0502, 0.0199, 0.00994])
        self.measurements = self.plotWidget.plot(self.measuredFrequencies, self.measuredGains, pen=None,
                                                 symbol="o", symbolSize=9, symbolBrush="r",
                                                 name="Mesures (oscilloscope)")

    def plotTheory(self) -> None:
        """La courbe théorique, pour R = 1,5 kΩ et C = 100 nF, sur 400 fréquences de 10 Hz à 100 kHz."""
        self.frequencies = np.logspace(1, 5, 400)
        cutoff = cutoffFrequency(1500, 100e-9)
        self.theoryCurve = self.plotWidget.plot(self.frequencies, lowPassGain(self.frequencies, cutoff),
                                                pen=pg.mkPen("y", width=2), name="Théorie")

    def useLogLogScale(self) -> None:
        """Les deux axes en échelle logarithmique, puis un cadrage immédiat sur les données converties."""
        self.plotWidget.setLogMode(x=True, y=True)
        self.plotWidget.autoRange()

    def connectScaleControls(self) -> None:
        """Relie chaque case à cocher au slot de l'échelle de son axe."""
        self.frequencyLogCheck.toggled.connect(self.setFrequencyLog)
        self.gainLogCheck.toggled.connect(self.setGainLog)

    @Slot(bool)
    def setFrequencyLog(self, logarithmic: bool) -> None:
        """Met l'axe des fréquences en échelle logarithmique, ou linéaire, puis recadre ; l'autre axe ne change pas."""
        self.plotWidget.setLogMode(x=logarithmic)
        self.plotWidget.autoRange()

    @Slot(bool)
    def setGainLog(self, logarithmic: bool) -> None:
        """Met l'axe du gain en échelle logarithmique, ou linéaire, puis recadre ; l'autre axe ne change pas."""
        self.plotWidget.setLogMode(y=logarithmic)
        self.plotWidget.autoRange()

    def addCutoffLine(self) -> None:
        """Les deux axes en log, figés ; puis la ligne de la coupure, placée par l'exposant de fc."""
        self.frequencyLogCheck.setChecked(True)
        self.gainLogCheck.setChecked(True)
        self.frequencyLogCheck.setEnabled(False)
        self.gainLogCheck.setEnabled(False)
        cutoff = cutoffFrequency(1500, 100e-9)
        self.cutoffLine = pg.InfiniteLine(pos=np.log10(cutoff), angle=90, movable=True,
                                          pen=pg.mkPen("c", width=2), label="fc")
        self.plotWidget.addItem(self.cutoffLine)

    def _signalsSoFar(self) -> None:
        """Une synthèse en texte : rien ne s'exécute."""

    def countCall(self, slotName: str) -> None:
        """Compte un appel de plus du slot nommé, et écrit tous les comptes dans la lecture, un par ligne."""
        self.callCounts[slotName] = self.callCounts.get(slotName, 0) + 1
        lines = []
        for name, count in self.callCounts.items():
            lines.append(f"{name:<18}{count:>6} appels")
        self.readout.setText("\n".join(lines))

    def connectCutoffLine(self) -> None:
        """Un compteur d'appels vide ; puis le déplacement de la ligne relié au slot qui recalcule la théorie."""
        self.callCounts = {}
        self.cutoffLine.sigPositionChanged.connect(self.updateTheory)

    @Slot()
    def updateTheory(self) -> None:
        """Recalcule la courbe théorique pour la coupure de la ligne, et écrit fc sur la ligne."""
        self.countCall("updateTheory")
        cutoff = 10 ** self.cutoffLine.value()
        self.theoryCurve.setData(self.frequencies, lowPassGain(self.frequencies, cutoff))
        self.cutoffLine.label.setFormat(f"fc = {cutoff:.0f} Hz")

    def connectVisibleRange(self) -> None:
        """Une étiquette accrochée à la zone visible, puis le changement d'étendue relié à son slot."""
        self.rangeLabel = pg.TextItem(color="w")
        self.rangeLabel.setParentItem(self.plotWidget.getViewBox())
        self.rangeLabel.setPos(10, 200)
        self.plotWidget.getViewBox().sigRangeChanged.connect(self.showVisibleRange)

    @Slot(object, object)
    def showVisibleRange(self, viewBox: pg.ViewBox, ranges: list) -> None:
        """Écrit les fréquences visibles et leur nombre de décades, à partir des exposants reçus."""
        self.countCall("showVisibleRange")
        low, high = ranges[0]
        text = (f"Fréquences visibles : de {frequencyText(10 ** low)} à {frequencyText(10 ** high)}, "
                f"{high - low:.1f} décades")
        self.rangeLabel.setText(text.replace(".", ","))

    def connectShowAllButton(self) -> None:
        """Relie le bouton « Tout voir » à son slot."""
        self.showAllButton.clicked.connect(self.showAllData)

    @Slot()
    def showAllData(self) -> None:
        """Cadre une fois la zone visible sur toutes les données."""
        self.countCall("showAllData")
        self.plotWidget.autoRange()

    def addBand(self) -> None:
        """Une bande de fréquences déplaçable, de 5 à 100 kHz, reliée au slot qui colore ses mesures."""
        self.band = pg.LinearRegionItem(values=(np.log10(5000), np.log10(100000)), brush=(255, 255, 0, 30))
        self.plotWidget.addItem(self.band)
        self.band.sigRegionChanged.connect(self.highlightBand)
        self.highlightBand()

    def measurementsInBand(self) -> np.ndarray:
        """Un tableau de booléens de forme (13,) : True pour chaque mesure dont la fréquence est dans la bande."""
        low, high = self.band.getRegion()
        exponents = np.log10(self.measuredFrequencies)
        return (exponents >= low) & (exponents <= high)

    @Slot()
    def highlightBand(self) -> None:
        """Colore en jaune les mesures de la bande, en rouge les autres."""
        self.countCall("highlightBand")
        inside = self.measurementsInBand()
        self.measurements.scatter.setBrush(np.where(inside, "y", "r"))

    def connectBandRelease(self) -> None:
        """Une étiquette pour la pente, puis la fin du geste sur la bande reliée au slot qui la mesure."""
        self.slopeLabel = pg.TextItem(color="y")
        self.plotWidget.addItem(self.slopeLabel)
        self.band.sigRegionChangeFinished.connect(self.fitBandSlope)
        self.fitBandSlope()

    @Slot()
    def fitBandSlope(self) -> None:
        """Ajuste une droite aux mesures de la bande, en exposants, et écrit sa pente en bas de la bande."""
        self.countCall("fitBandSlope")
        inside = self.measurementsInBand()
        low, high = self.band.getRegion()
        self.slopeLabel.setPos(low, -2)
        if np.count_nonzero(inside) < 2:
            self.slopeLabel.setText("Moins de deux mesures : pas de pente")
            return
        slope, intercept = np.polyfit(np.log10(self.measuredFrequencies[inside]),
                                      np.log10(self.measuredGains[inside]), 1)
        self.slopeLabel.setText(f"Pente : {slope:.2f}".replace(".", ","))

    def connectResistanceSlider(self) -> None:
        """Relie le sélecteur de la résistance au slot qui déplace la ligne de la coupure."""
        self.resistanceSlider.valueChanged.connect(self.setResistance)

    @Slot()
    def setResistance(self) -> None:
        """Place la ligne de la coupure pour la résistance du sélecteur, et C = 100 nF."""
        self.countCall("setResistance")
        resistance = self.resistanceSlider.value() * 500
        self.cutoffLine.setValue(np.log10(cutoffFrequency(resistance, 100e-9)))

    def connectDraggedLine(self) -> None:
        """Relie le glissement de la ligne à la souris au slot qui règle le sélecteur."""
        self.cutoffLine.sigDragged.connect(self.matchResistance)

    @Slot()
    def matchResistance(self) -> None:
        """Règle le sélecteur sur la résistance de la ligne déplacée, selon la façon choisie de traiter l'écho."""
        self.countCall("matchResistance")
        cutoff = 10 ** self.cutoffLine.value()
        resistance = 1 / (2 * np.pi * cutoff * 100e-9)
        value = round(resistance / 500)
        strategy = self.echoCombo.currentData()
        if strategy == "disconnect":
            self.resistanceSlider.valueChanged.disconnect(self.setResistance)
            self.resistanceSlider.setValue(value)
            self.resistanceSlider.valueChanged.connect(self.setResistance)
        elif strategy == "blocker":
            with QSignalBlocker(self.resistanceSlider):
                self.resistanceSlider.setValue(value)
        else:
            self.resistanceSlider.setValue(value)

    def _inventoryOnly(self) -> None:
        """Un inventaire en texte : rien ne s'exécute."""

    def _exploreScales(self) -> None:
        """Connecte les deux cases à cocher, puis les révèle."""
        self.connectScaleControls()
        self.controls.reveal(self.frequencyLogCheck, self.gainLogCheck)

    def _moveCutoff(self) -> None:
        """Connecte la ligne, puis appelle le slot une première fois."""
        self.connectCutoffLine()
        self.updateTheory()

    def _readVisibleRange(self) -> None:
        """Connecte l'étendue, puis appelle le slot une première fois, avec la zone visible et son étendue."""
        self.connectVisibleRange()
        self.showVisibleRange(self.plotWidget.getViewBox(), self.plotWidget.viewRange())

    def _exploreShowAll(self) -> None:
        """Connecte le bouton, puis le révèle."""
        self.connectShowAllButton()
        self.controls.reveal(self.showAllButton)

    def _exploreResistance(self) -> None:
        """Connecte le sélecteur de la résistance, puis le révèle."""
        self.connectResistanceSlider()
        self.controls.reveal(self.resistanceSlider)

    def _exploreEcho(self) -> None:
        """Connecte le glissement de la ligne, puis révèle la liste de l'écho."""
        self.connectDraggedLine()
        self.controls.reveal(self.echoCombo)

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : le graphique et les mesures",
                explanation=(
                    "Rien de nouveau : le widget du graphique, son titre, ses axes, sa grille et sa "
                    "légende (notion 1.1), puis un nuage de points rouges (notion 1.2). Les deux "
                    "tableaux de mesures sont gardés dans <code>self.measuredFrequencies</code> "
                    "et <code>self.measuredGains</code>, le nuage dans "
                    "<code>self.measurements</code>."
                    "<br><br><i>Pour l'exemple</i> : un <b>filtre passe-bas RC</b>, qui laisse passer les "
                    "basses fréquences : une "
                    "résistance R = 1,5 kΩ suivie d'un condensateur C = 100 nF. Au laboratoire, "
                    "un générateur envoie à l'entrée une tension sinusoïdale Ve, de fréquence f. "
                    "Un oscilloscope mesure l'amplitude de la sortie Vs, aux bornes du "
                    "condensateur. Plus la fréquence est haute, plus le condensateur laisse passer "
                    "le courant sans garder de tension : Vs diminue. Le <b>gain</b> Vs/Ve, sans "
                    "unité, est relevé pour treize fréquences, de 10 Hz à 100 kHz. Il ne peut pas "
                    "dépasser 1 : le gain de 1,04 à 10 Hz est l'incertitude de lecture à "
                    "l'oscilloscope, quelques pour cent. Les mesures sont écrites en clair dans le "
                    "code."
                    "<br><br>À gauche, presque tout se tasse contre l'axe vertical : de 10 Hz à "
                    "1 kHz, les mesures occupent 1 % de la largeur."
                ),
                run=self.setUpPlot,
                codeSource=(self.createPlotWidget, self.setUpPlot),
                references=[("PlotItem.plot", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.plot"))],
            ),
            QStepWalkthrough.Step(
                title="La courbe théorique",
                explanation=(
                    "Le gain du filtre suit G = 1/√(1 + (f/fc)²). La <b>fréquence de coupure</b> "
                    "fc = 1/(2πRC) vaut ici 1061 Hz : à cette fréquence, le gain vaut "
                    "1/√2 ≈ 0,71. Les formules sont admises : seule compte ici leur traduction en "
                    "Python, <code>lowPassGain()</code> et <code>cutoffFrequency()</code>. "
                    "<code>100e-9</code> est l'écriture scientifique de Python : 100 × 10<sup>−9</sup> F, "
                    "soit 100 nF."
                    "<br><br><code>np.logspace(1, 5, 400)</code> rend 400 fréquences de "
                    "10<sup>1</sup> à 10<sup>5</sup> Hz, régulièrement espacées en exposant : "
                    "autant de fréquences entre 10 et 100 Hz qu'entre 10 et 100 kHz. Gardées dans "
                    "<code>self.frequencies</code>, elles resserviront à chaque recalcul. La "
                    "courbe est gardée dans <code>self.theoryCurve</code>."
                    "<br><br>Autour de 1 kHz, la courbe passe d'un palier, où G vaut presque 1, à "
                    "une descente : c'est son <b>coude</b>. À cette échelle, il reste invisible."
                ),
                run=self.plotTheory,
                codeSource=(lowPassGain, cutoffFrequency, self.plotTheory),
                references=[("numpy.logspace", numpyDocUrl("logspace"))],
            ),
            QStepWalkthrough.Step(
                title="Les deux axes en échelle logarithmique",
                explanation=(
                    "<code>setLogMode(x=True, y=True)</code> passe les deux axes en échelle "
                    "logarithmique. La notion 1.5 n'y passait que l'axe vertical. Chaque décade, "
                    "de 10 à 100 Hz, de 100 Hz à 1 kHz, prend maintenant la même largeur."
                    "<br><br>La zone visible ne se recadre qu'au prochain dessin de l'écran : "
                    "jusque-là, <code>viewRange()</code> (notion 1.7) rend encore l'ancienne "
                    "étendue, en hertz. Un slot qui la lirait se tromperait, comme le montrera "
                    "l'étape « La zone visible et ses arguments ». <code>autoRange()</code> "
                    "(notion 1.7) la recadre tout de suite. En 1.5, rien ne lisait l'étendue : "
                    "<code>setLogMode()</code> suffisait."
                    "<br><br>La courbe devient presque deux droites, reliées par le coude :"
                    "<ul>"
                    "<li>loin sous la coupure, f/fc est petit : G vaut presque 1, une droite "
                    "horizontale à 10<sup>0</sup> ;</li>"
                    "<li>loin au-dessus, 1 + (f/fc)² vaut presque (f/fc)² : G vaut presque fc/f. "
                    "Chaque décade de fréquence divise alors le gain par 10 ;</li>"
                    "<li>sur ces axes, c'est une droite qui descend d'une décade de gain par "
                    "décade de fréquence : une <b>pente</b> de −1.</li>"
                    "</ul>"
                    "C'est le cas d'une <b>loi de puissance</b> : G proportionnel à "
                    "f<sup>n</sup>, ici fc/f = fc·f<sup>−1</sup>, donc n = −1. Comme "
                    "log(f<sup>n</sup>) = n·log(f), toute loi de puissance devient une droite de "
                    "pente n. La notion 1.5 faisait de même avec une exponentielle, l'axe "
                    "vertical seul en échelle logarithmique."
                ),
                run=self.useLogLogScale,
                references=[("PlotItem.setLogMode", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.setLogMode"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : chaque axe à son tour",
                explanation=(
                    "Deux cases à cocher paraissent sous le graphique, cochées au départ : "
                    "<code>frequencyLogCheck</code>, « Fréquence en échelle logarithmique », et "
                    "<code>gainLogCheck</code>, « Gain en échelle logarithmique ». Chacune est "
                    "reliée au slot de son axe."
                    "<br><br><code>setLogMode()</code> ne reçoit ici qu'un des deux axes : l'autre "
                    "garde son échelle. <code>autoRange()</code> recadre ensuite, comme à l'étape "
                    "précédente. Les quatre combinaisons :"
                    "<ul>"
                    "<li>aucune : tout se tasse à gauche ;</li>"
                    "<li>la fréquence seule : le gain passe de 1 à 0 en forme de S autour de fc, "
                    "la présentation la plus courante d'un filtre ;</li>"
                    "<li>le gain seul : les petits gains des hautes fréquences se lisent, mais les "
                    "basses fréquences restent tassées à gauche ;</li>"
                    "<li>les deux : deux droites.</li>"
                    "</ul>"
                    "Essayer les quatre, puis revenir aux deux axes en échelle logarithmique."
                ),
                run=self._exploreScales,
                codeSource=(self.connectScaleControls, self.setFrequencyLog, self.setGainLog),
                references=[("PlotItem.setLogMode", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.setLogMode"))],
            ),
            QStepWalkthrough.Step(
                title="Le piège des exposants",
                explanation=(
                    "En échelle logarithmique, la zone visible ne compte plus en hertz, mais en "
                    "<b>exposants</b> de 10 : x = 3 désigne 10<sup>3</sup> = 1000 Hz. Tout ce que "
                    "la zone visible échange avec le code suit cette règle : la position d'une "
                    "ligne, une étendue."
                    "<br><br>PyQtGraph convertit lui-même les courbes (<code>PlotDataItem</code>), "
                    "qu'elles viennent de <code>plot()</code> ou de <code>addItem()</code> : leurs "
                    "données restent en hertz et en gains. Les autres éléments graphiques, une "
                    "ligne, un texte, et même un <code>ScatterPlotItem</code> construit à part, se "
                    "placent en exposants, et ne se convertissent pas quand l'échelle change. "
                    "<code>np.log10(valeur)</code> rend l'exposant de 10 d'une valeur : la ligne "
                    "de la coupure reçoit <code>np.log10(cutoff)</code>, environ 3,03. Avec "
                    "<code>pos=1061</code>, elle serait à 10<sup>1061</sup> Hz, hors de vue. "
                    "<code>movable=True</code> la rend déplaçable, pour l'étape « Déplacer la "
                    "coupure »."
                    "<br><br>Si l'on décochait ensuite « Fréquence », la ligne resterait à 3,03, "
                    "soit 3 Hz sur un axe linéaire, collée à l'axe vertical. Le code remet donc les "
                    "deux axes en échelle logarithmique, puis grise les deux cases :"
                    "<ul>"
                    "<li><code>setChecked(True)</code> coche une case comme un clic : elle émet "
                    "<code>toggled</code>, et son slot met l'axe en échelle logarithmique. Une "
                    "case déjà cochée n'émet rien ;</li>"
                    "<li><code>setEnabled(False)</code> la grise : la souris ne la change plus.</li>"
                    "</ul>"
                    "<code>label=\"fc\"</code> donne son étiquette à la ligne (notion 1.3)."
                ),
                run=self.addCutoffLine,
                references=[
                    ("numpy.log10", numpyDocUrl("log10")),
                    ("InfiniteLine", pyqtgraphDocUrl(_InfiniteLinePage, "InfiniteLine")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Les signaux déjà vus, en un tableau",
                explanation=(
                    "Les étapes suivantes font réagir le graphique. Avant elles, une synthèse des "
                    "signaux déjà reliés dans ce guide. Un signal se décrit par quatre "
                    "réponses : quel objet l'émet, quand, avec quels arguments, et si la souris "
                    "seule le provoque, ou aussi le code."
                    "<br><br><table border='1' cellspacing='0' cellpadding='3'>"
                    "<tr><th>Émetteur</th><th>Signal</th><th>Émis quand…</th><th>Arguments</th>"
                    "<th>Par le code ?</th><th>Vu en</th></tr>"
                    "<tr><td><code>QCheckBox</code></td><td><code>toggled</code></td><td>la "
                    "case change d'état</td><td>le nouvel état</td><td>oui, "
                    "<code>setChecked()</code></td><td>1.2</td></tr>"
                    "<tr><td><code>QSlider</code></td><td><code>valueChanged</code></td><td>la "
                    "valeur change</td><td>la nouvelle valeur</td><td>oui, "
                    "<code>setValue()</code></td><td>1.3</td></tr>"
                    "<tr><td><code>InfiniteLine</code></td><td><code>sigPositionChanged</code>"
                    "</td><td>la ligne bouge</td><td>la ligne</td><td>oui, "
                    "<code>setValue()</code></td><td>1.3</td></tr>"
                    "<tr><td><code>PlotDataItem</code></td><td><code>sigPointsClicked</code>"
                    "</td><td>un clic sur des points</td><td>la courbe, les points, "
                    "l'évènement</td><td>non</td><td>1.3</td></tr>"
                    "<tr><td><code>QTimer</code></td><td><code>timeout</code></td><td>l'intervalle "
                    "est écoulé</td><td>aucun</td><td>ni l'un ni l'autre : le temps</td>"
                    "<td>1.4</td></tr>"
                    "<tr><td><code>QPushButton</code></td><td><code>clicked</code></td><td>un "
                    "clic</td><td>un booléen, toujours faux pour un bouton simple</td><td>oui, "
                    "<code>click()</code>, rarement employé</td><td>1.4</td></tr>"
                    "<tr><td><code>QComboBox</code></td><td><code>currentIndexChanged</code></td>"
                    "<td>le choix change</td><td>le nouvel indice</td><td>oui, "
                    "<code>setCurrentIndex()</code></td><td>1.7</td></tr>"
                    "<tr><td><code>PlotItem</code></td><td><code>sigRangeChangedManually</code>"
                    "</td><td>la souris ou le bouton « A » change l'étendue</td><td>les axes "
                    "que la souris peut changer</td><td>non</td><td>1.7</td></tr>"
                    "</table>"
                    "<br>Les signaux de PyQtGraph commencent par <code>sig</code>, ceux de Qt non. "
                    "Un slot relié reçoit les premiers arguments du signal, autant qu'il en "
                    "déclare : <code>updateReadLabel()</code>, en 1.3, n'en déclarait aucun."
                    "<br><br>La colonne « Par le code ? » est la plus souvent oubliée. Un signal "
                    "émis aussi par le code se déclenche même quand l'utilisateur ne fait rien, "
                    "et peut relancer le slot qui vient de changer la valeur. Les étapes « Une "
                    "commande de plus » et « Couper l'écho » le montrent."
                ),
                run=self._signalsSoFar,
                codeSource=(),
                references=[("Signal (Qt for Python)", qtDocUrl("QtCore", "Signal"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : déplacer la coupure, et compter les appels",
                explanation=(
                    "Nouveau : la position d'une ligne se lit en exposant. "
                    "<code>value()</code> rend la position de la ligne, ici l'exposant de fc, et "
                    "<code>10 ** value()</code> la ramène en hertz."
                    "<br><br><code>connectCutoffLine()</code> relie "
                    "<code>sigPositionChanged</code> de la ligne au slot "
                    "<code>updateTheory()</code>. Celui-ci recalcule la courbe théorique par "
                    "<code>setData()</code> (notion 1.3), avec les fréquences en hertz, et récrit "
                    "l'étiquette de la ligne par <code>label.setFormat()</code> (notion 1.3). Le "
                    "guide appelle le slot une fois à l'arrivée sur l'étape, pour l'étiquette de "
                    "départ."
                    "<br><br>Pour voir les signaux partir, chaque slot de la suite commence par "
                    "<code>self.countCall(nom)</code>. Ce compteur d'appels est écrit pour cette "
                    "notion, en Python ordinaire :"
                    "<ul>"
                    "<li><code>self.callCounts</code> est un dictionnaire : le nom d'un slot, et "
                    "son nombre d'appels. <code>connectCutoffLine()</code> le crée vide ;</li>"
                    "<li><code>get(nom, 0)</code> rend le compte du slot, ou 0 s'il n'a jamais été "
                    "appelé ;</li>"
                    "<li>chaque compte s'écrit dans la lecture (notion 1.5), un slot par ligne : "
                    "<code>:&lt;18</code> aligne le nom à gauche sur 18 caractères, "
                    "<code>:&gt;6</code> le nombre à droite sur 6. <code>\"\\n\".join(lines)</code> "
                    "relie les lignes par des sauts de ligne.</li>"
                    "</ul>"
                    "Faire glisser la ligne pour que la théorie passe au mieux par les mesures : "
                    "le compte de <code>updateTheory</code> monte à chaque mouvement. La vraie "
                    "coupure est un peu au-dessous de 1061 Hz. Le condensateur fait un peu plus de "
                    "100 nF : sa valeur n'est garantie qu'à 5 % près."
                ),
                run=self._moveCutoff,
                codeSource=(self.connectCutoffLine, self.countCall, self.updateTheory),
                references=[("InfiniteLine.value", pyqtgraphDocUrl(_InfiniteLinePage, "InfiniteLine.value"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : la zone visible et ses arguments",
                explanation=(
                    "Nouveau : <code>sigRangeChanged</code> de la zone visible transmet trois "
                    "arguments :"
                    "<ul>"
                    "<li>la zone visible elle-même, utile à un slot relié à plusieurs graphiques ;"
                    "</li>"
                    "<li>les étendues, <code>[[gauche, droite], [bas, haut]]</code>, ici en "
                    "exposants ;</li>"
                    "<li>les axes changés, que le slot ne déclare pas, donc ne reçoit pas.</li>"
                    "</ul>"
                    "<code>@Slot(object, object)</code> déclare les deux premiers ; "
                    "<code>object</code> veut dire « n'importe quel objet Python », le type que "
                    "PyQtGraph donne à ses signaux. Le signal est pris sur la zone visible, par "
                    "<code>getViewBox()</code>. Le widget le relaie aussi, mais avec deux arguments "
                    "seulement : le widget lui-même, et les étendues."
                    "<br><br><code>showVisibleRange()</code> ramène les bornes en hertz, compte les "
                    "décades par une soustraction d'exposants, et l'écrit dans une étiquette. "
                    "<code>frequencyText()</code>, écrite au niveau du module, écrit une fréquence "
                    "en Hz, ou en kHz dès 1000 Hz."
                    "<br><br>Cette étiquette n'est pas ajoutée par <code>addItem()</code>, mais "
                    "accrochée à la zone visible par <code>setParentItem()</code>, comme la barre "
                    "d'échelle de la notion 1.7. Elle se place donc en pixels de la zone visible, "
                    "et non en exposants : <code>setPos(10, 200)</code> la met à 10 pixels du bord "
                    "gauche et à 200 du haut, sous le palier du gain, quel que soit le zoom."
                    "<br><br>Un signal de changement n'est émis que si quelque chose change. À "
                    "l'arrivée sur l'étape, rien n'a changé : le guide appelle le slot une fois, "
                    "avec ce que le signal aurait transmis, la zone visible et son étendue, rendue "
                    "par <code>viewRange()</code> (notion 1.7)."
                    "<br><br>Zoomer à la molette : l'étiquette suit, et le compte de "
                    "<code>showVisibleRange</code> monte."
                ),
                run=self._readVisibleRange,
                codeSource=(self.connectVisibleRange, frequencyText, self.showVisibleRange),
                references=[("ViewBox.sigRangeChanged", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : un bouton et son slot",
                explanation=(
                    "Un bouton paraît, <code>showAllButton</code>, « Tout voir ». Son slot "
                    "<code>showAllData()</code> appelle <code>autoRange()</code> (notion 1.7)."
                    "<br><br>Pourquoi ne pas relier <code>clicked</code> directement à "
                    "<code>autoRange()</code>, une méthode de PyQtGraph ? Parce que "
                    "<code>clicked</code> transmet un booléen. PySide6 le passe au premier "
                    "paramètre de la méthode reliée, si elle en déclare un. "
                    "<code>autoRange(padding=None)</code> de la zone visible recevrait "
                    "<code>False</code> comme marge. Dans un calcul, Python compte <code>False</code> "
                    "comme 0 : une marge nulle. Selon la façon dont une méthode de PyQtGraph est "
                    "écrite, elle reçoit ou non ce booléen, et rien ne le dit à l'œil. Un slot "
                    "<code>@Slot()</code> sans paramètre lève le doute : il ignore le booléen."
                    "<br><br>Zoomer, puis cliquer « Tout voir ». La lecture compte "
                    "<code>showAllData</code> une fois par clic, et <code>showVisibleRange</code> "
                    "une fois de plus : le cadrage a changé l'étendue."
                ),
                run=self._exploreShowAll,
                codeSource=(self.connectShowAllButton, self.showAllData),
                references=[("ViewBox.autoRange", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.autoRange"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : une bande, en direct",
                explanation=(
                    "Nouveau : <code>pg.LinearRegionItem</code> est une <b>bande</b> "
                    "déplaçable entre deux bornes, données ici en exposants : de 5 à 100 kHz. On "
                    "la fait glisser par le milieu, ou on tire un de ses bords. "
                    "<code>getRegion()</code> rend ses deux bornes, en exposants elles aussi. Son "
                    "signal <code>sigRegionChanged</code> est émis <b>en direct</b>, à chaque "
                    "mouvement : il convient à un effet léger. <code>highlightBand()</code> colore "
                    "en jaune les mesures de la bande. <code>addBand()</code> l'appelle aussi une "
                    "fois, pour les couleurs de départ."
                    "<br><br><code>measurementsInBand()</code> compare les exposants des "
                    "fréquences aux deux bornes, avec numpy :"
                    "<ul>"
                    "<li><code>exponents &gt;= low</code> compare chaque élément et rend un "
                    "tableau de booléens, un par mesure ;</li>"
                    "<li><code>&amp;</code> combine deux tableaux de booléens, élément par élément : "
                    "<code>and</code> ne s'applique qu'à deux valeurs seules. Les parenthèses sont "
                    "nécessaires, car <code>&amp;</code> passe avant <code>&gt;=</code> ;</li>"
                    "<li><code>np.where(inside, \"y\", \"r\")</code> rend un tableau de lettres : "
                    "<code>\"y\"</code> où <code>inside</code> vaut <code>True</code>, "
                    "<code>\"r\"</code> ailleurs. Comme pour un stylo (notion 1.1), une lettre "
                    "suffit pour un pinceau.</li>"
                    "</ul>"
                    "Le nuage d'une courbe est son attribut <code>scatter</code>, un "
                    "<code>ScatterPlotItem</code> : son <code>setBrush(liste)</code> donne un "
                    "pinceau par point (notion 1.2)."
                    "<br><br>Faire glisser la bande : le compte de <code>highlightBand</code> "
                    "monte à chaque mouvement."
                ),
                run=self.addBand,
                codeSource=(self.addBand, self.measurementsInBand, self.highlightBand),
                references=[
                    ("LinearRegionItem", pyqtgraphDocUrl(_RegionPage, "LinearRegionItem")),
                    ("numpy.where", numpyDocUrl("where")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : la bande, au relâchement",
                explanation=(
                    "Nouveau : <code>sigRegionChangeFinished</code> n'est émis qu'<b>à la fin</b> "
                    "du geste, quand la souris lâche la bande. Il convient à un résultat qui n'a "
                    "de sens qu'une fois la bande choisie : <code>fitBandSlope()</code> mesure la "
                    "pente des mesures de la bande, et l'écrit en bas de la bande. "
                    "<code>connectBandRelease()</code> l'appelle aussi une fois, pour la pente de "
                    "départ. Le code, lui, émet ce signal à chaque <code>setRegion(bornes)</code>, "
                    "le mutateur de <code>getRegion()</code>, geste ou pas."
                    "<br><br>Trois outils de numpy :"
                    "<ul>"
                    "<li><code>np.count_nonzero(inside)</code> compte les <code>True</code> : le "
                    "nombre de mesures dans la bande. Il en faut deux pour une droite ;</li>"
                    "<li><code>tableau[inside]</code> ne garde que les éléments où "
                    "<code>inside</code> vaut <code>True</code> ;</li>"
                    "<li><code>np.polyfit(x, y, 1)</code> rend la pente et l'ordonnée à l'origine "
                    "de la droite qui passe au plus près des points (x, y). Ici, x et y sont les "
                    "exposants : la pente est celle du graphique.</li>"
                    "</ul>"
                    "L'étiquette de la pente est ajoutée par <code>addItem()</code> : elle se place "
                    "en exposants, à la borne gauche de la bande, à x = <code>low</code>, et au "
                    "gain 0,01, à y = −2."
                    "<br><br>Faire glisser la bande, puis la lâcher : <code>highlightBand</code> "
                    "compte chaque mouvement, <code>fitBandSlope</code> un seul appel par geste. "
                    "Vers les hautes fréquences, la pente vaut environ −1 ; vers les basses, "
                    "environ 0."
                ),
                run=self.connectBandRelease,
                codeSource=(self.connectBandRelease, self.fitBandSlope),
                references=[
                    ("LinearRegionItem", pyqtgraphDocUrl(_RegionPage, "LinearRegionItem")),
                    ("numpy.polyfit", numpyDocUrl("polyfit")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : une commande de plus",
                explanation=(
                    "Un sélecteur numérique (<code>QSlider</code>) paraît : "
                    "<code>resistanceSlider</code>, « Résistance R ». Il va de 0,5 à 10 kΩ, par pas "
                    "de 0,5 kΩ, et part de 1,5 kΩ. Le panneau affiche sa valeur en kΩ, mais sa "
                    "valeur lue compte des demi-kΩ : <code>value() * 500</code> la donne en ohms. "
                    "Le slot <code>setResistance()</code> place la ligne de la coupure par "
                    "<code>setValue()</code>, en exposant, en gardant C = 100 nF."
                    "<br><br>Nouveau : rien d'autre n'est relié, et pourtant la théorie et "
                    "l'étiquette de la ligne suivent. <code>setValue()</code> émet "
                    "<code>sigPositionChanged</code>, comme la souris : <code>updateTheory()</code> "
                    "s'exécute. La lecture le montre : à chaque pas du sélecteur, "
                    "<code>setResistance</code> et <code>updateTheory</code> montent ensemble."
                    "<br><br>Déplacer le sélecteur."
                ),
                run=self._exploreResistance,
                codeSource=(self.connectResistanceSlider, self.setResistance),
                references=[("InfiniteLine.setValue", pyqtgraphDocUrl(_InfiniteLinePage, "InfiniteLine.setValue"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : couper l'écho",
                explanation=(
                    "Le sens inverse : la ligne déplacée à la souris règle le sélecteur. "
                    "<code>matchResistance()</code> résout fc = 1/(2πRC) pour R, "
                    "R = 1/(2π·fc·C), puis arrondit au demi-kΩ. Hors de 0,5 à 10 kΩ, le "
                    "sélecteur s'arrête à sa borne."
                    "<br><br><b>Ne réagir qu'à la souris.</b> Relié à "
                    "<code>sigPositionChanged</code>, ce slot s'exécuterait aussi quand le "
                    "sélecteur déplace la ligne : il recalculerait pour rien la valeur que le "
                    "sélecteur vient de donner. Nouveau : <code>sigDragged</code> est émis "
                    "seulement quand la souris fait glisser la ligne. Le code ne l'émet jamais."
                    "<br><br><b>L'écho.</b> Chaque fois que la valeur arrondie change, "
                    "<code>setValue()</code> du sélecteur émet <code>valueChanged</code>. "
                    "<code>setResistance()</code> replace alors la ligne à la résistance arrondie, "
                    "loin de la souris. La ligne hoquette : elle saute en arrière, puis repart avec "
                    "la souris. La liste déroulante <code>echoCombo</code>, « Contre l'écho », "
                    "choisit une des trois branches :"
                    "<ul>"
                    "<li>« rien » : l'écho reste ;</li>"
                    "<li>« déconnexion ciblée », le choix de départ : "
                    "<code>disconnect(slot)</code> retire la seule connexion de "
                    "<code>setResistance()</code>, puis <code>connect(slot)</code> la rétablit. "
                    "Les autres slots de <code>valueChanged</code> s'exécutent toujours, comme "
                    "le texte de la valeur, à droite du sélecteur ;</li>"
                    "<li>« QSignalBlocker » : <code>QSignalBlocker(objet)</code>, de "
                    "<code>PySide6.QtCore</code>, fait taire tous les signaux de l'objet. "
                    "<code>with QSignalBlocker(…):</code> ouvre un bloc : le silence commence à "
                    "l'entrée, et finit à la sortie, après les lignes indentées. Aucun slot ne "
                    "reçoit les signaux entre les deux, pas même le texte de la valeur : il ne "
                    "suit plus.</li>"
                    "</ul>"
                    "Ces trois choix portent les valeurs <code>\"none\"</code>, "
                    "<code>\"disconnect\"</code> et <code>\"blocker\"</code>, que "
                    "<code>currentData()</code> rend."
                    "Faire glisser lentement la ligne sur une décade, avec chacun des trois choix. "
                    "Avec « rien », elle hoquette, et <code>setResistance</code> monte à chaque "
                    "saut. Avec les deux autres, elle glisse, et <code>setResistance</code> ne "
                    "bouge plus. Avec « QSignalBlocker », le texte de la valeur ne suit plus."
                ),
                run=self._exploreEcho,
                codeSource=(self.connectDraggedLine, self.matchResistance),
                references=[
                    ("InfiniteLine.sigDragged", pyqtgraphDocUrl(_InfiniteLinePage, "InfiniteLine")),
                    ("QSignalBlocker", qtDocUrl("QtCore", "QSignalBlocker")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Pour aller plus loin : les signaux de PyQtGraph",
                explanation=(
                    "Un inventaire des signaux de PyQtGraph les plus utiles, par classe. Le "
                    "graphique et son widget relaient <code>sigRangeChanged</code>, "
                    "<code>sigXRangeChanged</code>, <code>sigYRangeChanged</code> et "
                    "<code>sigRangeChangedManually</code>. Relayé, <code>sigRangeChanged</code> ne "
                    "transmet que deux arguments. "
                    "<code>GraphicsScene</code> est la scène, que la notion 2.4 présentera. "
                    "<code>QGraphicsObject</code> est la classe de Qt dont héritent tous les "
                    "éléments graphiques : un <code>QGraphicsItem</code> qui émet des signaux."
                    "<br><br>" + _InventoryHtml +
                    "<br>Trois stratégies, vues dans les notions 1.7 et 1.8, et une quatrième à "
                    "connaître :"
                    "<ul>"
                    "<li><b>qui a changé ?</b> Un signal de la souris seule "
                    "(<code>sigRangeChangedManually</code>, <code>sigDragged</code>) ignore les "
                    "changements faits par le code ;</li>"
                    "<li><b>en direct ou à la fin ?</b> Les signaux en <code>…Finished</code> "
                    "attendent la fin d'un geste de la souris. Certains sont aussi émis par le "
                    "code, comme celui de la bande : la colonne « Par le code ? » le dit ;</li>"
                    "<li><b>couper l'écho</b>, par une déconnexion ciblée, ou par "
                    "<code>QSignalBlocker</code>, qui fait taire tous les slots ;</li>"
                    "<li><b>limiter la cadence</b>, non montrée ici : "
                    "<code>pg.SignalProxy(signal, rateLimit=…, slot=…)</code> relaie un signal au "
                    "plus <code>rateLimit</code> fois par seconde. Utile pour la souris, qui émet "
                    "à chaque pixel.</li>"
                    "</ul>"
                ),
                run=self._inventoryOnly,
                codeSource=(),
                references=[
                    ("ViewBox", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox")),
                    ("LinearRegionItem", pyqtgraphDocUrl(_RegionPage, "LinearRegionItem")),
                ],
            ),
        ]
