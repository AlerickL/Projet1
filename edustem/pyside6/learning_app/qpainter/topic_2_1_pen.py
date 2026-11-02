"""Notion 2.1 : le stylo.

Contexte : tout ce que `QPainter` trace comme ligne ou comme contour passe
par son stylo, un `QPen`. Le stylo décide de la couleur, de l'épaisseur,
du style du trait, de la forme de ses extrémités et de ses jonctions.

Étapes couvertes : récapitulatif (couleur et épaisseur), le stylo par
défaut, un trait épais centré sur sa ligne, les styles de trait, les
extrémités, les jonctions, `setPen()` qui copie le stylo, un motif de
tirets sur mesure, `Qt.PenStyle.NoPen`, puis un stylo réglé à la main.

Chaque étape est une méthode de `QTopicPenTab`. Les étapes dessinent dans
la même image, `self.image`. Celles qui comparent plusieurs traits repartent
d'une image blanche (`fill`).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Slot
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


class QTopicPenTab(QWidget):
    """Onglet de la notion 2.1 : le stylo (`QPen`) et tout ce qu'il règle.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        canvas: Le canevas qui affiche l'image (outil présenté en 1.1).
        readout: La lecture sous le canevas (outil présenté en 1.3).
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        widthSlider, styleCombo, capCombo, joinCombo: Épaisseur, style,
            extrémité et jonction du stylo réglé à la main.
        image: La surface de la notion, ou None avant le récapitulatif.
    """

    TabTitle = "Le stylo"
    TabToolTip = "QPen : couleur, épaisseur, style de trait, extrémités et jonctions"
    RecommendedPanelWidth = 600
    Objective = (
        "Choisir l'apparence d'un trait avec un stylo (<code>QPen</code>) : sa couleur, son "
        "épaisseur, son style, la forme de ses extrémités et de ses coins."
    )
    KeyConcepts = [
        "Le stylo trace les lignes et les contours. Le peintre en a toujours un : noir, d'un "
        "pixel, plein.",
        "Un trait épais est centré sur sa ligne géométrique.",
        "Les extrémités et les jonctions ne se voient que sur un trait épais.",
        "<code>setPen()</code> copie le stylo : le modifier ensuite ne change rien tant qu'on ne "
        "le redonne pas au peintre.",
        "Un motif de tirets se mesure en épaisseurs de trait, pas en pixels.",
        "<code>Qt.PenStyle.NoPen</code> supprime le trait : seul un remplissage peut alors se "
        "voir.",
    ]
    KeyApis = [
        "QPen", "QPainter.pen", "QPen.width", "QPen.style", "QPen.setCapStyle",
        "QPen.setJoinStyle", "QPen.setColor", "QPen.setDashPattern", "Qt.PenStyle",
        "Qt.PenCapStyle", "Qt.PenJoinStyle",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.widthSlider = self.controls.addSlider("Épaisseur", 1, 40, 24, suffix="px")
        self.styleCombo = self.controls.addComboBox("Style", [
            ("Plein (SolidLine)", Qt.PenStyle.SolidLine),
            ("Tirets (DashLine)", Qt.PenStyle.DashLine),
            ("Points (DotLine)", Qt.PenStyle.DotLine),
            ("Tiret-point (DashDotLine)", Qt.PenStyle.DashDotLine),
            ("Aucun trait (NoPen)", Qt.PenStyle.NoPen),
        ])
        self.capCombo = self.controls.addComboBox("Extrémité", [
            ("Nette (FlatCap)", Qt.PenCapStyle.FlatCap),
            ("Carrée (SquareCap)", Qt.PenCapStyle.SquareCap),
            ("Ronde (RoundCap)", Qt.PenCapStyle.RoundCap),
        ], currentIndex=1)
        self.joinCombo = self.controls.addComboBox("Jonction", [
            ("Pointe (MiterJoin)", Qt.PenJoinStyle.MiterJoin),
            ("Biseau (BevelJoin)", Qt.PenJoinStyle.BevelJoin),
            ("Arrondie (RoundJoin)", Qt.PenJoinStyle.RoundJoin),
        ], currentIndex=1)
        self.controls.setMaximumWidth(480)

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.canvas)
        contentLayout.addWidget(self.readout)
        contentLayout.addWidget(self.controls)
        contentLayout.addStretch(1)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Ramène le canevas, la lecture et les contrôles à leur état de départ, avant chaque rejeu."""
        self.controls.resetControls()
        self.readout.clear()
        self.canvas.setImage(QImage())
        self.image = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface blanche de 480 × 360 pixels, et la montre."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setImage(self.image)

    def drawReminder(self) -> None:
        """Comme en 1.1 : un stylo de couleur et d'épaisseur choisies, un trait."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(46, 134, 222), 6))
            painter.drawLine(40, 180, 440, 180)
        self.canvas.setImage(self.image)

    def drawWithDefaultPen(self) -> None:
        """Repart d'une image blanche, dessine sans régler de stylo, et lit le stylo du peintre."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            pen = painter.pen()
            self.readout.setText(f"pen.width() -> {pen.width()}\npen.style() -> {pen.style()}")
            painter.drawLine(40, 60, 440, 60)
            painter.drawRect(40, 120, 180, 180)
            painter.drawEllipse(260, 120, 180, 180)
        self.canvas.setImage(self.image)

    def drawCenteredWidths(self) -> None:
        """Repart d'une image blanche, trace cinq épaisseurs, et la ligne géométrique de la dernière."""
        self.readout.clear()
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            widths = [1, 2, 4, 8, 16]
            for index, width in enumerate(widths):
                painter.setPen(QPen(QColor(46, 134, 222), width))
                y = 60 + index * 60
                painter.drawLine(60, y, 420, y)
            painter.setPen(QPen(QColor(231, 76, 60), 1))
            painter.drawLine(60, 300, 420, 300)
        self.canvas.setImage(self.image)

    def drawPenStyles(self) -> None:
        """Repart d'une image blanche, puis trace une ligne dans chacun de cinq styles."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            styles = [Qt.PenStyle.SolidLine, Qt.PenStyle.DashLine, Qt.PenStyle.DotLine,
                      Qt.PenStyle.DashDotLine, Qt.PenStyle.DashDotDotLine]
            for index, style in enumerate(styles):
                painter.setPen(QPen(QColor(46, 134, 222), 4, style))
                y = 60 + index * 60
                painter.drawLine(60, y, 420, y)
        self.canvas.setImage(self.image)

    def drawCapStyles(self) -> None:
        """Repart d'une image blanche, trace trois traits épais, un par extrémité, et leurs vrais bouts."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(149, 165, 166), 1, Qt.PenStyle.DashLine))
            painter.drawLine(140, 20, 140, 340)
            painter.drawLine(340, 20, 340, 340)
            caps = [Qt.PenCapStyle.FlatCap, Qt.PenCapStyle.SquareCap, Qt.PenCapStyle.RoundCap]
            for index, cap in enumerate(caps):
                y = 80 + index * 100
                pen = QPen(QColor(46, 134, 222), 40)
                pen.setCapStyle(cap)
                painter.setPen(pen)
                painter.drawLine(140, y, 340, y)
                painter.setPen(QPen(QColor(231, 76, 60), 2))
                painter.drawLine(140, y, 340, y)
        self.canvas.setImage(self.image)

    def drawJoinStyles(self) -> None:
        """Repart d'une image blanche, puis trace trois lignes brisées épaisses, une par jonction."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            joins = [Qt.PenJoinStyle.MiterJoin, Qt.PenJoinStyle.BevelJoin, Qt.PenJoinStyle.RoundJoin]
            for index, join in enumerate(joins):
                center = 90 + index * 150
                points = [QPointF(center - 45, 230), QPointF(center, 155), QPointF(center + 45, 230)]
                pen = QPen(QColor(46, 134, 222), 30)
                pen.setJoinStyle(join)
                painter.setPen(pen)
                painter.drawPolyline(points)
                painter.setPen(QPen(QColor(231, 76, 60), 2))
                painter.drawPolyline(points)
        self.canvas.setImage(self.image)

    def drawCopiedPen(self) -> None:
        """Repart d'une image blanche ; change la couleur du stylo après setPen(), puis la redonne."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            pen = QPen(QColor(46, 134, 222), 12)
            painter.setPen(pen)
            pen.setColor(QColor(231, 76, 60))
            painter.drawLine(60, 120, 420, 120)  # encore bleu : le peintre a sa copie
            painter.setPen(pen)
            painter.drawLine(60, 240, 420, 240)  # rouge : la copie est remplacée
        self.canvas.setImage(self.image)

    def drawDashPattern(self) -> None:
        """Repart d'une image blanche ; un motif de tirets sur mesure, avec puis sans prolongement."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            pen = QPen(QColor(46, 134, 222), 8)
            pen.setDashPattern([4, 2])
            painter.setPen(pen)
            painter.drawLine(40, 80, 440, 80)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawLine(40, 180, 440, 180)
            pen.setDashPattern([1, 1, 4, 1])
            painter.setPen(pen)
            painter.drawLine(40, 280, 440, 280)
        self.canvas.setImage(self.image)

    def drawWithNoPen(self) -> None:
        """Repart d'une image blanche ; un rectangle tracé, puis un autre sans stylo, à la place marquée."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(149, 165, 166), 1, Qt.PenStyle.DashLine))
            painter.drawRect(260, 60, 180, 240)
            painter.drawLine(260, 60, 440, 300)
            painter.setPen(QPen(QColor(46, 134, 222), 4))
            painter.drawRect(40, 60, 180, 240)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(260, 60, 180, 240)
            painter.drawLine(260, 60, 440, 300)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie le sélecteur numérique et les trois listes déroulantes au slot qui redessine."""
        self.widthSlider.valueChanged.connect(self.redrawPen)
        self.styleCombo.currentIndexChanged.connect(self.redrawPen)
        self.capCombo.currentIndexChanged.connect(self.redrawPen)
        self.joinCombo.currentIndexChanged.connect(self.redrawPen)

    @Slot()
    def redrawPen(self) -> None:
        """Lit les quatre contrôles, puis redessine."""
        self.drawChosenPen(self.widthSlider.value(), self.styleCombo.currentData(),
                           self.capCombo.currentData(), self.joinCombo.currentData())

    def drawChosenPen(self, width: int, style: Qt.PenStyle, cap: Qt.PenCapStyle,
                      join: Qt.PenJoinStyle) -> None:
        """Repart d'une image blanche, puis trace une ligne brisée avec le stylo décrit, et sa ligne géométrique."""
        pen = QPen(QColor(46, 134, 222), width, style)
        pen.setCapStyle(cap)
        pen.setJoinStyle(join)
        points = [QPointF(60, 280), QPointF(140, 80), QPointF(240, 280), QPointF(300, 120),
                  QPointF(420, 160)]
        self.readout.setText(f"pen.width() -> {pen.width()}\npen.style() -> {pen.style()}")
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(pen)
            painter.drawPolyline(points)
            painter.setPen(QPen(QColor(231, 76, 60), 2))
            painter.drawPolyline(points)
        self.canvas.setImage(self.image)

    def _explorePen(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine avec le stylo de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawPen()

    def _recap(self) -> None:
        """Crée la surface, puis trace le trait du récapitulatif."""
        self.createSurface()
        self.drawReminder()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : couleur et épaisseur",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée l'image blanche. Un "
                    "stylo (<code>QPen</code>) bleu de 6 pixels, donné au peintre par "
                    "<code>setPen()</code>, trace un trait (notion 1.1)."
                    "<br><br>Les étapes de cette notion comparent plusieurs traits côte à côte. "
                    "Chacune repart donc d'une image blanche, par "
                    "<code>self.image.fill(Qt.GlobalColor.white)</code>."
                ),
                run=self._recap,
                codeSource=(self.createSurface, self.drawReminder),
                references=[
                    ("QPainter.setPen", qtDocUrl("QtGui", "QPainter", "setPen")),
                    ("QPen", qtDocUrl("QtGui", "QPen")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le stylo par défaut",
                explanation=(
                    "Tout peintre reçoit un stylo à sa création : le stylo par défaut. Ces trois "
                    "formes sont tracées avec lui, sans aucun réglage. "
                    "<code>painter.pen()</code> rend ce stylo. Ses "
                    "accesseurs <code>width()</code> et <code>style()</code> rendent son épaisseur "
                    "et son style, affichés par la lecture : 1 pixel, trait plein "
                    "(<code>SolidLine</code>, l'un des styles de trait présentés à l'étape 5). Sa "
                    "couleur est le noir. <code>drawEllipse(x, y, "
                    "largeur, hauteur)</code> reçoit ici son rectangle englobant (notion 1.2) en "
                    "quatre nombres, sans <code>QRectF</code>."
                    "<br><br>Le stylo trace les lignes et les contours, jamais l'intérieur d'une "
                    "forme."
                ),
                run=self.drawWithDefaultPen,
                references=[
                    ("QPainter.pen", qtDocUrl("QtGui", "QPainter", "pen")),
                    ("QPen.width", qtDocUrl("QtGui", "QPen", "width")),
                    ("QPen.style", qtDocUrl("QtGui", "QPen", "style")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Un trait épais est centré sur sa ligne",
                explanation=(
                    "Un trait épais est centré sur sa ligne géométrique, celle que décrivent les "
                    "coordonnées. Ici, cinq traits de 1, 2, 4, 8 et 16 pixels. Le dernier, de 16 "
                    "pixels, déborde de 8 pixels de chaque côté de y = 300 : la ligne rouge d'un "
                    "pixel marque cette ligne géométrique. Aux deux bouts aussi, le trait dépasse "
                    "de 8 pixels : c'est l'extrémité carrée par défaut, expliquée à l'étape 6. "
                    "La lecture, vidée par "
                    "<code>clear()</code>, se cache (notion 1.3)."
                ),
                run=self.drawCenteredWidths,
                references=[("QPen", qtDocUrl("QtGui", "QPen"))],
            ),
            QStepWalkthrough.Step(
                title="Styles de trait",
                explanation=(
                    "<code>QPen</code> reçoit un troisième argument : le style du trait, une "
                    "constante de <code>Qt.PenStyle</code>. De haut en bas :"
                    "<ul>"
                    "<li><code>SolidLine</code> : plein ;</li>"
                    "<li><code>DashLine</code> : des tirets ;</li>"
                    "<li><code>DotLine</code> : des points ;</li>"
                    "<li><code>DashDotLine</code> et <code>DashDotDotLine</code> : deux "
                    "combinaisons.</li></ul>"
                    "Les cinq traits ont la même épaisseur. La "
                    "longueur des tirets suit l'épaisseur du stylo : l'étape « Un motif sur "
                    "mesure » le mesure."
                ),
                run=self.drawPenStyles,
                references=[
                    ("Qt.PenStyle", qtDocUrl("QtCore", "Qt", "PenStyle")),
                    ("QPen", qtDocUrl("QtGui", "QPen")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Extrémités",
                explanation=(
                    "<code>setCapStyle()</code> choisit la forme des bouts du trait, une "
                    "constante de <code>Qt.PenCapStyle</code>. Les trois traits vont tous de "
                    "x = 140 à x = 340 : leur ligne géométrique est en rouge, leurs bouts sont "
                    "marqués en tirets gris."
                    "<br><br><code>FlatCap</code> s'arrête net au bout. <code>SquareCap</code>, le "
                    "défaut, prolonge le trait d'une demi-épaisseur : 20 pixels de chaque côté "
                    "ici. <code>RoundCap</code> le prolonge d'autant, en arrondi. L'anticrénelage "
                    "(notion 1.3) adoucit les arrondis."
                ),
                run=self.drawCapStyles,
                references=[
                    ("QPen.setCapStyle", qtDocUrl("QtGui", "QPen", "setCapStyle")),
                    ("Qt.PenCapStyle", qtDocUrl("QtCore", "Qt", "PenCapStyle")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Jonctions",
                explanation=(
                    "Là où deux segments d'une ligne brisée se rejoignent, le stylo doit remplir "
                    "le coin. <code>setJoinStyle()</code> en choisit la forme, une constante de "
                    "<code>Qt.PenJoinStyle</code>. <code>MiterJoin</code> prolonge les bords "
                    "jusqu'à une pointe. <code>BevelJoin</code>, le défaut, coupe le coin en "
                    "biseau. <code>RoundJoin</code> l'arrondit."
                    "<br><br>Une jonction n'existe qu'entre les segments d'une même forme : une "
                    "ligne brisée, mais aussi les coins d'un rectangle ou d'un polygone. Deux "
                    "<code>drawLine()</code> séparés n'en ont pas."
                ),
                run=self.drawJoinStyles,
                references=[
                    ("QPen.setJoinStyle", qtDocUrl("QtGui", "QPen", "setJoinStyle")),
                    ("Qt.PenJoinStyle", qtDocUrl("QtCore", "Qt", "PenJoinStyle")),
                ],
            ),
            QStepWalkthrough.Step(
                title="setPen() copie le stylo",
                explanation=(
                    "<code>setPen(pen)</code> donne au peintre une <b>copie</b> du stylo. "
                    "<code>setColor()</code> change ensuite la couleur de <code>pen</code> en "
                    "rouge, mais le peintre garde sa copie bleue : le premier trait est bleu. Un "
                    "second <code>setPen(pen)</code> remplace la copie : le second trait est "
                    "rouge."
                    "<br><br>Retenir : après chaque modification d'un stylo, le redonner au "
                    "peintre par <code>setPen()</code>."
                ),
                run=self.drawCopiedPen,
                references=[
                    ("QPainter.setPen", qtDocUrl("QtGui", "QPainter", "setPen")),
                    ("QPen.setColor", qtDocUrl("QtGui", "QPen", "setColor")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Un motif sur mesure",
                explanation=(
                    "<code>setDashPattern([4, 2])</code> alterne 4 unités de trait et 2 de vide. "
                    "L'unité est l'<b>épaisseur du stylo</b> : à 8 pixels, des tirets de 32 et "
                    "des trous de 16 pixels. Chaque réglage est suivi de <code>setPen(pen)</code>, "
                    "comme à l'étape précédente."
                    "<br><br>Premier trait : avec l'extrémité par défaut, <code>SquareCap</code>, "
                    "chaque tiret s'allonge d'une demi-épaisseur à chaque bout : 40 pixels de "
                    "trait, 8 de vide. Deuxième trait : <code>FlatCap</code> rend le motif exact. "
                    "Troisième trait : le motif <code>[1, 1, 4, 1]</code> alterne un point de 8 "
                    "pixels, un trou de 8, un tiret de 32 et un trou de 8."
                ),
                run=self.drawDashPattern,
                references=[
                    ("QPen.setDashPattern", qtDocUrl("QtGui", "QPen", "setDashPattern")),
                    ("QPen.setCapStyle", qtDocUrl("QtGui", "QPen", "setCapStyle")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Qt.PenStyle.NoPen : aucun trait",
                explanation=(
                    "<code>setPen()</code> accepte aussi un style seul, au lieu d'un "
                    "<code>QPen</code>. Avec <code>setPen(Qt.PenStyle.NoPen)</code>, plus aucune "
                    "ligne ni aucun contour n'est tracé. Le rectangle et la diagonale de droite sont bien "
                    "demandés, mais rien n'apparaît : les tirets gris marquent leur place. "
                    "Le rectangle de gauche, tracé avant, sert de témoin."
                    "<br><br>Seul, <code>NoPen</code> ne sert à rien. Il prend son sens avec un "
                    "remplissage, sujet de la notion 2.2."
                ),
                run=self.drawWithNoPen,
                references=[("Qt.PenStyle", qtDocUrl("QtCore", "Qt", "PenStyle"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : épaisseur, style, extrémité, jonction",
                explanation=(
                    "Quatre contrôles paraissent sous le canevas :"
                    "<ul>"
                    "<li><code>widthSlider</code>, un sélecteur numérique, règle l'épaisseur de 1 "
                    "à 40 pixels (24 au départ) ;</li>"
                    "<li><code>styleCombo</code> choisit le style ;</li>"
                    "<li><code>capCombo</code> choisit l'extrémité ;</li>"
                    "<li><code>joinCombo</code> choisit la jonction.</li></ul>"
                    "Chaque choix des trois listes porte sa constante de Qt, écrite entre "
                    "parenthèses, et <code>currentData()</code> la rend. Au départ, les réglages "
                    "par défaut du style, de l'extrémité et de la jonction : "
                    "<code>SolidLine</code>, <code>SquareCap</code>, <code>BevelJoin</code>."
                    "<br><br><code>connectControls()</code> relie les quatre signaux au slot "
                    "<code>redrawPen()</code>, qui lit les contrôles et appelle "
                    "<code>drawChosenPen()</code>. Celle-ci construit le stylo, affiche son "
                    "épaisseur et son style dans la lecture, repart d'une image blanche, puis trace une ligne brisée et, en rouge, sa ligne "
                    "géométrique."
                    "<br><br>Comparer <code>FlatCap</code> et <code>SquareCap</code>, puis la "
                    "pointe de <code>MiterJoin</code> sur le coin le plus aigu."
                ),
                run=self._explorePen,
                codeSource=(self.connectControls, self.redrawPen, self.drawChosenPen),
                references=[("QPen", qtDocUrl("QtGui", "QPen"))],
            ),
        ]
