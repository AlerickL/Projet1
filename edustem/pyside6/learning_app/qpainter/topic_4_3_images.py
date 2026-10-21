"""Notion 4.3 : les images.

Contexte : un peintre (`QPainter`) peut dessiner sur n'importe quelle `QImage`,
pas seulement sur la surface de la notion. On fabrique donc ici une petite
image à part, une planche de quatre icônes, en la dessinant soi-même. On la
dessine ensuite dans la surface, entière ou en partie, agrandie, répétée ou
translucide. Aucune image externe n'est chargée.

Étapes couvertes : récapitulatif (les quatre icônes, agrandies par
`scale`), une seconde image plus petite et `drawImage`, la mise à l'échelle
(rectangle cible), le lissage (`SmoothPixmapTransform`), une portion
(rectangle source), une mosaïque, l'opacité (`setOpacity`), lire un pixel
(`pixelColor`), écrire des pixels (`setPixelColor`), puis la taille cible,
la portion source et l'opacité réglées à la main.

Chaque étape est une méthode de `QTopicImagesTab`, sauf les icônes, une
fonction du module. Les étapes dessinent dans la même image, `self.image`.
Celles qui changent de sujet repartent d'une image blanche ou transparente
(`fill`).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, Qt, Slot
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


def drawIcons(painter: QPainter) -> None:
    """Dessine, avec anticrénelage et sans contour, quatre icônes dans un carré de 64 × 64 : disque, carré arrondi, triangle et losange."""
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(225, 112, 85))
    painter.drawEllipse(4, 4, 24, 24)
    painter.setBrush(QColor(0, 184, 148))
    painter.drawRoundedRect(36, 4, 24, 24, 5, 5)
    painter.setBrush(QColor(9, 132, 227))
    painter.drawPolygon([QPointF(16, 36), QPointF(28, 60), QPointF(4, 60)])
    painter.setBrush(QColor(253, 203, 110))
    painter.drawPolygon([QPointF(48, 36), QPointF(60, 48), QPointF(48, 60), QPointF(36, 48)])


class QTopicImagesTab(QWidget):
    """Onglet de la notion 4.3 : fabriquer une image, puis la dessiner dans une autre.

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
        sizeSlider, portionCombo, opacitySlider: La taille cible, la portion
            source et l'opacité de la planche.
        image: La surface de la notion, ou None avant le récapitulatif.
        sheet: La planche de quatre icônes (64 × 64 pixels), ou None avant
            l'étape qui la fabrique.
    """

    TabTitle = "Images"
    TabToolTip = "Dessiner dans une QImage à part, puis drawImage : échelle, portion, mosaïque, opacité, pixels"
    RecommendedPanelWidth = 600
    Objective = (
        "Fabriquer une image en la dessinant avec un peintre, puis la dessiner dans une autre : "
        "entière ou en partie, agrandie, répétée, translucide. Lire et écrire un pixel précis."
    )
    KeyConcepts = [
        "Un peintre peut dessiner sur n'importe quelle <code>QImage</code> : on peut fabriquer ses "
        "propres images.",
        "Le rectangle cible fixe la taille du dessin ; le rectangle source choisit la portion de "
        "l'image.",
        "Sans lissage, une image agrandie montre ses pixels ; avec lissage, elle devient floue.",
        "L'opacité du peintre s'applique à tout ce qu'il dessine ensuite, images comprises.",
        "Une image est une grille de pixels, qu'on peut lire et écrire un par un.",
    ]
    KeyApis = [
        "QPainter.drawImage", "QPainter.RenderHint.SmoothPixmapTransform", "QPainter.setOpacity",
        "QImage.pixelColor", "QImage.setPixelColor",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None
        self.sheet: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.sizeSlider = self.controls.addSlider("Taille cible", 16, 340, 160, suffix="px")
        self.portionCombo = self.controls.addComboBox("Portion source", [
            ("Planche entière, QRect(0, 0, 64, 64)", QRect(0, 0, 64, 64)),
            ("Disque, QRect(0, 0, 32, 32)", QRect(0, 0, 32, 32)),
            ("Carré, QRect(32, 0, 32, 32)", QRect(32, 0, 32, 32)),
            ("Triangle, QRect(0, 32, 32, 32)", QRect(0, 32, 32, 32)),
            ("Losange, QRect(32, 32, 32, 32)", QRect(32, 32, 32, 32)),
        ])
        self.opacitySlider = self.controls.addSlider("Opacité", 0, 100, 100, suffix="%")
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
        self.sheet = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface blanche de 480 × 360 pixels, et la montre."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setImage(self.image)

    def drawLargeIcons(self) -> None:
        """Dessine les quatre icônes dans la surface, agrandies 4 fois."""
        with QPainter(self.image) as painter:
            painter.translate(112, 52)
            painter.scale(4, 4)
            drawIcons(painter)
        self.canvas.setImage(self.image)

    def makeSheet(self) -> None:
        """Repart d'une image blanche ; fabrique la planche de 64 × 64 pixels, puis la dessine dans la surface."""
        self.image.fill(Qt.GlobalColor.white)
        self.sheet = QImage(64, 64, QImage.Format.Format_ARGB32)
        self.sheet.fill(QColor(223, 230, 233))
        with QPainter(self.sheet) as painter:
            drawIcons(painter)
        with QPainter(self.image) as painter:
            painter.drawImage(20, 20, self.sheet)
        self.canvas.setImage(self.image)

    def drawScaledSheet(self) -> None:
        """Dessine la planche dans un rectangle cible de 160 × 160 pixels : elle est agrandie pour le remplir."""
        with QPainter(self.image) as painter:
            painter.drawImage(QRect(110, 20, 160, 160), self.sheet)
        self.canvas.setImage(self.image)

    def drawSmoothSheet(self) -> None:
        """Dessine la même planche agrandie, avec le lissage SmoothPixmapTransform."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(QRect(300, 20, 160, 160), self.sheet)
        self.canvas.setImage(self.image)

    def drawSheetPortions(self) -> None:
        """Dessine seulement deux cases de la planche, choisies par un rectangle source."""
        triangleCell = QRect(0, 32, 32, 32)
        diamondCell = QRect(32, 32, 32, 32)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(QRect(20, 200, 140, 140), self.sheet, triangleCell)
            painter.drawImage(QRect(180, 200, 140, 140), self.sheet, diamondCell)
        self.canvas.setImage(self.image)

    def drawMosaicExplicit(self) -> None:
        """Repart d'une image transparente, puis répète la planche à la main, sur la gauche, en trois rangées."""
        self.image.fill(Qt.GlobalColor.transparent)
        with QPainter(self.image) as painter:
            for y in range(0, 192, 64):
                for x in range(0, 256, 64):
                    painter.drawImage(x, y, self.sheet)
        self.canvas.setImage(self.image)

    def drawMosaicWithBrush(self) -> None:
        """Continue la mosaïque sur la droite, d'un seul fillRect() avec un pinceau fait de la planche."""
        with QPainter(self.image) as painter:
            painter.fillRect(256, 0, 224, 192, QBrush(self.sheet))
        self.canvas.setImage(self.image)

    def drawWithOpacity(self) -> None:
        """Dessine trois copies de la planche, de plus en plus transparentes, grâce à setOpacity()."""
        opacities = [1.0, 0.6, 0.25]
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            for index, opacity in enumerate(opacities):
                painter.setOpacity(opacity)
                painter.drawImage(QRect(40 + 150 * index, 225, 100, 100), self.sheet)
        self.canvas.setImage(self.image)

    def readPixels(self) -> None:
        """Repart d'une image blanche, agrandit la planche 4 fois, puis lit deux de ses pixels et les entoure."""
        self.image.fill(Qt.GlobalColor.white)
        disc = self.sheet.pixelColor(16, 16)
        background = self.sheet.pixelColor(1, 1)
        self.readout.setText(f"sheet.pixelColor(16, 16) -> {disc.name()}, alpha {disc.alpha()}\n"
                             f"sheet.pixelColor(1, 1) -> {background.name()}, alpha {background.alpha()}")
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.drawImage(QRect(20, 20, 256, 256), self.sheet)
            painter.setPen(QPen(QColor(45, 52, 54), 2))
            painter.drawEllipse(QPointF(20 + (16 + 0.5) * 4, 20 + (16 + 0.5) * 4), 7, 7)
            painter.drawEllipse(QPointF(20 + (1 + 0.5) * 4, 20 + (1 + 0.5) * 4), 7, 7)
        self.canvas.setImage(self.image)

    def writePixels(self) -> None:
        """Fabrique un cœur de 11 × 9 pixels, pixel par pixel, puis le dessine agrandi 12 fois et à sa taille."""
        self.readout.clear()
        rows = [
            "..##...##..",
            ".####.####.",
            "###########",
            "###########",
            ".#########.",
            "..#######..",
            "...#####...",
            "....###....",
            ".....#.....",
        ]
        heart = QImage(11, 9, QImage.Format.Format_ARGB32)
        heart.fill(Qt.GlobalColor.transparent)
        for y in range(9):
            row = rows[y]
            for x in range(11):
                if row[x] == "#":
                    heart.setPixelColor(x, y, QColor(214, 48, 49))
        with QPainter(self.image) as painter:
            painter.drawImage(QRect(300, 40, 132, 108), heart)
            painter.drawImage(445, 90, heart)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie les deux sélecteurs numériques et la liste déroulante au slot qui redessine."""
        self.sizeSlider.valueChanged.connect(self.redrawSheetPortion)
        self.portionCombo.currentIndexChanged.connect(self.redrawSheetPortion)
        self.opacitySlider.valueChanged.connect(self.redrawSheetPortion)

    @Slot()
    def redrawSheetPortion(self) -> None:
        """Lit les trois contrôles, convertit l'opacité de pour cent en fraction, puis redessine."""
        self.drawSheetPortion(self.sizeSlider.value(), self.portionCombo.currentData(),
                              self.opacitySlider.value() / 100)

    def drawSheetPortion(self, size: int, source: QRect, opacity: float) -> None:
        """Repart d'une image transparente ; la portion source de la planche, centrée dans un carré de size pixels."""
        self.image.fill(Qt.GlobalColor.transparent)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.setOpacity(opacity)
            painter.drawImage(QRect(240 - size // 2, 180 - size // 2, size, size), self.sheet,
                              source)
        self.canvas.setImage(self.image)

    def _exploreImage(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine avec leurs valeurs de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawSheetPortion()

    def _recap(self) -> None:
        """Crée la surface, puis dessine les icônes agrandies du récapitulatif."""
        self.createSurface()
        self.drawLargeIcons()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        drawImageUrl = qtDocUrl("QtGui", "QPainter", "drawImage")
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : quatre icônes",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée l'image blanche (notion "
                    "1.1). <code>drawIcons(painter)</code> reçoit un peintre actif et dessine "
                    "quatre formes pleines sans contour (notions 1.2 et 2.2), dans un carré de "
                    "64 × 64. Elle ne rend rien. <code>drawRoundedRect()</code> y reçoit ses "
                    "nombres un à un, comme à la notion 2.3. Ici, <code>translate()</code> et "
                    "<code>scale(4, 4)</code> (notion 3.2) les agrandissent 4 fois."
                    "<br><br>Ces quatre formes sont aussi l'icône de l'application, dans la barre "
                    "de titre : la même fonction les y dessine, à chaque taille d'icône."
                ),
                run=self._recap,
                codeSource=(drawIcons, self.createSurface, self.drawLargeIcons),
                references=[("QPainter.scale", qtDocUrl("QtGui", "QPainter", "scale"))],
            ),
            QStepWalkthrough.Step(
                title="Une seconde image, plus petite",
                explanation=(
                    "L'image repart du blanc. Un peintre peut dessiner sur n'importe quelle "
                    "<code>QImage</code>, pas seulement sur la surface de la notion. On en crée "
                    "donc une seconde, la planche (<code>self.sheet</code>), de 64 × 64 pixels, "
                    "comme en notion 1.1. Ses pixels ne sont pas initialisés à la création : "
                    "<code>fill()</code> la remplit d'abord de gris clair."
                    "<br><br>Un premier peintre dessine les quatre icônes sur la planche, à leur "
                    "taille réelle. Un second dessine la planche terminée dans la surface, par "
                    "<code>drawImage(x, y, image)</code> : le coin haut gauche de la planche va au "
                    "point (20, 20)."
                ),
                run=self.makeSheet,
                references=[
                    ("QImage", qtDocUrl("QtGui", "QImage")),
                    ("QPainter.drawImage", drawImageUrl),
                ],
            ),
            QStepWalkthrough.Step(
                title="Mettre à l'échelle : le rectangle cible",
                explanation=(
                    "Avec un <code>QRect</code> au lieu d'un point, <code>drawImage()</code> "
                    "étire la planche pour remplir ce rectangle cible : ici 160 × 160 pixels, 2,5 "
                    "fois la taille réelle. Par défaut, chaque pixel de la planche est simplement "
                    "répété : les bords en escalier du disque et du triangle apparaissent. Un "
                    "rectangle cible d'une autre proportion déformerait la planche."
                ),
                run=self.drawScaledSheet,
                references=[("QPainter.drawImage", drawImageUrl)],
            ),
            QStepWalkthrough.Step(
                title="Lisser l'agrandissement",
                explanation=(
                    "<code>setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)</code> fait "
                    "calculer chaque pixel agrandi à partir de ses voisins. Les escaliers "
                    "disparaissent, mais la planche agrandie devient un peu floue. Ce réglage est distinct de "
                    "<code>Antialiasing</code> (notion 1.3), qui ne concerne que les formes. Son "
                    "nom vient de <code>QPixmap</code>, une autre classe d'image de Qt, faite "
                    "pour l'affichage à l'écran ; il vaut aussi pour une <code>QImage</code>."
                ),
                run=self.drawSmoothSheet,
                references=[("QPainter.RenderHint", qtDocUrl("QtGui", "QPainter", "RenderHint"))],
            ),
            QStepWalkthrough.Step(
                title="Une portion : le rectangle source",
                explanation=(
                    "Un troisième argument, le rectangle source, choisit la portion de la planche à "
                    "dessiner, dans le repère de la planche. Ici, la case du bas à gauche (le "
                    "triangle), puis celle du bas à droite (le losange), chacune agrandie dans son "
                    "rectangle cible. C'est le principe d'une planche d'images (en anglais, "
                    "<i>sprite sheet</i>) : toutes les icônes d'un jeu dans une seule image, dont "
                    "on découpe la case voulue."
                ),
                run=self.drawSheetPortions,
                references=[("QPainter.drawImage", drawImageUrl)],
            ),
            QStepWalkthrough.Step(
                title="Une mosaïque",
                explanation=(
                    "L'image repart entièrement transparente (notion 2.3). Deux boucles répètent "
                    "la planche tous les 64 pixels : quatre colonnes, de x = 0 à 255, sur trois "
                    "rangées. Chaque planche est un appel de <code>drawImage()</code>."
                ),
                run=self.drawMosaicExplicit,
                references=[("QPainter.drawImage", drawImageUrl)],
            ),
            QStepWalkthrough.Step(
                title="La même mosaïque, avec un pinceau",
                explanation=(
                    "Un pinceau peut être fait d'une image : <code>QBrush(self.sheet)</code>. "
                    "Il remplit alors en répétant la planche, comme une mosaïque. Un seul "
                    "<code>fillRect()</code> (notion 2.2) couvre ici toute la droite, de x = 256 "
                    "à 479 : aucune boucle."
                    "<br><br>La mosaïque continue sans raccord. Le pinceau répète la planche à partir "
                    "de l'origine du repère, (0, 0), et non du coin du rectangle rempli : 256 "
                    "étant un multiple de 64, ses planches tombent exactement dans le "
                    "prolongement des autres. La dernière colonne dépasse de l'image : la partie "
                    "qui sort est simplement ignorée (notion 1.1)."
                ),
                run=self.drawMosaicWithBrush,
                references=[
                    ("QBrush", qtDocUrl("QtGui", "QBrush")),
                    ("QPainter.fillRect", qtDocUrl("QtGui", "QPainter", "fillRect")),
                ],
            ),
            QStepWalkthrough.Step(
                title="L'opacité : setOpacity()",
                explanation=(
                    "<code>setOpacity()</code> rend translucide tout ce que le peintre dessine "
                    "ensuite, images comprises, de 0,0 (invisible) à 1,0 (opaque). Les trois "
                    "copies sont dessinées à 1,0, 0,6 et 0,25 : le damier apparaît à travers. "
                    "L'opacité reste en vigueur jusqu'au prochain <code>setOpacity()</code>. Un "
                    "peintre neuf repart à 1,0."
                ),
                run=self.drawWithOpacity,
                references=[("QPainter.setOpacity", qtDocUrl("QtGui", "QPainter", "setOpacity"))],
            ),
            QStepWalkthrough.Step(
                title="Lire un pixel : pixelColor()",
                explanation=(
                    "L'image repart du blanc, et la planche y est agrandie 4 fois. "
                    "<code>pixelColor(x, y)</code> rend la couleur d'un pixel de la planche, sous "
                    "forme de <code>QColor</code>. La lecture affiche les deux couleurs lues, "
                    "écrites par <code>name()</code> en hexadécimal (notion 2.3), avec leur "
                    "alpha : le centre du disque, puis le fond."
                    "<br><br>Les deux cercles entourent ces pixels sur la planche agrandie. Le "
                    "centre du pixel (16, 16) est au point (16,5 ; 16,5), à la demi-coordonnée "
                    "(notion 1.3). Agrandi 4 fois et décalé de 20 : "
                    "<code>20 + (16 + 0.5) * 4</code>."
                ),
                run=self.readPixels,
                references=[("QImage.pixelColor", qtDocUrl("QtGui", "QImage", "pixelColor"))],
            ),
            QStepWalkthrough.Step(
                title="Écrire des pixels : setPixelColor()",
                explanation=(
                    "La lecture se cache. <code>setPixelColor(x, y, couleur)</code> fixe un seul "
                    "pixel, sans peintre. Une liste de chaînes décrit un cœur de 11 × 9 pixels : "
                    "chaque <code>#</code> devient un pixel rouge. <code>row[x]</code> est le "
                    "caractère de rang x de la chaîne."
                    "<br><br>Dessiné agrandi 12 fois, sans lissage, le cœur montre chacun de ses "
                    "pixels. À sa taille réelle, à droite, il est minuscule. Pour de vraies "
                    "formes, un peintre reste bien plus commode : <code>setPixelColor()</code> "
                    "sert aux effets pixel par pixel."
                ),
                run=self.writePixels,
                references=[("QImage.setPixelColor", qtDocUrl("QtGui", "QImage", "setPixelColor"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : taille, portion et opacité",
                explanation=(
                    "Trois contrôles paraissent sous le canevas :"
                    "<ul>"
                    "<li>le sélecteur numérique <code>sizeSlider</code> règle le côté du "
                    "rectangle cible, de 16 à 340 pixels (160 au départ) ;</li>"
                    "<li>la liste déroulante <code>portionCombo</code> choisit le rectangle "
                    "source : la planche entière (au départ) ou une de ses quatre cases. Chaque "
                    "choix porte son <code>QRect</code>, écrit dans le libellé, et "
                    "<code>currentData()</code> le rend ;</li>"
                    "<li>le sélecteur numérique <code>opacitySlider</code> règle l'opacité de 0 à "
                    "100 % (100 au départ).</li></ul>"
                    "<br><br><code>connectControls()</code> relie les trois signaux au slot "
                    "<code>redrawSheetPortion()</code>. Il lit les contrôles, divise l'opacité par "
                    "100, puis appelle <code>drawSheetPortion()</code>. Celle-ci repart d'une "
                    "image transparente et dessine la portion au centre de l'image."
                    "<br><br>Essayer une petite taille, puis une grande : la portion est réduite "
                    "ou agrandie pour remplir le rectangle cible. Choisir une case : seule cette "
                    "portion est dessinée, à la taille choisie. Baisser l'opacité : le damier du "
                    "canevas paraît à travers."
                ),
                run=self._exploreImage,
                codeSource=(self.connectControls, self.redrawSheetPortion, self.drawSheetPortion),
                references=[
                    ("QPainter.drawImage", drawImageUrl),
                    ("QPainter.setOpacity", qtDocUrl("QtGui", "QPainter", "setOpacity")),
                ],
            ),
        ]
