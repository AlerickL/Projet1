"""Notion 4.1 : un tableau de bord, la synthèse du guide.

Contexte : une plaque de 40 cm × 30 cm est chauffée par deux éléments. Le
premier chauffe sans varier ; le second suit un cycle de 8 s. Un capteur,
posé entre les deux, mesure la température 20 fois par seconde. Le tableau
de bord réunit, dans une seule grille de graphiques, la carte de la plaque
et l'historique du capteur, avec un seuil d'alerte, la moyenne et l'écart
type des dix dernières secondes.

Aucun geste nouveau (D-039) : la grille de graphiques (1.5), la carte de
chaleur et sa barre de couleurs (2.4, 2.5), un nuage d'un point (1.2), le
tampon et le minuteur (1.4), la ligne déplaçable (1.3), la moyenne et
l'écart type (1.6). Chaque étape renvoie à sa notion d'origine.

Chaque étape est une méthode de `QTopicDashboardTab`. La pause quand la
page est cachée est de la plomberie (`pauseWhileHidden`), dite en mots.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QRectF, Qt, QTimer, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from ..common.q_timer_pause import pauseWhileHidden
from .plot_reset import removeLayoutItems, resetPlotItem

_ImageItemPage = "api_reference/graphicsItems/imageitem"


def plateTemperature(x: float | np.ndarray, y: float | np.ndarray, t: float | np.ndarray) -> float | np.ndarray:
    """La température en (x, y), en °C, à l'instant t, en secondes.

    20 °C partout, plus une bosse en cloche par élément chauffant : celui
    de gauche, en (10, 15), ajoute 40 °C en son centre ; celui de droite,
    en (30, 15), ajoute entre 5 et 55 °C, sur un cycle de 8 s. `x`, `y` et
    `t` sont des réels, ou des tableaux de même forme ; le résultat a cette
    forme.
    """
    left = 40 * np.exp(-((x - 10) ** 2 + (y - 15) ** 2) / 98)
    right = (30 + 25 * np.sin(2 * np.pi * t / 8)) * np.exp(-((x - 30) ** 2 + (y - 15) ** 2) / 98)
    return 20 + left + right


def temperatureGrid(t: float) -> np.ndarray:
    """La température de la plaque à l'instant t, sur une grille de 81 × 61 points, un tous les 0,5 cm.

    Rend un tableau de réels de forme (81, 61) : grid[i, j] vaut la
    température en (xs[i], ys[j]).
    """
    xs = np.linspace(0, 40, 81)
    ys = np.linspace(0, 30, 61)
    gridX, gridY = np.meshgrid(xs, ys, indexing="ij")
    return plateTemperature(gridX, gridY, t)


class QTopicDashboardTab(QWidget):
    """Onglet de la notion 4.1 : un tableau de bord qui surveille une plaque chauffée.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        layoutWidget, mapPlot, sensorPlot: La grille de graphiques et ses
            deux graphiques, créés une seule fois.
        readout: La lecture sous la grille (outil présenté en 1.5).
        timer: Le minuteur, créé une seule fois, arrêté avant chaque rejeu.
        controls: Les contrôles des étapes « À vous » (plomberie).
        pauseButton: Le bouton de pause et de reprise.
        time: L'instant présent du tableau de bord, en secondes.
        image: L'image de la plaque, ou None.
        rng: Le générateur du bruit du capteur, ou None.
        sensorPoint: Le point du capteur sur la carte, ou None.
        times, temperatures: Le tampon des mesures, ou None.
        curve: La courbe des mesures, ou None.
        threshold: Le seuil d'alerte, en °C.
        thresholdLine: La ligne du seuil, ou None.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Un tableau de bord"
    TabToolTip = "Une carte, un capteur en temps réel, un seuil et des statistiques, dans une seule grille"
    RecommendedPanelWidth = 640
    Objective = (
        "Réunir dans un tableau de bord les gestes du guide : la carte d'une plaque chauffée, "
        "la température d'un capteur en temps réel, un seuil d'alerte, la moyenne et l'écart "
        "type des dernières secondes, le tout mis à jour par un seul minuteur."
    )
    KeyConcepts = [
        "Un tableau de bord est une grille de graphiques : chaque graphique répond à une "
        "question, et tous montrent le même instant.",
        "La carte montre la plaque entière à un instant ; la courbe montre un seul point au fil "
        "du temps. Les deux se complètent.",
        "Un seuil d'alerte se compare à la dernière mesure ; une couleur le signale d'un coup "
        "d'œil.",
        "La moyenne et l'écart type résument la fenêtre glissante : ils changent avec elle.",
        "Un seul minuteur fait tout avancer : une mesure, la carte, l'alerte et les statistiques, "
        "à chaque signal.",
    ]
    KeyApis = [
        "GraphicsLayoutWidget.addPlot", "ImageItem.setImage", "ColorBarItem", "ScatterPlotItem.setBrush",
        "InfiniteLine", "InfiniteLine.sigPositionChanged", "numpy.mean", "numpy.std", "QTimer",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.time = 0.0
        self.image: pg.ImageItem | None = None
        self.rng: np.random.Generator | None = None
        self.sensorPoint: pg.ScatterPlotItem | None = None
        self.times: np.ndarray | None = None
        self.temperatures: np.ndarray | None = None
        self.curve: pg.PlotDataItem | None = None
        self.threshold = 0.0
        self.thresholdLine: pg.InfiniteLine | None = None

        self.createLayout()
        self.readout = QReadoutLabel()
        self.createTimer()
        pauseWhileHidden(self, self.timer)
        self.controls = QControlPanel()
        self.pauseButton = self.controls.addButton("Pause")

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
        """Arrête le minuteur, vide les graphiques et la lecture, et remet les contrôles à zéro."""
        self.timer.stop()
        self.controls.resetControls()
        self.pauseButton.setText("Pause")
        self.readout.clear()
        removeLayoutItems(self.layoutWidget, keep=(self.mapPlot, self.sensorPlot))
        resetPlotItem(self.mapPlot)
        resetPlotItem(self.sensorPlot)
        self.time = 0.0
        self.image = None
        self.rng = None
        self.sensorPoint = None
        self.times = None
        self.temperatures = None
        self.curve = None
        self.threshold = 0.0
        self.thresholdLine = None

    # -- Étapes ------------------------------------------------------------------------------------

    def createLayout(self) -> None:
        """Crée la grille : la carte en haut à gauche, l'historique du capteur en bas, sur deux colonnes."""
        self.layoutWidget = pg.GraphicsLayoutWidget()
        self.mapPlot = self.layoutWidget.addPlot(row=0, col=0)
        self.sensorPlot = self.layoutWidget.addPlot(row=1, col=0, colspan=2)

    def setUpPlots(self) -> None:
        """Titres, axes et grille des deux graphiques ; échelle égale pour la carte, axe vertical fixe pour le capteur."""
        self.mapPlot.setTitle("Température de la plaque")
        self.mapPlot.setLabel("bottom", "x", units="cm")
        self.mapPlot.setLabel("left", "y", units="cm")
        self.mapPlot.setAspectLocked(True)
        self.sensorPlot.setTitle("Capteur : les 10 dernières secondes")
        self.sensorPlot.setLabel("bottom", "Temps", units="s")
        self.sensorPlot.setLabel("left", "Température", units="°C")
        self.sensorPlot.showGrid(x=True, y=True, alpha=0.3)
        self.sensorPlot.setYRange(25, 60, padding=0)

    def showMap(self) -> None:
        """L'instant présent, t = 10 s, et la température de la plaque à cet instant, en image."""
        self.time = 10.0
        self.image = pg.ImageItem(temperatureGrid(self.time))
        step = 0.5
        self.image.setRect(QRectF(-step / 2, -step / 2, 40 + step, 30 + step))
        self.mapPlot.addItem(self.image)

    def addColorBar(self) -> None:
        """La palette « plasma », de 20 à 80 °C, et sa barre de couleurs dans la deuxième colonne."""
        colorMap = pg.colormap.get("plasma")
        self.image.setColorMap(colorMap)
        self.image.setLevels((20, 80))
        colorBar = pg.ColorBarItem(values=(20, 80), colorMap=colorMap, label="Température (°C)")
        colorBar.setImageItem(self.image)
        self.layoutWidget.addItem(colorBar, row=0, col=1)

    def addSensor(self) -> None:
        """Le capteur en (22, 12) : un point vert sur la carte, son nom, et le générateur de son bruit."""
        self.sensorPoint = pg.ScatterPlotItem([22], [12], size=14, brush=pg.mkBrush("g"), pen=pg.mkPen("w"))
        self.mapPlot.addItem(self.sensorPoint)
        label = pg.TextItem("capteur", color="w", anchor=(0.5, 1.4))
        label.setPos(22, 12)
        self.mapPlot.addItem(label)
        self.rng = np.random.default_rng(3)

    def readSensor(self, t: float | np.ndarray) -> float | np.ndarray:
        """La température lue par le capteur à l'instant t : celle de la plaque en (22, 12), plus un bruit.

        `t` est un instant en secondes, ou un tableau d'instants de forme
        (n,) ; le résultat est un réel, ou un tableau de réels de même forme.
        """
        return plateTemperature(22, 12, t) + self.rng.normal(0, 0.3, np.shape(t))

    def createHistory(self) -> None:
        """Le tampon : 200 mesures, une tous les 0,05 s, jusqu'à l'instant présent ; puis leur courbe."""
        self.times = (np.arange(200) + 1) / 20
        self.temperatures = self.readSensor(self.times)
        self.curve = self.sensorPlot.plot(self.times, self.temperatures, pen=pg.mkPen("y", width=2))

    def addThreshold(self) -> None:
        """Le seuil, 45 °C ; sa ligne, horizontale et déplaçable ; puis la couleur du capteur selon le seuil."""
        self.threshold = 45.0
        self.thresholdLine = pg.InfiniteLine(pos=self.threshold, angle=0, movable=True,
                                             pen=pg.mkPen("r", width=2, style=Qt.PenStyle.DashLine),
                                             label="Seuil : {value:.0f} °C")
        self.sensorPlot.addItem(self.thresholdLine)
        self.updateAlarm()

    def updateAlarm(self) -> None:
        """Le point du capteur devient rouge si la dernière mesure dépasse le seuil, vert sinon."""
        if self.temperatures[-1] > self.threshold:
            self.sensorPoint.setBrush(pg.mkBrush("r"))
        else:
            self.sensorPoint.setBrush(pg.mkBrush("g"))

    def showStatistics(self) -> None:
        """Écrit dans la lecture la dernière mesure, la moyenne et l'écart type des 10 dernières secondes."""
        mean = np.mean(self.temperatures)
        sigma = np.std(self.temperatures, ddof=1)
        text = (f"t = {self.time:.1f} s ; mesure : {self.temperatures[-1]:.1f} °C ; "
                f"sur 10 s : moyenne {mean:.1f} °C, écart type {sigma:.1f} °C")
        self.readout.setText(text.replace(".", ","))

    def pushSample(self, t: float) -> None:
        """Décale le tampon d'une case, puis écrit dans la dernière la mesure de l'instant t."""
        self.times[:-1] = self.times[1:]
        self.temperatures[:-1] = self.temperatures[1:]
        self.times[-1] = t
        self.temperatures[-1] = self.readSensor(t)
        self.curve.setData(self.times, self.temperatures)

    def createTimer(self) -> None:
        """Crée le minuteur, et relie son signal timeout au slot qui fait avancer le tableau de bord."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advanceTime)

    @Slot()
    def advanceTime(self) -> None:
        """Avance de 0,05 s : une mesure de plus, la carte de cet instant, l'alerte et les statistiques."""
        self.time += 0.05
        self.pushSample(self.time)
        self.image.setImage(temperatureGrid(self.time), levels=(20, 80))
        self.updateAlarm()
        self.showStatistics()

    def startDashboard(self) -> None:
        """Démarre le minuteur : un signal toutes les 50 ms, soit 20 mesures par seconde."""
        self.timer.start(50)

    def connectPauseButton(self) -> None:
        """Relie le bouton au slot qui met en pause ou relance."""
        self.pauseButton.clicked.connect(self.togglePause)

    @Slot()
    def togglePause(self) -> None:
        """Arrête ou relance le minuteur, et change le texte du bouton."""
        if self.timer.isActive():
            self.timer.stop()
            self.pauseButton.setText("Reprendre")
        else:
            self.timer.start(50)
            self.pauseButton.setText("Pause")

    def connectThresholdLine(self) -> None:
        """Relie le déplacement de la ligne du seuil au slot qui change le seuil."""
        self.thresholdLine.sigPositionChanged.connect(self.setThreshold)

    @Slot()
    def setThreshold(self) -> None:
        """Le seuil prend la position de la ligne, et l'alerte est revue aussitôt."""
        self.threshold = self.thresholdLine.value()
        self.updateAlarm()

    def _exploreThreshold(self) -> None:
        """Connecte la ligne du seuil."""
        self.connectThresholdLine()

    def _explorePause(self) -> None:
        """Connecte le bouton, puis le révèle."""
        self.connectPauseButton()
        self.controls.reveal()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="La grille du tableau de bord",
                explanation=(
                    "Cette notion n'apporte aucun geste nouveau : elle réunit ceux du guide dans "
                    "un seul tableau de bord. Chaque étape dit d'où vient chacun. Elle repart "
                    "de zéro : pas d'étape de récapitulatif."
                    "<br><br>Une plaque de 40 cm × 30 cm est chauffée par deux éléments. Celui de "
                    "gauche chauffe sans varier ; celui de droite suit un cycle de 8 s. Un "
                    "capteur, posé entre les deux, mesure la température. Le tableau de bord "
                    "répond à deux questions : où la plaque est-elle chaude, et que mesure le "
                    "capteur ?"
                    "<br><br>Une grille de graphiques (notion 1.5) : "
                    "<code>addPlot(row=0, col=0)</code> crée la carte en haut à gauche. "
                    "<code>colspan=2</code> étend le graphique du capteur, en bas, sur deux "
                    "colonnes, comme <code>rowspan</code> l'étendait sur deux rangées. En haut, "
                    "la cellule de droite reste libre : elle recevra la barre de couleurs. La "
                    "grille de graphiques est créée avec la page ; <code>setUpPlots()</code> "
                    "donne aux graphiques titres, axes et lignes de repère. "
                    "L'échelle égale garde ses proportions à la plaque (notion 1.7), et l'axe "
                    "vertical du capteur reste fixe, de 25 à 60 °C (notion 1.4)."
                ),
                run=self.setUpPlots,
                codeSource=(self.createLayout, self.setUpPlots),
                references=[
                    ("GraphicsLayout.addPlot", pyqtgraphDocUrl("api_reference/graphicsItems/graphicslayout",
                                                               "GraphicsLayout.addPlot")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La plaque, en image",
                explanation=(
                    "<code>plateTemperature(x, y, t)</code> rend la température en un point, à un "
                    "instant : 20 °C, plus une bosse en cloche par élément chauffant. "
                    "<code>np.exp(-d² / 98)</code> vaut 1 au centre de l'élément et diminue avec "
                    "la distance d ; 98, en cm², règle la largeur de la bosse. À d = √98, "
                    "environ 10 cm, la bosse est tombée à 37 % de sa hauteur ; à 20 cm, à 2 %. "
                    "L'élément de droite chauffe plus ou moins selon "
                    "<code>np.sin()</code>, sur un cycle de 8 s."
                    "<br><br><code>temperatureGrid(t)</code> la calcule d'un coup sur une grille de points "
                    "de 81 × 61 points, un tous les 0,5 cm, avec <code>np.meshgrid</code>, comme "
                    "le potentiel de la notion 2.4. <code>showMap()</code> fixe l'instant "
                    "présent du tableau de bord, t = 10 s, et montre la plaque à cet instant : "
                    "une <code>ImageItem</code> placée par <code>setRect()</code>, une case par "
                    "pixel (notion 2.4)."
                    "<br><br>À gauche, deux taches claires : les deux éléments. Sans palette, "
                    "l'image est en niveaux de gris."
                ),
                run=self.showMap,
                codeSource=(plateTemperature, temperatureGrid, self.showMap),
                references=[
                    ("numpy.exp", numpyDocUrl("exp")),
                    ("ImageItem", pyqtgraphDocUrl(_ImageItemPage, "ImageItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La palette et la barre de couleurs",
                explanation=(
                    "La palette « plasma » (notion 2.5) va du violet sombre au jaune : plus c'est "
                    "clair, plus c'est chaud. <code>setLevels((20, 80))</code> fixe ses bouts à "
                    "20 et 80 °C : une couleur garde le même sens à tout instant. La barre de "
                    "couleurs (notion 2.4) prend la deuxième colonne du haut, que "
                    "<code>colspan</code> avait laissée libre en bas."
                    "<br><br>À gauche, à cet instant, l'élément de droite est au sommet de son cycle : "
                    "sa tache est la plus claire, près de 76 °C en son centre."
                ),
                run=self.addColorBar,
                references=[
                    ("ImageItem.setLevels", pyqtgraphDocUrl(_ImageItemPage, "ImageItem.setLevels")),
                    ("ColorBarItem", pyqtgraphDocUrl("api_reference/graphicsItems/colorbaritem", "ColorBarItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le capteur, sur la carte",
                explanation=(
                    "Le capteur est en (22, 12), entre les deux éléments. Sur la carte, un nuage "
                    "d'un seul point (<code>ScatterPlotItem</code>, notion 1.2), vert, et son nom "
                    "(<code>TextItem</code>, notion 2.4)."
                    "<br><br>Il est simulé comme le pendule de la notion 1.4 : "
                    "<code>readSensor(t)</code> rend la température de la plaque en (22, 12), "
                    "plus un bruit d'environ ±0,3 °C, tiré par un générateur à graine fixe. Pour "
                    "un tableau d'instants, elle rend une mesure par instant."
                ),
                run=self.addSensor,
                codeSource=(self.addSensor, self.readSensor),
                references=[
                    ("ScatterPlotItem", pyqtgraphDocUrl("api_reference/graphicsItems/scatterplotitem",
                                                        "ScatterPlotItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Dix secondes d'historique",
                explanation=(
                    "Le tampon de la notion 1.4 : 200 cases, une mesure tous les 0,05 s, soit "
                    "10 s. Ici, il se remplit d'un seul coup. "
                    "<code>(np.arange(200) + 1) / 20</code> rend les instants 0,05 ; 0,1 ; … ; "
                    "10 s, et <code>readSensor()</code> les mesure tous d'un appel. La dernière "
                    "mesure est celle de l'instant présent."
                    "<br><br>À gauche, la courbe du capteur monte et descend avec le cycle de "
                    "l'élément de droite : la carte montre la plaque entière à un instant, la "
                    "courbe un seul point au fil du temps."
                ),
                run=self.createHistory,
                references=[("numpy.arange", numpyDocUrl("arange"))],
            ),
            QStepWalkthrough.Step(
                title="Le seuil d'alerte",
                explanation=(
                    "<code>self.threshold</code> fixe le seuil d'alerte à 45 °C. Une ligne "
                    "horizontale le montre : une "
                    "<code>InfiniteLine</code> (notion 1.3), avec <code>angle=0</code> au lieu de "
                    "90. Son étiquette affiche sa position. <code>movable=True</code> la rend "
                    "déjà déplaçable, mais rien ne réagit encore : l'étape « À vous » s'en "
                    "chargera."
                    "<br><br><code>updateAlarm()</code> compare la dernière mesure, "
                    "<code>self.temperatures[-1]</code>, au seuil, et colore le point du capteur "
                    "par <code>setBrush()</code> (notion 1.2) : rouge au-dessus, vert sinon. Une "
                    "couleur se lit d'un coup d'œil, sans lire de nombre."
                    "<br><br>À gauche, à t = 10 s, la mesure dépasse le seuil : le point devient "
                    "rouge."
                ),
                run=self.addThreshold,
                codeSource=(self.addThreshold, self.updateAlarm),
                references=[
                    ("InfiniteLine", pyqtgraphDocUrl("api_reference/graphicsItems/infiniteline", "InfiniteLine")),
                    ("ScatterPlotItem.setBrush", pyqtgraphDocUrl("api_reference/graphicsItems/scatterplotitem",
                                                                 "ScatterPlotItem.setBrush")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La moyenne et l'écart type de la fenêtre",
                explanation=(
                    "La lecture sous la grille de graphiques (présentée en notion 1.5) résume la fenêtre : la "
                    "dernière mesure, puis la moyenne et l'écart type des 200 mesures du tampon "
                    "(notion 1.6). Le texte s'écrit en deux f-strings, l'une sous l'autre, entre "
                    "parenthèses : Python colle deux chaînes voisines en une seule. "
                    "<code>np.mean()</code> rend la moyenne, et "
                    "<code>np.std(…, ddof=1)</code> l'écart type. Le tampon couvre un cycle "
                    "complet et un quart : l'écart type mesure ici surtout le cycle de l'élément, "
                    "bien plus que le bruit du capteur."
                    "<br><br>Les nombres prennent la virgule décimale par "
                    "<code>replace(\".\", \",\")</code>, comme en notion 1.3."
                ),
                run=self.showStatistics,
                references=[
                    ("numpy.mean", numpyDocUrl("mean")),
                    ("numpy.std", numpyDocUrl("std")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Tout s'anime : un seul minuteur",
                explanation=(
                    "Un minuteur (<code>QTimer</code>, notion 1.4) est créé une seule fois, avec "
                    "la page, et son signal <code>timeout</code> est relié au slot "
                    "<code>advanceTime()</code>. À chaque signal, celui-ci avance l'instant présent "
                    "de 0,05 s, puis met tout le tableau de bord à jour : une mesure de plus par "
                    "<code>pushSample(t)</code>, la fenêtre glissante de la notion 1.4, qui "
                    "reçoit ici l'instant en paramètre au lieu de le compter elle-même ; la carte "
                    "de cet instant par <code>setImage()</code> (notion 2.5), qui garde les bouts "
                    "de la palette avec <code>levels</code> ; l'alerte ; les statistiques."
                    "<br><br><code>createTimer()</code> est affichée pour être lue : elle s'est "
                    "exécutée une seule fois, à la création de la page. À cette étape s'exécute "
                    "<code>startDashboard()</code> : <code>start(50)</code>, un signal toutes "
                    "les 50 ms, soit 20 mesures par seconde."
                    "<br><br>À gauche, tout bouge ensemble : la tache de droite pâlit puis "
                    "s'éclaire, la courbe défile, et le point du capteur rougit quand la mesure "
                    "dépasse 45 °C. Les quatre éléments montrent toujours le même instant, celui "
                    "qu'écrit la lecture."
                    "<br><br>Quand on quitte la page de cette notion, le guide arrête le "
                    "minuteur, et le relance au retour."
                ),
                run=self.startDashboard,
                codeSource=(self.createTimer, self.advanceTime, self.pushSample, self.startDashboard),
                references=[
                    ("QTimer", qtDocUrl("QtCore", "QTimer")),
                    ("ImageItem.setImage", pyqtgraphDocUrl(_ImageItemPage, "ImageItem.setImage")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : déplacer le seuil",
                explanation=(
                    "<code>connectThresholdLine()</code> relie le signal "
                    "<code>sigPositionChanged</code> de la ligne du seuil (notion 1.3) au slot "
                    "<code>setThreshold()</code>. Celui-ci lit la position de la ligne par "
                    "<code>value()</code>, en fait le nouveau seuil, et revoit aussitôt "
                    "l'alerte."
                    "<br><br>Faire glisser la ligne rouge à la souris, vers 35 °C : le point du "
                    "capteur rougit presque tout le temps. Vers 55 °C, il ne rougit plus jamais. "
                    "Chercher le seuil qui ne déclenche l'alerte qu'au sommet du cycle."
                ),
                run=self._exploreThreshold,
                codeSource=(self.connectThresholdLine, self.setThreshold),
                references=[("InfiniteLine.sigPositionChanged",
                             pyqtgraphDocUrl("api_reference/graphicsItems/infiniteline",
                                             "InfiniteLine"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : pause et reprise",
                explanation=(
                    "Un bouton paraît sous la lecture : <code>pauseButton</code>, « Pause », comme "
                    "en notion 1.4. <code>connectPauseButton()</code> relie son signal "
                    "<code>clicked</code> au slot <code>togglePause()</code>, qui arrête ou "
                    "relance le minuteur et change le texte du bouton."
                    "<br><br>Mettre en pause quand le point est rouge : la carte, la courbe et la "
                    "lecture restent figées au même instant. Comparer la couleur de la carte "
                    "sous le capteur avec la dernière mesure de la courbe, puis reprendre."
                ),
                run=self._explorePause,
                codeSource=(self.connectPauseButton, self.togglePause),
                references=[("QTimer", qtDocUrl("QtCore", "QTimer"))],
            ),
        ]
