"""Notion 4.1 : les chemins.

Contexte : les formes de base (notion 1.2) ne suffisent plus dès qu'un
contour mêle droites et courbes. Un `QPainterPath` décrit un tel contour,
segment par segment. `drawPath()` le dessine ensuite d'un seul coup, contour
et remplissage compris.

Étapes couvertes : récapitulatif (une ligne brisée par `drawPolyline`), la
même ligne en chemin ouvert (`moveTo`, `lineTo`), un chemin fermé et rempli
(`closeSubpath`), une courbe quadratique puis une courbe cubique avec leurs
points de contrôle, des formes toutes faites ajoutées au chemin (`addRect`,
`addEllipse`, `addText`), les deux règles de remplissage sur une étoile, les
opérations entre chemins, puis les points de contrôle d'une courbe de
Bézier réglés à la main.

Chaque étape est une méthode de `QTopicPathsTab`, sauf deux fonctions du
module, montrées. Les étapes dessinent dans la même image, `self.image`.
Celles qui changent de sujet repartent d'une image blanche (`fill`).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Slot
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


def drawControlLine(painter: QPainter, anchor: QPointF, control: QPointF) -> None:
    """Dessine un point de contrôle jaune, relié en tirets à l'extrémité de courbe qu'il tire."""
    painter.save()
    painter.setPen(QPen(QColor(99, 110, 114), 1, Qt.PenStyle.DashLine))
    painter.drawLine(anchor, control)
    painter.setPen(QPen(QColor(45, 52, 54), 2))
    painter.setBrush(QColor(253, 203, 110))
    painter.drawEllipse(control, 6, 6)
    painter.restore()


def starPath() -> QPainterPath:
    """Une étoile à cinq branches autour de (0, 0), tracée d'un seul trait : chaque sommet saute le suivant."""
    points = [QPointF(0, -85), QPointF(50, 69), QPointF(-81, -26), QPointF(81, -26),
              QPointF(-50, 69)]
    path = QPainterPath()
    path.moveTo(points[0])
    for point in points[1:]:
        path.lineTo(point)
    path.closeSubpath()
    return path


class QTopicPathsTab(QWidget):
    """Onglet de la notion 4.1 : décrire un contour libre avec `QPainterPath`, puis le dessiner.

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
        x1Slider, y1Slider, x2Slider, y2Slider: Les coordonnées des deux
            points de contrôle de la courbe de Bézier.
        image: La surface de la notion, ou None avant le récapitulatif.
    """

    TabTitle = "Chemins"
    TabToolTip = "QPainterPath : droites, courbes, formes ajoutées, règles de remplissage, opérations"
    RecommendedPanelWidth = 600
    Objective = (
        "Décrire un contour quelconque, fait de droites et de courbes, avec un chemin "
        "(<code>QPainterPath</code>), puis le dessiner d'un seul appel. Combiner des chemins entre "
        "eux pour obtenir des formes qu'aucune méthode de base ne dessine."
    )
    KeyConcepts = [
        "Un chemin se construit comme un tracé à main levée : on place un point de départ, puis "
        "on ajoute des segments.",
        "Un chemin fermé relie son dernier point au premier ; le pinceau remplit l'intérieur.",
        "Une courbe de Bézier est tirée par des points de contrôle qu'elle ne traverse pas.",
        "Un même chemin peut contenir plusieurs formes, dessinées d'un seul appel avec le même "
        "style.",
        "La règle de remplissage décide si une zone entourée deux fois est à l'intérieur ou non.",
        "Union, intersection et différence produisent de nouveaux chemins.",
    ]
    KeyApis = [
        "QPainterPath.moveTo", "QPainterPath.lineTo", "QPainterPath.closeSubpath",
        "QPainterPath.quadTo", "QPainterPath.cubicTo", "QPainterPath.addRect",
        "QPainterPath.addEllipse", "QPainterPath.addText", "QPainterPath.setFillRule",
        "QPainterPath.united", "QPainterPath.intersected", "QPainterPath.subtracted",
        "QPainter.drawPath",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.controls = QControlPanel()
        self.x1Slider = self.controls.addSlider("Contrôle 1, x", 0, 480, 120, suffix="px")
        self.y1Slider = self.controls.addSlider("Contrôle 1, y", 0, 360, 60, suffix="px")
        self.x2Slider = self.controls.addSlider("Contrôle 2, x", 0, 480, 360, suffix="px")
        self.y2Slider = self.controls.addSlider("Contrôle 2, y", 0, 360, 340, suffix="px")
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
        """Crée la surface blanche de 480 × 360 pixels, montre la grille, puis l'image."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setGridVisible(True)
        self.canvas.setImage(self.image)

    def drawPolylineReminder(self) -> None:
        """Trace une ligne brisée grise de cinq points, avec drawPolyline()."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(178, 190, 195), 10))
            painter.drawPolyline([QPointF(30, 150), QPointF(80, 60), QPointF(120, 110),
                                  QPointF(160, 40), QPointF(210, 150)])
        self.canvas.setImage(self.image)

    def drawOpenPath(self) -> None:
        """Construit la même ligne brisée en chemin : moveTo() pose la pointe, chaque lineTo() ajoute un segment."""
        path = QPainterPath()
        path.moveTo(30, 150)
        path.lineTo(80, 60)
        path.lineTo(120, 110)
        path.lineTo(160, 40)
        path.lineTo(210, 150)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(46, 134, 222), 4))
            painter.drawPath(path)
        self.canvas.setImage(self.image)

    def drawClosedPath(self) -> None:
        """Trace la même ligne brisée 170 pixels plus bas, la ferme avec closeSubpath(), et la remplit."""
        path = QPainterPath()
        path.moveTo(30, 320)
        path.lineTo(80, 230)
        path.lineTo(120, 280)
        path.lineTo(160, 210)
        path.lineTo(210, 320)
        path.closeSubpath()
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(30, 55, 153), 4))
            painter.setBrush(QColor(130, 204, 221))
            painter.drawPath(path)
        self.canvas.setImage(self.image)

    def drawQuadCurve(self) -> None:
        """Trace une courbe quadratique : un seul point de contrôle, qui tire la courbe vers lui."""
        start = QPointF(270, 150)
        control = QPointF(360, 20)
        end = QPointF(450, 150)
        path = QPainterPath()
        path.moveTo(start)
        path.quadTo(control, end)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(225, 112, 85), 4))
            painter.drawPath(path)
            drawControlLine(painter, start, control)
            drawControlLine(painter, end, control)
        self.canvas.setImage(self.image)

    def drawCubicCurve(self) -> None:
        """Trace une courbe cubique : deux points de contrôle, un par extrémité, pour une courbe en S."""
        start = QPointF(270, 300)
        end = QPointF(450, 230)
        control1 = QPointF(300, 190)
        control2 = QPointF(420, 350)
        path = QPainterPath()
        path.moveTo(start)
        path.cubicTo(control1, control2, end)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(142, 68, 173), 4))
            painter.drawPath(path)
            drawControlLine(painter, start, control1)
            drawControlLine(painter, end, control2)
        self.canvas.setImage(self.image)

    def drawAddedShapes(self) -> None:
        """Repart d'une image blanche, puis réunit un rectangle, un disque et un texte dans un seul chemin."""
        self.image.fill(Qt.GlobalColor.white)
        font = QFont("Georgia")
        font.setPixelSize(90)
        font.setBold(True)
        path = QPainterPath()
        path.addRect(30, 40, 120, 100)
        path.addEllipse(QPointF(230, 90), 55, 55)
        path.addText(305, 125, font, "Qt")
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(0, 98, 102), 2))
            painter.setBrush(QColor(85, 239, 196))
            painter.drawPath(path)
        self.canvas.setImage(self.image)

    def drawOddEvenStar(self) -> None:
        """Remplit l'étoile, placée en (120, 265), avec la règle par défaut : OddEvenFill."""
        star = starPath()
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(120, 265)
            painter.setPen(QPen(QColor(179, 57, 57), 2))
            painter.setBrush(QColor(255, 218, 121))
            painter.drawPath(star)
        self.canvas.setImage(self.image)

    def drawWindingStar(self) -> None:
        """Remplit la même étoile, placée en (360, 265), avec la règle WindingFill : le centre devient plein."""
        star = starPath()
        star.setFillRule(Qt.FillRule.WindingFill)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(360, 265)
            painter.setPen(QPen(QColor(179, 57, 57), 2))
            painter.setBrush(QColor(255, 218, 121))
            painter.drawPath(star)
        self.canvas.setImage(self.image)

    def drawOperations(self) -> None:
        """Repart d'une image blanche : deux disques a et b, puis leur union, leur intersection, leur différence."""
        self.image.fill(Qt.GlobalColor.white)
        a = QPainterPath()
        a.addEllipse(QPointF(95, 100), 60, 60)
        b = QPainterPath()
        b.addEllipse(QPointF(145, 100), 60, 60)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(178, 190, 195), 1))
            painter.drawLine(240, 0, 240, 360)
            painter.drawLine(0, 180, 480, 180)
            painter.setPen(QPen(QColor(45, 52, 54), 1))
            painter.drawText(10, 172, "a et b")
            painter.drawText(250, 172, "a.united(b)")
            painter.drawText(10, 352, "a.intersected(b)")
            painter.drawText(250, 352, "a.subtracted(b)")
            painter.setPen(QPen(QColor(45, 52, 54), 2))
            painter.drawPath(a)
            painter.drawPath(b)
            painter.setBrush(QColor(162, 155, 254))
            painter.drawPath(a.united(b).translated(240, 0))
            painter.drawPath(a.intersected(b).translated(0, 180))
            painter.drawPath(a.subtracted(b).translated(240, 180))
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie les quatre sélecteurs numériques au slot qui redessine."""
        self.x1Slider.valueChanged.connect(self.redrawBezier)
        self.y1Slider.valueChanged.connect(self.redrawBezier)
        self.x2Slider.valueChanged.connect(self.redrawBezier)
        self.y2Slider.valueChanged.connect(self.redrawBezier)

    @Slot()
    def redrawBezier(self) -> None:
        """Lit les quatre sélecteurs numériques, puis redessine la courbe."""
        control1 = QPointF(self.x1Slider.value(), self.y1Slider.value())
        control2 = QPointF(self.x2Slider.value(), self.y2Slider.value())
        self.drawBezier(control1, control2)

    def drawBezier(self, control1: QPointF, control2: QPointF) -> None:
        """Repart d'une image blanche ; une courbe cubique entre deux extrémités fixes, tirée par les deux points de contrôle."""
        start = QPointF(60, 200)
        end = QPointF(420, 200)
        path = QPainterPath()
        path.moveTo(start)
        path.cubicTo(control1, control2, end)
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(142, 68, 173), 5))
            painter.drawPath(path)
            drawControlLine(painter, start, control1)
            drawControlLine(painter, end, control2)
        self.canvas.setImage(self.image)

    def _exploreControls(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine avec leurs valeurs de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawBezier()

    def _recap(self) -> None:
        """Crée la surface, puis trace la ligne brisée du récapitulatif."""
        self.createSurface()
        self.drawPolylineReminder()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : une ligne brisée",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée l'image blanche et "
                    "affiche la grille (notion 1.1). <code>drawPolyline()</code> trace une ligne "
                    "brisée par une liste de points (notion 1.2), ici en gris et en 10 pixels "
                    "d'épaisseur."
                    "<br><br>Une ligne brisée ne contient que des segments droits. Les étapes "
                    "suivantes décrivent un contour qui mêle droites et courbes."
                ),
                run=self._recap,
                codeSource=(self.createSurface, self.drawPolylineReminder),
                references=[("QPainter.drawPolyline", qtDocUrl("QtGui", "QPainter", "drawPolyline"))],
            ),
            QStepWalkthrough.Step(
                title="Une ligne brisée : moveTo() et lineTo()",
                explanation=(
                    "Un chemin (<code>QPainterPath</code>, de <code>PySide6.QtGui</code>) décrit un tracé à main levée, sans "
                    "rien dessiner. <code>moveTo(x, y)</code> place le point de départ, sans rien tracer. Chaque "
                    "<code>lineTo(x, y)</code> ajoute un segment depuis le point courant."
                    "<br><br>Ensuite, <code>drawPath(path)</code> dessine le chemin avec le stylo "
                    "du peintre. Ce chemin passe par les mêmes points que la ligne grise : le "
                    "trait bleu court en son milieu. Il reste ouvert : rien ne relie le dernier "
                    "point au premier."
                ),
                run=self.drawOpenPath,
                references=[
                    ("QPainterPath.moveTo", qtDocUrl("QtGui", "QPainterPath", "moveTo")),
                    ("QPainterPath.lineTo", qtDocUrl("QtGui", "QPainterPath", "lineTo")),
                    ("QPainter.drawPath", qtDocUrl("QtGui", "QPainter", "drawPath")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Fermer et remplir : closeSubpath",
                explanation=(
                    "La même ligne brisée, 170 pixels plus bas. <code>closeSubpath()</code> "
                    "ajoute le segment qui revient au premier point. Son nom vient de "
                    "« sous-chemin » (<i>subpath</i>) : le tracé commencé au dernier "
                    "<code>moveTo()</code>, détaillé à l'étape 7. Le pinceau (notion 2.2) "
                    "remplit l'intérieur."
                    "<br><br>Ici, un chemin diffère de <code>drawPolyline()</code>, qui ne "
                    "remplit jamais (notion 2.2). Sans <code>closeSubpath()</code>, le pinceau "
                    "remplirait quand même le chemin, comme s'il était fermé. Seul son contour "
                    "resterait ouvert en bas."
                ),
                run=self.drawClosedPath,
                references=[
                    ("QPainterPath.closeSubpath", qtDocUrl("QtGui", "QPainterPath", "closeSubpath")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une courbe quadratique : quadTo()",
                explanation=(
                    "<code>quadTo(contrôle, fin)</code> ajoute une courbe du point courant "
                    "jusqu'à <code>fin</code>. Le point de contrôle, en jaune, tire la courbe "
                    "vers lui sans qu'elle le traverse."
                    "<br><br>Les tirets sont les tangentes de la courbe à ses deux "
                    "extrémités. La tangente est la droite qui touche la courbe en un point, en "
                    "suivant sa direction. Au départ, la courbe part donc vers le point de "
                    "contrôle ; à l'arrivée, elle en vient."
                    "<br><br><code>drawControlLine(painter, extrémité, contrôle)</code> dessine "
                    "ces repères : un trait en tirets et un disque jaune. Elle isole ses réglages de "
                    "stylo et de pinceau avec <code>save()</code> et <code>restore()</code> "
                    "(notion 3.2). Elle ne rend rien."
                ),
                run=self.drawQuadCurve,
                codeSource=(drawControlLine, self.drawQuadCurve),
                references=[("QPainterPath.quadTo", qtDocUrl("QtGui", "QPainterPath", "quadTo"))],
            ),
            QStepWalkthrough.Step(
                title="Une courbe cubique : cubicTo()",
                explanation=(
                    "<code>cubicTo(contrôle1, contrôle2, fin)</code> donne un point de contrôle à "
                    "chaque extrémité. Le premier fixe la direction de départ, le second la "
                    "direction d'arrivée. Tirés dans deux sens opposés, ils produisent une courbe "
                    "en S, impossible avec un seul contrôle. Les deux courbes sont des courbes de "
                    "Bézier : la quadratique a un point de contrôle, la cubique deux. Les "
                    "logiciels de dessin vectoriel emploient surtout la cubique."
                ),
                run=self.drawCubicCurve,
                references=[("QPainterPath.cubicTo", qtDocUrl("QtGui", "QPainterPath", "cubicTo"))],
            ),
            QStepWalkthrough.Step(
                title="Ajouter des formes toutes faites",
                explanation=(
                    "L'image repart du blanc. <code>addRect()</code>, <code>addEllipse()</code> "
                    "et <code>addText()</code> ajoutent chacune une forme complète au chemin. "
                    "Chaque forme est un morceau séparé du chemin, un sous-chemin. Leurs "
                    "arguments sont ceux de <code>drawRect()</code>, <code>drawEllipse()</code> "
                    "(notion 1.2) et <code>drawText()</code> (notion 3.1). Pour "
                    "<code>addText(x, y, police, texte)</code>, y est la ligne de base."
                    "<br><br><code>setPixelSize(90)</code> fixe la taille de la police en "
                    "pixels, et non en points comme <code>QFont(famille, taille)</code> (notion "
                    "3.1). Le texte devient un contour comme les autres : un seul "
                    "<code>drawPath()</code> dessine les trois formes, avec le même stylo et le "
                    "même pinceau."
                ),
                run=self.drawAddedShapes,
                references=[
                    ("QPainterPath.addRect", qtDocUrl("QtGui", "QPainterPath", "addRect")),
                    ("QPainterPath.addEllipse", qtDocUrl("QtGui", "QPainterPath", "addEllipse")),
                    ("QPainterPath.addText", qtDocUrl("QtGui", "QPainterPath", "addText")),
                    ("QFont.setPixelSize", qtDocUrl("QtGui", "QFont", "setPixelSize")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Règle de remplissage : OddEvenFill",
                explanation=(
                    "Quand un chemin recoupe sa propre trajectoire, une règle de remplissage "
                    "décide quelles zones sont à l'intérieur. La règle par défaut d'un chemin, "
                    "<code>OddEvenFill</code>, part du point et trace une demi-droite dans "
                    "n'importe quelle direction. Elle compte combien de fois cette demi-droite "
                    "croise le contour. Un nombre impair : le point est à l'intérieur. Un nombre "
                    "pair : à l'extérieur."
                    "<br><br>Ici, <code>starPath()</code> rend une étoile autour de (0, 0). Ses "
                    "cinq sommets sont écrits dans l'ordre du tracé : chacun saute le sommet "
                    "voisin. Le trait recoupe donc sa propre trajectoire. <code>points[1:]</code> "
                    "est la liste sans son premier point. Comme la flèche de la notion 3.2, "
                    "l'étoile est placée par <code>translate()</code>. Le pentagone central reste "
                    "vide : depuis une pointe, on croise le contour une fois ; depuis le centre, "
                    "deux fois."
                ),
                run=self.drawOddEvenStar,
                codeSource=(starPath, self.drawOddEvenStar),
                references=[("Qt.FillRule", qtDocUrl("QtCore", "Qt", "FillRule"))],
            ),
            QStepWalkthrough.Step(
                title="Règle de remplissage : WindingFill",
                explanation=(
                    "La même étoile, à droite, avec "
                    "<code>setFillRule(Qt.FillRule.WindingFill)</code>. Cette règle compte "
                    "combien de tours le contour fait autour du point, dans un même sens. En "
                    "suivant le trait de l'étoile, on tourne deux fois autour du centre, et une "
                    "seule fois autour d'une pointe. Tout compte différent de zéro est à "
                    "l'intérieur : l'étoile est pleine."
                    "<br><br>La règle appartient au chemin, pas au peintre."
                ),
                run=self.drawWindingStar,
                references=[
                    ("QPainterPath.setFillRule", qtDocUrl("QtGui", "QPainterPath", "setFillRule")),
                    ("Qt.FillRule", qtDocUrl("QtCore", "Qt", "FillRule")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Opérations entre chemins",
                explanation=(
                    "L'image repart du blanc. Deux disques qui se chevauchent, a et b, en haut à "
                    "gauche. <code>a.united(b)</code>, <code>a.intersected(b)</code> et "
                    "<code>a.subtracted(b)</code> rendent chacune un nouveau chemin : l'union, "
                    "la partie commune, et a privé de b. Les chemins a et b ne changent pas."
                    "<br><br><code>translated(dx, dy)</code> rend lui aussi une copie, déplacée, "
                    "ici pour placer chaque résultat dans son quart d'image. Ces opérations "
                    "fabriquent des formes qu'aucune méthode de base ne dessine, comme ce "
                    "croissant de lune."
                ),
                run=self.drawOperations,
                references=[
                    ("QPainterPath.united", qtDocUrl("QtGui", "QPainterPath", "united")),
                    ("QPainterPath.intersected", qtDocUrl("QtGui", "QPainterPath", "intersected")),
                    ("QPainterPath.subtracted", qtDocUrl("QtGui", "QPainterPath", "subtracted")),
                    ("QPainterPath.translated", qtDocUrl("QtGui", "QPainterPath", "translated")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : déplacer les points de contrôle",
                explanation=(
                    "Quatre sélecteurs numériques paraissent sous le canevas. Ils règlent les "
                    "coordonnées des deux points de contrôle : <code>x1Slider</code> et "
                    "<code>y1Slider</code> pour le premier (120 et 60 au départ), "
                    "<code>x2Slider</code> et <code>y2Slider</code> pour le second (360 et 340). "
                    "x va de 0 à 480, y de 0 à 360."
                    "<br><br><code>connectControls()</code> relie les quatre signaux au slot "
                    "<code>redrawBezier()</code>. Il construit les deux points, puis appelle "
                    "<code>drawBezier()</code>, qui repart d'une image blanche et dessine la "
                    "courbe cubique entre deux extrémités fixes."
                    "<br><br>Croiser les deux contrôles pour faire une boucle. Les poser sur la "
                    "ligne des extrémités, à y = 200, pour obtenir une droite."
                ),
                run=self._exploreControls,
                codeSource=(self.connectControls, self.redrawBezier, self.drawBezier),
                references=[("QPainterPath.cubicTo", qtDocUrl("QtGui", "QPainterPath", "cubicTo"))],
            ),
        ]
