"""Notion 1.4 : un graphique en temps réel.

Contexte : un capteur simulé mesure l'angle d'un pendule 50 fois par
seconde. Le graphique affiche les dix dernières secondes et défile à mesure
que les mesures arrivent. C'est l'usage pour lequel PyQtGraph est conçu :
redessiner une courbe des dizaines de fois par seconde sans ralentir
l'application.

Étapes couvertes : le capteur simulé (un générateur à graine), un tampon de
taille fixe (deux tableaux numpy), le tampon qui se remplit
(`appendSample()`), la fenêtre glissante (`pushSample()`), le décalage d'un
bloc de mesures en un seul geste (`pushSamples()`), puis un `QTimer` qui
ajoute une mesure toutes les 20 ms. Un bouton met ensuite en pause.

Chaque étape est une méthode de `QTopicRealTimeTab`. La pause quand la page
est cachée est de la plomberie (`pauseWhileHidden`), dite en mots.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, numpyPageUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from ..common.q_timer_pause import pauseWhileHidden
from .plot_reset import resetPlotItem


class QTopicRealTimeTab(QWidget):
    """Onglet de la notion 1.4 : un graphique qui défile en temps réel.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        plotWidget: Le widget du graphique, créé une seule fois.
        timer: Le minuteur, créé une seule fois, arrêté avant chaque rejeu.
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        pauseButton: Le bouton de pause et de reprise.
        rng: Le générateur du bruit du capteur, ou None.
        times, angles: Le tampon des mesures, ou None.
        count: Le nombre de mesures lues depuis le départ.
        curve: La courbe des mesures, ou None.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Temps réel"
    TabToolTip = "Un tampon numpy, une fenêtre glissante et un QTimer : un graphique qui défile"
    RecommendedPanelWidth = 640
    Objective = (
        "Afficher des mesures à mesure qu'elles arrivent : un tampon de taille fixe, une "
        "fenêtre qui glisse, et un minuteur qui ajoute une mesure 50 fois par seconde."
    )
    KeyConcepts = [
        "Un générateur à graine fixe simule un bruit, le même à chaque exécution.",
        "Un tampon de taille fixe garde les N dernières mesures : la mémoire ne grandit pas.",
        "Quand le tampon est plein, tout est décalé d'une case et la mesure la plus ancienne "
        "disparaît : la fenêtre glisse. Des mesures arrivées ensemble se rangent d'un seul "
        "décalage.",
        "Un minuteur émet un signal à intervalle régulier, sans bloquer l'application.",
        "On met à jour la même courbe (<code>setData()</code>) plutôt que d'en tracer une "
        "nouvelle à chaque mesure.",
    ]
    KeyApis = [
        "numpy.random.default_rng", "numpy.random.Generator.normal", "numpy.zeros",
        "PlotDataItem.setData", "QTimer", "QTimer.timeout",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.rng: np.random.Generator | None = None
        self.times: np.ndarray | None = None
        self.angles: np.ndarray | None = None
        self.count = 0
        self.curve: pg.PlotDataItem | None = None

        self.createPlotWidget()
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
        contentLayout.addWidget(self.plotWidget, 1)
        contentLayout.addWidget(self.controls)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Arrête le minuteur, vide le graphique, et remet le bouton à « Pause »."""
        self.timer.stop()
        self.controls.resetControls()
        self.pauseButton.setText("Pause")
        resetPlotItem(self.plotWidget.getPlotItem())
        self.rng = None
        self.times = None
        self.angles = None
        self.count = 0
        self.curve = None

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidget(self) -> None:
        """Crée le widget du graphique, vide."""
        self.plotWidget = pg.PlotWidget()

    def setUpPlot(self) -> None:
        """Titre, axes, grille, et un axe vertical fixe de −30° à 30°."""
        self.plotWidget.setTitle("Angle d'un pendule, mesuré 50 fois par seconde")
        self.plotWidget.setLabel("bottom", "Temps", units="s")
        self.plotWidget.setLabel("left", "Angle", units="°")
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)
        self.plotWidget.setYRange(-30, 30, padding=0)

    def createSensor(self) -> None:
        """Le générateur du bruit du capteur, à graine fixe."""
        self.rng = np.random.default_rng(7)

    def readSensor(self, t: float | np.ndarray) -> float | np.ndarray:
        """L'angle du pendule, en degrés : 20·cos(πt), plus un bruit.

        `t` est un instant en secondes, ou un tableau d'instants de forme
        (n,) ; le résultat est un réel, ou un tableau de réels de même forme.
        """
        return 20 * np.cos(np.pi * t) + self.rng.normal(0, 0.5, np.shape(t))

    def createBuffer(self) -> None:
        """Un tampon de 500 mesures, soit 10 s, et une courbe encore vide."""
        self.times = np.zeros(500)
        self.angles = np.zeros(500)
        self.count = 0
        self.curve = self.plotWidget.plot(pen=pg.mkPen("y", width=2))

    def appendSample(self) -> None:
        """Lit une mesure, la range dans la première case libre, et met la courbe à jour."""
        t = self.count / 50
        self.times[self.count] = t
        self.angles[self.count] = self.readSensor(t)
        self.count += 1
        self.curve.setData(self.times[:self.count], self.angles[:self.count])

    def fillBuffer(self) -> None:
        """500 mesures d'un coup : le tampon est plein."""
        for i in range(500):
            self.appendSample()

    def pushSample(self) -> None:
        """Décale tout le tampon d'une case, puis écrit la nouvelle mesure dans la dernière."""
        t = self.count / 50
        self.times[:-1] = self.times[1:]
        self.angles[:-1] = self.angles[1:]
        self.times[-1] = t
        self.angles[-1] = self.readSensor(t)
        self.count += 1
        self.curve.setData(self.times, self.angles)

    def slideWindow(self) -> None:
        """100 mesures de plus, arrivées une à une, sur le tampon plein : la fenêtre glisse de 2 s."""
        for i in range(100):
            self.pushSample()

    def pushSamples(self, sampleCount: int) -> None:
        """Décale le tampon de `sampleCount` cases d'un seul coup, puis écrit les nouvelles mesures à la fin."""
        newTimes = (self.count + np.arange(sampleCount)) / 50
        self.times[:-sampleCount] = self.times[sampleCount:]
        self.angles[:-sampleCount] = self.angles[sampleCount:]
        self.times[-sampleCount:] = newTimes
        self.angles[-sampleCount:] = self.readSensor(newTimes)
        self.count += sampleCount
        self.curve.setData(self.times, self.angles)

    def slideWindowAtOnce(self) -> None:
        """100 mesures de plus, arrivées ensemble : un seul décalage de 100 cases."""
        self.pushSamples(100)

    def createTimer(self) -> None:
        """Crée le minuteur, et relie son signal timeout au slot qui ajoute une mesure."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advanceRecording)

    @Slot()
    def advanceRecording(self) -> None:
        """Ajoute une mesure : dans une case libre, ou en faisant glisser la fenêtre."""
        if self.count < 500:
            self.appendSample()
        else:
            self.pushSample()

    def startMeasuring(self) -> None:
        """Démarre le minuteur : une mesure toutes les 20 ms."""
        self.timer.start(20)

    def connectControls(self) -> None:
        """Relie le bouton au slot qui met en pause ou relance."""
        self.pauseButton.clicked.connect(self.togglePause)

    @Slot()
    def togglePause(self) -> None:
        """Arrête ou relance le minuteur, et change le texte du bouton."""
        if self.timer.isActive():
            self.timer.stop()
            self.pauseButton.setText("Reprendre")
        else:
            self.timer.start(20)
            self.pauseButton.setText("Pause")

    def _explorePause(self) -> None:
        """Connecte le bouton, puis le révèle."""
        self.connectControls()
        self.controls.reveal()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : graphique, titre, axes",
                explanation=(
                    "Rien de nouveau : le widget du graphique, le titre, les axes et la grille "
                    "(notion 1.1). <code>setYRange()</code> fixe l'axe vertical de −30° à 30° "
                    "(notion 1.2). Sans lui, l'axe changerait d'échelle à chaque mesure et le "
                    "graphique sautillerait. L'axe horizontal reste automatique : il suivra les "
                    "données."
                ),
                run=self.setUpPlot,
                codeSource=(self.createPlotWidget, self.setUpPlot),
                references=[("ViewBox.setYRange", pyqtgraphDocUrl("api_reference/graphicsItems/viewbox",
                                                                  "ViewBox.setYRange"))],
            ),
            QStepWalkthrough.Step(
                title="Des mesures simulées",
                explanation=(
                    "Le capteur est simulé. Le pendule oscille de 20° de part et d'autre de la "
                    "verticale, avec une période de 2 s : son angle vaut 20·cos(πt), en degrés, "
                    "t en secondes. Un vrai capteur ajoute un bruit."
                    "<br><br><code>np.random.default_rng(7)</code> crée un générateur de nombres "
                    "aléatoires. La graine, 7, fixe la suite des tirages : le bruit est le même "
                    "à chaque exécution. <code>self.rng.normal(0, 0.5, forme)</code> tire des "
                    "nombres autour de 0, un par case d'un tableau de cette forme. Le deuxième "
                    "argument fixe l'étendue habituelle des tirages : environ deux sur trois "
                    "tombent entre −0,5 et 0,5. C'est un bruit d'environ ±0,5°."
                    "<br><br><code>readSensor(t)</code> rend une mesure de l'angle à l'instant "
                    "t, ou une mesure par instant si t est un tableau. <code>np.shape(t)</code> "
                    "rend la forme de t : <code>()</code> pour un seul nombre, d'où un seul "
                    "tirage, <code>(n,)</code> pour un tableau de n instants. Rien ne change "
                    "encore à gauche."
                ),
                run=self.createSensor,
                codeSource=(self.createSensor, self.readSensor),
                references=[
                    ("numpy.random.default_rng", numpyPageUrl("reference/random/generator", "numpy.random.default_rng")),
                    ("numpy.random.Generator.normal",
                     numpyPageUrl("reference/random/generated/numpy.random.Generator.normal")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Un tampon de taille fixe",
                explanation=(
                    "Le <b>tampon</b> : deux tableaux de 500 cases, préparés par "
                    "<code>np.zeros()</code>, pour les instants et les angles. À 50 mesures par "
                    "seconde, ils gardent 10 s de mesures. Leur taille ne changera jamais. "
                    "<code>self.count</code> compte les mesures lues."
                    "<br><br><code>plot()</code> sans données crée la courbe, vide pour "
                    "l'instant : rien ne paraît à gauche."
                ),
                run=self.createBuffer,
                references=[("numpy.zeros", numpyDocUrl("zeros"))],
            ),
            QStepWalkthrough.Step(
                title="Le tampon se remplit",
                explanation=(
                    "<code>appendSample()</code> lit une mesure, la range dans la première case "
                    "libre, celle d'indice <code>self.count</code>, puis compte une mesure de "
                    "plus. <code>setData()</code> (notion 1.3) donne ensuite à la courbe la "
                    "partie remplie du tampon : <code>self.times[:self.count]</code> désigne ses "
                    "<code>self.count</code> premières cases. À 50 mesures par seconde, la mesure "
                    "de rang <code>self.count</code> arrive à l'instant "
                    "<code>self.count / 50</code>, en secondes."
                    "<br><br><code>fillBuffer()</code> l'appelle 500 fois. À gauche, le tampon "
                    "est plein : 10 s de mesures, cinq périodes."
                ),
                run=self.fillBuffer,
                codeSource=(self.appendSample, self.fillBuffer),
                references=[
                    ("PlotDataItem.setData", pyqtgraphDocUrl("api_reference/graphicsItems/plotdataitem",
                                                             "PlotDataItem.setData")),
                    ("Indexation numpy", numpyPageUrl("user/basics.indexing")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La fenêtre glissante",
                explanation=(
                    "Le tampon est plein : une nouvelle mesure n'a plus de case libre. "
                    "<code>pushSample()</code> décale tout d'une case. "
                    "<code>self.times[:-1]</code> désigne toutes les cases sauf la dernière, "
                    "<code>self.times[1:]</code> toutes sauf la première. "
                    "<code>self.times[:-1] = self.times[1:]</code> recopie donc chaque case dans "
                    "sa voisine de gauche. La plus ancienne mesure disparaît, et la nouvelle "
                    "s'écrit dans la dernière case, d'indice −1."
                    "<br><br>À gauche, la courbe a glissé : l'axe du temps va maintenant de 2 s "
                    "à 12 s. C'est la <b>fenêtre glissante</b>."
                    "<br><br><i>Pour l'exemple</i> : <code>slideWindow()</code> appelle "
                    "<code>pushSample()</code> 100 fois, soit 2 s de mesures arrivées une à une, "
                    "comme le minuteur les livrera bientôt. Chaque appel recopie les 499 autres "
                    "cases : ici, 100 recopies du tampon pour 100 mesures. L'étape suivante "
                    "montre le geste à employer quand les mesures arrivent ensemble."
                ),
                run=self.slideWindow,
                codeSource=(self.pushSample, self.slideWindow),
                references=[("Indexation numpy", numpyPageUrl("user/basics.indexing"))],
            ),
            QStepWalkthrough.Step(
                title="Décaler d'un bloc",
                explanation=(
                    "Un capteur livre souvent ses mesures par paquets : 100 mesures d'un coup, "
                    "par exemple. Les ranger une à une recopierait le tampon 100 fois. "
                    "<code>pushSamples(sampleCount)</code> le décale de "
                    "<code>sampleCount</code> cases en un seul geste : "
                    "<code>self.times[:-sampleCount] = self.times[sampleCount:]</code>, le même "
                    "découpage qu'à l'étape précédente, décalé de plusieurs cases. Les "
                    "<code>sampleCount</code> dernières cases reçoivent ensuite les nouvelles "
                    "mesures, toutes ensemble."
                    "<br><br><code>np.arange(sampleCount)</code> rend 0, 1, …, sampleCount − 1 : "
                    "ajoutés au compte des mesures, puis divisés par 50, ce sont les instants "
                    "des nouvelles mesures. <code>readSensor()</code> les mesure d'un seul appel."
                    "<br><br>À gauche, la fenêtre a glissé de 2 s encore, en une seule recopie "
                    "du tampon : l'axe du temps va de 4 s à 14 s."
                ),
                run=self.slideWindowAtOnce,
                codeSource=(self.pushSamples, self.slideWindowAtOnce),
                references=[("numpy.arange", numpyDocUrl("arange"))],
            ),
            QStepWalkthrough.Step(
                title="Le temps réel : un minuteur",
                explanation=(
                    "Un minuteur (<code>QTimer</code>, de <code>PySide6.QtCore</code>) émet son "
                    "signal <code>timeout</code> à intervalle régulier. Il est créé une seule "
                    "fois, avec la page, et son signal est relié au slot "
                    "<code>advanceRecording()</code>. Celui-ci appelle <code>appendSample()</code> tant "
                    "que le tampon n'est pas plein, puis <code>pushSample()</code>. Le minuteur "
                    "livre une mesure à la fois : <code>pushSamples()</code>, l'étape précédente, "
                    "servirait à un capteur qui livre ses mesures par paquets."
                    "<br><br><code>createTimer()</code> est affichée pour être lue : elle s'est "
                    "exécutée une seule fois, à la création de la page. À cette étape s'exécute "
                    "<code>startMeasuring()</code>."
                    "<br><br><code>start(20)</code> démarre le minuteur, avec un intervalle de "
                    "20 ms : 50 mesures par seconde, comme le capteur. "
                    "<code>QTimer(self)</code> donne la page pour parent au minuteur : elle le "
                    "garde, et le détruit avec elle. Entre deux mesures, "
                    "l'application reste libre de réagir. Une seule courbe est mise à jour à "
                    "chaque fois : PyQtGraph la redessine sans effort."
                    "<br><br>Ici, les étapes précédentes ont déjà rempli le tampon : le slot "
                    "appelle <code>pushSample()</code> à chaque fois. La première branche ne sert "
                    "qu'au démarrage, tampon vide. À gauche, la courbe défile : l'axe du temps "
                    "avance d'une seconde par seconde."
                    "<br><br>Quand on quitte la page de cette notion, le guide arrête le "
                    "minuteur, et le relance au retour."
                ),
                run=self.startMeasuring,
                codeSource=(self.createTimer, self.advanceRecording, self.startMeasuring),
                references=[
                    ("QTimer", qtDocUrl("QtCore", "QTimer")),
                    ("QTimer.timeout", qtDocUrl("QtCore", "QTimer", "timeout")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : pause et reprise",
                explanation=(
                    "Un bouton paraît sous le graphique : <code>pauseButton</code>, « Pause ». "
                    "<code>connectControls()</code> relie son signal <code>clicked</code> au "
                    "slot <code>togglePause()</code>. <code>isActive()</code> dit si le "
                    "minuteur tourne. S'il tourne, le slot l'arrête (<code>stop()</code>) et "
                    "le bouton devient « Reprendre » ; sinon, il le relance."
                    "<br><br>En pause, le graphique reste figé : agrandir alors avec la molette "
                    "pour examiner le bruit, puis revenir par le bouton « A » (notion 1.1). Ce "
                    "bouton rend automatiques les deux axes : l'axe vertical perd ses bornes de "
                    "±30° et épouse les mesures, entre −21° et 21° environ. À la reprise, il "
                    "sautille donc un peu, comme le récapitulatif l'annonçait."
                ),
                run=self._explorePause,
                codeSource=(self.connectControls, self.togglePause),
                references=[("QTimer", qtDocUrl("QtCore", "QTimer"))],
            ),
        ]
