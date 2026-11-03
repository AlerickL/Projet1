"""Notion 3.2 : les transformations.

Contexte : plutôt que de recalculer les coordonnées d'une forme pour la
déplacer, la tourner ou l'agrandir, on transforme le repère du `QPainter`.
La forme, elle, est toujours dessinée de la même façon, autour de (0, 0).
Une seule forme sert toute la notion : une flèche pointée vers la droite.

Étapes couvertes : récapitulatif (une flèche placée à la main), la flèche
dessinée autour de l'origine, `translate()`, `rotate()` et son sens, l'ordre
des transformations, `scale()`, le stylo cosmétique, `shear()`,
`save()`/`restore()` pour isoler une transformation, et une rosace faite
d'une boucle de rotations. Translation, rotation, échelle et ordre se
règlent ensuite à la main.

Chaque étape est une méthode de `QTopicTransformsTab`, sauf la flèche, une
fonction du module. Les étapes dessinent dans la même image, `self.image`.
Celles qui changent de sujet repartent d'une image blanche (`fill`).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Slot
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


def drawArrow(painter: QPainter) -> None:
    """Dessine une flèche de 80 pixels vers la droite, queue sur (0, 0), et laisse au peintre un pinceau blanc."""
    painter.drawPolygon([
        QPointF(0, -10), QPointF(50, -10), QPointF(50, -22), QPointF(80, 0),
        QPointF(50, 22), QPointF(50, 10), QPointF(0, 10),
    ])
    painter.setBrush(QColor(255, 255, 255))
    painter.drawEllipse(QPointF(0, 0), 4, 4)


class QTopicTransformsTab(QWidget):
    """Onglet de la notion 3.2 : déplacer, tourner, agrandir le repère du peintre.

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
        dxSlider, dySlider, angleSlider, scaleSlider: Translation (pixels),
            rotation (degrés) et échelle (pour cent) de la flèche.
        orderCombo: L'ordre de la translation et de la rotation.
        image: La surface de la notion, ou None avant le récapitulatif.
    """

    TabTitle = "Transformations"
    TabToolTip = "translate(), rotate(), scale(), shear(), save() et restore(), l'ordre des transformations"
    RecommendedPanelWidth = 600
    Objective = (
        "Déplacer, tourner et agrandir le repère du peintre plutôt que les coordonnées de chaque "
        "forme, comprendre pourquoi l'ordre des transformations compte, et isoler une "
        "transformation avec <code>save()</code> et <code>restore()</code>."
    )
    KeyConcepts = [
        "Une transformation change le repère, pas la forme : la même flèche, dessinée autour de "
        "(0, 0), apparaît déplacée, tournée ou agrandie.",
        "Les transformations s'accumulent : chaque appel part du repère laissé par le "
        "précédent. Un peintre neuf part du repère de l'image.",
        "<code>rotate()</code> tourne autour de l'origine courante. Un angle positif tourne "
        "dans le sens horaire à l'écran.",
        "Le repère est une matrice, un <code>QTransform</code>. L'ordre des appels change le "
        "résultat, comme l'ordre d'un produit de matrices.",
        "<code>save()</code> mémorise l'état du peintre, <code>restore()</code> y revient.",
    ]
    KeyApis = [
        "QPainter.translate", "QPainter.rotate", "QPainter.scale", "QPainter.shear",
        "QPainter.save", "QPainter.restore", "QTransform", "QPen.isCosmetic", "QPen.setCosmetic",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.dxSlider = self.controls.addSlider("translate x", 0, 480, 200, suffix="px")
        self.dySlider = self.controls.addSlider("translate y", 0, 360, 120, suffix="px")
        self.angleSlider = self.controls.addSlider("rotate", -180, 180, 30, suffix="°")
        self.scaleSlider = self.controls.addSlider("scale", 25, 300, 100, suffix="%")
        self.orderCombo = self.controls.addComboBox("Ordre", [
            ("translate() puis rotate() (True)", True),
            ("rotate() puis translate() (False)", False),
        ])
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
        self.canvas.setGridVisible(False)
        self.image = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface blanche de 480 × 360 pixels, montre la grille, puis l'image."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setGridVisible(True)
        self.canvas.setImage(self.image)

    def drawArrowByHand(self) -> None:
        """Dessine une flèche grise dont la queue est au point (120, 80), chaque sommet calculé à la main."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(173, 181, 189))
            painter.drawPolygon([
                QPointF(120, 70), QPointF(170, 70), QPointF(170, 58), QPointF(200, 80),
                QPointF(170, 102), QPointF(170, 90), QPointF(120, 90),
            ])
        self.canvas.setImage(self.image)

    def drawArrowAtOrigin(self) -> None:
        """Dessine la flèche orange sans aucune transformation : autour de (0, 0)."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(230, 126, 34))
            drawArrow(painter)
        self.canvas.setImage(self.image)

    def drawTranslated(self) -> None:
        """Déplace l'origine deux fois, et dessine une flèche bleue après chaque fois."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(120, 80)
            painter.setBrush(QColor(46, 134, 222))
            drawArrow(painter)
            painter.translate(0, 100)
            painter.setBrush(QColor(46, 134, 222))
            drawArrow(painter)
        self.canvas.setImage(self.image)

    def drawRotated(self) -> None:
        """Repart d'une image blanche ; un arc de 0 à 90°, puis la flèche tournée de 90°."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(160, 180)
            painter.setBrush(QColor(173, 181, 189))
            drawArrow(painter)
            painter.setPen(QPen(QColor(231, 76, 60), 3))
            painter.drawArc(QRectF(-100, -100, 200, 200), 0 * 16, 90 * 16)
            painter.rotate(90)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setBrush(QColor(46, 134, 222))
            drawArrow(painter)
        self.canvas.setImage(self.image)

    def drawBothOrders(self) -> None:
        """Repart d'une image blanche ; deux peintres font les mêmes appels, dans deux ordres."""
        self.image.fill(Qt.GlobalColor.white)
        dashed = QPen(QColor(108, 117, 125), 1, Qt.PenStyle.DashLine)
        solid = QPen(QColor(0, 0, 0), 1)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(60, 60)
            painter.setBrush(QColor(173, 181, 189))
            drawArrow(painter)
            painter.setPen(dashed)
            painter.drawLine(0, 0, 220, 0)
            painter.translate(220, 0)
            painter.rotate(45)
            painter.setPen(solid)
            painter.setBrush(QColor(46, 134, 222))
            drawArrow(painter)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(60, 60)
            painter.rotate(45)
            painter.setPen(dashed)
            painter.drawLine(0, 0, 220, 0)
            painter.translate(220, 0)
            painter.setPen(solid)
            painter.setBrush(QColor(231, 76, 60))
            drawArrow(painter)
        self.canvas.setImage(self.image)

    def drawScaled(self) -> None:
        """Repart d'une image blanche ; la flèche agrandie, puis retournée, chacune par son peintre."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(40, 90)
            painter.scale(2, 2)
            painter.setBrush(QColor(155, 93, 229))
            drawArrow(painter)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(440, 90)
            painter.scale(-1.5, 1.5)
            painter.setBrush(QColor(241, 91, 181))
            drawArrow(painter)
        self.canvas.setImage(self.image)

    def drawCosmeticPen(self) -> None:
        """Repart d'une image blanche ; deux flèches agrandies 3 fois, stylo d'épaisseur 1 puis 0."""
        self.image.fill(Qt.GlobalColor.white)
        widePen = QPen(QColor(0, 0, 0), 1)
        cosmeticPen = QPen(QColor(0, 0, 0), 0)
        self.readout.setText(f"widePen.isCosmetic() -> {widePen.isCosmetic()}\n"
                             f"cosmeticPen.isCosmetic() -> {cosmeticPen.isCosmetic()}")
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(100, 90)
            painter.scale(3, 3)
            painter.setPen(widePen)
            painter.setBrush(QColor(46, 134, 222))
            drawArrow(painter)
            painter.translate(0, 57)
            painter.setPen(cosmeticPen)
            painter.setBrush(QColor(46, 134, 222))
            drawArrow(painter)
        self.canvas.setImage(self.image)

    def drawSheared(self) -> None:
        """Repart d'une image blanche ; un carré, puis le même carré cisaillé à l'horizontale."""
        self.readout.clear()
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(173, 181, 189))
            painter.translate(60, 120)
            painter.drawRect(0, 0, 100, 100)
            painter.translate(200, 0)
            painter.shear(0.5, 0)
            painter.setBrush(QColor(231, 111, 81))
            painter.drawRect(0, 0, 100, 100)
        self.canvas.setImage(self.image)

    def drawClock(self) -> None:
        """Repart d'une image blanche ; une horloge qui indique 10 h, chaque aiguille isolée."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(240, 180)
            painter.setBrush(QColor(241, 250, 238))
            painter.drawEllipse(QPointF(0, 0), 150, 150)
            painter.setBrush(QColor(231, 76, 60))

            painter.save()
            painter.rotate(-150)
            painter.setBrush(QColor(29, 53, 87))
            drawArrow(painter)
            painter.restore()

            painter.save()
            painter.rotate(-90)
            painter.scale(1.6, 0.7)
            painter.setBrush(QColor(46, 134, 222))
            drawArrow(painter)
            painter.restore()

            painter.drawEllipse(QPointF(0, 0), 8, 8)
            painter.setPen(QPen(QColor(0, 0, 0), 4))
            painter.drawLine(0, -150, 0, -125)
        self.canvas.setImage(self.image)

    def drawRosette(self) -> None:
        """Repart d'une image blanche ; douze pétales, une boucle de rotations."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(240, 180)
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            for index in range(12):
                painter.setBrush(QColor.fromHsv(index * 30, 150, 235))
                painter.drawEllipse(QRectF(10, -16, 150, 32))
                painter.rotate(30)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie les quatre sélecteurs numériques et la liste déroulante au slot qui redessine."""
        self.dxSlider.valueChanged.connect(self.redrawTransformedArrow)
        self.dySlider.valueChanged.connect(self.redrawTransformedArrow)
        self.angleSlider.valueChanged.connect(self.redrawTransformedArrow)
        self.scaleSlider.valueChanged.connect(self.redrawTransformedArrow)
        self.orderCombo.currentIndexChanged.connect(self.redrawTransformedArrow)

    @Slot()
    def redrawTransformedArrow(self) -> None:
        """Lit les cinq contrôles, convertit l'échelle de pour cent en facteur, puis redessine."""
        self.drawTransformedArrow(self.dxSlider.value(), self.dySlider.value(),
                                  self.angleSlider.value(), self.scaleSlider.value() / 100,
                                  self.orderCombo.currentData())

    def drawTransformedArrow(self, dx: int, dy: int, angle: int, factor: float,
                             translateFirst: bool) -> None:
        """Repart d'une image blanche ; la flèche grise, puis la flèche dans le repère transformé, et ses axes."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(173, 181, 189))
            drawArrow(painter)
            if translateFirst:
                painter.translate(dx, dy)
                painter.rotate(angle)
            else:
                painter.rotate(angle)
                painter.translate(dx, dy)
            painter.setPen(QPen(QColor(52, 58, 64), 1))
            painter.setFont(QFont("Georgia", 13))
            painter.drawText(170, -6, "x′")
            painter.drawText(6, 170, "y′")
            painter.scale(factor, factor)

            axisPen = QPen(QColor(108, 117, 125), 0)
            axisPen.setDashPattern([10, 6])
            painter.setPen(axisPen)
            painter.drawLine(-600, 0, 600, 0)
            painter.drawLine(0, -600, 0, 600)
            painter.setPen(QPen(QColor(0, 0, 0), 0))
            painter.setBrush(QColor(231, 111, 81))
            drawArrow(painter)
        self.canvas.setImage(self.image)

    def _exploreTransform(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine avec leurs valeurs de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawTransformedArrow()

    def _recap(self) -> None:
        """Crée la surface, puis dessine la flèche placée à la main."""
        self.createSurface()
        self.drawArrowByHand()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : une flèche placée à la main",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée l'image blanche et "
                    "affiche la grille (notion 1.1). Un polygone de sept sommets "
                    "(<code>QPointF</code>, notions 1.2 et 1.3), rempli de gris par le pinceau, "
                    "dessine une flèche. <code>setBrush()</code> y reçoit une couleur seule : le "
                    "raccourci de la notion 2.2. Sa queue est au point (120, 80)."
                    "<br><br>Pour la placer là, chaque sommet a été calculé à la main : 120 de "
                    "plus sur x, 80 de plus sur y. La placer ailleurs, ou la tourner, "
                    "obligerait à tout recalculer. Cette notion fait autrement : elle déplace "
                    "le repère."
                ),
                run=self._recap,
                codeSource=(self.createSurface, self.drawArrowByHand),
                references=[("QPainter.drawPolygon", qtDocUrl("QtGui", "QPainter", "drawPolygon"))],
            ),
            QStepWalkthrough.Step(
                title="Une flèche dessinée autour de (0, 0)",
                explanation=(
                    "La fonction <code>drawArrow(painter)</code> reçoit un peintre actif et "
                    "dessine toujours la même flèche : sa queue sur (0, 0), sa pointe sur "
                    "(80, 0). Un petit disque blanc marque sa queue. Elle ne rend rien."
                    "<br><br>Sans transformation, la flèche orange tombe dans le coin en haut à "
                    "gauche, à moitié hors de l'image : sa moitié haute a des y négatifs."
                    "<br><br><code>drawArrow()</code> change le pinceau du peintre pour son "
                    "disque blanc, et ne le remet pas. Chaque appel est donc précédé de "
                    "<code>setBrush()</code>, qui choisit la couleur de la flèche."
                ),
                run=self.drawArrowAtOrigin,
                codeSource=(drawArrow, self.drawArrowAtOrigin),
                references=[("QPainter.drawPolygon", qtDocUrl("QtGui", "QPainter", "drawPolygon"))],
            ),
            QStepWalkthrough.Step(
                title="translate() : déplacer l'origine",
                explanation=(
                    "<code>translate(120, 80)</code> déplace l'origine du repère au point "
                    "(120, 80) de l'image. La flèche bleue, dessinée autour de (0, 0), apparaît "
                    "donc là : elle recouvre exactement la flèche grise du récapitulatif, sans "
                    "aucun calcul."
                    "<br><br>Les transformations s'accumulent : <code>translate(0, 100)</code> "
                    "part de la nouvelle origine. La seconde flèche bleue a donc sa queue au "
                    "point (120, 180) de l'image."
                ),
                run=self.drawTranslated,
                references=[("QPainter.translate", qtDocUrl("QtGui", "QPainter", "translate"))],
            ),
            QStepWalkthrough.Step(
                title="rotate() : tourner autour de l'origine",
                explanation=(
                    "<code>rotate(angle)</code> tourne le repère autour de l'origine, d'un angle "
                    "en degrés. Un angle positif tourne dans le sens horaire de l'écran. L'image "
                    "repart du blanc. Ici, l'origine est déplacée en (160, 180), puis la flèche "
                    "grise y est dessinée. Après <code>rotate(90)</code>, la flèche bleue, "
                    "dessinée ensuite, pointe vers le bas."
                    "<br><br>L'arc rouge va de 0 à 90°, comme en notion 1.2 : il monte, dans le "
                    "sens antihoraire de l'écran. Pourquoi l'inverse de l'arc ? "
                    "<code>rotate()</code> applique la matrice de rotation des mathématiques. "
                    "Avec l'axe y vers le bas, elle tourne dans le sens horaire. Les angles de "
                    "<code>drawArc()</code>, eux, sont définis dans le sens antihoraire de "
                    "l'écran."
                    "<br><br>Le peintre range son repère dans une matrice, un "
                    "<code>QTransform</code>. Chaque <code>translate()</code> ou "
                    "<code>rotate()</code> la multiplie par la matrice de ce geste. C'est une "
                    "matrice 3 × 3. Une matrice 2 × 2 sait tourner et étirer, mais pas "
                    "déplacer : une troisième colonne porte donc la translation."
                ),
                run=self.drawRotated,
                references=[
                    ("QPainter.rotate", qtDocUrl("QtGui", "QPainter", "rotate")),
                    ("QTransform", qtDocUrl("QtGui", "QTransform")),
                ],
            ),
            QStepWalkthrough.Step(
                title="L'ordre compte : tourner sur place ou autour de l'origine",
                explanation=(
                    "L'ordre des transformations compte : les mêmes appels, dans deux ordres, "
                    "donnent deux repères différents. L'image repart du blanc. Ici, deux "
                    "peintres se suivent, chacun dans son bloc "
                    "<code>with</code>. Un peintre neuf part du repère de l'image, comme il part "
                    "du stylo par défaut (notion 2.1). Les deux font les mêmes appels, "
                    "<code>translate(220, 0)</code> et <code>rotate(45)</code>, à partir de la "
                    "flèche grise, mais dans deux ordres."
                    "<br><br>Bleu : on avance de 220 pixels vers la droite, puis on tourne. La "
                    "flèche tourne sur place, autour de sa queue. Rouge : on tourne d'abord, et "
                    "l'axe x tourne avec le repère. <code>translate(220, 0)</code> avance alors "
                    "de 220 pixels le long de l'axe tourné, en diagonale. Les tirets "
                    "montrent chaque trajet."
                    "<br><br>Le produit de deux matrices dépend de leur ordre : c'est la même "
                    "chose ici. Pour tourner une forme sur elle-même, on déplace d'abord "
                    "l'origine sur son pivot, puis on tourne."
                ),
                run=self.drawBothOrders,
                references=[
                    ("QPainter.translate", qtDocUrl("QtGui", "QPainter", "translate")),
                    ("QPainter.rotate", qtDocUrl("QtGui", "QPainter", "rotate")),
                ],
            ),
            QStepWalkthrough.Step(
                title="scale() : agrandir, réduire, retourner",
                explanation=(
                    "L'image repart du blanc. <code>scale(2, 2)</code> multiplie par 2 toutes "
                    "les longueurs : celles de x, puis celles de y. L'épaisseur du contour est "
                    "doublée aussi : le trait d'un pixel en fait maintenant deux."
                    "<br><br>Un facteur négatif retourne le repère. Avec <code>scale(-1.5, "
                    "1.5)</code>, la flèche rose pointe vers la gauche. Chaque flèche a son "
                    "peintre, donc son propre repère."
                ),
                run=self.drawScaled,
                references=[("QPainter.scale", qtDocUrl("QtGui", "QPainter", "scale"))],
            ),
            QStepWalkthrough.Step(
                title="Le stylo cosmétique : une épaisseur qui ignore l'échelle",
                explanation=(
                    "Un stylo d'épaisseur 0 est <b>cosmétique</b> : il trace toujours un pixel, "
                    "quelle que soit l'échelle. L'image repart du blanc. Ici, deux flèches dans "
                    "le même repère, agrandi 3 fois par <code>scale(3, 3)</code>. La flèche du "
                    "haut a un stylo d'épaisseur 1 : son contour fait 3 pixels. La flèche du bas "
                    "a un stylo d'épaisseur 0 : son contour reste à 1 pixel. Entre les deux, "
                    "<code>translate(0, 57)</code> agit dans le repère agrandi : 57 unités, soit "
                    "171 pixels vers le bas."
                    "<br><br>L'accesseur <code>isCosmetic()</code> "
                    "le dit : <code>False</code> pour <code>widePen</code>, <code>True</code> "
                    "pour <code>cosmeticPen</code>. Son mutateur, <code>setCosmetic(True)</code>, "
                    "rend cosmétique un stylo de n'importe quelle épaisseur : un stylo de 3 "
                    "pixels garde alors ses 3 pixels, quelle que soit l'échelle. Un stylo "
                    "cosmétique sert à tracer un repère ou une grille fine dans un dessin "
                    "agrandi."
                ),
                run=self.drawCosmeticPen,
                references=[
                    ("QPen.isCosmetic", qtDocUrl("QtGui", "QPen", "isCosmetic")),
                    ("QPen.setCosmetic", qtDocUrl("QtGui", "QPen", "setCosmetic")),
                ],
            ),
            QStepWalkthrough.Step(
                title="shear() : cisailler",
                explanation=(
                    "L'image repart du blanc, et la lecture se cache. <code>shear(0.5, "
                    "0)</code> décale chaque point vers la droite de la moitié de son y : x "
                    "devient x + 0,5 × y. Le carré devient un parallélogramme. Son bord haut "
                    "(y = 0) ne bouge pas, son bord bas (y = 100) glisse de 50 pixels. "
                    "<code>shear(0, 0.5)</code> ferait de même à la verticale."
                ),
                run=self.drawSheared,
                references=[("QPainter.shear", qtDocUrl("QtGui", "QPainter", "shear"))],
            ),
            QStepWalkthrough.Step(
                title="save() et restore() : isoler une transformation",
                explanation=(
                    "<code>save()</code> mémorise l'état du peintre : repère, stylo, pinceau et "
                    "police. <code>restore()</code> y revient. Entre les deux, on tourne et on "
                    "étire à volonté. Chaque <code>save()</code> a son <code>restore()</code>."
                    "<br><br>L'image repart du blanc. Ici, une horloge indique 10 h : l'aiguille "
                    "des heures est sur le 10, celle des minutes sur le 12. Chaque aiguille a sa "
                    "propre rotation, autour du même centre. <code>scale(1.6, 0.7)</code> allonge "
                    "la flèche et l'amincit : l'aiguille des minutes est plus longue et plus "
                    "fine."
                    "<br><br>Deux preuves, à la fin. Le pinceau est redevenu rouge : le disque "
                    "central n'est pas blanc, malgré <code>drawArrow()</code>. Le repère n'est "
                    "plus tourné : le trait noir, de (0, -150) à (0, -125), tombe bien sur midi."
                ),
                run=self.drawClock,
                references=[
                    ("QPainter.save", qtDocUrl("QtGui", "QPainter", "save")),
                    ("QPainter.restore", qtDocUrl("QtGui", "QPainter", "restore")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une rosace : une boucle de rotations",
                explanation=(
                    "Une boucle de rotations répète un motif autour de l'origine : le motif est "
                    "dessiné toujours au même endroit, et le repère tourne entre deux dessins. "
                    "L'image repart du blanc. Ici, le motif est un pétale : une ellipse allongée "
                    "à droite de l'origine. Après chaque pétale, "
                    "<code>rotate(30)</code> tourne le repère. Les rotations s'accumulent : "
                    "douze pétales font le tour complet, 12 × 30° = 360°. La teinte change à "
                    "chaque tour (HSV, notion 2.3). Aucun sinus ni cosinus à calculer."
                ),
                run=self.drawRosette,
                references=[("QPainter.rotate", qtDocUrl("QtGui", "QPainter", "rotate"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : translation, rotation, échelle et ordre",
                explanation=(
                    "Cinq contrôles paraissent sous le canevas :"
                    "<ul>"
                    "<li><code>dxSlider</code> et <code>dySlider</code> règlent la translation, "
                    "de 0 à 480 pixels (200 au départ) et de 0 à 360 (120 au départ) ;</li>"
                    "<li><code>angleSlider</code> règle la rotation, de −180 à 180° (30 au "
                    "départ) ;</li>"
                    "<li><code>scaleSlider</code> règle l'échelle, de 25 à 300 % (100 au "
                    "départ) ;</li>"
                    "<li>la liste déroulante <code>orderCombo</code> choisit l'ordre : "
                    "<code>currentData()</code> rend <code>True</code> pour "
                    "<code>translate()</code> puis <code>rotate()</code>, <code>False</code> "
                    "pour l'inverse. Elle part de <code>translate()</code> puis "
                    "<code>rotate()</code>.</li></ul>"
                    "<br><br><code>connectControls()</code> relie les cinq signaux au slot "
                    "<code>redrawTransformedArrow()</code>. Il lit les contrôles, divise l'échelle "
                    "par 100 pour en faire un facteur, puis appelle "
                    "<code>drawTransformedArrow()</code>. Celle-ci repart d'une image blanche, "
                    "dessine la flèche grise sans transformation, puis la flèche orange dans le "
                    "repère transformé."
                    "<ul>"
                    "<li>Les tirets montrent les axes de ce repère. Le stylo cosmétique, "
                    "<code>axisPen</code>, les garde fins à toute échelle. Son motif "
                    "<code>[10, 6]</code> (notion 2.1) se compte en épaisseurs de stylo ; un "
                    "stylo d'épaisseur 0 compte comme un stylo d'un pixel. Les tirets font donc "
                    "10 pixels et les espaces 6, à toute échelle.</li>"
                    "<li>Les étiquettes x′ et y′ sont écrites après la rotation, mais avant "
                    "<code>scale()</code> : elles tournent avec les axes, sans changer de taille, "
                    "à 170 pixels de l'origine.</li></ul>"
                    "<br><br>Avec une rotation non nulle, changer l'ordre : la flèche saute "
                    "ailleurs."
                ),
                run=self._exploreTransform,
                codeSource=(self.connectControls, self.redrawTransformedArrow,
                            self.drawTransformedArrow),
                references=[
                    ("QPainter.translate", qtDocUrl("QtGui", "QPainter", "translate")),
                    ("QPainter.rotate", qtDocUrl("QtGui", "QPainter", "rotate")),
                    ("QPainter.scale", qtDocUrl("QtGui", "QPainter", "scale")),
                ],
            ),
        ]
