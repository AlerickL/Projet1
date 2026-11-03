"""Notion 1.3 : la qualité du trait.

Contexte : un trait qui paraît net à l'échelle 1 se révèle, agrandi pixel par
pixel, fait de marches d'escalier ou de pixels gris. Cette notion montre
d'où viennent ces défauts, et comment obtenir un trait lisse ou parfaitement
net. L'agrandissement du canevas, présenté à la première étape, montre
chaque fois une petite portion de l'image, agrandie huit fois.

Étapes couvertes : le récapitulatif de la surface, une diagonale et un cercle sans anticrénelage,
l'anticrénelage (`setRenderHint`), un trait d'un pixel sur une coordonnée
entière puis sur une demi-coordonnée, `QPoint` qui tronque en silence, la
version entière de `drawLine`, le même essai sans anticrénelage, un trait
de 2 pixels, puis le mélange des couleurs du trait et du fond. Deux cases à
cocher, un sélecteur numérique et deux listes déroulantes règlent ensuite
anticrénelage, décalage d'un demi-pixel, épaisseur et couleurs.

Chaque étape est une méthode de `QTopicStrokeQualityTab`. Les étapes
dessinent dans la même image, `self.image`, et la redonnent au canevas à la
fin.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, QRect, Qt, Slot
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl, qtPageUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


# Les couleurs des deux listes déroulantes de l'étape « À vous » : nom et couleur.
_PatternColors = [
    ("Bleu nuit", QColor(29, 53, 87)),
    ("Bleu", QColor(0, 0, 255)),
    ("Jaune", QColor(255, 255, 0)),
    ("Rouge", QColor(230, 57, 70)),
    ("Blanc", QColor(255, 255, 255)),
    ("Noir", QColor(0, 0, 0)),
]


class QTopicStrokeQualityTab(QWidget):
    """Onglet de la notion 1.3 : escalier, anticrénelage et demi-coordonnée.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Contenu de l'étape "Vue d'ensemble",
            construite automatiquement par `QStepWalkthrough`.

    Attributs d'instance:
        canvas: Le canevas qui affiche l'image (outil présenté en 1.1 ; son
            agrandissement est présenté ici).
        readout: La lecture sous le canevas (outil présenté ici).
        controls: Le panneau des contrôles de l'étape « À vous » (plomberie).
        antialiasingCheck, halfPixelCheck, widthSlider: L'anticrénelage, le
            décalage d'un demi-pixel et l'épaisseur du motif d'essai.
        strokeColorCombo, backgroundColorCombo: La couleur du trait et celle
            du fond.
        image: La surface de la notion, ou None avant la première étape.
    """

    TabTitle = "Qualité du trait"
    TabToolTip = "Escalier, anticrénelage, coordonnées entières et demi-coordonnées, agrandis pixel par pixel"
    RecommendedPanelWidth = 640
    Objective = (
        "Comprendre ce qui rend un trait dentelé, flou ou net à l'échelle du pixel, et savoir "
        "obtenir un trait lisse ou parfaitement net."
    )
    KeyConcepts = [
        "Sans anticrénelage, chaque pixel est plein ou vide : une oblique avance par marches.",
        "L'anticrénelage colore les pixels du bord selon la part que le trait en couvre.",
        "Le centre d'un pixel est à la demi-coordonnée : un trait d'un pixel y est net, sur une "
        "coordonnée entière il est flou.",
        "Les types entiers (<code>QPoint</code>, et <code>drawLine</code> avec quatre nombres) "
        "coupent en silence la partie décimale des coordonnées ; <code>QPointF</code> les garde "
        "réelles.",
        "Un trait d'épaisseur paire est net sur une coordonnée entière.",
        "L'anticrénelage mélange la couleur du trait et celle du fond, composante par "
        "composante : un même trait n'a pas les mêmes bords sur deux fonds.",
    ]
    KeyApis = [
        "QPainter.setRenderHint", "QPainter.RenderHint", "QPointF", "QPoint",
        "QPainter.drawLine",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.antialiasingCheck = self.controls.addCheckBox("Anticrénelage", checked=True)
        self.halfPixelCheck = self.controls.addCheckBox("Décalage d'un demi-pixel (+0,5)", checked=True)
        self.widthSlider = self.controls.addSlider("Épaisseur", 1, 6, 1, suffix="px")
        self.strokeColorCombo = self.controls.addComboBox("Trait", _PatternColors, currentIndex=0)
        self.backgroundColorCombo = self.controls.addComboBox("Fond", _PatternColors, currentIndex=4)
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
        self.canvas.setViewRect(None)
        self.image = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface blanche de 480 × 360 pixels, et la montre."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setImage(self.image)

    def drawAliasedShapes(self) -> None:
        """Agrandit le coin haut gauche, puis y trace une diagonale et un cercle, sans anticrénelage."""
        self.canvas.setViewRect(QRect(0, 0, 60, 45))
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(29, 53, 87), 1))
            painter.drawLine(4, 6, 28, 14)
            painter.drawEllipse(QPointF(44, 11), 8, 8)
        self.canvas.setImage(self.image)

    def drawAntialiasedShapes(self) -> None:
        """Les mêmes formes, 22 pixels plus bas, avec anticrénelage."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(29, 53, 87), 1))
            painter.drawLine(4, 28, 28, 36)
            painter.drawEllipse(QPointF(44, 33), 8, 8)
        self.canvas.setImage(self.image)

    def drawOnInteger(self) -> None:
        """Agrandit une nouvelle portion, puis trace un trait d'un pixel sur y = 66."""
        self.canvas.setViewRect(QRect(0, 60, 60, 45))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(29, 53, 87), 1))
            painter.drawLine(QPointF(4, 66), QPointF(56, 66))
        self.canvas.setImage(self.image)

    def drawOnHalf(self) -> None:
        """Le même trait, sur la demi-coordonnée y = 72.5."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(29, 53, 87), 1))
            painter.drawLine(QPointF(4, 72.5), QPointF(56, 72.5))
        self.canvas.setImage(self.image)

    def drawWithQPoint(self) -> None:
        """Essaie y = 80.5 avec QPoint, et affiche le y que QPoint a gardé."""
        y = QPoint(4, 80.5).y()
        self.readout.setText(f"QPoint(4, 80.5).y() -> {y}")
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(29, 53, 87), 1))
            painter.drawLine(QPoint(4, 80.5), QPoint(56, 80.5))
        self.canvas.setImage(self.image)

    def drawWithFourNumbers(self) -> None:
        """Essaie y = 88.9 avec quatre nombres : Qt choisit l'écriture entière de drawLine."""
        self.readout.setText(f"int(88.9) -> {int(88.9)}")
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(29, 53, 87), 1))
            painter.drawLine(4, 88.9, 56, 88.9)
        self.canvas.setImage(self.image)

    def drawWithoutAntialiasing(self) -> None:
        """Vide la lecture ; une coordonnée entière et une demi-coordonnée, cette fois sans anticrénelage."""
        self.readout.clear()
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(29, 53, 87), 1))
            painter.drawLine(QPointF(4, 95), QPointF(56, 95))
            painter.drawLine(QPointF(4, 100.5), QPointF(56, 100.5))
        self.canvas.setImage(self.image)

    def drawEvenWidth(self) -> None:
        """Agrandit une nouvelle portion, puis trace un trait de 2 pixels : entier, puis demi."""
        self.canvas.setViewRect(QRect(0, 110, 60, 45))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(29, 53, 87), 2))
            painter.drawLine(QPointF(4, 122), QPointF(56, 122))
            painter.drawLine(QPointF(4, 134.5), QPointF(56, 134.5))
        self.canvas.setImage(self.image)

    def drawOnTwoBackgrounds(self) -> None:
        """Agrandit une nouvelle portion : un fond bleu à gauche, puis une oblique jaune anticrénelée."""
        self.canvas.setViewRect(QRect(0, 160, 60, 45))
        with QPainter(self.image) as painter:
            painter.fillRect(0, 160, 30, 45, QColor(0, 0, 255))
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(255, 255, 0), 2))
            painter.drawLine(QPointF(4, 198), QPointF(56, 166))
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie les cases à cocher, le sélecteur numérique et les listes déroulantes au slot qui redessine."""
        self.antialiasingCheck.toggled.connect(self.redrawTestPattern)
        self.halfPixelCheck.toggled.connect(self.redrawTestPattern)
        self.widthSlider.valueChanged.connect(self.redrawTestPattern)
        self.strokeColorCombo.currentIndexChanged.connect(self.redrawTestPattern)
        self.backgroundColorCombo.currentIndexChanged.connect(self.redrawTestPattern)

    @Slot()
    def redrawTestPattern(self) -> None:
        """Lit les contrôles, puis redessine le motif d'essai."""
        offset = 0.0
        if self.halfPixelCheck.isChecked():
            offset = 0.5
        self.drawTestPattern(self.antialiasingCheck.isChecked(), self.widthSlider.value(), offset,
                             self.strokeColorCombo.currentData(), self.backgroundColorCombo.currentData())

    def drawTestPattern(self, antialiased: bool, width: int, offset: float,
                        strokeColor: QColor, backgroundColor: QColor) -> None:
        """Remplit l'image du fond, puis trace une horizontale, une verticale, une oblique et un cercle."""
        self.canvas.setViewRect(QRect(0, 0, 60, 45))
        self.readout.setText(f"8 + offset -> {8 + offset}")
        self.image.fill(backgroundColor)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, antialiased)
            painter.setPen(QPen(strokeColor, width))
            painter.drawLine(QPointF(4, 8 + offset), QPointF(56, 8 + offset))
            painter.drawLine(QPointF(8 + offset, 16), QPointF(8 + offset, 41))
            painter.drawLine(QPointF(16 + offset, 16 + offset), QPointF(34 + offset, 40 + offset))
            painter.drawEllipse(QPointF(46 + offset, 28 + offset), 9, 9)
        self.canvas.setImage(self.image)

    def _exploreQuality(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine le motif de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawTestPattern()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : la surface",
                explanation=(
                    "Rien de nouveau : comme à la notion 1.1, <code>createSurface()</code> crée "
                    "une image blanche de 480 × 360 pixels, puis la confie au canevas, qui la "
                    "montre."
                ),
                run=self.createSurface,
                references=[("QImage", qtDocUrl("QtGui", "QImage"))],
            ),
            QStepWalkthrough.Step(
                title="Sans anticrénelage : l'escalier",
                explanation=(
                    "Sans réglage, chaque pixel est soit plein, soit vide. Une oblique avance "
                    "donc par marches, et un cercle par paliers. À l'échelle 1, ces marches se "
                    "voient à peine, mais elles donnent un aspect dentelé. Ici, un peintre trace "
                    "une diagonale et un cercle, d'un pixel d'épaisseur."
                    "<br><br>Le canevas sait aussi <b>agrandir</b> une portion de l'image : "
                    "<code>setViewRect(rect)</code> reçoit un <code>QRect</code> dans le repère de "
                    "l'image, et l'agrandit pour remplir le canevas. Ici, "
                    "<code>QRect(0, 0, 60, 45)</code> : le coin haut gauche, agrandi huit fois. "
                    "Chaque carré est un pixel. L'image elle-même ne change pas."
                ),
                run=self.drawAliasedShapes,
                references=[("Rendu crénelé", qtPageUrl("coordsys", "aliased-painting"))],
            ),
            QStepWalkthrough.Step(
                title="setRenderHint() : l'anticrénelage",
                explanation=(
                    "<code>setRenderHint(QPainter.RenderHint.Antialiasing)</code> active "
                    "l'anticrénelage pour ce peintre. Les pixels du bord prennent une teinte "
                    "intermédiaire, selon la part du pixel que le trait couvre. À distance, le "
                    "trait paraît lisse. Le réglage ne vaut que pour ce peintre : un peintre neuf "
                    "repart sans anticrénelage. Un second argument, facultatif, est un booléen : "
                    "<code>True</code>, la valeur par défaut, active le réglage ; "
                    "<code>False</code> le désactive."
                ),
                run=self.drawAntialiasedShapes,
                references=[
                    ("QPainter.setRenderHint", qtDocUrl("QtGui", "QPainter", "setRenderHint")),
                    ("QPainter.RenderHint", qtDocUrl("QtGui", "QPainter", "RenderHint")),
                    ("Rendu anticrénelé", qtPageUrl("coordsys", "anti-aliased-painting")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Un trait d'un pixel sur une coordonnée entière",
                explanation=(
                    "Nouvelle portion agrandie : y de 60 à 104. Les points du trait sont des "
                    "<code>QPointF</code>, la version réelle du point (notion 1.2) : leurs "
                    "coordonnées peuvent avoir une partie décimale, comme 72,5. L'étape suivante "
                    "en a besoin."
                    "<br><br>Un trait d'un pixel à y = 66 couvre la bande de 65,5 à 66,5. Or le "
                    "pixel 65 va de 65 à 66, et le pixel 66 de 66 à 67 : le trait couvre la "
                    "moitié de chacun. Avec l'anticrénelage, on obtient <b>deux rangées "
                    "pâles</b>, d'un bleu à demi mêlé au blanc, au lieu d'une rangée foncée. Le "
                    "trait paraît flou."
                ),
                run=self.drawOnInteger,
                references=[
                    ("QPointF", qtDocUrl("QtCore", "QPointF")),
                    ("QPainter.drawLine", qtDocUrl("QtGui", "QPainter", "drawLine")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Sur une demi-coordonnée : un trait net",
                explanation=(
                    "À y = 72,5, le trait couvre la bande de 72 à 73 : exactement le pixel 72. "
                    "Une seule rangée, pleinement foncée. Le centre d'un pixel est à la "
                    "demi-coordonnée. Un trait d'un pixel bien net se pose donc sur un centre."
                ),
                run=self.drawOnHalf,
                references=[("QPointF", qtDocUrl("QtCore", "QPointF"))],
            ),
            QStepWalkthrough.Step(
                title="QPoint tronque en silence",
                explanation=(
                    "<code>QPoint</code>, la version entière du point (notion 1.2), ne "
                    "garde que des entiers. "
                    "<code>QPoint(4, 80.5)</code> devient <code>QPoint(4, 80)</code>, sans "
                    "erreur : son accesseur <code>y()</code> rend 80. Le trait retombe sur une "
                    "coordonnée entière et redevient flou."
                    "<br><br>Pour le lire, un nouvel outil de ce guide paraît sous le canevas : la "
                    "<b>lecture</b> (<code>self.readout</code>). <code>setText(texte)</code> y "
                    "affiche un texte, ici une valeur lue par le code. Elle reste cachée tant "
                    "qu'elle est vide, et garde son texte jusqu'au suivant. Ce que rend un appel "
                    "s'y écrit <code>appel -> valeur</code>, la valeur telle que Python l'écrit : "
                    "c'est du code, avec un point décimal, et non la virgule de la prose."
                ),
                run=self.drawWithQPoint,
                references=[
                    ("QPoint", qtDocUrl("QtCore", "QPoint")),
                    ("QPointF", qtDocUrl("QtCore", "QPointF")),
                ],
            ),
            QStepWalkthrough.Step(
                title="drawLine() à quatre nombres : l'écriture entière",
                explanation=(
                    "Une méthode de Qt accepte souvent plusieurs écritures (notion 1.2) : "
                    "<code>drawLine()</code> reçoit deux points, ou quatre nombres. Avec quatre "
                    "nombres, même réels, Qt choisit l'écriture entière et tronque en silence, "
                    "comme <code>int()</code> en Python : <code>int(88.9)</code> vaut 88. "
                    "<code>drawLine(4, 88.9, 56, 88.9)</code> trace donc sur y = 88 : deux "
                    "rangées pâles, 87 et 88, que l'agrandissement montre. La lecture affiche la "
                    "troncature de Python, la même que celle de Qt ; celle de Qt se voit dans "
                    "l'agrandissement."
                    "<br><br>Pour des coordonnées réelles, toujours des <code>QPointF</code>. "
                    "Pour un rectangle, de même, <code>QRectF</code> plutôt que "
                    "<code>QRect</code>."
                    "<br><br>La version entière reste exacte quand tous les nombres sont "
                    "entiers par nature : une zone de pixels à agrandir, comme celle de "
                    "<code>setViewRect()</code>, ou un cadre aux bords entiers. Ce guide "
                    "l'emploie alors, comme beaucoup de code Qt."
                ),
                run=self.drawWithFourNumbers,
                references=[
                    ("QPainter.drawLine", qtDocUrl("QtGui", "QPainter", "drawLine")),
                    ("QRectF", qtDocUrl("QtCore", "QRectF")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Sans anticrénelage, pas de demi-pixel",
                explanation=(
                    "La lecture ne sert plus ici : <code>clear()</code> la vide, ce qui la cache."
                    "<br><br>Sans anticrénelage, un pixel est plein ou vide : jamais de gris. Un trait "
                    "d'un pixel remplit la rangée de la partie entière de y. Le trait à y = 95 "
                    "remplit la rangée 95, celui à y = 100,5 la rangée 100. À y = 100,9, ce "
                    "serait encore la rangée 100. Les deux traits sont nets. En contrepartie, la "
                    "position perd sa partie décimale, et les obliques gardent leurs marches."
                ),
                run=self.drawWithoutAntialiasing,
                references=[("Rendu crénelé", qtPageUrl("coordsys", "aliased-painting"))],
            ),
            QStepWalkthrough.Step(
                title="Un trait de 2 pixels : la règle s'inverse",
                explanation=(
                    "Nouvelle portion agrandie : y de 110 à 154. Avec un stylo de 2 pixels et "
                    "l'anticrénelage, le trait à y = 122 couvre de 121 à 123 : deux rangées "
                    "pleines, net. À y = 134,5, il couvre de 133,5 à 135,5 : une rangée pleine "
                    "et deux demi-rangées pâles. La règle : épaisseur impaire, "
                    "demi-coordonnée ; épaisseur paire, coordonnée entière."
                ),
                run=self.drawEvenWidth,
                references=[("QPen", qtDocUrl("QtGui", "QPen"))],
            ),
            QStepWalkthrough.Step(
                title="L'anticrénelage mélange les couleurs",
                explanation=(
                    "Nouvelle portion agrandie : y de 160 à 204. Un pixel du bord n'est pas "
                    "seulement plus clair : il prend une couleur entre celle du trait et celle "
                    "du fond. Le peintre mélange les deux couleurs composante par composante, "
                    "rouge, vert et bleu (notion 1.1), selon la part du pixel que le trait couvre."
                    "<br><br>L'oblique jaune, <code>QColor(255, 255, 0)</code>, traverse deux "
                    "fonds. Sur le blanc, ses bords sont d'un jaune pâle. Sur le bleu, "
                    "<code>QColor(0, 0, 255)</code>, un pixel à moitié couvert reçoit la moyenne "
                    "des deux : (128, 128, 128), un <b>gris</b>. Le même trait a donc des bords "
                    "différents selon ce qu'il recouvre. Deux couleurs complémentaires, comme le "
                    "jaune et le bleu, donnent un bord terne. Deux couleurs sont complémentaires "
                    "quand leurs composantes s'additionnent en blanc : (255, 255, 0) plus "
                    "(0, 0, 255) donne (255, 255, 255)."
                    "<br><br><i>Pour l'exemple</i> : <code>fillRect(x, y, largeur, hauteur, "
                    "couleur)</code> remplit un rectangle d'une couleur, ici la moitié gauche de "
                    "la portion. La notion 2.2 y revient."
                ),
                run=self.drawOnTwoBackgrounds,
                references=[
                    ("QPainter.setRenderHint", qtDocUrl("QtGui", "QPainter", "setRenderHint")),
                    ("QPainter.fillRect", qtDocUrl("QtGui", "QPainter", "fillRect")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : anticrénelage, épaisseur, demi-pixel",
                explanation=(
                    "Cinq contrôles paraissent sous le canevas :"
                    "<ul>"
                    "<li>deux cases à cocher (<code>QCheckBox</code>), cochées au départ : "
                    "<code>antialiasingCheck</code> active l'anticrénelage, "
                    "<code>halfPixelCheck</code> ajoute le décalage d'un demi-pixel, 0,5, à "
                    "toutes les coordonnées (<code>offset</code> dans le code) ;</li>"
                    "<li>un sélecteur numérique, <code>widthSlider</code>, règle l'épaisseur, de 1 "
                    "à 6 pixels, et part de 1 ;</li>"
                    "<li>deux listes déroulantes, <code>strokeColorCombo</code> et "
                    "<code>backgroundColorCombo</code>, choisissent la couleur du trait et celle "
                    "du fond, parmi bleu nuit, bleu, jaune, rouge, blanc et noir. Le trait part "
                    "en bleu nuit, le fond en blanc. Chaque choix porte sa <code>QColor</code>, "
                    "lue par <code>currentData()</code>.</li></ul>"
                    "<code>connectControls()</code> relie leurs signaux au slot "
                    "<code>redrawTestPattern()</code>. Le slot lit l'état des cases par "
                    "<code>isChecked()</code>, puis appelle <code>drawTestPattern()</code>. "
                    "Celle-ci agrandit le coin haut gauche et affiche le y de l'horizontale. Elle "
                    "remplit l'image de la couleur du fond. Nouveau : <code>fill()</code> accepte "
                    "aussi une <code>QColor</code>. Puis elle trace le motif d'essai. "
                    "<code>setRenderHint()</code> y reçoit son second argument, le booléen de "
                    "l'étape 4."
                    "<br><br>Essayer chaque épaisseur, avec et sans le décalage d'un demi-pixel. L'horizontale et "
                    "la verticale peuvent être à la fois lisses et nettes. L'oblique et le "
                    "cercle, eux, ont le choix entre l'escalier et les pixels de bord. Puis "
                    "changer les couleurs : un trait jaune sur un fond bleu montre des bords "
                    "gris."
                ),
                run=self._exploreQuality,
                codeSource=(self.connectControls, self.redrawTestPattern, self.drawTestPattern),
                references=[
                    ("QPainter.setRenderHint", qtDocUrl("QtGui", "QPainter", "setRenderHint")),
                    ("QCheckBox", qtDocUrl("QtWidgets", "QCheckBox")),
                    ("QComboBox.currentData", qtDocUrl("QtWidgets", "QComboBox", "currentData")),
                ],
            ),
        ]
