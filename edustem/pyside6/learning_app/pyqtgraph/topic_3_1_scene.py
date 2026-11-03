"""Notion 3.1 : une scène 3D, sa vue et sa caméra.

Contexte : aucune donnée encore. Cette notion pose les repères d'une scène
3D, avant d'y placer des données aux notions suivantes.

Étapes couvertes : la vue 3D (`GLViewWidget`) et son titre, les axes
(`GLAxisItem`) et leurs noms (`GLTextItem`), une grille au sol
(`GLGridItem`), la caméra (distance, élévation, azimut), un premier point
dans l'espace (`GLScatterPlotItem`), puis la navigation à la souris.

Chaque étape est une méthode de `QTopicSceneTab`. `createView()` et
`nameAxes()` servent aussi aux notions suivantes, qui les importent.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..common.doc_urls import pyqtgraphDocUrl
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .plot_reset import resetGLView

_GLPage = "api_reference/3dgraphics"


def createView() -> tuple[QWidget, QLabel, gl.GLViewWidget]:
    """Crée une vue 3D et un QLabel au-dessus d'elle pour son titre, rangés dans un widget."""
    titleLabel = QLabel()
    titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
    view = gl.GLViewWidget()
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(titleLabel)
    layout.addWidget(view, 1)
    return container, titleLabel, view


def nameAxes(view: gl.GLViewWidget, length: float) -> None:
    """Écrit X, Y et Z à la distance `length` de l'origine, sur chaque axe, dans sa couleur."""
    for text, position, color in [("X", (length, 0, 0), (110, 110, 255, 255)),
                                  ("Y", (0, length, 0), (255, 255, 0, 255)),
                                  ("Z", (0, 0, length), (0, 255, 0, 255))]:
        view.addItem(gl.GLTextItem(pos=position, text=text, color=color))


class QTopicSceneTab(QWidget):
    """Onglet de la notion 3.1 : la vue, les repères et la caméra.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        viewContainer, titleLabel, view: La vue 3D et son titre, créés une
            seule fois par `createView()`.
        walkthrough: Le panneau d'étapes.
    """

    TabTitle = "Scène 3D"
    TabToolTip = "La vue, les axes et leurs noms, la grille, la caméra, un premier point"
    RecommendedPanelWidth = 640
    Objective = (
        "Poser les repères d'une scène 3D : la vue, des axes nommés, une grille au sol, et une "
        "caméra décrite par trois nombres. Puis y placer un premier point et naviguer à la souris."
    )
    KeyConcepts = [
        "Une scène 3D vide n'a aucun repère de distance : les axes et la grille en donnent.",
        "La caméra tourne autour d'un point central. Distance, élévation et azimut suffisent à "
        "décrire n'importe quel point de vue.",
        "En 3D, une position est un triplet (x, y, z) ; plusieurs positions forment un tableau à "
        "trois colonnes.",
        "La souris fait tourner, zoomer et déplacer la vue, sans code à écrire.",
    ]
    KeyApis = [
        "GLViewWidget", "GLAxisItem", "GLTextItem", "GLGridItem", "GLViewWidget.setCameraPosition",
        "GLScatterPlotItem",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.viewContainer, self.titleLabel, self.view = createView()

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )
        createSplitterLayout(self, self.viewContainer, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Vide la scène, remet la caméra en place (voir plot_reset.py) et efface le titre."""
        resetGLView(self.view)
        self.titleLabel.setText("")

    # -- Étapes ------------------------------------------------------------------------------------

    def _viewAlreadyCreated(self) -> None:
        """La vue est créée avec la page, par createView() : rien à faire à cette étape."""

    def setViewTitle(self) -> None:
        """Le titre, dans le QLabel au-dessus de la vue."""
        self.titleLabel.setText("Une scène 3D et ses repères")

    def addAxes(self) -> None:
        """Les trois axes, longs de 5 unités, partant de l'origine."""
        axes = gl.GLAxisItem()
        axes.setSize(5, 5, 5)
        self.view.addItem(axes)

    def addAxisNames(self) -> None:
        """Le nom de chaque axe, un peu au-delà de son extrémité."""
        nameAxes(self.view, 5.5)

    def addGrid(self) -> None:
        """Une grille au sol, de 10 × 10 unités, une ligne par unité."""
        grid = gl.GLGridItem()
        grid.setSize(10, 10)
        grid.setSpacing(1, 1)
        self.view.addItem(grid)

    def placeCamera(self) -> None:
        """La caméra, à 14 unités, 45° au-dessus du sol, à 120° de l'axe x."""
        self.view.setCameraPosition(distance=14, elevation=45, azimuth=120)

    def addFirstPoint(self) -> None:
        """Un point rouge en (3, 2, 4)."""
        positions = np.array([[3.0, 2.0, 4.0]])
        point = gl.GLScatterPlotItem(pos=positions, color=(1, 0, 0, 1), size=15)
        self.view.addItem(point)

    def _exploreWithMouse(self) -> None:
        """La souris navigue déjà : rien à écrire."""

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Créer la vue 3D",
                explanation=(
                    "Pas de récapitulatif : la 3D repart de zéro, avec sa propre vue et ses "
                    "propres éléments graphiques. "
                    "<br><br>La 3D de PyQtGraph vit dans un module à part :"
                    "<pre>import pyqtgraph.opengl as gl</pre>"
                    "<code>gl</code> regroupe les classes 3D, dont les noms commencent par "
                    "<code>GL</code>. Elles dessinent avec <b>OpenGL</b>, la bibliothèque de "
                    "dessin 3D de la carte graphique. Il faut donc une carte graphique qui le "
                    "prenne en charge, ce qui est le cas de presque tout ordinateur."
                    "<br><br>La <b>vue 3D</b> (<code>gl.GLViewWidget</code>) est un widget Qt "
                    "ordinaire, comme le widget du graphique 2D. Elle n'a pas de "
                    "<code>setTitle()</code> : <code>createView()</code> place un "
                    "<code>QLabel</code> au-dessus d'elle pour le titre, centré, et range les "
                    "deux dans un widget par un layout vertical. Le <code>1</code> de "
                    "<code>addWidget(view, 1)</code> est un facteur d'étirement : la vue prend "
                    "toute la hauteur que le titre laisse. Elle rend les trois : le widget, le "
                    "titre et la vue."
                    "<br><br>La page l'appelle une seule fois, à sa création : "
                    "<code>self.viewContainer, self.titleLabel, self.view = createView()</code>. "
                    "Les notions suivantes l'importent et font de même."
                    "<br><br>La vue est vide : un fond noir, sans aucun repère."
                ),
                run=self._viewAlreadyCreated,
                codeSource=(createView,),
                references=[("GLViewWidget", pyqtgraphDocUrl(f"{_GLPage}/glviewwidget", "opengl.GLViewWidget"))],
            ),
            QStepWalkthrough.Step(
                title="Un titre",
                explanation=(
                    "Le titre s'écrit dans le <code>QLabel</code>, par <code>setText()</code>."
                ),
                run=self.setViewTitle,
                references=[("GLViewWidget", pyqtgraphDocUrl(f"{_GLPage}/glviewwidget", "opengl.GLViewWidget"))],
            ),
            QStepWalkthrough.Step(
                title="Les axes",
                explanation=(
                    "La <b>scène 3D</b> est l'ensemble des éléments placés dans la vue. "
                    "<code>gl.GLAxisItem</code> en est un : les trois axes, partant de "
                    "l'origine. <code>setSize(x, y, z)</code> fixe leur longueur. "
                    "<code>addItem()</code> l'ajoute à la vue, comme à un graphique 2D."
                    "<br><br>Leurs couleurs sont fixes : X en bleu, Y en jaune, Z en vert. "
                    "Attention : ailleurs, la convention la plus courante est X rouge, Y vert, "
                    "Z bleu. L'axe Z est vertical."
                ),
                run=self.addAxes,
                references=[("GLAxisItem", pyqtgraphDocUrl(f"{_GLPage}/glaxisitem", "opengl.GLAxisItem"))],
            ),
            QStepWalkthrough.Step(
                title="Nommer les axes",
                explanation=(
                    "<code>gl.GLTextItem(pos=…, text=…, color=…)</code> écrit un texte à une "
                    "position (x, y, z) de la scène. Le texte reste toujours face à la caméra. "
                    "Sa couleur est un tuple de quatre nombres de 0 à 255 : rouge, vert, bleu, "
                    "opacité, comme en 2D."
                    "<br><br><code>nameAxes(view, length)</code> écrit X, Y et Z sur chaque axe, à "
                    "la distance <code>length</code> de l'origine, dans la couleur de l'axe. Sans "
                    "cela, la convention des couleurs ne se devine pas. Les notions suivantes "
                    "l'importent."
                ),
                run=self.addAxisNames,
                codeSource=(nameAxes, self.addAxisNames),
                references=[("GLTextItem", pyqtgraphDocUrl(f"{_GLPage}/gltextitem", "opengl.GLTextItem"))],
            ),
            QStepWalkthrough.Step(
                title="Une grille comme sol",
                explanation=(
                    "<code>gl.GLGridItem</code> trace un quadrillage dans le plan horizontal, "
                    "z = 0. Sans lui, rien n'indique la distance ni la perspective. "
                    "<code>setSize(x, y)</code> fixe son étendue, centrée sur l'origine, et "
                    "<code>setSpacing(x, y)</code> l'écart entre ses lignes."
                    "<br><br>Piège : les axes X et Y sont dans ce même plan. Ajoutée avant eux, "
                    "la grille les masquerait ; ajoutée après, elle les laisse visibles. C'est "
                    "l'inverse de la règle 2D, où le dernier ajouté passe par-dessus (notion "
                    "2.5) : en 3D, deux éléments au même endroit ne s'empilent pas, et le premier "
                    "dessiné l'emporte."
                ),
                run=self.addGrid,
                references=[("GLGridItem", pyqtgraphDocUrl(f"{_GLPage}/glgriditem", "opengl.GLGridItem"))],
            ),
            QStepWalkthrough.Step(
                title="La caméra : distance, élévation, azimut",
                explanation=(
                    "La <b>caméra</b> est le point d'où l'on regarde la scène. Elle vise un "
                    "point central, l'origine par défaut. "
                    "<code>setCameraPosition()</code> la place par trois nombres :"
                    "<ul>"
                    "<li><code>distance</code>, son éloignement du point central ;</li>"
                    "<li><code>elevation</code>, sa hauteur, en degrés au-dessus du sol : 0° à "
                    "l'horizon, 90° à la verticale ;</li>"
                    "<li><code>azimuth</code>, l'angle autour de l'axe vertical Z, compté depuis "
                    "l'axe X, dans le sens antihoraire vu d'en haut.</li>"
                    "</ul>"
                    "Ici, la caméra recule à 14 unités, monte à 45° et tourne à 120° de l'axe X : "
                    "elle regarde maintenant la scène depuis le côté des y positifs et des x "
                    "négatifs."
                ),
                run=self.placeCamera,
                references=[("GLViewWidget", pyqtgraphDocUrl(f"{_GLPage}/glviewwidget", "opengl.GLViewWidget"))],
            ),
            QStepWalkthrough.Step(
                title="Un premier point",
                explanation=(
                    "<code>gl.GLScatterPlotItem</code> est le nuage de points en 3D (notion "
                    "1.2). <code>pos</code> reçoit un tableau d'une rangée par point et de trois "
                    "colonnes, x, y et z : ici, une seule rangée, le point (3, 2, 4). "
                    "<code>size</code> donne son diamètre en pixels."
                    "<br><br>Sa couleur est un tuple de quatre nombres de <b>0 à 1</b> : rouge, "
                    "vert, bleu, opacité. <code>(1, 0, 0, 1)</code> est un rouge opaque. C'est "
                    "l'écriture de toute couleur 3D donnée par un tuple : points, courbes, "
                    "maillages, surfaces. Font exception le texte (<code>GLTextItem</code>) et "
                    "les tableaux de couleurs d'une image ou d'un volume (notion 3.5), de 0 à "
                    "255."
                ),
                run=self.addFirstPoint,
                references=[("GLScatterPlotItem",
                             pyqtgraphDocUrl(f"{_GLPage}/glscatterplotitem", "opengl.GLScatterPlotItem"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : naviguer à la souris",
                explanation=(
                    "La vue 3D se manipule déjà à la souris, sans code à écrire :"
                    "<ul>"
                    "<li>glisser avec le bouton gauche fait tourner la caméra autour du point "
                    "central : elle change d'azimut et d'élévation ;</li>"
                    "<li>la molette change sa distance ;</li>"
                    "<li>glisser avec le bouton du milieu déplace le point central.</li>"
                    "</ul>"
                    "<br><br>Tourner autour du point rouge : il garde sa place dans l'espace, "
                    "à la verticale du croisement de lignes (3, 2) de la grille."
                ),
                run=self._exploreWithMouse,
                codeSource=(),
                references=[("GLViewWidget", pyqtgraphDocUrl(f"{_GLPage}/glviewwidget", "opengl.GLViewWidget"))],
            ),
        ]
