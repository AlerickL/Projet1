"""Notion 1.7 : contrôler la vue d'un graphique, par le code et à la souris.

Contexte : une sortie à vélo autour du mont Royal, enregistrée par un
téléphone, une position toutes les 2 s. Deux graphiques d'un genre nouveau
dans le guide : la carte, vue du ciel, qui exige la même échelle sur ses
deux axes ; le profil d'altitude, qu'on exagère en hauteur et qu'on explore
sur la distance seule. Note de conception, jamais affichée : la trace est
simulée, une boucle autour d'une colline en cloche.

Étapes couvertes : deux widgets du graphique dans un séparateur, la trace,
l'échelle égale (`setAspectLocked`), la distance parcourue, l'exagération
verticale et le piège du ratio, le widget, le graphique et la zone visible
(`getPlotItem`, `getViewBox`, `setMouseMode`), une carte sans axes et sa
barre d'échelle (`hideAxis`, `ScaleBar`), l'ajustement automatique par axe
(`enableAutoRange`, `setAutoVisible`), la souris sur un seul axe et des
bornes (`setMouseEnabled`, `setLimits`). Puis trois « À vous » : zoomer par
le code (`autoRange`), les modes d'affichage, et reprendre la main sur une
carte qui suit le cycliste (`viewRange`, `setRange`,
`sigRangeChangedManually`).

Chaque étape est une méthode de `QTopicViewTab`. Les fonctions de calcul,
`rideTrack()` et `trackDistance()`, sont écrites au niveau du module.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import SIGNAL, Qt, QTimer, Slot
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from ..common.q_timer_pause import pauseWhileHidden
from .plot_reset import resetPlotItem

_PlotItemPage = "api_reference/graphicsItems/plotitem"
_ViewBoxPage = "api_reference/graphicsItems/viewbox"


def rideTrack() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """La trace d'une sortie autour du sommet : l'est, le nord et l'altitude, en mètres.

    Rend trois tableaux de réels de forme (720,), une position toutes les
    2 s pendant 24 min. L'est et le nord sont comptés depuis le sommet.
    """
    angles = np.linspace(0, 2 * np.pi, 720)
    bends = 80 * np.sin(11 * angles) * np.clip(np.sin(angles), 0, None) ** 2  # des virages, au nord
    radius = 1000 + 450 * np.cos(angles) + bends
    east = radius * np.cos(angles)
    north = 0.75 * radius * np.sin(angles)
    elevation = 45 + 185 * np.exp(-(east ** 2 + north ** 2) / (2 * 650 ** 2))
    return east, north, elevation


def trackDistance(east: np.ndarray, north: np.ndarray) -> np.ndarray:
    """La distance parcourue depuis le départ, en mètres, à chaque position de la trace.

    `east` et `north` sont des tableaux de réels de forme (n,) ; le résultat
    aussi, et il commence à 0.
    """
    steps = np.hypot(np.diff(east), np.diff(north))
    return np.concatenate(([0.0], np.cumsum(steps)))


class QTopicViewTab(QWidget):
    """Onglet de la notion 1.7 : la carte et le profil d'une sortie à vélo.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        mapWidget, profileWidget: Les widgets de la carte et du profil,
            créés une seule fois.
        plotSplitter: Le séparateur qui les range l'un sous l'autre.
        timer: Le minuteur de la lecture de la sortie, créé une seule fois.
        controls: Le panneau des contrôles des étapes « À vous » (plomberie).
        wholeButton, climbButton, altitudeCheck: Les contrôles du zoom par
            le code.
        axesCheck, rectangleCheck, exaggerationCombo: Les contrôles des modes
            d'affichage.
        pauseButton, recenterButton: Les contrôles de la lecture.
        east, north, elevation, distance: Les tableaux de la trace, ou None
            avant leur étape.
        scaleBar, rider, riderLine: La barre d'échelle, la cible du cycliste
            sur la carte et sa ligne sur le profil, ou None avant leur étape.
        rideIndex: L'indice de la position du cycliste dans la trace.
        following: True tant que la carte suit le cycliste.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Contrôler la vue"
    TabToolTip = "Échelle égale, axes cachés, zoom par axe, bornes, et une carte qui suit le cycliste"
    RecommendedPanelWidth = 640
    Objective = (
        "Choisir ce que montre un graphique : ses proportions, ses règles graduées, son étendue "
        "sur chaque axe, ce que la souris peut y faire. Puis piloter la vue par le code, sans "
        "retirer la main à l'utilisateur."
    )
    KeyConcepts = [
        "Une carte exige la même échelle sur ses deux axes. Un profil d'altitude s'exagère en "
        "hauteur, d'un facteur choisi et annoncé.",
        "Le widget du graphique contient le graphique, qui contient la zone visible. La zone "
        "visible décide de l'étendue montrée : l'intervalle visible sur chaque axe.",
        "Chaque axe a son propre ajustement automatique. Cadrer une fois n'est pas laisser "
        "l'ajustement actif.",
        "La souris peut être limitée à un axe, et l'étendue bornée.",
        "Un signal distingue un changement d'étendue fait à la souris d'un changement fait par le "
        "code.",
    ]
    KeyApis = [
        "ViewBox.setAspectLocked", "PlotWidget.getPlotItem", "PlotItem.getViewBox", "ViewBox.setMouseMode",
        "PlotItem.hideAxis", "PlotItem.showAxis", "ScaleBar", "ViewBox.enableAutoRange",
        "ViewBox.setAutoVisible", "ViewBox.setMouseEnabled", "ViewBox.setLimits", "ViewBox.autoRange",
        "ViewBox.viewRange", "ViewBox.setRange", "ViewBox.sigRangeChangedManually",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.east: np.ndarray | None = None
        self.north: np.ndarray | None = None
        self.elevation: np.ndarray | None = None
        self.distance: np.ndarray | None = None
        self.scaleBar: pg.ScaleBar | None = None
        self.rider: pg.TargetItem | None = None
        self.riderLine: pg.InfiniteLine | None = None
        self.rideIndex = 0
        self.following = True

        self.createPlotWidgets()
        self.createTimer()
        pauseWhileHidden(self, self.timer)
        self.controls = QControlPanel()
        self.wholeButton = self.controls.addButton("Tout voir")
        self.climbButton = self.controls.addButton("La montée")
        self.altitudeCheck = self.controls.addCheckBox("Altitude ajustée à la portion visible du profil",
                                                       checked=True)
        self.axesCheck = self.controls.addCheckBox("Axes de la carte", checked=False)
        self.rectangleCheck = self.controls.addCheckBox("Zoom par rectangle sur la carte", checked=True)
        self.exaggerationCombo = self.controls.addComboBox(
            "Exagération du profil", [("libre", None), ("× 1", 1.0), ("× 5", 0.2), ("× 10", 0.1)])
        self.pauseButton = self.controls.addButton("Pause")
        self.recenterButton = self.controls.addButton("Recentrer")

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.plotSplitter, 1)
        contentLayout.addWidget(self.controls)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Arrête la lecture, vide la carte et le profil, et remet les contrôles à zéro."""
        self.timer.stop()
        self.controls.resetControls()
        self.pauseButton.setText("Pause")
        mapPlot = self.mapWidget.getPlotItem()
        if mapPlot.receivers(SIGNAL("sigRangeChangedManually(PyObject)")) > 0:
            mapPlot.sigRangeChangedManually.disconnect()
        if self.scaleBar is not None:
            # The scale bar connected itself to the view box when it received its parent.
            self.mapWidget.getViewBox().sigRangeChanged.disconnect(self.scaleBar.updateBar)
            self.mapWidget.scene().removeItem(self.scaleBar)
        resetPlotItem(mapPlot)
        resetPlotItem(self.profileWidget.getPlotItem())
        self.east = None
        self.north = None
        self.elevation = None
        self.distance = None
        self.scaleBar = None
        self.rider = None
        self.riderLine = None
        self.rideIndex = 0
        self.following = True

    # -- Étapes ------------------------------------------------------------------------------------

    def createPlotWidgets(self) -> None:
        """Crée la carte et le profil, deux widgets du graphique rangés l'un sous l'autre."""
        self.mapWidget = pg.PlotWidget()
        self.profileWidget = pg.PlotWidget()
        self.plotSplitter = QSplitter(Qt.Orientation.Vertical)
        self.plotSplitter.addWidget(self.mapWidget)
        self.plotSplitter.addWidget(self.profileWidget)
        self.plotSplitter.setSizes([500, 260])

    def setUpPlots(self) -> None:
        """Titres, axes et grilles de la carte et du profil."""
        self.mapWidget.setTitle("Sortie à vélo autour du mont Royal : la carte")
        self.mapWidget.setLabel("bottom", "Est", units="m")
        self.mapWidget.setLabel("left", "Nord", units="m")
        self.mapWidget.showGrid(x=True, y=True, alpha=0.3)
        self.profileWidget.setTitle("Le profil d'altitude")
        self.profileWidget.setLabel("bottom", "Distance parcourue", units="m")
        self.profileWidget.setLabel("left", "Altitude", units="m")
        self.profileWidget.showGrid(x=True, y=True, alpha=0.3)

    def drawTrack(self) -> None:
        """La trace sur la carte, en jaune, et le départ, un point vert."""
        self.east, self.north, self.elevation = rideTrack()
        self.mapWidget.plot(self.east, self.north, pen=pg.mkPen("y", width=3))
        self.mapWidget.plot([self.east[0]], [self.north[0]], pen=None, symbol="o", symbolSize=12,
                            symbolBrush="g")

    def lockMapAspect(self) -> None:
        """Sur la carte, un mètre vaut le même nombre de pixels vers l'est et vers le nord."""
        self.mapWidget.setAspectLocked(True)

    def drawProfile(self) -> None:
        """Le profil : l'altitude en fonction de la distance parcourue, en vert."""
        self.distance = trackDistance(self.east, self.north)
        self.profileWidget.plot(self.distance, self.elevation, pen=pg.mkPen("g", width=2))

    def exaggerateProfile(self) -> None:
        """Le profil verrouillé, un mètre d'altitude cinq fois plus haut qu'un mètre de distance."""
        self.profileWidget.setAspectLocked(True, ratio=0.2)

    def zoomByRectangle(self) -> None:
        """Le zoom par rectangle sur la carte, réglé sur sa zone visible, la seule à le connaître."""
        plotItem = self.mapWidget.getPlotItem()
        viewBox = plotItem.getViewBox()
        viewBox.setMouseMode(pg.ViewBox.RectMode)

    def replaceAxesByScale(self) -> None:
        """Cache les axes de la carte, et les remplace par une barre de 500 m en bas à droite."""
        self.mapWidget.hideAxis("left")
        self.mapWidget.hideAxis("bottom")
        self.scaleBar = pg.ScaleBar(size=500, suffix="m", offset=(-20, -20))
        self.scaleBar.setParentItem(self.mapWidget.getViewBox())

    def zoomOnClimb(self) -> None:
        """Le profil libéré et cadré sur la montée ; son altitude s'ajuste à la portion visible."""
        self.profileWidget.setAspectLocked(False)
        self.profileWidget.setXRange(1500, 3500, padding=0)
        self.profileWidget.setAutoVisible(y=True)

    def constrainProfileMouse(self) -> None:
        """Sur le profil, la souris n'agit que sur la distance, entre le départ et l'arrivée."""
        self.profileWidget.setMouseEnabled(x=True, y=False)
        self.profileWidget.setLimits(xMin=0, xMax=self.distance[-1], minXRange=100)

    def connectZoomControls(self) -> None:
        """Relie les deux boutons et la case à cocher du zoom à leur slot."""
        self.wholeButton.clicked.connect(self.showWholeRide)
        self.climbButton.clicked.connect(self.showClimb)
        self.altitudeCheck.toggled.connect(self.setAltitudeFollowing)

    @Slot()
    def showWholeRide(self) -> None:
        """Cadre une fois la carte et le profil sur toute la sortie, puis rend à l'altitude son ajustement choisi."""
        self.mapWidget.autoRange()
        self.profileWidget.autoRange()
        self.profileWidget.enableAutoRange(axis="y", enable=self.altitudeCheck.isChecked())

    @Slot()
    def showClimb(self) -> None:
        """Cadre le profil sur la montée, de 1,5 à 3,5 km."""
        self.profileWidget.setXRange(1500, 3500, padding=0)

    @Slot(bool)
    def setAltitudeFollowing(self, enabled: bool) -> None:
        """Active ou coupe l'ajustement automatique de l'altitude du profil."""
        self.profileWidget.enableAutoRange(axis="y", enable=enabled)

    def connectDisplayControls(self) -> None:
        """Relie les deux cases à cocher et la liste déroulante des modes d'affichage à leur slot."""
        self.axesCheck.toggled.connect(self.setMapAxesVisible)
        self.rectangleCheck.toggled.connect(self.setRectangleZoom)
        self.exaggerationCombo.currentIndexChanged.connect(self.setExaggeration)

    @Slot(bool)
    def setMapAxesVisible(self, visible: bool) -> None:
        """Montre ou cache les axes de la carte ; la barre d'échelle les remplace quand ils sont cachés."""
        self.mapWidget.showAxis("left", visible)
        self.mapWidget.showAxis("bottom", visible)
        self.scaleBar.setVisible(not visible)

    @Slot(bool)
    def setRectangleZoom(self, enabled: bool) -> None:
        """Choisit le geste de la souris sur la carte : tracer un rectangle, ou glisser."""
        if enabled:
            self.mapWidget.getViewBox().setMouseMode(pg.ViewBox.RectMode)
        else:
            self.mapWidget.getViewBox().setMouseMode(pg.ViewBox.PanMode)

    @Slot()
    def setExaggeration(self) -> None:
        """Verrouille le profil au ratio choisi dans la liste, ou le libère."""
        ratio = self.exaggerationCombo.currentData()
        if ratio is None:
            self.profileWidget.setAspectLocked(False)
        else:
            self.profileWidget.setAspectLocked(True, ratio=ratio)

    def createTimer(self) -> None:
        """Crée le minuteur de la lecture, et relie son signal timeout au slot qui avance le cycliste."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advanceRider)

    def startRide(self) -> None:
        """Le cycliste au départ, une cible sur la carte et une ligne sur le profil ; la lecture démarre."""
        self.rider = pg.TargetItem(pos=(self.east[0], self.north[0]), size=22, movable=False,
                                   pen=pg.mkPen("w", width=2))
        self.mapWidget.addItem(self.rider)
        self.riderLine = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen("w", width=2))
        self.profileWidget.addItem(self.riderLine)
        self.rideIndex = 0
        self.following = True
        self.centerMapOn(self.east[0], self.north[0], 1200)
        self.timer.start(50)

    def centerMapOn(self, x: float, y: float, width: float) -> None:
        """Cadre la carte sur le point (x, y), sur une largeur et une hauteur de `width` mètres."""
        self.mapWidget.setRange(xRange=(x - width / 2, x + width / 2), yRange=(y - width / 2, y + width / 2),
                                padding=0)

    @Slot()
    def advanceRider(self) -> None:
        """Avance le cycliste d'une position ; si la carte le suit, la recentre sur lui sans changer le zoom."""
        self.rideIndex = (self.rideIndex + 1) % self.distance.shape[0]
        x = self.east[self.rideIndex]
        y = self.north[self.rideIndex]
        self.rider.setPos(x, y)
        self.riderLine.setValue(self.distance[self.rideIndex])
        if self.following:
            (left, right), (bottom, top) = self.mapWidget.viewRange()
            self.centerMapOn(x, y, min(right - left, top - bottom))

    def connectRideControls(self) -> None:
        """Relie le changement d'étendue fait à la souris, et les deux boutons de la lecture, à leur slot."""
        self.mapWidget.sigRangeChangedManually.connect(self.stopFollowing)
        self.recenterButton.clicked.connect(self.followRider)
        self.pauseButton.clicked.connect(self.togglePause)

    @Slot()
    def stopFollowing(self) -> None:
        """Cesse de recentrer la carte sur le cycliste."""
        self.following = False

    @Slot()
    def followRider(self) -> None:
        """Recentre la carte sur le cycliste, sur 1200 m, et la fait suivre de nouveau."""
        self.following = True
        self.centerMapOn(self.east[self.rideIndex], self.north[self.rideIndex], 1200)

    @Slot()
    def togglePause(self) -> None:
        """Arrête ou relance la lecture, et change le texte du bouton."""
        if self.timer.isActive():
            self.timer.stop()
            self.pauseButton.setText("Reprendre")
        else:
            self.timer.start(50)
            self.pauseButton.setText("Pause")

    def _exploreZoom(self) -> None:
        """Connecte les contrôles du zoom, puis les révèle."""
        self.connectZoomControls()
        self.controls.reveal(self.wholeButton, self.climbButton, self.altitudeCheck)

    def _exploreDisplay(self) -> None:
        """Connecte les contrôles des modes d'affichage, puis les révèle."""
        self.connectDisplayControls()
        self.controls.reveal(self.axesCheck, self.rectangleCheck, self.exaggerationCombo)

    def _exploreRide(self) -> None:
        """Connecte les contrôles de la lecture, puis les révèle."""
        self.connectRideControls()
        self.controls.reveal(self.pauseButton, self.recenterButton)

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : la carte et le profil",
                explanation=(
                    "Rien de nouveau dans PyQtGraph : deux widgets du graphique (notion 1.1), "
                    "chacun avec son titre, les titres de ses axes et sa grille. Un séparateur de "
                    "Qt (<code>QSplitter</code>) les range l'un sous l'autre : "
                    "<code>addWidget()</code> y ajoute un widget, et <code>setSizes()</code> "
                    "donne leurs hauteurs de départ, en pixels. La poignée entre les deux règle "
                    "leur partage à la souris. Le guide place le séparateur dans la zone de "
                    "contenu, comme tout widget."
                    "<br><br>La notion 1.5 rangeait plusieurs graphiques dans un seul widget. Ici, "
                    "chaque graphique a le sien. L'étape « Le widget, le graphique et la zone "
                    "visible » éclaire cette différence."
                    "<br><br><i>Pour l'exemple</i> : une sortie à vélo autour du mont Royal, à "
                    "Montréal. En haut, la carte, la position vue du ciel. En bas, le profil, "
                    "l'altitude en fonction de la distance parcourue."
                ),
                run=self.setUpPlots,
                codeSource=(self.createPlotWidgets, self.setUpPlots),
                references=[("QSplitter", qtDocUrl("QtWidgets", "QSplitter"))],
            ),
            QStepWalkthrough.Step(
                title="La trace sur la carte",
                explanation=(
                    "Une application de téléphone note la position du vélo toutes les 2 s : c'est "
                    "la <b>trace</b>. <code>rideTrack()</code> rend trois tableaux de 720 "
                    "valeurs, soit 24 min de sortie : l'est et le nord, en mètres, comptés depuis "
                    "le sommet, puis l'altitude. Ils sont gardés dans <code>self.east</code>, "
                    "<code>self.north</code> et <code>self.elevation</code>."
                    "<br><br>La carte montre le nord en fonction de l'est : le parcours vu du ciel. "
                    "Le départ est un nuage d'un seul point, vert (notion 1.2). "
                    "<code>plot()</code> attend des tableaux : un seul point se donne par deux "
                    "listes d'un élément, <code>[self.east[0]]</code> et "
                    "<code>[self.north[0]]</code>."
                    "<br><br>À gauche, le parcours remplit tout le widget. Chaque axe est étiré à "
                    "sa guise : la carte est déformée, comme le montre l'étape suivante."
                    "<br><br><i>Pour l'exemple</i> : la trace est simulée, en coordonnées "
                    "polaires. Chaque position est à la distance <code>radius</code> du sommet, "
                    "dans la direction de son angle : <code>radius * np.cos(angles)</code> vers "
                    "l'est, <code>radius * np.sin(angles)</code> vers le nord. Les angles font le "
                    "tour, de 0 à 2π. Le facteur 0,75 aplatit le parcours du nord au sud. Le rayon "
                    "varie : <code>450 * np.cos(angles)</code> l'allonge de 450 m à l'est et le "
                    "raccourcit de 450 m à l'ouest, où la route passe plus près du sommet. Au "
                    "nord s'ajoutent des virages (<code>bends</code>), les oscillations rapides "
                    "de <code>np.sin(11 * angles)</code>. <code>np.clip(valeurs, 0, None)</code> "
                    "remplace par 0 chaque valeur négative ; <code>None</code> veut dire « sans "
                    "borne supérieure ». Le sinus est positif au nord et négatif au sud : les "
                    "virages ne paraissent qu'au nord, adoucis par le carré. L'altitude est une colline en cloche, "
                    "185 m au-dessus d'une plaine à 45 m : <code>east ** 2 + north ** 2</code> "
                    "est le carré de la distance au sommet, et 650 m règle la largeur de la "
                    "colline."
                ),
                run=self.drawTrack,
                codeSource=(rideTrack, self.drawTrack),
                references=[("numpy.clip", numpyDocUrl("clip"))],
            ),
            QStepWalkthrough.Step(
                title="Une carte qui ne ment pas : la même échelle",
                explanation=(
                    "Par défaut, la zone visible étire chaque axe pour remplir le widget : un mètre "
                    "vers l'est n'a pas la même longueur à l'écran qu'un mètre vers le nord. Une "
                    "carte ainsi déformée ment sur les distances et les angles. "
                    "<code>setAspectLocked(True)</code> verrouille les proportions : un mètre vaut "
                    "le même nombre de pixels sur les deux axes. Pour garder toute la trace, "
                    "l'étendue s'élargit sur l'un des deux axes, celui qui a de la place de trop : "
                    "ici, l'est, car le widget est plus large que haut."
                    "<br><br><i>Essai</i> : tirer la poignée du séparateur, entre la carte et le "
                    "profil. La carte change de taille, mais garde ses proportions."
                ),
                run=self.lockMapAspect,
                references=[("ViewBox.setAspectLocked", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setAspectLocked"))],
            ),
            QStepWalkthrough.Step(
                title="Le profil d'altitude",
                explanation=(
                    "Le profil montre l'altitude en fonction de la <b>distance parcourue</b>, pas "
                    "de l'est. <code>trackDistance()</code> la calcule avec numpy :"
                    "<ul>"
                    "<li><code>np.diff(east)</code> rend les écarts entre positions voisines, une "
                    "valeur de moins que le tableau ;</li>"
                    "<li><code>np.hypot(a, b)</code> rend √(a² + b²) pour chaque paire de "
                    "valeurs, ici les écarts vers l'est et vers le nord : la longueur de chaque "
                    "pas ;</li>"
                    "<li><code>np.cumsum(steps)</code> rend les sommes cumulées : la distance "
                    "après chaque pas ;</li>"
                    "<li><code>np.concatenate(tableaux)</code> met bout à bout les tableaux d'un "
                    "tuple, d'où les doubles parenthèses. Ici, <code>[0.0]</code> devant, la "
                    "distance au départ : le résultat a autant de valeurs que la trace.</li>"
                    "</ul>"
                    "La sortie fait environ 6,3 km. L'axe l'écrit en kilomètres : PyQtGraph ajoute "
                    "le préfixe à l'unité (notion 1.1)."
                ),
                run=self.drawProfile,
                codeSource=(trackDistance, self.drawProfile),
                references=[
                    ("numpy.diff", numpyDocUrl("diff")),
                    ("numpy.hypot", numpyDocUrl("hypot")),
                    ("numpy.cumsum", numpyDocUrl("cumsum")),
                    ("numpy.concatenate", numpyDocUrl("concatenate")),
                ],
            ),
            QStepWalkthrough.Step(
                title="L'exagération verticale : le piège du ratio",
                explanation=(
                    "À la même échelle que la distance, une montée de 130 m sur 3 km serait une "
                    "ligne presque plate. Un profil d'altitude s'exagère donc en hauteur, d'un "
                    "<b>facteur d'exagération</b> choisi et annoncé, ici 5. "
                    "<code>setAspectLocked(True, ratio=…)</code> verrouille les proportions avec "
                    "un <code>ratio</code> choisi. Sans <code>ratio</code>, comme pour la carte, "
                    "il vaut 1 : la même échelle."
                    "<br><br>Le piège : <code>ratio</code> est le nombre de pixels d'un mètre "
                    "horizontal, divisé par le nombre de pixels d'un mètre vertical. Pour qu'un "
                    "mètre d'altitude prenne cinq fois plus de pixels, <code>ratio</code> vaut "
                    "1/5, soit 0,2. Avec <code>ratio=5</code>, le relief serait écrasé cinq "
                    "fois, et non exagéré."
                    "<br><br>Avant cette étape, le profil était étiré pour remplir le widget. À "
                    "la taille habituelle de la fenêtre, cela l'exagérait déjà environ dix fois : "
                    "une exagération ni choisie, ni annoncée, qui change avec la taille de la "
                    "fenêtre. À gauche, le profil exagéré cinq fois est donc moins haut. L'étendue "
                    "s'élargit sur l'axe qui a de la place de trop, comme pour la carte : ici, la "
                    "distance."
                ),
                run=self.exaggerateProfile,
                references=[("ViewBox.setAspectLocked", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setAspectLocked"))],
            ),
            QStepWalkthrough.Step(
                title="Le widget, le graphique et la zone visible",
                explanation=(
                    "La <b>vue</b>, dans cette notion, est ce que montre un graphique : son "
                    "étendue, ses proportions, ses règles graduées. Trois objets s'emboîtent pour "
                    "la produire, chacun avec son rôle :"
                    "<ul>"
                    "<li>le <b>widget du graphique</b> (<code>PlotWidget</code>) est un widget "
                    "Qt : il se range dans un layout ou un séparateur, et il contient un seul "
                    "graphique ;</li>"
                    "<li>le <b>graphique</b> (<code>PlotItem</code>) porte le titre, les axes, "
                    "la légende et les éléments graphiques. Ce n'est pas un widget, mais un élément "
                    "graphique dessiné dans le widget. C'est pourquoi la grille de la notion 1.5 "
                    "en range plusieurs dans un seul widget ;</li>"
                    "<li>la <b>zone visible</b> (<code>ViewBox</code>), au centre du graphique, "
                    "décide de ce que fait la souris et de l'<b>étendue</b> montrée : "
                    "l'intervalle visible sur chaque axe.</li>"
                    "</ul>"
                    "<code>getPlotItem()</code> rend le graphique d'un widget, et "
                    "<code>getViewBox()</code> la zone visible d'un graphique. Le code fait ici "
                    "le chemin complet, du widget au graphique puis à la zone visible, pour "
                    "montrer l'emboîtement."
                    "<br><br>Les relais :"
                    "<ul>"
                    "<li>le widget relaie <b>toutes</b> les méthodes du graphique, "
                    "<code>getViewBox()</code> comprise. La suite l'appelle donc directement sur "
                    "le widget ;</li>"
                    "<li>le graphique ne relaie qu'une <b>liste</b> de méthodes de sa zone "
                    "visible : celles de l'étendue, des proportions et de la souris par axe, comme "
                    "<code>setAspectLocked()</code>. La page de <code>PlotItem</code> donne cette "
                    "liste ;</li>"
                    "<li><code>setMouseMode()</code> n'en fait pas partie : appelée sur le widget, "
                    "elle lèverait une <code>AttributeError</code>. Elle passe par "
                    "<code>getViewBox()</code>.</li>"
                    "</ul>"
                    "<br><br><code>setMouseMode()</code> choisit le geste du bouton gauche. "
                    "<code>pg.ViewBox.RectMode</code> : glisser trace un rectangle, et la carte "
                    "s'agrandit sur lui. <code>pg.ViewBox.PanMode</code>, le défaut, déplace les "
                    "données."
                    "<br><br><i>Essai</i> : tracer un rectangle autour des virages, puis revenir "
                    "par le bouton « A » (notion 1.1)."
                ),
                run=self.zoomByRectangle,
                references=[
                    ("PlotWidget.getPlotItem", pyqtgraphDocUrl("api_reference/widgets/plotwidget",
                                                               "PlotWidget.getPlotItem")),
                    ("PlotItem.getViewBox", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.getViewBox")),
                    ("ViewBox.setMouseMode", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setMouseMode")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une carte sans axes, avec une barre d'échelle",
                explanation=(
                    "<code>hideAxis(côté)</code>, une méthode du graphique, cache la règle graduée "
                    "d'un côté, <code>\"left\"</code> ou <code>\"bottom\"</code> : ses graduations, "
                    "son titre et les lignes de sa grille. Attention aux deux sens du mot "
                    "« axe ». Les méthodes des règles graduées nomment un côté du graphique. "
                    "Celles de la zone visible nomment une direction, <code>x</code> ou "
                    "<code>y</code>, comme les étapes suivantes."
                    "<br><br>Une carte se lit mieux sans axes. Mais sans eux, elle perd toute "
                    "mesure : une <b>barre d'échelle</b> la rend."
                    "<br><br><code>pg.ScaleBar(size=500, suffix=\"m\", offset=…)</code> est une "
                    "barre qui représente 500 m, avec son texte « 500 m ». Sa longueur en pixels "
                    "suit le zoom. <code>offset=(-20, -20)</code> la place à 20 pixels du bord "
                    "droit et du bord du bas, comme la légende (notion 1.1) : un nombre négatif "
                    "compte depuis la droite ou le bas."
                    "<br><br>Deux façons de placer un élément :"
                    "<ul>"
                    "<li><code>addItem()</code> le place parmi les données, en unités des axes : "
                    "il bouge et grandit avec le zoom, comme une courbe ;</li>"
                    "<li><code>setParentItem(parent)</code>, une méthode de tout élément "
                    "graphique, en fait l'enfant d'un autre élément. Enfant de la zone visible, "
                    "rendue par <code>getViewBox()</code>, la barre se place en pixels de la zone "
                    "visible : elle reste dans son coin, quel que soit le zoom.</li>"
                    "</ul>"
                    "La notion 2.3 reviendra sur les parents. La barre est gardée dans "
                    "<code>self.scaleBar</code> : une étape « À vous » la cachera quand les axes "
                    "reviendront."
                    "<br><br><i>Essai</i> : zoomer sur la carte. La barre garde sa place, mais "
                    "s'allonge."
                ),
                run=self.replaceAxesByScale,
                references=[
                    ("PlotItem.hideAxis", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.hideAxis")),
                    ("ScaleBar", pyqtgraphDocUrl("api_reference/graphicsItems/scalebar", "ScaleBar")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Cadrer par le code, un axe à la fois",
                explanation=(
                    "<b>Cadrer</b>, c'est choisir l'étendue d'un axe. Chaque axe, x ou y, a son "
                    "propre <b>ajustement automatique</b> : actif, il cadre l'axe sur les données "
                    "à chaque changement. Au départ, il est actif sur les deux axes."
                    "<ul>"
                    "<li><code>setAspectLocked(False)</code> libère d'abord le profil : "
                    "verrouillés, ses deux axes ne se cadrent plus séparément ;</li>"
                    "<li><code>setXRange()</code> (notion 1.2) cadre la distance sur la montée, de "
                    "1,5 à 3,5 km. Il coupe l'ajustement automatique de l'axe x seulement : celui "
                    "de l'altitude reste actif ;</li>"
                    "<li><code>setAutoVisible(y=True)</code> ajuste l'altitude aux seules données "
                    "visibles. Il n'active pas l'ajustement : il change seulement les données "
                    "qu'il regarde. Sans lui, l'altitude resterait cadrée sur toute la sortie, de "
                    "57 à 184 m.</li>"
                    "</ul>"
                    "À gauche, la montée remplit toute la hauteur du profil, de 104 à 180 m "
                    "environ."
                ),
                run=self.zoomOnClimb,
                references=[
                    ("ViewBox.setXRange", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setXRange")),
                    ("ViewBox.setAutoVisible", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setAutoVisible")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La souris sur un seul axe, entre des bornes",
                explanation=(
                    "<code>setMouseEnabled(x=True, y=False)</code> réserve la souris à l'axe "
                    "horizontal : la molette et le glisser n'agissent plus que sur la distance. "
                    "L'altitude suit l'ajustement de l'étape précédente."
                    "<br><br><code>setLimits()</code> borne l'étendue. "
                    "<code>xMin</code> et <code>xMax</code> sont les limites de l'axe x : "
                    "jamais avant le départ, ni après l'arrivée. "
                    "<code>self.distance[-1]</code> est la distance totale, la dernière valeur du "
                    "tableau. <code>minXRange</code> est la largeur minimale : jamais moins de "
                    "100 m."
                    "<br><br><i>Essai</i> : faire tourner la molette sur le profil. Seule la "
                    "distance s'agrandit, et l'altitude se recadre. Puis glisser le profil vers "
                    "la droite : il s'arrête net au départ, à 0 km. Agrandir encore : la molette "
                    "ne descend pas sous 100 m de large."
                ),
                run=self.constrainProfileMouse,
                references=[
                    ("ViewBox.setMouseEnabled", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setMouseEnabled")),
                    ("ViewBox.setLimits", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setLimits")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : zoomer par le code",
                explanation=(
                    "Trois contrôles paraissent sous le profil : les boutons <code>wholeButton</code>, "
                    "« Tout voir », et <code>climbButton</code>, « La montée », puis la case à "
                    "cocher <code>altitudeCheck</code>, cochée au départ. "
                    "<code>connectZoomControls()</code> les relie à leur slot."
                    "<br><br>Nouveau : deux façons d'ajuster l'étendue aux données."
                    "<ul>"
                    "<li><code>autoRange()</code> cadre les deux axes sur toutes les données, "
                    "<b>une seule fois</b> ;</li>"
                    "<li><code>enableAutoRange(axis=\"y\", enable=True)</code> active "
                    "l'ajustement automatique de l'axe y, un mode qui dure. "
                    "<code>enable=False</code> le coupe. Sans <code>axis</code>, il agit sur les "
                    "deux axes : c'est ce que fait le bouton « A » de PyQtGraph.</li>"
                    "</ul>"
                    "<br><br>Piège : comme tout cadrage par le code, <code>autoRange()</code> "
                    "<b>coupe</b> l'ajustement automatique des deux axes. Sans la dernière ligne "
                    "de <code>showWholeRide()</code>, l'altitude cesserait de s'ajuster, case "
                    "cochée ou non. Cette ligne lui rend l'ajustement choisi par la case : "
                    "<code>isChecked()</code> rend <code>True</code> si elle est cochée."
                    "<br><br><code>setAltitudeFollowing()</code> reçoit l'état de la case et le "
                    "passe à <code>enableAutoRange(axis=\"y\", enable=…)</code> : décochée, "
                    "l'altitude ne s'ajuste plus."
                    "<br><br>Cliquer « La montée », puis zoomer à la molette sur le profil, case "
                    "cochée : l'altitude se recadre. Décocher la case et zoomer encore : "
                    "l'altitude reste figée. Cliquer « Tout voir »."
                ),
                run=self._exploreZoom,
                codeSource=(self.connectZoomControls, self.showWholeRide, self.showClimb,
                            self.setAltitudeFollowing),
                references=[
                    ("ViewBox.autoRange", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.autoRange")),
                    ("ViewBox.enableAutoRange", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.enableAutoRange")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : les modes d'affichage",
                explanation=(
                    "Trois contrôles de plus. Chacun défait, à volonté, un geste d'une étape "
                    "précédente :"
                    "<ul>"
                    "<li>la case <code>axesCheck</code>, « Axes de la carte », décochée au "
                    "départ. Nouveau : <code>showAxis(côté, visible)</code> montre la règle graduée de ce "
                    "côté si <code>visible</code> vaut <code>True</code>, et la cache sinon. La "
                    "barre d'échelle se cache quand les axes paraissent ;</li>"
                    "<li>la case <code>rectangleCheck</code>, « Zoom par rectangle sur la "
                    "carte », cochée au départ. Cochée, glisser sur la carte trace un rectangle ; "
                    "décochée, glisser déplace la carte ;</li>"
                    "<li>la liste déroulante <code>exaggerationCombo</code>, « Exagération du "
                    "profil », sur « libre » au départ. Chaque choix porte une valeur, que <code>currentData()</code> rend, "
                    "et son signal <code>currentIndexChanged</code> est émis quand le choix change. "
                    "La valeur est le <code>ratio</code> à passer : <code>None</code> pour "
                    "« libre », qui libère le profil, puis 1 ; 0,2 ; 0,1 pour × 1, × 5 et "
                    "× 10.</li>"
                    "</ul>"
                    "Verrouillé, le profil ne peut plus cadrer son altitude seul : ses deux axes "
                    "bougent ensemble."
                    "<br><br>Choisir « × 1 » : le vrai relief, presque plat. Puis « × 10 ». Puis "
                    "« libre » : le profil remplit de nouveau le widget. Montrer les axes de la "
                    "carte, puis les cacher."
                ),
                run=self._exploreDisplay,
                codeSource=(self.connectDisplayControls, self.setMapAxesVisible, self.setRectangleZoom,
                            self.setExaggeration),
                references=[
                    ("PlotItem.showAxis", pyqtgraphDocUrl(_PlotItemPage, "PlotItem.showAxis")),
                    ("ViewBox.setMouseMode", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setMouseMode")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Rejouer la sortie : la carte suit le cycliste",
                explanation=(
                    "Le cycliste repart. Rien de nouveau dans ce qui le fait avancer :"
                    "<ul>"
                    "<li><code>createTimer()</code> est affichée pour être lue : elle s'est "
                    "exécutée une seule fois, à la création de la page, comme à la notion 1.4. À "
                    "cette étape s'exécute <code>startRide()</code> ;</li>"
                    "<li>le cycliste est une cible (<code>TargetItem</code>, notion 1.3) sur la "
                    "carte, et une ligne (<code>InfiniteLine</code>, notion 1.3) sur le profil, "
                    "déplacée par son mutateur <code>setValue()</code> ;</li>"
                    "<li>le minuteur appelle <code>advanceRider()</code> toutes les 50 ms. "
                    "Chaque appel avance d'une position, soit 2 s de sortie : la lecture va "
                    "40 fois plus vite que le vélo. Le reste de la division (<code>%</code>) par "
                    "<code>self.distance.shape[0]</code>, le nombre de positions, ramène l'indice "
                    "à 0 à la fin de la trace : la sortie recommence ;</li>"
                    "<li><code>self.following</code> dit si la carte suit le cycliste. Il vaut "
                    "<code>True</code> au départ.</li>"
                    "</ul>"
                    "Nouveau : <code>viewRange()</code> rend l'étendue, "
                    "<code>[[gauche, droite], [bas, haut]]</code>, en unités des axes. "
                    "<code>(left, right), (bottom, top) = …</code> range ces quatre nombres dans "
                    "quatre variables d'un coup. Et <code>setRange(xRange=…, yRange=…)</code> "
                    "cadre les deux axes d'un seul appel. Avec des proportions verrouillées, "
                    "<code>setXRange()</code> puis <code>setYRange()</code> se contrediraient : "
                    "pour garder les proportions, le second élargirait de nouveau l'étendue que le "
                    "premier venait de fixer."
                    "<br><br><code>centerMapOn()</code> demande un carré de <code>width</code> "
                    "mètres autour du cycliste. Les proportions verrouillées l'élargissent sur "
                    "l'axe qui a de la place de trop, sans le déformer. La plus petite des deux "
                    "dimensions visibles est donc le côté de ce carré : "
                    "<code>advanceRider()</code> la redonne, et le zoom ne change pas. Au départ, "
                    "la carte se rapproche : un carré de 1200 m."
                    "<br><br>Quand on quitte cette notion, le guide arrête le minuteur, et le "
                    "relance au retour."
                ),
                run=self.startRide,
                codeSource=(self.createTimer, self.startRide, self.centerMapOn, self.advanceRider),
                references=[
                    ("ViewBox.viewRange", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.viewRange")),
                    ("ViewBox.setRange", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox.setRange")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : reprendre la main",
                explanation=(
                    "Une carte de téléphone suit le cycliste, jusqu'à ce qu'on la déplace. Elle "
                    "propose alors de la recentrer. Pour en faire autant, il faut savoir <b>qui</b> "
                    "a changé l'étendue."
                    "<br><br>Nouveau : la zone visible émet deux signaux."
                    "<ul>"
                    "<li><code>sigRangeChanged</code> est émis à chaque changement de l'étendue, "
                    "quelle qu'en soit la cause : la souris, le code, ou un widget redimensionné. "
                    "Relié ici, il arrêterait le suivi au premier recentrage du minuteur ;</li>"
                    "<li><code>sigRangeChangedManually</code> est émis seulement quand "
                    "l'utilisateur change l'étendue : molette, glisser ou rectangle. Jamais par "
                    "<code>setRange()</code>, ni par un widget redimensionné.</li>"
                    "</ul>"
                    "Le graphique relaie ces signaux, et le widget ceux de son graphique. "
                    "<code>self.mapWidget.sigRangeChangedManually</code> est celui du graphique de "
                    "la carte. Le graphique l'émet aussi quand on clique son bouton « A » : un "
                    "geste de l'utilisateur, lui aussi. Son argument, les deux axes que la souris "
                    "peut changer, ne sert pas ici."
                    "<br><br><code>connectRideControls()</code> relie ce signal à "
                    "<code>stopFollowing()</code>. Deux boutons paraissent : "
                    "<code>recenterButton</code>, « Recentrer », relié à "
                    "<code>followRider()</code>, et <code>pauseButton</code>, « Pause », comme à la "
                    "notion 1.4."
                    "<br><br>« Tout voir », lui, appelle <code>autoRange()</code> par le code : le "
                    "suivi continue, et au tic suivant la carte se recentre sur le cycliste, au "
                    "nouveau zoom."
                    "<br><br>Faire tourner la molette sur la carte, ou y tracer un rectangle : elle "
                    "cesse de suivre. Cliquer « Recentrer ». Tirer la poignée du séparateur : la "
                    "carte change d'étendue, mais continue de suivre. Cliquer « Tout voir » : elle "
                    "suit toujours."
                ),
                run=self._exploreRide,
                codeSource=(self.connectRideControls, self.stopFollowing, self.followRider, self.togglePause),
                references=[("ViewBox.sigRangeChangedManually", pyqtgraphDocUrl(_ViewBoxPage, "ViewBox"))],
            ),
        ]
