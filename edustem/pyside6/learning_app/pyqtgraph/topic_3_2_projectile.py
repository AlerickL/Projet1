"""Notion 3.2 : une trajectoire 3D, un tir dévié par le vent.

Contexte : un projectile part du sol avec une vitesse et un angle donnés. Un
vent latéral le pousse sur le côté, selon y, pendant que la gravité le
ramène au sol. La trajectoire sort du plan vertical du tir : une vraie
courbe 3D, qu'un graphique plan ne montrerait pas en entier.

Étapes couvertes : un récapitulatif de la scène (notion 3.1), la caméra
centrée sur le tir, la position à un instant (formules du tir), la
trajectoire (`GLLinePlotItem`), des positions échantillonnées, une
annotation au sommet, une flèche 3D assemblée d'un cylindre et d'un cône
(`MeshData`, `GLMeshItem`), couchée et placée par `rotate()` et
`translate()`, la mise à jour en place des éléments 3D, puis trois
sélecteurs numériques pour la vitesse, l'angle et le vent.

Chaque étape est une méthode de `QTopicProjectileTab` : elle lit et modifie
directement `self.view`.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import Slot
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import numpyDocUrl, pyqtgraphDocUrl, qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetGLView
from .topic_3_1_scene import createView, nameAxes

_GLPage = "api_reference/3dgraphics"


def flightTime(speed: float, angle: float) -> float:
    """La durée du vol, du départ au retour au sol (z = 0), en secondes ; l'angle en degrés."""
    return 2 * speed * np.sin(np.radians(angle)) / 9.8


def positionAt(t: float | np.ndarray, speed: float, angle: float,
               wind: float) -> tuple[float | np.ndarray, float | np.ndarray, float | np.ndarray]:
    """La position (x, y, z) : x la portée, y la dérive due au vent, z la hauteur.

    `t` est un instant en secondes, ou un tableau d'instants de forme (n,) ;
    x, y et z sont des réels, ou des tableaux de cette forme.
    """
    theta = np.radians(angle)
    x = speed * np.cos(theta) * t
    y = 0.5 * wind * t ** 2
    z = speed * np.sin(theta) * t - 0.5 * 9.8 * t ** 2
    return x, y, z


def trajectory(speed: float, angle: float, wind: float, pointCount: int) -> np.ndarray:
    """La trajectoire en `pointCount` instants également espacés.

    Rend un tableau de réels de forme (pointCount, 3) : une rangée (x, y, z)
    par instant.
    """
    times = np.linspace(0, flightTime(speed, angle), pointCount)
    x, y, z = positionAt(times, speed, angle, wind)
    return np.column_stack((x, y, z))


def apex(speed: float, angle: float, wind: float) -> tuple[float, float, float]:
    """Le sommet de la trajectoire, atteint à la moitié du vol."""
    return positionAt(flightTime(speed, angle) / 2, speed, angle, wind)


class QTopicProjectileTab(QWidget):
    """Onglet de la notion 3.2 : la trajectoire d'un tir dévié par le vent.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        viewContainer, titleLabel, view: La vue 3D et son titre, créés une
            seule fois par `createView()` (notion 3.1).
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        speedSlider, angleSlider, windSlider: Les sélecteurs numériques du tir.
        trajectoryLine, samples, apexLabel, windShaft, windHead, windLabel:
            Les éléments 3D, ou None avant leur étape.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Trajectoire 3D"
    TabToolTip = "Un tir dévié par le vent : courbe, points et texte en 3D, une flèche assemblée"
    RecommendedPanelWidth = 640
    Objective = (
        "Représenter un mouvement dans l'espace : la trajectoire d'un projectile dévié par le "
        "vent, des positions échantillonnées, une annotation, une flèche 3D assemblée pour le "
        "vent, puis mettre la trajectoire à jour selon la vitesse, l'angle et le vent."
    )
    KeyConcepts = [
        "Une trajectoire soumise à deux effets, la gravité et le vent, sort du plan : la 3D "
        "devient nécessaire.",
        "La caméra tourne autour d'un point central, qu'on place au milieu des données.",
        "Une courbe 3D est un tableau à trois colonnes : une rangée (x, y, z) par point.",
        "Il n'y a pas de flèche 3D toute faite : on l'assemble avec des formes simples, puis on "
        "la tourne et la déplace.",
        "Les éléments 3D se mettent à jour en place, sans être recréés.",
    ]
    KeyApis = [
        "GLViewWidget.setCameraPosition", "GLLinePlotItem", "GLScatterPlotItem", "GLTextItem",
        "MeshData.cylinder", "GLMeshItem", "GLGraphicsItem.rotate", "GLGraphicsItem.translate",
        "GLLinePlotItem.setData",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.trajectoryLine: gl.GLLinePlotItem | None = None
        self.samples: gl.GLScatterPlotItem | None = None
        self.apexLabel: gl.GLTextItem | None = None
        self.windShaft: gl.GLMeshItem | None = None
        self.windHead: gl.GLMeshItem | None = None
        self.windLabel: gl.GLTextItem | None = None

        self.viewContainer, self.titleLabel, self.view = createView()
        self.controls = QControlPanel()
        self.speedSlider = self.controls.addSlider("Vitesse initiale", 100, 300, 250, divisor=10, suffix="m/s")
        self.angleSlider = self.controls.addSlider("Angle de tir", 20, 80, 50, suffix="°")
        self.windSlider = self.controls.addSlider("Vent", 0, 50, 20, divisor=10, suffix="m/s²")

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.viewContainer, 1)
        contentLayout.addWidget(self.controls)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Vide la scène, remet la caméra en place (voir plot_reset.py) et les contrôles."""
        self.controls.resetControls()
        resetGLView(self.view)
        self.titleLabel.setText("")
        self.trajectoryLine = None
        self.samples = None
        self.apexLabel = None
        self.windShaft = None
        self.windHead = None
        self.windLabel = None

    # -- Étapes ------------------------------------------------------------------------------------

    def setUpScene(self) -> None:
        """Titre, axes nommés et grille au sol, à l'échelle d'un tir de quelques dizaines de mètres."""
        self.titleLabel.setText("Un tir dévié par le vent")
        axes = gl.GLAxisItem()
        axes.setSize(15, 15, 15)
        self.view.addItem(axes)
        nameAxes(self.view, 17)
        grid = gl.GLGridItem()
        grid.setSize(160, 160)
        grid.setSpacing(10, 10)
        self.view.addItem(grid)

    def centerCamera(self) -> None:
        """La caméra vise le milieu du tir, et non plus l'origine."""
        self.view.setCameraPosition(pos=QVector3D(30, 8, 12), distance=60, elevation=30, azimuth=-140)

    def _formulasOnly(self) -> None:
        """Les formules sont des fonctions : rien n'est tracé à cette étape."""

    def drawTrajectory(self) -> None:
        """La trajectoire pour 20 m/s, 50° et un vent de 2 m/s², en 100 points, en jaune."""
        points = trajectory(20, 50, 2.0, 100)
        self.trajectoryLine = gl.GLLinePlotItem(pos=points, color=(1, 1, 0, 1), width=3, antialias=True)
        self.view.addItem(self.trajectoryLine)

    def addSamples(self) -> None:
        """Onze positions, également espacées dans le temps, en rouge."""
        self.samples = gl.GLScatterPlotItem(pos=trajectory(20, 50, 2.0, 11), color=(1, 0, 0, 1), size=10)
        self.view.addItem(self.samples)

    def annotateApex(self) -> None:
        """La hauteur du sommet, écrite à son emplacement."""
        top = apex(20, 50, 2.0)
        text = f"Sommet : {top[2]:.1f} m"
        self.apexLabel = gl.GLTextItem(pos=top, text=text.replace(".", ","), color=(255, 255, 255, 255))
        self.view.addItem(self.apexLabel)

    def buildWindShaft(self) -> None:
        """La hampe de la flèche du vent : un cylindre vert de 8 m, debout à l'origine."""
        shaft = gl.MeshData.cylinder(rows=1, cols=16, radius=[0.4, 0.4], length=8)
        self.windShaft = gl.GLMeshItem(meshdata=shaft, color=(0, 1, 0, 1), shader="shaded")
        self.view.addItem(self.windShaft)

    def addWindHead(self) -> None:
        """La pointe : un cône vert de 3 m, monté de 8 m pour se poser sur la hampe."""
        head = gl.MeshData.cylinder(rows=1, cols=16, radius=[1.0, 0.0], length=3)
        self.windHead = gl.GLMeshItem(meshdata=head, color=(0, 1, 0, 1), shader="shaded")
        self.windHead.translate(0, 0, 8)
        self.view.addItem(self.windHead)

    def placeWindArrow(self) -> None:
        """La flèche couchée selon +y, la direction du vent, puis placée à l'écart du tir."""
        for item in [self.windShaft, self.windHead]:
            item.rotate(-90, 1, 0, 0)
            item.translate(25, -14, 2)
        self.windLabel = gl.GLTextItem(pos=(25, -9, 5), text="Vent : 2,0 m/s²", color=(0, 255, 0, 255))
        self.view.addItem(self.windLabel)

    def setLaunch(self, speed: float, angle: float, wind: float) -> None:
        """Recalcule la trajectoire, les positions, le sommet et le vent, et les donne aux éléments existants."""
        self.trajectoryLine.setData(pos=trajectory(speed, angle, wind, 100))
        self.samples.setData(pos=trajectory(speed, angle, wind, 11))
        top = apex(speed, angle, wind)
        self.apexLabel.setData(pos=top, text=f"Sommet : {top[2]:.1f} m".replace(".", ","))
        self.windLabel.setData(text=f"Vent : {wind:.1f} m/s²".replace(".", ","))

    def launchFaster(self) -> None:
        """Le même tir, à 25 m/s au lieu de 20 m/s."""
        self.setLaunch(25.0, 50.0, 2.0)

    def connectControls(self) -> None:
        """Relie les trois sélecteurs numériques au slot qui met le tir à jour."""
        self.speedSlider.valueChanged.connect(self.updateLaunch)
        self.angleSlider.valueChanged.connect(self.updateLaunch)
        self.windSlider.valueChanged.connect(self.updateLaunch)

    @Slot()
    def updateLaunch(self) -> None:
        """Lit la vitesse, l'angle et le vent, puis met le tir à jour."""
        speed = self.speedSlider.value() / 10
        angle = self.angleSlider.value()
        wind = self.windSlider.value() / 10
        self.setLaunch(speed, angle, wind)

    def _exploreLaunch(self) -> None:
        """Connecte les sélecteurs numériques, puis les révèle."""
        self.connectControls()
        self.controls.reveal()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : la vue, les axes, la grille",
                explanation=(
                    "Rien de nouveau : les gestes de la notion 3.1. <code>createView()</code> et "
                    "<code>nameAxes()</code> sont importées de son fichier, comme en 1.5 : "
                    "<code>from .topic_3_1_scene import createView, nameAxes</code>. "
                    "<code>createView()</code> est affichée pour rappel : elle s'est exécutée une "
                    "seule fois, à la création de la page. Les repères sont agrandis pour un tir de plusieurs "
                    "dizaines de mètres : une grille de 160 m de côté, une ligne tous les 10 m."
                    "<br><br>La caméra, elle, n'a pas encore bougé : elle vise l'origine depuis sa "
                    "distance par défaut, 10 unités, bien trop près pour cette grille."
                ),
                run=self.setUpScene,
                codeSource=(createView, self.setUpScene),
                references=[("GLGridItem", pyqtgraphDocUrl(f"{_GLPage}/glgriditem", "opengl.GLGridItem"))],
            ),
            QStepWalkthrough.Step(
                title="Centrer la caméra sur le tir",
                explanation=(
                    "La caméra tourne autour d'un point central, l'origine par défaut. Le tir, "
                    "lui, part de l'origine et s'en va vers les x positifs : autour de l'origine, "
                    "une partie sortirait du cadre. <code>pos</code> déplace le point central. Il "
                    "reçoit un <code>QVector3D(x, y, z)</code>, du module "
                    "<code>PySide6.QtGui</code>."
                    "<br><br><i>Pour l'exemple</i> : le point central est à peu près le milieu du tir. "
                    "La caméra recule à 60 m, monte à 30° et se place derrière le départ, du côté "
                    "des x et des y négatifs : la dérive due au vent se verra de biais."
                ),
                run=self.centerCamera,
                references=[
                    ("GLViewWidget", pyqtgraphDocUrl(f"{_GLPage}/glviewwidget", "opengl.GLViewWidget")),
                    ("QVector3D", qtDocUrl("QtGui", "QVector3D")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La position à un instant",
                explanation=(
                    "Le projectile part de l'origine avec une vitesse v (en m/s) et un angle θ "
                    "au-dessus du sol. Sans frottement, à l'instant t (en s) : "
                    "x = v·cos θ·t, la portée, et z = v·sin θ·t − ½·g·t², la hauteur, en "
                    "mètres, avec g = 9,8 m/s². Il retombe au sol (z = 0) après la durée "
                    "2·v·sin θ/g."
                    "<br><br>Le vent souffle selon y. On suppose qu'il pousse le projectile avec "
                    "une accélération constante a, en m/s², une simplification voulue : la "
                    "dérive vaut y = ½·a·t²."
                    "<br><br><code>flightTime()</code> rend la durée du vol, "
                    "<code>positionAt()</code> le tuple (x, y, z) à l'instant t, ou trois tableaux "
                    "si t est un tableau d'instants, comme <code>displacement()</code> à la notion "
                    "1.3. <code>wind</code> est l'accélération a. Les angles sont en degrés, "
                    "convertis par <code>np.radians()</code>. Rien n'est encore tracé."
                ),
                run=self._formulasOnly,
                codeSource=(flightTime, positionAt),
                references=[],
            ),
            QStepWalkthrough.Step(
                title="La trajectoire tracée",
                explanation=(
                    "<code>trajectory(speed, angle, wind, pointCount)</code> découpe la durée du "
                    "vol en <code>pointCount</code> instants également espacés, du départ à "
                    "l'arrivée, et calcule leurs positions d'un seul appel. "
                    "<code>np.column_stack()</code> (notion 2.5) range x, y et z en trois "
                    "colonnes : un tableau de forme (<code>pointCount</code>, 3), une rangée par "
                    "point."
                    "<br><br><i>Pour l'exemple</i> : 20 m/s, 50° et un vent de 2 m/s²."
                    "<br><br><code>gl.GLLinePlotItem</code> relie ces points par une ligne : la "
                    "courbe 3D. <code>color</code> s'écrit de 0 à 1, <code>width</code> est "
                    "l'épaisseur en pixels, et <code>antialias=True</code> adoucit les bords de "
                    "la ligne, l'anticrénelage. Sans le vent, la courbe resterait dans le plan "
                    "y = 0 : c'est la dérive qui la tord."
                ),
                run=self.drawTrajectory,
                codeSource=(trajectory, self.drawTrajectory),
                references=[
                    ("numpy.column_stack", numpyDocUrl("column_stack")),
                    ("GLLinePlotItem", pyqtgraphDocUrl(f"{_GLPage}/gllineplotitem", "opengl.GLLinePlotItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Des positions échantillonnées",
                explanation=(
                    "La même fonction, avec 11 instants au lieu de 100 : du départ à l'arrivée, "
                    "un tous les dixièmes de la durée du vol. Le sixième tombe à la moitié du vol, "
                    "au sommet. <code>gl.GLScatterPlotItem</code> (notion 3.1) reçoit tout le "
                    "tableau d'un coup."
                    "<br><br>À gauche, les points se resserrent au sommet : le projectile y va le "
                    "moins vite."
                ),
                run=self.addSamples,
                references=[("GLScatterPlotItem",
                             pyqtgraphDocUrl(f"{_GLPage}/glscatterplotitem", "opengl.GLScatterPlotItem"))],
            ),
            QStepWalkthrough.Step(
                title="Annoter le sommet",
                explanation=(
                    "La montée et la descente durent autant l'une que l'autre : le sommet est "
                    "atteint à la moitié du vol. <code>apex()</code> rend sa position. "
                    "<code>gl.GLTextItem</code> (notion 3.1) y écrit la hauteur atteinte. "
                    "<code>top[2]</code> est la troisième coordonnée du tuple, z."
                ),
                run=self.annotateApex,
                codeSource=(apex, self.annotateApex),
                references=[("GLTextItem", pyqtgraphDocUrl(f"{_GLPage}/gltextitem", "opengl.GLTextItem"))],
            ),
            QStepWalkthrough.Step(
                title="Un maillage : la hampe",
                explanation=(
                    "Il n'y a pas de flèche 3D toute faite : on la construit, une hampe puis une "
                    "pointe. Un <b>maillage</b> est une forme faite de triangles. "
                    "<code>gl.MeshData.cylinder()</code> construit celui d'un cylindre debout, de "
                    "l'origine vers le haut, le long de l'axe Z :"
                    "<ul>"
                    "<li><code>radius</code> donne le rayon à chaque bout, ici deux rayons "
                    "égaux ;</li>"
                    "<li><code>length</code> donne la hauteur ;</li>"
                    "<li><code>rows</code> est son nombre d'étages en hauteur ;</li>"
                    "<li><code>cols</code> est son nombre de facettes autour : 16 suffisent à le "
                    "faire paraître rond.</li>"
                    "</ul>"
                    "<code>gl.GLMeshItem</code> affiche un maillage. "
                    "<code>shader</code> choisit le <b>nuanceur</b>, le calcul qui donne sa couleur "
                    "à chaque point de la forme. <code>\"shaded\"</code> assombrit les faces "
                    "tournées loin de la lumière : le volume se voit."
                    "<br><br>À gauche : un cylindre vert, debout à l'origine."
                ),
                run=self.buildWindShaft,
                references=[
                    ("MeshData", pyqtgraphDocUrl(f"{_GLPage}/meshdata", "opengl.MeshData")),
                    ("GLMeshItem", pyqtgraphDocUrl(f"{_GLPage}/glmeshitem", "opengl.GLMeshItem")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La pointe : un cône",
                explanation=(
                    "Le même cylindre, avec un rayon nul au bout, donne un cône : la pointe. "
                    "<code>translate(dx, dy, dz)</code> déplace un élément 3D : le cône monte de "
                    "8 m, au bout de la hampe."
                    "<br><br>À gauche : une flèche verte, debout à l'origine."
                ),
                run=self.addWindHead,
                references=[
                    ("GLGraphicsItem.translate",
                     pyqtgraphDocUrl(f"{_GLPage}/glgraphicsitem", "opengl.GLGraphicsItem.GLGraphicsItem.translate")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Coucher et placer la flèche",
                explanation=(
                    "<code>rotate()</code> et <code>translate()</code> sont des méthodes de "
                    "<code>GLGraphicsItem</code>, la classe commune de tous les éléments 3D de "
                    "PyQtGraph : elles valent pour chacun. "
                    "<code>rotate(angle, x, y, z)</code> tourne un élément 3D de "
                    "<code>angle</code> degrés autour de l'axe (x, y, z), qui passe par "
                    "l'origine de la scène. Le sens d'un angle positif suit la <b>règle de la "
                    "main droite</b> : le pouce le long de l'axe, les doigts repliés donnent le "
                    "sens de la rotation. Autour de X, +90° envoie donc Y vers Z, et −90° envoie "
                    "Z vers Y. Ici, −90° autour de l'axe X : ce qui montait le long de Z pointe "
                    "maintenant le long de Y, la direction du vent. Le cône, monté "
                    "de 8 m, tourne avec : il reste au bout du cylindre."
                    "<br><br>En 3D, l'ordre compte : chaque <code>rotate()</code> ou "
                    "<code>translate()</code> s'ajoute aux précédents et s'applique après eux. "
                    "C'est le contraire des trois réglages indépendants de la notion 2.2 "
                    "(<code>setRotation()</code>, <code>setScale()</code>, <code>setPos()</code>). "
                    "<code>translate(25, -14, 2)</code> place "
                    "donc la flèche couchée à l'écart du tir. Un <code>GLTextItem</code>, gardé dans "
                    "<code>self.windLabel</code>, la nomme."
                ),
                run=self.placeWindArrow,
                references=[("GLGraphicsItem.rotate",
                             pyqtgraphDocUrl(f"{_GLPage}/glgraphicsitem", "opengl.GLGraphicsItem.GLGraphicsItem.rotate"))],
            ),
            QStepWalkthrough.Step(
                title="Mettre à jour en 3D",
                explanation=(
                    "Les éléments 3D se mettent à jour en place, comme les courbes 2D. "
                    "<code>setData(pos=…)</code> donne un nouveau tableau de positions à la "
                    "ligne et au nuage. <code>setData(pos=…, text=…)</code> déplace le texte et "
                    "le récrit ; <code>setData(text=…)</code> le récrit seulement. "
                    "<code>setLaunch()</code> met tout à jour, pour une vitesse, un angle et un "
                    "vent donnés."
                    "<br><br>Ici, la vitesse passe de 20 à 25 m/s. À gauche : le tir porte plus "
                    "loin, monte plus haut, et dure plus longtemps. Le vent a donc plus de temps "
                    "pour le dévier."
                ),
                run=self.launchFaster,
                codeSource=(self.setLaunch, self.launchFaster),
                references=[("GLLinePlotItem", pyqtgraphDocUrl(f"{_GLPage}/gllineplotitem",
                                                               "opengl.GLLinePlotItem"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : la vitesse, l'angle et le vent",
                explanation=(
                    "Trois sélecteurs numériques paraissent sous la vue :"
                    "<ul>"
                    "<li><code>speedSlider</code> va de 100 à 300 : divisé par 10, il donne la "
                    "vitesse initiale, de 10 à 30 m/s par pas de 0,1. Il part de 250, soit "
                    "25 m/s ;</li>"
                    "<li><code>angleSlider</code> donne l'angle de tir, de 20 à 80°, et part de "
                    "50° ;</li>"
                    "<li><code>windSlider</code> va de 0 à 50 : divisé par 10, il donne "
                    "l'accélération du vent, de 0 à 5 m/s². Il part de 20, soit 2 m/s².</li>"
                    "</ul>"
                    "Le panneau des contrôles affiche, à côté de chaque sélecteur, sa valeur "
                    "déjà divisée, avec son unité : c'est là qu'on la lit. "
                    "<code>connectControls()</code> relie leur signal <code>valueChanged</code> au "
                    "slot <code>updateLaunch()</code>, qui lit les trois valeurs et appelle "
                    "<code>setLaunch()</code> de l'étape précédente."
                    "<br><br>Plus le tir est haut, plus il dure, et plus le vent le dévie. "
                    "Comparer 30° et 70° à la même vitesse. Sans vent, la trajectoire reste dans "
                    "le plan vertical y = 0. La flèche du vent garde sa longueur : seul son texte "
                    "donne la valeur du vent. À 30 m/s et 45°, la portée dépasse 90 m : le tir "
                    "sort de la grille, qui s'arrête à 80 m de l'origine."
                ),
                run=self._exploreLaunch,
                codeSource=(self.connectControls, self.updateLaunch),
                references=[("QSlider", qtDocUrl("QtWidgets", "QSlider"))],
            ),
        ]
