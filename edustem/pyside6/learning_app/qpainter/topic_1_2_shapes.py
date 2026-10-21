"""Notion 1.2 : les formes de base.

Contexte : la notion 1.1 a créé une surface et y a tracé des traits. Celle-ci
passe en revue toutes les formes simples de `QPainter`, chacune dans sa case
d'un tableau de 4 × 3 cases de 120 pixels.

Étapes couvertes : récapitulatif (une surface, un trait), les classes
géométriques (point, segment, rectangle, polygone), les points et leur
taille, rectangles droits et arrondis, l'ellipse par son rectangle englobant
puis par son centre et ses rayons, l'arc et ses angles, la part de tarte et
la corde, les lignes brisées ouvertes et fermées, puis plusieurs segments ou
plusieurs points d'un seul appel. Une liste déroulante et deux sélecteurs
numériques règlent ensuite la forme, l'angle de départ et l'étendue d'un arc.

Chaque étape est une méthode de `QTopicShapesTab`. Les étapes dessinent
dans la même image, `self.image`, et la redonnent au canevas à la fin.
"""

from __future__ import annotations

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Slot
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


class QTopicShapesTab(QWidget):
    """Onglet de la notion 1.2 : toutes les formes de base de `QPainter`.

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
        shapeCombo, startSlider, spanSlider: La forme, l'angle de départ et
            l'étendue, en degrés.
        image: La surface de la notion, ou None avant le récapitulatif.
    """

    TabTitle = "Formes de base"
    TabToolTip = "Points, rectangles, ellipses, arcs, parts de tarte, cordes, lignes brisées et polygones"
    RecommendedPanelWidth = 640
    Objective = (
        "Dessiner chacune des formes simples de <code>QPainter</code>, et savoir comment chacune "
        "se place : par ses coins, par un rectangle englobant, par un centre et des rayons, ou "
        "par une liste de points."
    )
    KeyConcepts = [
        "Qt décrit la géométrie par de petites classes : point, segment, rectangle, polygone. "
        "Chacune existe en version entière et en version réelle.",
        "Beaucoup de méthodes du peintre reçoivent soit des nombres un à un, soit un objet "
        "géométrique.",
        "Un rectangle se donne par son coin haut gauche, sa largeur et sa hauteur.",
        "Une ellipse se donne par son rectangle englobant, ou par son centre et ses deux rayons.",
        "Les angles des arcs se comptent en seizièmes de degré, à partir de trois heures, dans "
        "le sens inverse des aiguilles d'une montre.",
        "Une ligne brisée reste ouverte ; un polygone se referme de lui-même.",
        "Une liste de points suffit pour plusieurs segments ou plusieurs points d'un seul appel.",
    ]
    KeyApis = [
        "QPainter.drawPoint", "QPainter.drawRect", "QPainter.drawRoundedRect",
        "QPainter.drawEllipse", "QPainter.drawArc", "QPainter.drawPie", "QPainter.drawChord",
        "QPainter.drawPolyline", "QPainter.drawPolygon", "QPainter.drawLines",
        "QPainter.drawPoints", "QPointF", "QLineF", "QRectF", "QPolygonF",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.controls = QControlPanel()
        self.shapeCombo = self.controls.addComboBox(
            "Forme", [("Arc", "drawArc"), ("Part de tarte", "drawPie"), ("Corde", "drawChord")],
            currentIndex=1)
        self.startSlider = self.controls.addSlider("Départ", 0, 360, 30, suffix="°")
        self.spanSlider = self.controls.addSlider("Étendue", -360, 360, 120, suffix="°")
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
        """Crée la surface blanche de 480 × 360 pixels, et montre la grille du repère."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setGridVisible(True)
        self.canvas.setImage(self.image)

    def drawReminder(self) -> None:
        """Comme en 1.1 : un stylo bleu de 2 pixels, un trait."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(43, 108, 176), 2))
            painter.drawLine(20, 45, 100, 45)
        self.canvas.setImage(self.image)

    def drawGeometryObjects(self) -> None:
        """Un segment rangé dans des variables nommées, puis tracé d'un seul argument."""
        start = QPointF(20, 62)
        end = QPointF(100, 62)
        segment = QLineF(start, end)
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(43, 108, 176), 2))
            painter.drawLine(segment)
        self.canvas.setImage(self.image)

    def drawSizedPoints(self) -> None:
        """Quatre points : leur taille est l'épaisseur du stylo."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(43, 108, 176), 1))
            painter.drawPoint(25, 90)  # deux nombres
            painter.setPen(QPen(QColor(43, 108, 176), 4))
            painter.drawPoint(45, 90)
            painter.setPen(QPen(QColor(43, 108, 176), 8))
            painter.drawPoint(QPointF(68, 90))  # un point
            painter.setPen(QPen(QColor(43, 108, 176), 12))
            painter.drawPoint(QPointF(95, 90))
        self.canvas.setImage(self.image)

    def drawRectangles(self) -> None:
        """Un rectangle par quatre nombres, puis un rectangle arrondi par un QRectF."""
        rounded = QRectF(260, 20, 80, 80)
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(228, 87, 46), 2))
            painter.drawRect(140, 20, 80, 80)
            painter.drawRoundedRect(rounded, 20, 20)
        self.canvas.setImage(self.image)

    def drawEllipseInRect(self) -> None:
        """Une ellipse dans son rectangle englobant, montré en gris."""
        bounds = QRectF(380, 30, 80, 60)
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(184, 194, 204), 1))
            painter.drawRect(bounds)
            painter.setPen(QPen(QColor(42, 157, 143), 2))
            painter.drawEllipse(bounds)
        self.canvas.setImage(self.image)

    def drawCircleFromCenter(self) -> None:
        """Un cercle donné par son centre et ses deux rayons égaux, et son centre marqué."""
        center = QPointF(60, 180)
        radius = 40
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(42, 157, 143), 2))
            painter.drawEllipse(center, radius, radius)
            painter.setPen(QPen(QColor(42, 157, 143), 6))
            painter.drawPoint(center)
        self.canvas.setImage(self.image)

    def drawGraduatedArc(self) -> None:
        """Un cercle gris gradué à 0, 90, 180 et 270 degrés, puis un arc de 270 degrés."""
        dial = QRectF(140, 140, 80, 80)
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(184, 194, 204), 1))
            painter.drawEllipse(dial)
            painter.setPen(QPen(QColor(184, 194, 204), 6))
            painter.drawPoint(180, 140)  # 90 degrés : midi
            painter.drawPoint(140, 180)  # 180 degrés : neuf heures
            painter.drawPoint(180, 220)  # 270 degrés : six heures
            painter.setPen(QPen(QColor(142, 68, 173), 3))
            painter.drawArc(dial, 0 * 16, 270 * 16)
            painter.setPen(QPen(QColor(142, 68, 173), 8))
            painter.drawPoint(220, 180)  # 0 degré : trois heures
        self.canvas.setImage(self.image)

    def drawPieAndChord(self) -> None:
        """Une part de tarte et une corde, avec les mêmes angles."""
        pieBounds = QRectF(260, 140, 80, 80)
        chordBounds = QRectF(380, 140, 80, 80)
        startAngle = 30 * 16
        spanAngle = 120 * 16
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(142, 68, 173), 2))
            painter.drawPie(pieBounds, startAngle, spanAngle)
            painter.drawChord(chordBounds, startAngle, spanAngle)
        self.canvas.setImage(self.image)

    def drawPolylineAndPolygon(self) -> None:
        """Une ligne brisée (ouverte) par une liste, puis un polygone (fermé) par un QPolygonF."""
        zigzag = [
            QPointF(20, 340), QPointF(40, 270), QPointF(60, 320),
            QPointF(80, 270), QPointF(100, 340),
        ]
        crown = QPolygonF([
            QPointF(140, 340), QPointF(160, 270), QPointF(180, 320),
            QPointF(200, 270), QPointF(220, 340),
        ])
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(233, 162, 59), 2))
            painter.drawPolyline(zigzag)
            painter.drawPolygon(crown)
        self.canvas.setImage(self.image)

    def drawLinesAndPoints(self) -> None:
        """Trois segments d'un seul appel, puis une grille de points d'un seul appel."""
        segments = [
            QLineF(260, 270, 340, 290),
            QLineF(260, 300, 340, 320),
            QLineF(260, 330, 340, 350),
        ]
        points = []
        for x in range(390, 460, 15):
            for y in range(270, 350, 15):
                points.append(QPointF(x, y))
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(233, 162, 59), 2))
            painter.drawLines(segments)
            painter.setPen(QPen(QColor(233, 162, 59), 5))
            painter.drawPoints(points)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie la liste déroulante et les deux sélecteurs numériques au slot qui redessine."""
        self.shapeCombo.currentIndexChanged.connect(self.redrawAngleShape)
        self.startSlider.valueChanged.connect(self.redrawAngleShape)
        self.spanSlider.valueChanged.connect(self.redrawAngleShape)

    @Slot()
    def redrawAngleShape(self) -> None:
        """Lit la forme choisie et les deux angles, puis redessine."""
        self.drawAngleShape(self.shapeCombo.currentData(),
                            self.startSlider.value(), self.spanSlider.value())

    def drawAngleShape(self, shape: str, startDegrees: int, spanDegrees: int) -> None:
        """Repart d'une image blanche, puis dessine en grand un arc, une part de tarte ou une corde."""
        dial = QRectF(140, 60, 240, 240)
        startAngle = startDegrees * 16
        spanAngle = spanDegrees * 16
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(184, 194, 204), 1))
            painter.drawEllipse(dial)
            painter.drawLine(dial.center(), QPointF(380, 180))  # repère : 0 degré
            painter.setPen(QPen(QColor(142, 68, 173), 3))
            if shape == "drawArc":
                painter.drawArc(dial, startAngle, spanAngle)
            elif shape == "drawPie":
                painter.drawPie(dial, startAngle, spanAngle)
            elif shape == "drawChord":
                painter.drawChord(dial, startAngle, spanAngle)
        self.canvas.setImage(self.image)

    def _exploreAngles(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine la forme de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawAngleShape()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : une surface, un trait",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée une image blanche de "
                    "480 × 360 pixels (notion 1.1, étape 2). Elle montre aussi la grille, par "
                    "<code>setGridVisible(True)</code> (notion 1.1, étape 4), puis donne l'image "
                    "au canevas. Puis un peintre trace un trait avec un stylo bleu de 2 pixels. "
                    "<code>setImage()</code> reste la dernière ligne de tout code qui dessine."
                    "<br><br>Chaque forme de la notion occupe une case de 120 pixels de côté. "
                    "Les étapes s'accumulent dans la même image."
                ),
                run=self._recap,
                codeSource=(self.createSurface, self.drawReminder),
                references=[
                    ("QImage", qtDocUrl("QtGui", "QImage")),
                    ("QPainter.drawLine", qtDocUrl("QtGui", "QPainter", "drawLine")),
                    ("QPen", qtDocUrl("QtGui", "QPen")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Points, segments, rectangles : les classes géométriques",
                explanation=(
                    "Qt décrit la géométrie par quelques petites classes. Chacune range ses "
                    "nombres dans un seul objet, qu'on passe ensuite en un seul argument :"
                    "<ul>"
                    "<li><code>QPointF(x, y)</code> : un point ;</li>"
                    "<li><code>QLineF(début, fin)</code> : un segment, entre deux points ;</li>"
                    "<li><code>QRectF(x, y, largeur, hauteur)</code> : un rectangle, par son coin "
                    "haut gauche et sa taille ;</li>"
                    "<li><code>QPolygonF(points)</code> : une suite de points, faite d'une liste."
                    "</li></ul>"
                    "Chacune existe en deux versions : réelle, avec F pour <i>float</i>, et "
                    "entière, sans F (<code>QPoint</code>, <code>QLine</code>, <code>QRect</code>, "
                    "<code>QPolygon</code>). Ce guide emploie la version réelle pour ce qu'il "
                    "dessine : la notion 1.3 montre pourquoi. La version entière sert quand tous "
                    "les nombres sont entiers par nature, comme un rectangle de pixels. Les trois premières viennent de <code>PySide6.QtCore</code>, "
                    "<code>QPolygonF</code> de <code>PySide6.QtGui</code>."
                    "<br><br>Beaucoup de méthodes du peintre acceptent deux écritures : les "
                    "nombres un à un, ou un objet géométrique. Le récapitulatif écrivait "
                    "<code>drawLine(20, 45, 100, 45)</code>. Ici, le segment est d'abord rangé "
                    "dans des variables nommées, <code>start</code>, <code>end</code> puis "
                    "<code>segment</code>, et <code>drawLine(segment)</code> le trace, sous le "
                    "premier. Chaque nombre a un nom : le code se lit mieux, et un même objet "
                    "peut servir plusieurs fois."
                ),
                run=self.drawGeometryObjects,
                references=[
                    ("QPointF", qtDocUrl("QtCore", "QPointF")),
                    ("QLineF", qtDocUrl("QtCore", "QLineF")),
                    ("QRectF", qtDocUrl("QtCore", "QRectF")),
                    ("QPolygonF", qtDocUrl("QtGui", "QPolygonF")),
                ],
            ),
            QStepWalkthrough.Step(
                title="drawPoint() : un point",
                explanation=(
                    "<code>drawPoint()</code> colore un point, donné par deux nombres, "
                    "<code>drawPoint(x, y)</code>, ou par un objet, "
                    "<code>drawPoint(QPointF(x, y))</code>. Les deux écritures donnent le même "
                    "point. Avec un stylo de 1 pixel, c'est un seul pixel, presque invisible. Le "
                    "point prend l'épaisseur du stylo : ici 1, 4, 8 et 12 pixels. Il est carré, "
                    "parce que le stylo a des extrémités carrées par défaut (notion 2.1)."
                ),
                run=self.drawSizedPoints,
                references=[("QPainter.drawPoint", qtDocUrl("QtGui", "QPainter", "drawPoint"))],
            ),
            QStepWalkthrough.Step(
                title="drawRect() et drawRoundedRect() : des rectangles",
                explanation=(
                    "<code>drawRect(x, y, largeur, hauteur)</code> part du coin haut gauche. "
                    "<code>drawRoundedRect()</code> reçoit ici un <code>QRectF</code>, "
                    "<code>rounded</code>, l'autre écriture du même rectangle. Il reçoit en plus "
                    "deux rayons d'arrondi, horizontal et vertical, ici 20 pixels. Seul le contour "
                    "est tracé : l'intérieur reste vide. Le remplissage est le rôle du pinceau "
                    "(notion 2.2)."
                ),
                run=self.drawRectangles,
                references=[
                    ("QPainter.drawRect", qtDocUrl("QtGui", "QPainter", "drawRect")),
                    ("QPainter.drawRoundedRect", qtDocUrl("QtGui", "QPainter", "drawRoundedRect")),
                ],
            ),
            QStepWalkthrough.Step(
                title="drawEllipse() : dans un rectangle englobant",
                explanation=(
                    "<code>drawEllipse(rect)</code> trace l'ellipse qui touche les quatre côtés "
                    "d'un rectangle, son rectangle englobant. Le même objet, <code>bounds</code>, "
                    "sert deux fois : <code>drawRect()</code> le dessine en gris, puis "
                    "<code>drawEllipse()</code> y inscrit l'ellipse. Un rectangle carré donnerait "
                    "un cercle."
                ),
                run=self.drawEllipseInRect,
                references=[
                    ("QPainter.drawEllipse", qtDocUrl("QtGui", "QPainter", "drawEllipse")),
                    ("QRectF", qtDocUrl("QtCore", "QRectF")),
                ],
            ),
            QStepWalkthrough.Step(
                title="drawEllipse() : par le centre et les rayons",
                explanation=(
                    "<code>drawEllipse(centre, rx, ry)</code> reçoit un point, le centre, puis "
                    "le rayon horizontal et le rayon vertical. Deux rayons égaux donnent un "
                    "cercle. Ce cercle de centre (60, 180) et de rayon 40 est le même que celui du "
                    "rectangle <code>QRectF(20, 140, 80, 80)</code>. Le gros point marque le "
                    "centre : <code>drawPoint(center)</code> reçoit le même objet."
                ),
                run=self.drawCircleFromCenter,
                references=[
                    ("QPainter.drawEllipse", qtDocUrl("QtGui", "QPainter", "drawEllipse")),
                    ("QPointF", qtDocUrl("QtCore", "QPointF")),
                ],
            ),
            QStepWalkthrough.Step(
                title="drawArc() : les angles",
                explanation=(
                    "<code>drawArc(rect, départ, étendue)</code> trace une portion de l'ellipse "
                    "du rectangle. Le cercle gris est gradué comme un rapporteur. L'angle 0 est à "
                    "trois heures, marqué du point violet. 90° est à midi, 180° à neuf heures, "
                    "270° à six heures. Un angle positif tourne dans le sens inverse des aiguilles "
                    "d'une montre, comme en mathématiques, même si l'axe y descend."
                    "<br><br>Les angles sont en <b>seizièmes de degré</b> : d'où "
                    "<code>270 * 16</code>. L'arc part de trois heures, passe par midi et neuf "
                    "heures, et s'arrête à six heures. Oublier le <code>* 16</code> donnerait un "
                    "arc 16 fois trop court."
                ),
                run=self.drawGraduatedArc,
                references=[("QPainter.drawArc", qtDocUrl("QtGui", "QPainter", "drawArc"))],
            ),
            QStepWalkthrough.Step(
                title="drawPie() et drawChord() : fermer l'arc",
                explanation=(
                    "Mêmes paramètres que <code>drawArc()</code>, ici de 30° à 150°. Les deux "
                    "angles sont rangés une fois dans <code>startAngle</code> et "
                    "<code>spanAngle</code>, puis servent aux deux formes. <code>drawPie()</code> "
                    "relie les deux bouts de l'arc au centre : une part de "
                    "tarte. <code>drawChord()</code> les relie entre eux par un segment : la "
                    "corde."
                ),
                run=self.drawPieAndChord,
                references=[
                    ("QPainter.drawPie", qtDocUrl("QtGui", "QPainter", "drawPie")),
                    ("QPainter.drawChord", qtDocUrl("QtGui", "QPainter", "drawChord")),
                ],
            ),
            QStepWalkthrough.Step(
                title="drawPolyline() et drawPolygon() : une liste de points",
                explanation=(
                    "Les deux méthodes relient des points dans l'ordre. "
                    "<code>drawPolyline()</code> reçoit ici une liste Python de "
                    "<code>QPointF</code>, <code>zigzag</code>, et s'arrête au dernier point : la "
                    "ligne reste ouverte. <code>drawPolygon()</code> reçoit un "
                    "<code>QPolygonF</code>, <code>crown</code>, fait des mêmes points décalés de "
                    "120 pixels. Il revient au premier point : la forme se ferme d'elle-même, ici "
                    "par le bas. Les deux méthodes acceptent l'une ou l'autre écriture."
                ),
                run=self.drawPolylineAndPolygon,
                references=[
                    ("QPainter.drawPolyline", qtDocUrl("QtGui", "QPainter", "drawPolyline")),
                    ("QPainter.drawPolygon", qtDocUrl("QtGui", "QPainter", "drawPolygon")),
                ],
            ),
            QStepWalkthrough.Step(
                title="drawLines() et drawPoints() : plusieurs d'un coup",
                explanation=(
                    "<code>drawLines()</code> reçoit une liste de segments. Chaque "
                    "<code>QLineF</code> est ici créé par ses quatre nombres, "
                    "<code>QLineF(x1, y1, x2, y2)</code>, l'autre écriture de "
                    "<code>QLineF(début, fin)</code>. Les segments sont indépendants, sans lien "
                    "entre eux. <code>drawPoints()</code> dessine chaque point d'une liste. Ici, "
                    "deux boucles <code>for</code> imbriquées remplissent cette liste, colonne par "
                    "colonne. Un seul appel dessine ensuite les 30 points."
                ),
                run=self.drawLinesAndPoints,
                references=[
                    ("QPainter.drawLines", qtDocUrl("QtGui", "QPainter", "drawLines")),
                    ("QPainter.drawPoints", qtDocUrl("QtGui", "QPainter", "drawPoints")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : départ et étendue",
                explanation=(
                    "Trois contrôles paraissent sous le canevas. La liste déroulante "
                    "<code>shapeCombo</code> (<code>QComboBox</code>) choisit la forme : chaque "
                    "choix porte le nom de sa méthode, <code>\"drawArc\"</code>, "
                    "<code>\"drawPie\"</code> ou <code>\"drawChord\"</code>, lu par "
                    "<code>currentData()</code>. Deux sélecteurs numériques règlent les angles, "
                    "en degrés : <code>startSlider</code> de 0° à 360°, <code>spanSlider</code> "
                    "de −360° à 360°."
                    "<br><br><code>connectControls()</code> relie les trois signaux au slot "
                    "<code>redrawAngleShape()</code>. Le slot lit les contrôles et appelle "
                    "<code>drawAngleShape()</code>. Celle-ci range le cadran dans "
                    "<code>dial</code> et convertit les angles en seizièmes de degré, une fois. "
                    "Elle repart d'une image blanche, puis teste la chaîne reçue par "
                    "<code>if</code> et <code>elif</code>. Le trait gris horizontal marque "
                    "l'angle 0 : il part du centre du cadran, que rend l'accesseur "
                    "<code>dial.center()</code>."
                    "<br><br>Choisir une étendue négative : la forme tourne dans le sens des "
                    "aiguilles d'une montre."
                ),
                run=self._exploreAngles,
                codeSource=(self.connectControls, self.redrawAngleShape, self.drawAngleShape),
                references=[
                    ("QPainter.drawArc", qtDocUrl("QtGui", "QPainter", "drawArc")),
                    ("QComboBox.currentData", qtDocUrl("QtWidgets", "QComboBox", "currentData")),
                ],
            ),
        ]

    def _recap(self) -> None:
        """Crée la surface, puis trace le trait du récapitulatif."""
        self.createSurface()
        self.drawReminder()
