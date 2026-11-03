"""Notion 1.3 : interagir avec un graphique.

Contexte : un bloc suspendu à un ressort oscille de haut en bas en perdant
de l'énergie à cause du frottement (un oscillateur amorti). Son
déplacement vertical suit y(t) = A·e^(−γt)·cos(ωt), avec A = 2 m et
ω = 6 rad/s. Le coefficient d'amortissement γ (gamma) décide de la vitesse
à laquelle l'oscillation s'éteint. Les mesures sont les extrémités de
chaque oscillation, relevées sur une vidéo. Note de conception, jamais
affichée : elles ont été simulées avec γ = 0,5 /s, une valeur atteignable
au pas du sélecteur numérique.

Étapes couvertes : la formule, puis la courbe théorique, calculée d'un coup
sur un tableau d'instants, son enveloppe et le remplissage entre deux
courbes (`FillBetweenItem`), des mesures, une étiquette d'information
(`TextItem`). Puis l'interaction, une nouveauté par étape « À vous » : un
sélecteur numérique qui met la courbe à jour (`setData()`), une ligne de
lecture déplaçable (`InfiniteLine`), son étiquette récrite par un slot
relié à deux signaux, un clic sur une mesure (`sigPointsClicked`) qui
remplit l'étiquette d'information, puis une cible (`TargetItem`). Un
second clic retire l'étiquette et la cible.

Chaque étape est une méthode de `QTopicInteractionTab`. Les éléments
graphiques que l'interaction modifie sont gardés sur `self`.
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

_PlotDataItemPage = "api_reference/graphicsItems/plotdataitem"
_InfiniteLinePage = "api_reference/graphicsItems/infiniteline"


def displacement(t: float | np.ndarray, damping: float) -> float | np.ndarray:
    """Le déplacement y(t) = 2·e^(−γt)·cos(6t), en mètres.

    `t` est un instant en secondes, ou un tableau d'instants ; le résultat
    est un réel, ou un tableau de réels de même forme.
    """
    return 2.0 * np.exp(-damping * t) * np.cos(6.0 * t)


def envelope(t: float | np.ndarray, damping: float) -> float | np.ndarray:
    """L'amplitude 2·e^(−γt), en mètres, qui borne l'oscillation.

    `t` est un instant en secondes, ou un tableau d'instants ; le résultat
    est un réel, ou un tableau de réels de même forme.
    """
    return 2.0 * np.exp(-damping * t)


class QTopicInteractionTab(QWidget):
    """Onglet de la notion 1.3 : un oscillateur amorti, et l'interaction pas à pas.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        plotWidget: Le widget du graphique, créé une seule fois.
        controls: Le panneau des contrôles des étapes « À vous » (plomberie).
        dampingSlider: Le sélecteur numérique de l'amortissement γ.
        times: Les instants de la courbe théorique, ou None.
        curve, upperEnvelope, lowerEnvelope, measurements, readLine,
            infoLabel, target: Les éléments graphiques que l'interaction
            modifie, ou None avant leur étape.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Interaction"
    TabToolTip = "Un sélecteur numérique, une ligne de lecture, une mesure qu'on clique"
    RecommendedPanelWidth = 640
    Objective = (
        "Tracer une courbe théorique calculée, son enveloppe et des mesures, puis faire réagir le "
        "graphique à un contrôle, à une ligne que la souris déplace et à un clic sur un point."
    )
    KeyConcepts = [
        "Une formule écrite avec les fonctions de numpy se calcule d'un coup sur tout un tableau "
        "d'instants.",
        "Une courbe gardée dans un attribut se met à jour en place par <code>setData()</code>.",
        "PyQtGraph a ses propres éléments interactifs : une ligne déplaçable, des points "
        "cliquables. Ils émettent des signaux, comme un widget Qt.",
        "Un résultat s'écrit dans une étiquette d'information, et non dans le titre.",
        "Ce qu'un clic montre, un second clic le retire.",
        "Les mesures ne changent pas avec la théorie : c'est leur écart qui change.",
    ]
    KeyApis = [
        "FillBetweenItem", "PlotDataItem.setData", "InfiniteLine", "InfiniteLine.sigPositionChanged",
        "PlotDataItem.sigPointsClicked", "TextItem", "TargetItem",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.times: np.ndarray | None = None
        self.curve: pg.PlotDataItem | None = None
        self.upperEnvelope: pg.PlotDataItem | None = None
        self.lowerEnvelope: pg.PlotDataItem | None = None
        self.measurements: pg.PlotDataItem | None = None
        self.readLine: pg.InfiniteLine | None = None
        self.infoLabel: pg.TextItem | None = None
        self.target: pg.TargetItem | None = None

        self.createPlotWidget()
        self.controls = QControlPanel()
        self.dampingSlider = self.controls.addSlider("Amortissement γ", 0, 20, 2, divisor=10, suffix="/s")

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
        """Ramène le graphique et le sélecteur numérique à leur état d'origine."""
        self.controls.resetControls()
        resetPlotItem(self.plotWidget.getPlotItem())
        self.times = None
        self.curve = None
        self.upperEnvelope = None
        self.lowerEnvelope = None
        self.measurements = None
        self.readLine = None
        self.infoLabel = None
        self.target = None

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidget(self) -> None:
        """Crée le widget du graphique, vide."""
        self.plotWidget = pg.PlotWidget()

    def setUpPlot(self) -> None:
        """Titre, axes, grille et légende en haut à droite."""
        self.plotWidget.setTitle("Oscillateur amorti : un bloc suspendu à un ressort")
        self.plotWidget.setLabel("bottom", "Temps", units="s")
        self.plotWidget.setLabel("left", "Déplacement y", units="m")
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)
        self.plotWidget.addLegend(offset=(-10, 10))

    def _formulasOnly(self) -> None:
        """Les formules sont des fonctions : rien n'est tracé à cette étape."""

    def plotTheory(self) -> None:
        """500 instants de 0 à 10 s, puis la courbe théorique pour γ = 0,2 /s, gardée dans self.curve."""
        self.times = np.linspace(0, 10, 500)
        self.curve = self.plotWidget.plot(self.times, displacement(self.times, 0.2),
                                          pen=pg.mkPen("y", width=2), name="Théorie")

    def plotEnvelope(self) -> None:
        """L'enveloppe ±2·e^(−γt), pour γ = 0,2 /s, en tirets."""
        upper = envelope(self.times, 0.2)
        dashedPen = pg.mkPen("c", width=1, style=Qt.PenStyle.DashLine)
        self.upperEnvelope = self.plotWidget.plot(self.times, upper, pen=dashedPen)
        self.lowerEnvelope = self.plotWidget.plot(self.times, -upper, pen=dashedPen)

    def fillEnvelope(self) -> None:
        """Remplit, en cyan translucide, la bande entre les deux courbes de l'enveloppe."""
        fill = pg.FillBetweenItem(self.upperEnvelope, self.lowerEnvelope, brush=(0, 200, 200, 40))
        self.plotWidget.addItem(fill)

    def plotMeasurements(self) -> None:
        """Les extrémités relevées sur la vidéo, une par demi-période, en points rouges."""
        videoTimes = np.array([0.52, 1.05, 1.57, 2.09, 2.62, 3.14, 3.67, 4.19, 4.71, 5.24])
        videoPositions = np.array([-1.56, 1.19, -0.92, 0.71, -0.53, 0.39, -0.35, 0.27, -0.20, 0.13])
        self.measurements = self.plotWidget.plot(videoTimes, videoPositions, pen=None, symbol="o",
                                                 symbolSize=9, symbolBrush="r", name="Extrémités (vidéo)")

    def connectDampingSlider(self) -> None:
        """Relie le sélecteur numérique au slot qui met la courbe et l'enveloppe à jour."""
        self.dampingSlider.valueChanged.connect(self.updateDamping)

    @Slot()
    def updateDamping(self) -> None:
        """Recalcule la courbe et l'enveloppe pour le γ du sélecteur numérique."""
        damping = self.dampingSlider.value() / 10
        self.curve.setData(self.times, displacement(self.times, damping))
        upper = envelope(self.times, damping)
        self.upperEnvelope.setData(self.times, upper)
        self.lowerEnvelope.setData(self.times, -upper)

    def addReadLine(self) -> None:
        """Une ligne de lecture verticale, à t = 1 s, que la souris fait glisser."""
        self.readLine = pg.InfiniteLine(pos=1.0, angle=90, movable=True, pen="w",
                                        label="t = {value:.2f} s")
        self.plotWidget.addItem(self.readLine)

    def connectReadLine(self) -> None:
        """Relie au slot de l'étiquette le déplacement de la ligne, et le changement de γ."""
        self.readLine.sigPositionChanged.connect(self.updateReadLabel)
        self.dampingSlider.valueChanged.connect(self.updateReadLabel)

    @Slot()
    def updateReadLabel(self) -> None:
        """Écrit sur la ligne de lecture l'instant et le déplacement théorique à cet instant."""
        t = self.readLine.value()
        y = displacement(t, self.dampingSlider.value() / 10)
        text = f"t = {t:.2f} s\ny = {y:+.2f} m"
        self.readLine.label.setFormat(text.replace(".", ","))

    def addInfoLabel(self) -> None:
        """Une étiquette d'information, posée sur la première extrémité."""
        self.infoLabel = pg.TextItem(color="w", border=pg.mkPen("w"), fill=pg.mkBrush(20, 20, 20, 230))
        self.infoLabel.setText("Première extrémité : t = 0,52 s")
        self.infoLabel.setPos(0.52, -1.56)
        self.plotWidget.addItem(self.infoLabel)

    def connectMeasurements(self) -> None:
        """L'étiquette cachée, puis le clic sur une mesure relié au slot qui la remplit."""
        self.infoLabel.setVisible(False)
        self.measurements.sigPointsClicked.connect(self.showDeviation)

    @Slot(object, object, object)
    def showDeviation(self, curve: pg.PlotDataItem, points: list, event: object) -> None:
        """Écrit près de la mesure cliquée son écart à la théorie ; un second clic sur elle l'efface."""
        position = points[0].pos()
        if self.infoLabel.isVisible() and self.infoLabel.pos() == position:
            self.infoLabel.setVisible(False)
            return
        t = position.x()
        measured = position.y()
        theory = displacement(t, self.dampingSlider.value() / 10)
        text = f"Mesure à t = {t:.2f} s : y = {measured:+.2f} m\nÉcart à la théorie : {measured - theory:+.2f} m"
        self.infoLabel.setText(text.replace(".", ","))
        self.infoLabel.setPos(position)
        self.infoLabel.setVisible(True)

    def addTarget(self) -> None:
        """Une cible cachée, et un second slot relié au clic sur une mesure."""
        self.target = pg.TargetItem(pos=(0, 0), size=24, movable=False, pen=pg.mkPen("w", width=2))
        self.target.setVisible(False)
        self.plotWidget.addItem(self.target)
        self.measurements.sigPointsClicked.connect(self.placeTarget)

    @Slot(object, object, object)
    def placeTarget(self, curve: pg.PlotDataItem, points: list, event: object) -> None:
        """Place la cible sur la mesure cliquée et la montre ; la retire si elle y est déjà."""
        position = points[0].pos()
        if self.target.isVisible() and self.target.pos() == position:
            self.target.setVisible(False)
        else:
            self.target.setPos(position)
            self.target.setVisible(True)

    def _exploreDamping(self) -> None:
        """Connecte le sélecteur numérique, puis le révèle."""
        self.connectDampingSlider()
        self.controls.reveal()

    def _readCurve(self) -> None:
        """Connecte le slot de l'étiquette, puis l'appelle une première fois."""
        self.connectReadLine()
        self.updateReadLabel()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : graphique, axes, légende",
                explanation=(
                    "Rien de nouveau : le widget du graphique, son titre, les titres des axes et "
                    "la grille (notion 1.1). La légende s'accroche en haut à droite, avec "
                    "<code>offset=(-10, 10)</code> (notion 1.1)."
                ),
                run=self.setUpPlot,
                codeSource=(self.createPlotWidget, self.setUpPlot),
                references=[("PlotItem.addLegend", pyqtgraphDocUrl("api_reference/graphicsItems/plotitem",
                                                                   "PlotItem.addLegend"))],
            ),
            QStepWalkthrough.Step(
                title="La formule de l'oscillateur",
                explanation=(
                    "Le bloc pend au bout d'un ressort et oscille de haut en bas. Son "
                    "déplacement vertical, compté depuis sa position d'équilibre, suit "
                    "y(t) = A·e<sup>−γt</sup>·cos(ωt) :"
                    "<ul>"
                    "<li>y, le déplacement, en mètres, et t, le temps, en secondes ;</li>"
                    "<li>A = 2 m, l'amplitude de départ ;</li>"
                    "<li>ω = 6 rad/s, la pulsation, qui fixe la cadence des oscillations ;</li>"
                    "<li>γ, l'amortissement, en 1/s : e<sup>−γt</sup> diminue l'amplitude avec le "
                    "temps.</li>"
                    "</ul>"
                    "Une simplification : ω est pris constant, sans le léger ralentissement que "
                    "cause l'amortissement. La formule est admise : seule compte ici sa "
                    "traduction en Python."
                    "<br><br><code>displacement(t, damping)</code> calcule y. "
                    "<code>np.exp()</code> et <code>np.cos()</code> agissent sur chaque élément "
                    "d'un tableau : la fonction reçoit un instant ou tout un tableau d'instants, "
                    "et rend un résultat de même forme. Ses annotations le disent : "
                    "<code>float | np.ndarray</code>, un nombre ou un tableau numpy."
                    "<br><br>Elle est écrite au niveau du module, hors de toute classe : les "
                    "étapes l'appellent comme une fonction ordinaire. Rien n'est encore tracé."
                ),
                run=self._formulasOnly,
                codeSource=(displacement,),
                references=[("numpy.exp", numpyDocUrl("exp"))],
            ),
            QStepWalkthrough.Step(
                title="La courbe théorique",
                explanation=(
                    "Un seul appel de <code>displacement()</code> calcule les 500 déplacements "
                    "d'un coup, sur le tableau d'instants. <code>plot()</code> rend la courbe "
                    "qu'il crée, un <code>PlotDataItem</code> (notion 1.1). "
                    "<code>self.curve</code> la garde, pour la modifier plus loin."
                    "<br><br><i>Pour l'exemple</i> : 500 instants de 0 à 10 s, gardés dans "
                    "<code>self.times</code> pour les étapes suivantes, et γ = 0,2 /s."
                ),
                run=self.plotTheory,
                references=[
                    ("PlotItem.plot", pyqtgraphDocUrl("api_reference/graphicsItems/plotitem", "PlotItem.plot")),
                ],
            ),
            QStepWalkthrough.Step(
                title="L'enveloppe",
                explanation=(
                    "L'oscillation reste entre +2·e<sup>−γt</sup> et −2·e<sup>−γt</sup> : son "
                    "<b>enveloppe</b>. <code>envelope()</code> calcule 2·e<sup>−γt</sup> sur tout "
                    "le tableau d'instants, et <code>-upper</code> en change le signe. Les deux "
                    "courbes, en tirets, sont gardées dans <code>self.upperEnvelope</code> et "
                    "<code>self.lowerEnvelope</code>. Elles n'ont pas de <code>name</code> : "
                    "elles n'entrent pas dans la légende."
                ),
                run=self.plotEnvelope,
                codeSource=(envelope, self.plotEnvelope),
                references=[("PlotItem.plot", pyqtgraphDocUrl("api_reference/graphicsItems/plotitem",
                                                              "PlotItem.plot"))],
            ),
            QStepWalkthrough.Step(
                title="Remplir entre deux courbes",
                explanation=(
                    "<code>pg.FillBetweenItem(courbe1, courbe2, brush=…)</code> remplit la bande "
                    "entre deux courbes. C'est un élément graphique à part, ajouté par "
                    "<code>addItem()</code>."
                    "<br><br>Le pinceau est ici un tuple de quatre nombres : rouge, vert, bleu, "
                    "puis l'<b>opacité</b>, de 0 (transparent) à 255 (opaque). Avec 40, le cyan "
                    "reste pâle et laisse voir la grille. Un tuple suffit : PyQtGraph le passe "
                    "lui-même à <code>pg.mkBrush()</code> (notion 1.2). Il en va de même pour "
                    "les autres paramètres de pinceau, comme <code>symbolBrush</code>."
                ),
                run=self.fillEnvelope,
                references=[("FillBetweenItem", pyqtgraphDocUrl("api_reference/graphicsItems/fillbetweenitem",
                                                                "FillBetweenItem"))],
            ),
            QStepWalkthrough.Step(
                title="Des mesures : les extrémités du mouvement",
                explanation=(
                    "Pour mesurer le mouvement, on filmerait le bloc. Image par image, on "
                    "relèverait sa position chaque fois qu'il s'arrête pour repartir en sens "
                    "inverse : au plus haut, puis au plus bas de chaque oscillation. Ce sont ses "
                    "<b>extrémités</b>."
                    "<br><br>Une oscillation complète dure une <b>période</b>, T = 2π/ω ≈ 1,05 s. "
                    "Les extrémités se suivent toutes les demi-périodes, π/ω ≈ 0,52 s. En ces "
                    "instants, le déplacement atteint l'enveloppe : les points rouges devraient "
                    "la toucher."
                    "<br><br>Ils tombent en dedans : l'amortissement réel est plus fort que "
                    "0,2 /s. Les étapes suivantes cherchent le bon. "
                    "<code>self.measurements</code> garde le nuage de points (notion 1.2)."
                    "<br><br><i>Pour l'exemple</i> : ces mesures sont simulées, à la façon d'une "
                    "vidéo, et écrites en clair dans le code."
                ),
                run=self.plotMeasurements,
                references=[("PlotDataItem", pyqtgraphDocUrl(_PlotDataItemPage, "PlotDataItem"))],
            ),
            QStepWalkthrough.Step(
                title="Une étiquette d'information",
                explanation=(
                    "Une <b>étiquette d'information</b> écrit un résultat dans le graphique. "
                    "C'est un <code>pg.TextItem</code>, l'élément graphique d'un texte. "
                    "L'essentiel : elle se crée, reçoit son texte par <code>setText()</code> et "
                    "se place par <code>setPos()</code>. Le reste règle son apparence :"
                    "<ul>"
                    "<li><code>color</code> est la couleur du texte ;</li>"
                    "<li><code>border</code> lui donne un contour, par un stylo ;</li>"
                    "<li><code>fill</code> lui donne un fond, par un pinceau, ici presque opaque : "
                    "le texte reste lisible par-dessus la courbe ;</li>"
                    "<li><code>setText()</code> remplace son texte ;</li>"
                    "<li><code>setPos(x, y)</code> le place, en unités des axes, son coin en haut "
                    "à gauche sur le point.</li>"
                    "</ul>"
                    "<code>pg.mkBrush()</code> (notion 1.2) reçoit ici quatre nombres séparés : "
                    "rouge, vert, bleu et opacité. Cette écriture vaut le tuple "
                    "<code>(20, 20, 20, 230)</code>."
                    "<br><br>Un résultat va dans une étiquette comme celle-ci, jamais dans le "
                    "titre : le titre nomme le graphique, et récrit, il perdrait ce rôle."
                    "<br><br><i>Pour l'exemple</i> : l'étiquette est posée sur la première "
                    "extrémité."
                ),
                run=self.addInfoLabel,
                references=[("TextItem", pyqtgraphDocUrl("api_reference/graphicsItems/textitem", "TextItem"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : l'amortissement",
                explanation=(
                    "Un sélecteur numérique paraît sous le graphique : "
                    "<code>dampingSlider</code>, l'amortissement γ. Un <code>QSlider</code> ne "
                    "porte que des entiers : il va de 0 à 20, et la valeur lue divisée par 10 "
                    "donne γ, de 0 à 2 /s par pas de 0,1. Il part de 2, soit 0,2 /s. Le panneau "
                    "des contrôles affiche à côté de lui sa valeur déjà divisée, γ en /s : c'est "
                    "là qu'on la lit."
                    "<br><br>Nouveau : <code>setData(x, y)</code> remplace les données d'une "
                    "courbe déjà tracée, sans la retirer ni la recréer. "
                    "<code>connectDampingSlider()</code> relie le signal "
                    "<code>valueChanged</code> au slot <code>updateDamping()</code>, qui "
                    "recalcule la courbe et les deux bords de l'enveloppe. Le remplissage suit "
                    "l'enveloppe de lui-même. Les mesures, elles, ne bougent pas."
                    "<br><br>Chercher le γ qui fait toucher l'enveloppe aux extrémités."
                    "<br><br>L'interaction est le sujet de cette notion : chacune de ses étapes "
                    "« À vous » apporte une interaction nouvelle, puis la fait essayer."
                ),
                run=self._exploreDamping,
                codeSource=(self.connectDampingSlider, self.updateDamping),
                references=[("PlotDataItem.setData", pyqtgraphDocUrl(_PlotDataItemPage, "PlotDataItem.setData"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : une ligne de lecture",
                explanation=(
                    "Nouveau : <code>pg.InfiniteLine</code> trace une ligne qui traverse tout le "
                    "graphique. <code>pos</code> est sa position, ici t = 1 s ; "
                    "<code>angle=90</code> la rend verticale ; avec <code>movable=True</code>, "
                    "la souris la fait glisser. C'est une <b>ligne de lecture</b>."
                    "<br><br><code>label</code> lui donne une étiquette, l'<b>étiquette de la "
                    "ligne</b>, distincte de l'étiquette d'information de l'étape 8. Ce texte n'est pas une "
                    "f-string : c'est un gabarit, que PyQtGraph remplit chaque fois que la "
                    "ligne bouge. <code>{value}</code> devient la position de la ligne, et "
                    "<code>:.2f</code> l'écrit avec deux décimales. L'étiquette se place à "
                    "mi-hauteur de la zone visible, contre la ligne."
                    "<br><br>PyQtGraph remplit ce gabarit avec le point décimal de Python, comme "
                    "les nombres des graduations. Ces textes, mis en forme par PyQtGraph lui-même, "
                    "gardent le point. Partout où le code compose lui-même un texte, le guide met "
                    "la virgule, comme l'étape suivante le montre."
                    "<br><br>Faire glisser la ligne : son étiquette suit l'instant."
                ),
                run=self.addReadLine,
                references=[("InfiniteLine", pyqtgraphDocUrl(_InfiniteLinePage, "InfiniteLine"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : lire la courbe",
                explanation=(
                    "Nouveau : un slot qui récrit l'étiquette de la ligne avec la valeur de la "
                    "courbe. Trois temps."
                    "<br><br><b>1. Le slot.</b> <code>value()</code> rend la "
                    "position de la ligne. <code>self.readLine.label</code> est l'étiquette de la ligne, "
                    "et <code>setFormat(texte)</code> la récrit : il reçoit un texte et ne rend "
                    "rien. Le slot <code>updateReadLabel()</code> calcule y à l'instant de la "
                    "ligne, par <code>displacement()</code>, et écrit t et y."
                    "<br><br><b>2. Le texte</b>, du Python : "
                    "<code>:+.2f</code> écrit le signe, même positif, et <code>\\n</code> passe à la "
                    "ligne. Puis <code>replace(\".\", \",\")</code> remplace chaque point du texte "
                    "par une virgule : la virgule décimale du français. Le guide l'emploie pour "
                    "tout nombre décimal qu'il écrit."
                    "<br><br><b>3. Les signaux.</b> <code>connectReadLine()</code> relie le slot à deux signaux : "
                    "<code>sigPositionChanged</code> de la ligne, émis à chaque déplacement, et "
                    "<code>valueChanged</code> du sélecteur numérique. Ce signal a déjà un slot, "
                    "<code>updateDamping()</code> : un signal peut en avoir plusieurs, appelés "
                    "l'un après l'autre. Quand γ change, la courbe et l'étiquette suivent "
                    "ensemble. Le guide appelle aussi le slot une fois à "
                    "l'arrivée sur l'étape, pour l'étiquette de départ."
                    "<br><br>Faire glisser la ligne sur un sommet de la courbe, puis changer γ."
                ),
                run=self._readCurve,
                codeSource=(self.connectReadLine, self.updateReadLabel),
                references=[("InfiniteLine.sigPositionChanged", pyqtgraphDocUrl(_InfiniteLinePage,
                                                                                "InfiniteLine"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : cliquer une mesure",
                explanation=(
                    "Nouveau : les points d'une courbe sont cliquables. Le signal "
                    "<code>sigPointsClicked</code> de <code>self.measurements</code> transmet "
                    "trois arguments : la courbe, la liste des points cliqués et l'évènement de "
                    "la souris. Une liste, parce que plusieurs points peuvent se superposer sous "
                    "la souris ; ici, le premier suffit. Chaque élément de la liste est un point "
                    "du nuage, et sa méthode <code>pos()</code> rend sa position : un point de Qt "
                    "(<code>QPointF</code>), que ses accesseurs <code>x()</code> et "
                    "<code>y()</code> lisent."
                    "<br><br>L'étiquette d'information (étape 8) est cachée jusqu'au premier clic. "
                    "Le slot <code>showDeviation()</code> y écrit la mesure et son écart à "
                    "la théorie, pour le γ courant, puis la pose sur le point : "
                    "<code>setPos()</code> reçoit cette fois un <code>QPointF</code>, et non deux "
                    "nombres. Le texte prend la virgule décimale par <code>replace()</code>, comme "
                    "à l'étape précédente."
                    "<br><br>Le geste inverse : <code>isVisible()</code> rend <code>True</code> si "
                    "l'étiquette est montrée, et <code>pos()</code> rend sa position, réglée par "
                    "<code>setPos()</code>. Si l'étiquette est déjà sur ce point, le slot la "
                    "cache plutôt."
                    "<br><br>Cliquer une mesure, puis une autre. Changer γ et cliquer encore : "
                    "l'écart suit. Cliquer la mesure qui porte l'étiquette : elle disparaît."
                ),
                run=self.connectMeasurements,
                codeSource=(self.connectMeasurements, self.showDeviation),
                references=[
                    ("PlotDataItem.sigPointsClicked", pyqtgraphDocUrl(_PlotDataItemPage, "PlotDataItem")),
                    ("QPointF", qtDocUrl("QtCore", "QPointF")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : marquer la mesure, et la démarquer",
                explanation=(
                    "Nouveau : <code>pg.TargetItem</code> est une <b>cible</b>, un marqueur "
                    "rond barré d'une croix. Il reçoit sa position (<code>pos</code>), sa taille "
                    "en pixels (<code>size</code>), et son stylo (<code>pen</code>). Son "
                    "remplissage par défaut est un bleu translucide. Avec "
                    "<code>movable=False</code>, la souris ne la déplace pas. Elle est cachée "
                    "jusqu'au premier clic."
                    "<br><br>Un second slot, <code>placeTarget()</code>, est relié au même "
                    "<code>sigPointsClicked</code>, comme <code>valueChanged</code> à l'étape "
                    "« Lire la courbe ». Il place la cible sur "
                    "la mesure cliquée et la montre. Pour la retirer, cliquer de nouveau la "
                    "mesure marquée : le slot trouve la cible déjà sur ce point, et la cache. "
                    "Cachée plutôt que détruite, elle resservira au clic suivant. L'étiquette "
                    "de l'étape précédente fait de même."
                ),
                run=self.addTarget,
                codeSource=(self.addTarget, self.placeTarget),
                references=[("TargetItem", pyqtgraphDocUrl("api_reference/graphicsItems/targetitem",
                                                           "TargetItem"))],
            ),
        ]
