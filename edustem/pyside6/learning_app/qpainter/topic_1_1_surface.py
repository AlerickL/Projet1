"""Notion 1.1 : la surface et le peintre.

Contexte : première notion de l'application. L'étudiant crée sa surface
(une `QImage`), y trace des traits avec un peintre (`QPainter`) actif dans
un bloc `with`, lit le repère sur la grille, puis donne un stylo (`QPen`)
au peintre. Le canevas du guide, présenté à la première étape, affiche
l'image qu'on lui confie.

Étapes couvertes : la surface blanche, un premier trait, le repère (origine
en haut à gauche, y vers le bas), une ligne qui monte, la couleur et
l'épaisseur du stylo. Quatre sélecteurs numériques règlent ensuite les deux
extrémités d'un segment.

Chaque étape est une méthode de `QTopicSurfaceTab`. Les étapes dessinent
dans la même image, `self.image`, et la redonnent au canevas à la fin.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl, qtPageUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


class QTopicSurfaceTab(QWidget):
    """Onglet de la notion 1.1 : la surface, le peintre, le repère, le stylo.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        canvas: Le canevas qui affiche l'image de l'étudiant (outil
            d'observation, présenté à l'étape de la surface).
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        x1Slider, y1Slider, x2Slider, y2Slider: Les quatre sélecteurs
            numériques des extrémités du segment.
        image: La surface créée par l'étudiant, ou None avant l'étape de la
            surface.
    """

    TabTitle = "La surface et le peintre"
    TabToolTip = "Créer une image, y tracer des traits avec un peintre (QPainter), lire le repère"
    RecommendedPanelWidth = 640
    Objective = (
        "Créer une surface (<code>QImage</code>), y tracer des traits avec un peintre "
        "(<code>QPainter</code>) à des coordonnées précises, et régler la couleur et l'épaisseur "
        "du trait avec un stylo (<code>QPen</code>)."
    )
    KeyConcepts = [
        "La surface est une image de pixels : on la crée avec sa largeur et sa hauteur, puis on "
        "la remplit d'une couleur.",
        "Le peintre dessine sur une surface. Il est actif dans le bloc <code>with</code>, et "
        "termine à la sortie du bloc.",
        "Le repère : origine en haut à gauche, x vers la droite, y vers le bas.",
        "Le stylo donne au trait sa couleur et son épaisseur. On le donne au peintre avant de "
        "dessiner.",
        "Les dessins s'accumulent dans l'image, jusqu'à ce qu'on la remplisse de nouveau.",
    ]
    KeyApis = [
        "QImage", "QImage.fill", "QPainter", "QPainter.drawLine", "QPainter.setPen", "QPen",
        "QColor",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.controls = QControlPanel()
        self.x1Slider = self.controls.addSlider("x1", -120, 599, 60, suffix="px")
        self.y1Slider = self.controls.addSlider("y1", -120, 479, 300, suffix="px")
        self.x2Slider = self.controls.addSlider("x2", -120, 599, 420, suffix="px")
        self.y2Slider = self.controls.addSlider("y2", -120, 479, 60, suffix="px")
        self.controls.setMaximumWidth(480)

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.canvas)
        contentLayout.addWidget(self.controls)
        contentLayout.addStretch(1)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Ramène le canevas et les contrôles à leur état de départ, avant chaque rejeu."""
        self.controls.resetControls()
        self.canvas.setImage(QImage())
        self.canvas.setGridVisible(False)
        self.image = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface : une image de 480 × 360 pixels, remplie de blanc, puis la montre."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setImage(self.image)

    def drawFirstLine(self) -> None:
        """Trace un premier trait, de (100, 100) à (300, 100)."""
        with QPainter(self.image) as painter:
            painter.drawLine(100, 100, 300, 100)
        self.canvas.setImage(self.image)

    def drawVerticalLine(self) -> None:
        """Montre la grille du repère, puis trace un trait vertical : y augmente vers le bas."""
        self.canvas.setGridVisible(True)
        with QPainter(self.image) as painter:
            painter.drawLine(100, 100, 100, 300)
        self.canvas.setImage(self.image)

    def drawRisingLine(self) -> None:
        """Trace une ligne qui monte : de gauche à droite, y diminue."""
        with QPainter(self.image) as painter:
            painter.drawLine(100, 300, 300, 100)
        self.canvas.setImage(self.image)

    def closeSquare(self) -> None:
        """Donne au peintre un stylo orange de 4 pixels, puis ferme le carré."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(228, 87, 46), 4))
            painter.drawLine(300, 100, 300, 300)
            painter.drawLine(100, 300, 300, 300)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie chaque sélecteur numérique au slot qui redessine le segment."""
        self.x1Slider.valueChanged.connect(self.redrawSegment)
        self.y1Slider.valueChanged.connect(self.redrawSegment)
        self.x2Slider.valueChanged.connect(self.redrawSegment)
        self.y2Slider.valueChanged.connect(self.redrawSegment)

    @Slot()
    def redrawSegment(self) -> None:
        """Lit les quatre sélecteurs numériques, puis redessine le segment."""
        self.drawSegment(self.x1Slider.value(), self.y1Slider.value(),
                         self.x2Slider.value(), self.y2Slider.value())

    def drawSegment(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Repart d'une image blanche, puis trace un segment orange de (x1, y1) à (x2, y2)."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(228, 87, 46), 4))
            painter.drawLine(x1, y1, x2, y2)
        self.canvas.setImage(self.image)

    def _exploreEndpoints(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine le segment de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawSegment()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="La surface : une image blanche",
                explanation=(
                    "Première notion du guide : pas de récapitulatif, il n'y a encore rien à reprendre. "
                    "<br><br>Les classes du dessin viennent de deux modules de PySide6 :"
                    "<pre>from PySide6.QtCore import Qt\n"
                    "from PySide6.QtGui import QColor, QImage, QPainter, QPen</pre>"
                    "<code>Qt</code> est l'espace de noms des constantes de Qt, comme "
                    "<code>Qt.GlobalColor.white</code>, le blanc. Les autres classes importées "
                    "sont présentées à leur première utilisation, dans les étapes suivantes."
                    "<br><br>La surface est une image (<code>QImage</code>) : une grille de pixels. "
                    "<code>QImage(480, 360, QImage.Format.Format_ARGB32)</code> crée une image de "
                    "480 pixels de large et 360 de haut. Le format dit comment chaque pixel est "
                    "rangé : ici, une couleur avec son opacité (notion 2.3). Une image neuve n'a "
                    "pas de contenu défini : <code>fill()</code> la remplit d'une couleur."
                    "<br><br>À gauche, le <b>canevas</b> (<code>self.canvas</code>) est l'outil "
                    "d'affichage de ce guide. Ce n'est pas une classe de Qt : elle a été écrite "
                    "pour ce guide seulement, et le glossaire la range parmi « Les outils de ce "
                    "guide ». Jusqu'ici, il ne montrait qu'un damier : il n'avait "
                    "reçu aucune image. <code>setImage(image)</code> reçoit une "
                    "<code>QImage</code>, en garde une copie et l'affiche. Sa copie ne suit pas "
                    "les dessins faits ensuite : on lui redonne l'image après chaque dessin. Hors "
                    "de ce guide, seule cette ligne d'affichage changerait."
                ),
                run=self.createSurface,
                references=[
                    ("QImage", qtDocUrl("QtGui", "QImage")),
                    ("QImage.fill", qtDocUrl("QtGui", "QImage", "fill")),
                    ("Qt.GlobalColor", qtDocUrl("QtCore", "Qt", "GlobalColor")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Un peintre, un premier trait",
                explanation=(
                    "Le <b>peintre</b> (<code>QPainter</code>) dessine sur la surface qu'il "
                    "reçoit : <code>QPainter(self.image)</code>. Il est actif dans le bloc "
                    "<code>with</code>, et termine à la sortie du bloc. "
                    "<code>drawLine(x1, y1, x2, y2)</code> trace un trait du point (x1, y1) au "
                    "point (x2, y2), en pixels. Sans autre réglage, le trait est noir et fin."
                    "<br><br>Le bloc terminé, <code>setImage()</code> redonne l'image au "
                    "canevas : c'est la dernière ligne de tout code qui dessine."
                ),
                run=self.drawFirstLine,
                references=[
                    ("QPainter", qtDocUrl("QtGui", "QPainter")),
                    ("QPainter.drawLine", qtDocUrl("QtGui", "QPainter", "drawLine")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le repère : origine en haut à gauche",
                explanation=(
                    "<code>setGridVisible(True)</code> superpose au canevas une grille graduée, "
                    "tous les 20 pixels, avec un nombre tous les 100. Elle n'est pas dessinée "
                    "dans l'image : c'est un affichage du canevas. Elle montre le repère. Le "
                    "point (0, 0) est en haut à gauche. x augmente vers la droite et y <b>vers "
                    "le bas</b>, à l'inverse des axes d'un cours de mathématiques."
                    "<br><br>Le premier trait suit la ligne y = 100. Le nouveau part du même "
                    "point (100, 100) et descend jusqu'à y = 300. Le premier trait est toujours "
                    "là : chaque étape dessine par-dessus les précédentes, et l'image garde "
                    "tout ce qu'on y a dessiné."
                ),
                run=self.drawVerticalLine,
                references=[("Système de coordonnées", qtPageUrl("coordsys"))],
            ),
            QStepWalkthrough.Step(
                title="Une ligne qui monte",
                explanation=(
                    "Pour monter, on diminue y. Cette ligne part de (100, 300), en bas à gauche, "
                    "et arrive à (300, 100), plus haut et plus à droite. Les trois traits forment "
                    "un triangle dont on lit chaque sommet sur la grille."
                ),
                run=self.drawRisingLine,
                references=[("QPainter.drawLine", qtDocUrl("QtGui", "QPainter", "drawLine"))],
            ),
            QStepWalkthrough.Step(
                title="Le stylo : couleur et épaisseur",
                explanation=(
                    "Le <b>stylo</b> (<code>QPen</code>) décrit le trait : sa couleur, son "
                    "épaisseur, et d'autres réglages vus à la notion 2.1. "
                    "<code>QPen(QColor(228, 87, 46), 4)</code> décrit un trait orange de 4 pixels "
                    "d'épaisseur. <code>QColor(228, 87, 46)</code> écrit une couleur par ses "
                    "trois composantes, rouge, vert et bleu, chacune de 0 à 255. Les couleurs "
                    "sont détaillées à la notion 2.3."
                    "<br><br><code>setPen()</code> donne ce stylo au peintre, avant de dessiner. "
                    "Le réglage vaut jusqu'à la fin du bloc. Les deux traits orange ferment le "
                    "carré dont le triangle occupe la moitié."
                ),
                run=self.closeSquare,
                references=[
                    ("QPainter.setPen", qtDocUrl("QtGui", "QPainter", "setPen")),
                    ("QPen", qtDocUrl("QtGui", "QPen")),
                    ("QColor", qtDocUrl("QtGui", "QColor")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : les deux extrémités",
                explanation=(
                    "Quatre sélecteurs numériques (<code>QSlider</code>) paraissent sous le "
                    "canevas : <code>x1Slider</code>, <code>y1Slider</code>, "
                    "<code>x2Slider</code> et <code>y2Slider</code>. Ils règlent les deux "
                    "extrémités d'un segment, en pixels : x de −120 à 599, y de −120 à 479. Ils "
                    "partent d'un segment de (60, 300) à (420, 60). L'image ne va que de 0 à 479 "
                    "en x et de 0 à 359 en y : une extrémité peut donc sortir de l'image."
                    "<br><br><code>connectControls()</code> relie le signal "
                    "<code>valueChanged</code> de chacun au slot "
                    "<code>redrawSegment()</code>. Comme tout slot de ce guide, il porte le "
                    "décorateur <code>@Slot(…)</code>, qui déclare les arguments qu'il reçoit "
                    "(page « Prérequis », en bas de l'arbre). Le signal transmet la nouvelle "
                    "valeur, mais <code>@Slot()</code> ne déclare aucun paramètre : PySide6 "
                    "accepte un slot qui reçoit moins d'arguments que le signal n'en transmet. "
                    "Le slot lit plutôt "
                    "les quatre valeurs par <code>value()</code>, puis appelle "
                    "<code>drawSegment()</code>. Celle-ci remplit l'image de blanc, ce qui "
                    "efface les dessins précédents, trace le segment, puis redonne l'image au "
                    "canevas."
                    "<br><br>Comme dans toute étape « À vous », les contrôles sont créés avec la "
                    "page de la notion, cachés jusqu'ici. À l'arrivée sur l'étape, le guide "
                    "appelle la fonction affichée qui les relie, ici <code>connectControls()</code>, "
                    "puis les montre. « Comment se servir du guide », dans l'introduction, le dit "
                    "pour tout le guide."
                    " Ici, il appelle aussi le slot une fois : le segment de départ remplace le "
                    "carré."
                    "<br><br>Faire glisser les sélecteurs. Placer une extrémité en (0, 0) : elle "
                    "touche le coin en haut à gauche. Puis la sortir de l'image, à x = −100 par "
                    "exemple. Le peintre accepte un point hors de l'image, sans erreur : il trace "
                    "le segment entier, mais seuls les pixels qui tombent dans l'image sont "
                    "colorés. Le segment s'arrête au bord, dans la direction du point invisible."
                ),
                run=self._exploreEndpoints,
                codeSource=(self.connectControls, self.redrawSegment, self.drawSegment),
                references=[
                    ("QPainter.drawLine", qtDocUrl("QtGui", "QPainter", "drawLine")),
                    ("QSlider", qtDocUrl("QtWidgets", "QSlider")),
                ],
            ),
        ]
