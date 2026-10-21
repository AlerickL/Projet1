"""Notion 2.2 : le pinceau.

Contexte : la notion 2.1 a réglé le stylo, qui trace les contours. Le
pinceau (`QBrush`) remplit l'intérieur des formes fermées : d'une couleur
pleine, ou d'un motif.

Étapes couvertes : récapitulatif (un contour, rien dedans), un pinceau
plein, seules les formes fermées sont remplies, des motifs, des densités, un
motif ajouré, stylo et pinceau ensemble, `fillRect()`. Une liste déroulante
de motifs, une liste de couleurs et une case à cocher règlent ensuite le
pinceau.

Chaque étape est une méthode de `QTopicBrushTab`. Les étapes dessinent dans
la même image, `self.image`. Celles qui comparent plusieurs formes repartent
d'une image blanche (`fill`).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Slot
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


class QTopicBrushTab(QWidget):
    """Onglet de la notion 2.2 : le pinceau (`QBrush`) et le remplissage.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        canvas: Le canevas qui affiche l'image (outil présenté en 1.1).
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        styleCombo, colorCombo, outlineCheck: Motif et couleur du pinceau,
            présence d'un contour.
        image: La surface de la notion, ou None avant le récapitulatif.
    """

    TabTitle = "Le pinceau"
    TabToolTip = "QBrush : remplissage plein ou à motif, formes fermées, fillRect"
    RecommendedPanelWidth = 600
    Objective = (
        "Remplir l'intérieur des formes avec un pinceau (<code>QBrush</code>) : une couleur "
        "pleine ou un motif, avec ou sans contour, et remplir un rectangle sans toucher au stylo."
    )
    KeyConcepts = [
        "Le stylo trace le contour, le pinceau remplit l'intérieur. Un peintre neuf n'a pas de "
        "pinceau.",
        "Le pinceau ne remplit que les formes fermées : jamais une ligne, un arc ou une ligne "
        "brisée.",
        "Un motif ne colore que certains pixels : les autres laissent voir ce qui est dessous.",
        "Stylo et pinceau se choisissent indépendamment : contour seul, remplissage seul, ou les "
        "deux.",
        "<code>fillRect()</code> remplit un rectangle sans contour, sans changer le stylo ni le "
        "pinceau du peintre.",
    ]
    KeyApis = ["QBrush", "QPainter.setBrush", "Qt.BrushStyle", "QPainter.fillRect"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.controls = QControlPanel()
        self.styleCombo = self.controls.addComboBox("Motif", [
            ("Plein (SolidPattern)", Qt.BrushStyle.SolidPattern),
            ("Densité 50 % (Dense4Pattern)", Qt.BrushStyle.Dense4Pattern),
            ("Horizontales (HorPattern)", Qt.BrushStyle.HorPattern),
            ("Grille (CrossPattern)", Qt.BrushStyle.CrossPattern),
            ("Grille diagonale (DiagCrossPattern)", Qt.BrushStyle.DiagCrossPattern),
            ("Aucun pinceau (NoBrush)", Qt.BrushStyle.NoBrush),
        ], currentIndex=4)
        self.colorCombo = self.controls.addComboBox("Couleur", [
            ("Bleu, QColor(46, 134, 222)", QColor(46, 134, 222)),
            ("Jaune, QColor(246, 198, 103)", QColor(246, 198, 103)),
            ("Vert, QColor(72, 201, 176)", QColor(72, 201, 176)),
            ("Rouge, QColor(192, 57, 43)", QColor(192, 57, 43)),
        ])
        self.outlineCheck = self.controls.addCheckBox("Contour", checked=True)
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
        self.image = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface blanche de 480 × 360 pixels, et la montre."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setImage(self.image)

    def drawOutlines(self) -> None:
        """Un rectangle et une ellipse, tracés avec un stylo seulement."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(52, 73, 94), 3))
            painter.drawRect(40, 40, 180, 120)
            painter.drawEllipse(260, 40, 180, 120)
        self.canvas.setImage(self.image)

    def drawSolidBrush(self) -> None:
        """Les mêmes formes, plus bas, avec un pinceau plein en plus du stylo."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(52, 73, 94), 3))
            painter.setBrush(QBrush(QColor(246, 198, 103)))
            painter.drawRect(40, 200, 180, 120)
            painter.drawEllipse(260, 200, 180, 120)
        self.canvas.setImage(self.image)

    def drawOpenAndClosed(self) -> None:
        """Repart d'une image blanche ; avec le même pinceau, des formes ouvertes, puis fermées."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(52, 73, 94), 3))
            painter.setBrush(QBrush(QColor(246, 198, 103)))
            painter.drawPolyline([QPointF(40, 160), QPointF(100, 40), QPointF(160, 160), QPointF(220, 40)])
            painter.drawPolygon([QPointF(260, 160), QPointF(320, 40), QPointF(380, 160), QPointF(440, 40)])
            painter.drawArc(QRectF(40, 200, 180, 130), 0, 270 * 16)
            painter.drawPie(QRectF(260, 200, 180, 130), 0, 270 * 16)
        self.canvas.setImage(self.image)

    def drawPatterns(self) -> None:
        """Repart d'une image blanche, puis remplit six rectangles, un par motif de lignes."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(52, 73, 94), 2))
            patterns = [Qt.BrushStyle.HorPattern, Qt.BrushStyle.VerPattern,
                        Qt.BrushStyle.CrossPattern, Qt.BrushStyle.BDiagPattern,
                        Qt.BrushStyle.FDiagPattern, Qt.BrushStyle.DiagCrossPattern]
            for index, pattern in enumerate(patterns):
                painter.setBrush(QBrush(QColor(46, 134, 222), pattern))
                x = 30 + (index % 3) * 150
                y = 20 + (index // 3) * 110
                painter.drawRect(x, y, 120, 90)
        self.canvas.setImage(self.image)

    def drawDensities(self) -> None:
        """Ajoute, sous les motifs, une rangée de sept densités, de la plus pleine à la plus claire."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(52, 73, 94), 2))
            densities = [Qt.BrushStyle.Dense1Pattern, Qt.BrushStyle.Dense2Pattern,
                         Qt.BrushStyle.Dense3Pattern, Qt.BrushStyle.Dense4Pattern,
                         Qt.BrushStyle.Dense5Pattern, Qt.BrushStyle.Dense6Pattern,
                         Qt.BrushStyle.Dense7Pattern]
            for index, density in enumerate(densities):
                painter.setBrush(QBrush(QColor(46, 134, 222), density))
                painter.drawRect(30 + index * 62, 250, 52, 90)
        self.canvas.setImage(self.image)

    def drawSheerPattern(self) -> None:
        """Repart d'une image blanche ; trois bandes de couleur, puis un disque hachuré par-dessus."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(246, 198, 103)))
            painter.drawRect(0, 0, 160, 360)
            painter.setBrush(QBrush(QColor(72, 201, 176)))
            painter.drawRect(160, 0, 160, 360)
            painter.setBrush(QBrush(QColor(241, 148, 138)))
            painter.drawRect(320, 0, 160, 360)
            painter.setBrush(QBrush(QColor(52, 73, 94), Qt.BrushStyle.DiagCrossPattern))
            painter.drawEllipse(90, 30, 300, 300)
        self.canvas.setImage(self.image)

    def drawPenAndBrush(self) -> None:
        """Repart d'une image blanche ; trois disques : contour seul, remplissage seul, puis les deux."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(52, 73, 94), 6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(25, 115, 130, 130)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(72, 201, 176)))
            painter.drawEllipse(175, 115, 130, 130)
            painter.setPen(QPen(QColor(52, 73, 94), 6))
            painter.drawEllipse(325, 115, 130, 130)
        self.canvas.setImage(self.image)

    def drawWithFillRect(self) -> None:
        """Repart d'une image blanche ; fillRect() remplit, puis drawRect() montre stylo et pinceau inchangés."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(192, 57, 43), 6))
            painter.setBrush(QBrush(QColor(246, 198, 103)))
            painter.fillRect(40, 60, 180, 240, QColor(72, 201, 176))
            painter.fillRect(40, 60, 180, 240, QBrush(QColor(52, 73, 94), Qt.BrushStyle.BDiagPattern))
            painter.drawRect(260, 60, 180, 240)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie les deux listes déroulantes et la case à cocher au slot qui redessine."""
        self.styleCombo.currentIndexChanged.connect(self.redrawBrush)
        self.colorCombo.currentIndexChanged.connect(self.redrawBrush)
        self.outlineCheck.toggled.connect(self.redrawBrush)

    @Slot()
    def redrawBrush(self) -> None:
        """Lit les trois contrôles, puis redessine."""
        self.drawChosenBrush(self.styleCombo.currentData(), self.colorCombo.currentData(),
                             self.outlineCheck.isChecked())

    def drawChosenBrush(self, style: Qt.BrushStyle, color: QColor, outline: bool) -> None:
        """Repart d'une image blanche, puis dessine trois formes avec le pinceau décrit."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if outline:
                painter.setPen(QPen(QColor(52, 73, 94), 3))
            else:
                painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color, style))
            painter.drawRect(30, 60, 130, 240)
            painter.drawEllipse(175, 60, 130, 240)
            painter.drawPolygon([QPointF(390, 60), QPointF(450, 300), QPointF(330, 300)])
        self.canvas.setImage(self.image)

    def _exploreBrush(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine avec le pinceau de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawBrush()

    def _recap(self) -> None:
        """Crée la surface, puis trace les deux contours du récapitulatif."""
        self.createSurface()
        self.drawOutlines()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : un contour, rien dedans",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée l'image blanche, et un "
                    "stylo seul trace le contour de deux formes (notions 1.2 et 2.1). Leur "
                    "intérieur n'est pas peint en blanc : il n'est pas peint du tout. Un peintre "
                    "neuf n'a pas de pinceau."
                ),
                run=self._recap,
                codeSource=(self.createSurface, self.drawOutlines),
                references=[("QPainter.brush", qtDocUrl("QtGui", "QPainter", "brush"))],
            ),
            QStepWalkthrough.Step(
                title="Un pinceau plein",
                explanation=(
                    "Le <b>pinceau</b> (<code>QBrush</code>, de <code>PySide6.QtGui</code>) "
                    "remplit l'intérieur des formes. <code>QBrush(couleur)</code> crée un pinceau "
                    "plein. <code>setBrush()</code> le donne au peintre pour toutes les formes "
                    "qui suivent, comme <code>setPen()</code> pour le stylo. Chaque forme reçoit "
                    "alors les deux : le pinceau remplit l'intérieur, puis le stylo trace le "
                    "contour par-dessus."
                    "<br><br>Un raccourci, à connaître : <code>setBrush(couleur)</code> reçoit "
                    "une couleur seule, et crée un pinceau plein de cette couleur. "
                    "<code>setPen(couleur)</code> fait de même pour le stylo : un trait plein "
                    "d'un pixel. Ce guide écrit <code>QBrush</code> en entier jusqu'à la "
                    "notion 3.1, puis souvent la couleur seule."
                ),
                run=self.drawSolidBrush,
                references=[
                    ("QBrush", qtDocUrl("QtGui", "QBrush")),
                    ("QPainter.setBrush", qtDocUrl("QtGui", "QPainter", "setBrush")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Seules les formes fermées sont remplies",
                explanation=(
                    "Le pinceau ne remplit que les formes fermées : une ligne n'a pas "
                    "d'intérieur. Ici, même pinceau pour les quatre formes, qui repartent d'une "
                    "image blanche. À gauche, <code>drawPolyline()</code> et <code>drawArc()</code> "
                    "restent vides. À droite, <code>drawPolygon()</code> ferme le "
                    "même zigzag et <code>drawPie()</code> ferme le même arc : ils sont remplis. "
                    "Les arcs se placent par un rectangle englobant, un <code>QRectF</code>, comme à la notion 1.2."
                ),
                run=self.drawOpenAndClosed,
                references=[
                    ("QPainter.drawPolyline", qtDocUrl("QtGui", "QPainter", "drawPolyline")),
                    ("QPainter.drawPolygon", qtDocUrl("QtGui", "QPainter", "drawPolygon")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Des motifs",
                explanation=(
                    "<code>QBrush(couleur, motif)</code> remplit avec un motif plutôt qu'en "
                    "plein : une constante de <code>Qt.BrushStyle</code>. La couleur du pinceau "
                    "est celle des lignes du motif. Six motifs de lignes :"
                    "<ul>"
                    "<li><code>HorPattern</code> : des lignes horizontales ;</li>"
                    "<li><code>VerPattern</code> : des lignes verticales ;</li>"
                    "<li><code>CrossPattern</code> : une grille ;</li>"
                    "<li><code>BDiagPattern</code> : des diagonales qui montent vers la droite "
                    "(/) ;</li>"
                    "<li><code>FDiagPattern</code> : des diagonales qui descendent vers la "
                    "droite (\\) ;</li>"
                    "<li><code>DiagCrossPattern</code> : une grille diagonale.</li></ul>"
                    "<br><br><i>Pour l'exemple</i> : sans rapport avec les motifs, la boucle range "
                    "les six rectangles en deux rangées de trois. Chaque colonne décale x de 150 "
                    "pixels, chaque rangée décale y de 110."
                ),
                run=self.drawPatterns,
                references=[("Qt.BrushStyle", qtDocUrl("QtCore", "Qt", "BrushStyle"))],
            ),
            QStepWalkthrough.Step(
                title="Des densités",
                explanation=(
                    "Les motifs <code>Dense1Pattern</code> à <code>Dense7Pattern</code> colorent "
                    "une proportion fixe des pixels : environ 94 % pour le premier, 50 % pour "
                    "<code>Dense4Pattern</code>, 6 % pour le dernier. De loin, l'œil y voit une "
                    "teinte plus ou moins claire."
                ),
                run=self.drawDensities,
                references=[("Qt.BrushStyle", qtDocUrl("QtCore", "Qt", "BrushStyle"))],
            ),
            QStepWalkthrough.Step(
                title="Un motif est ajouré",
                explanation=(
                    "Un motif ne peint que ses lignes : entre elles, les trous laissent voir ce "
                    "qui est dessous. Ici, trois bandes pleines, sans contour "
                    "(<code>Qt.PenStyle.NoPen</code>, notion 2.1), puis un disque hachuré "
                    "par-dessus : les bandes paraissent entre les hachures."
                ),
                run=self.drawSheerPattern,
                references=[("Qt.BrushStyle", qtDocUrl("QtCore", "Qt", "BrushStyle"))],
            ),
            QStepWalkthrough.Step(
                title="Stylo et pinceau ensemble",
                explanation=(
                    "Stylo et pinceau se choisissent indépendamment. À gauche, contour seul. "
                    "<code>setBrush(Qt.BrushStyle.NoBrush)</code> retire le pinceau. Comme "
                    "<code>setPen()</code> (notion 2.1), <code>setBrush()</code> accepte un "
                    "style seul. Ce peintre neuf n'a pas encore de pinceau : ici, la ligne ne "
                    "change rien. Elle montre le geste qui retire un pinceau donné plus tôt. "
                    "Au centre, "
                    "remplissage seul : <code>setPen(Qt.PenStyle.NoPen)</code>. À droite, les "
                    "deux. Le contour de 6 pixels est centré sur le bord : il déborde de 3 pixels "
                    "vers l'extérieur. Le disque de droite paraît donc un peu plus grand que "
                    "celui du centre."
                ),
                run=self.drawPenAndBrush,
                references=[
                    ("QPainter.setBrush", qtDocUrl("QtGui", "QPainter", "setBrush")),
                    ("Qt.BrushStyle", qtDocUrl("QtCore", "Qt", "BrushStyle")),
                ],
            ),
            QStepWalkthrough.Step(
                title="fillRect() : remplir sans rien changer",
                explanation=(
                    "<code>fillRect(x, y, largeur, hauteur, couleur ou pinceau)</code>, déjà "
                    "employé en 1.3 pour poser un fond, remplit un rectangle avec la couleur ou "
                    "le pinceau reçu, sans contour. Il ne change ni "
                    "le stylo ni le pinceau du peintre : le <code>drawRect()</code> de droite "
                    "emploie toujours le stylo rouge et le pinceau jaune. Un second "
                    "<code>fillRect()</code>, hachuré, se pose ici sur le premier."
                ),
                run=self.drawWithFillRect,
                references=[("QPainter.fillRect", qtDocUrl("QtGui", "QPainter", "fillRect"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : motif, couleur, contour",
                explanation=(
                    "Trois contrôles paraissent sous le canevas :"
                    "<ul>"
                    "<li>la liste déroulante <code>styleCombo</code> choisit le motif : chaque "
                    "choix porte sa constante de <code>Qt.BrushStyle</code>, écrite entre "
                    "parenthèses. Six choix : plein, densité 50 %, horizontales, grille, grille "
                    "diagonale (au départ), aucun pinceau ;</li>"
                    "<li>la liste <code>colorCombo</code> choisit la couleur : chaque choix porte "
                    "la <code>QColor</code> écrite dans son libellé. Quatre choix : bleu (au "
                    "départ), jaune, vert, rouge ;</li>"
                    "<li>la case à cocher <code>outlineCheck</code>, cochée au départ, ajoute un "
                    "contour.</li></ul>"
                    "<code>currentData()</code> rend la valeur portée par le choix courant."
                    "<br><br><code>connectControls()</code> relie les trois signaux au slot "
                    "<code>redrawBrush()</code>, qui lit les contrôles et appelle "
                    "<code>drawChosenBrush()</code>. Celle-ci repart d'une image blanche, puis "
                    "dessine trois formes avec le pinceau décrit."
                    "<br><br>Choisir <code>NoBrush</code> et décocher le contour : plus rien ne "
                    "se voit."
                ),
                run=self._exploreBrush,
                codeSource=(self.connectControls, self.redrawBrush, self.drawChosenBrush),
                references=[
                    ("QBrush", qtDocUrl("QtGui", "QBrush")),
                    ("Qt.BrushStyle", qtDocUrl("QtCore", "Qt", "BrushStyle")),
                ],
            ),
        ]
