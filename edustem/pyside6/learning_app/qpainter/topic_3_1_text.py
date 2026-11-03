"""Notion 3.1 : le texte.

Contexte : écrire du texte dans une image avec `QPainter.drawText()`. Deux
façons de le placer. Par un point, qui est la ligne de base et non le haut du
texte. Ou par un rectangle, avec un alignement et un retour à la ligne. Puis
`QFontMetrics` mesure le texte, pour le placer soi-même au pixel près.

Étapes couvertes : récapitulatif (surface, grille, trait rouge),
`drawText(x, y, texte)` et sa ligne de base, `QFont` (famille, taille), gras
et italique, l'anticrénelage du texte (décidé par la police),
`drawText(rectangle, drapeaux, texte)` et l'alignement, le texte
trop long coupé au bord, `TextWordWrap` et le rectangle réellement occupé,
les mesures de `QFontMetrics`, les nombres d'une règle centrés sous leurs
graduations, `elidedText()`. Un texte, une taille et un alignement se règlent
ensuite à la main.

Chaque étape est une méthode de `QTopicTextTab`. Les étapes dessinent dans
la même image, `self.image`. Celles qui changent de sujet repartent d'une
image blanche (`fill`).
"""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt, Slot
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


class QTopicTextTab(QWidget):
    """Onglet de la notion 3.1 : placer, mettre en forme et mesurer du texte.

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
        textCombo, sizeSlider, alignmentCombo: Le texte, sa taille en points
            et son alignement dans le cadre.
        image: La surface de la notion, ou None avant le récapitulatif.
    """

    TabTitle = "Le texte"
    TabToolTip = "drawText() par un point ou dans un rectangle, QFont et QFontMetrics"
    RecommendedPanelWidth = 600
    Objective = (
        "Écrire du texte dans une image avec <code>drawText()</code>, choisir sa police avec "
        "<code>QFont</code>, l'aligner dans un rectangle, puis le mesurer avec "
        "<code>QFontMetrics</code> pour le placer soi-même."
    )
    KeyConcepts = [
        "Le y de <code>drawText(x, y, texte)</code> est la ligne de base : les lettres reposent "
        "dessus, seules les descentes (p, g, y) passent dessous.",
        "Le texte prend la couleur du stylo et la police donnée par <code>setFont()</code>.",
        "Le texte est anticrénelé par défaut. Sur une image, c'est la police qui en décide, par "
        "sa stratégie de style, et non une indication du peintre.",
        "Dans un rectangle, des drapeaux décident de l'alignement et du retour à la ligne. Un "
        "texte trop long y est coupé au bord.",
        "<code>QFontMetrics</code> donne les mesures d'une police : la largeur d'un texte, la "
        "hauteur au-dessus et au-dessous de la ligne de base. De quoi centrer un texte ou le "
        "raccourcir soi-même.",
    ]
    KeyApis = [
        "QPainter.drawText", "QPainter.setFont", "QFont", "QFont.setStyleStrategy",
        "Qt.AlignmentFlag", "Qt.TextFlag",
        "QPainter.fontMetrics", "QFontMetrics.horizontalAdvance", "QFontMetrics.ascent",
        "QFontMetrics.elidedText", "Qt.TextElideMode",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.controls = QControlPanel()
        self.textCombo = self.controls.addComboBox("Texte", [
            ("Un mot", "Bonjour"),
            ("Une phrase", "Le texte passe à la ligne entre deux mots."),
            ("Un paragraphe",
             "Un texte qui passe à la ligne tout seul quand il manque de place. Changer sa "
             "taille ou son alignement le redessine aussitôt."),
        ], currentIndex=2)
        self.sizeSlider = self.controls.addSlider("Taille", 6, 72, 20, suffix="pt")
        self.alignmentCombo = self.controls.addComboBox("Alignement", [
            ("En haut à gauche (AlignTop | AlignLeft)",
             Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft),
            ("En haut, centré (AlignTop | AlignHCenter)",
             Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter),
            ("Au centre (AlignCenter)", Qt.AlignmentFlag.AlignCenter),
            ("En bas à droite (AlignBottom | AlignRight)",
             Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight),
            ("Justifié (AlignTop | AlignJustify)",
             Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignJustify),
        ], currentIndex=2)
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
        self.canvas.setViewRect(None)
        self.image = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface blanche de 480 × 360 pixels, montre la grille, puis l'image."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setGridVisible(True)
        self.canvas.setImage(self.image)

    def drawGuideLine(self) -> None:
        """Trace une ligne rouge d'un pixel à y = 60."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(231, 76, 60), 1))
            painter.drawLine(20, 60, 460, 60)
        self.canvas.setImage(self.image)

    def drawOnBaseline(self) -> None:
        """Écrit un texte noir au point (40, 60), sur la ligne rouge."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawText(40, 60, "Bonjour ! Ce texte repose sur y = 60.")
        self.canvas.setImage(self.image)

    def drawWithFont(self) -> None:
        """Trace une ligne rouge à y = 150, change de police, puis écrit un mot dessus."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(231, 76, 60), 1))
            painter.drawLine(20, 150, 460, 150)
            painter.setFont(QFont("Georgia", 28))
            painter.setPen(QPen(QColor(29, 53, 87), 1))
            painter.drawText(40, 150, "Typographie")
        self.canvas.setImage(self.image)

    def drawBoldItalic(self) -> None:
        """Écrit trois mots, en modifiant la police et en la redonnant au peintre entre chacun."""
        with QPainter(self.image) as painter:
            font = QFont("Georgia", 20)
            painter.setFont(font)
            painter.drawText(40, 230, "Normal")
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(150, 230, "Gras")
            font.setItalic(True)
            painter.setFont(font)
            painter.drawText(240, 230, "Gras italique")
        self.canvas.setImage(self.image)

    def drawTextAntialiasing(self) -> None:
        """Agrandit le bas de l'image, puis écrit le même mot sans anticrénelage, puis avec."""
        self.canvas.setViewRect(QRect(36, 250, 120, 90))
        with QPainter(self.image) as painter:
            font = QFont("Georgia", 20)
            font.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
            painter.setFont(font)
            painter.drawText(40, 285, "Glyphe")
            font.setStyleStrategy(QFont.StyleStrategy.PreferDefault)
            painter.setFont(font)
            painter.drawText(40, 325, "Glyphe")
        self.canvas.setImage(self.image)

    def drawAlignedInRect(self) -> None:
        """Revient à l'image entière, repart du blanc, puis aligne trois textes dans un cadre gris."""
        self.canvas.setViewRect(None)
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            box = QRect(40, 30, 400, 130)
            painter.setPen(QPen(QColor(149, 165, 166), 1))
            painter.drawRect(box)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setFont(QFont("Georgia", 14))
            topLeft = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            painter.drawText(box, topLeft, "En haut à gauche")
            painter.drawText(box, Qt.AlignmentFlag.AlignCenter, "Au centre")
            bottomRight = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight
            painter.drawText(box, bottomRight, "En bas à droite")
        self.canvas.setImage(self.image)

    def drawTooLong(self) -> None:
        """Écrit un texte trop long dans un cadre étroit, sans autre drapeau que l'alignement."""
        with QPainter(self.image) as painter:
            box = QRect(20, 190, 210, 110)
            painter.setPen(QPen(QColor(149, 165, 166), 1))
            painter.drawRect(box)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setFont(QFont("Georgia", 13))
            painter.drawText(box, Qt.AlignmentFlag.AlignLeft,
                             "Ce texte est bien trop long pour une ligne.")
        self.canvas.setImage(self.image)

    def drawWordWrap(self) -> None:
        """Écrit le même texte avec retour à la ligne, et encadre en rouge la place qu'il occupe."""
        with QPainter(self.image) as painter:
            box = QRect(250, 190, 210, 110)
            painter.setPen(QPen(QColor(149, 165, 166), 1))
            painter.drawRect(box)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setFont(QFont("Georgia", 13))
            flags = Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap
            text = "Ce texte est bien trop long pour une ligne."
            usedRect = painter.drawText(box, flags, text)
            painter.setPen(QPen(QColor(231, 76, 60), 1, Qt.PenStyle.DashLine))
            painter.drawRect(usedRect)
        self.canvas.setImage(self.image)

    def drawMetrics(self) -> None:
        """Repart d'une image blanche, écrit un mot, puis trace et écrit ses mesures."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setFont(QFont("Georgia", 48))
            metrics = painter.fontMetrics()
            x = 40
            baseline = 110
            top = baseline - metrics.ascent()
            bottom = baseline + metrics.descent()
            width = metrics.horizontalAdvance("Glyphe")
            painter.drawText(x, baseline, "Glyphe")

            green = QColor(42, 157, 143)
            red = QColor(231, 76, 60)
            blue = QColor(46, 134, 222)
            orange = QColor(230, 126, 34)
            painter.setPen(QPen(green, 1))
            painter.drawLine(20, top, 460, top)
            painter.setPen(QPen(red, 1))
            painter.drawLine(20, baseline, 460, baseline)
            painter.setPen(QPen(blue, 1))
            painter.drawLine(20, bottom, 460, bottom)
            painter.setPen(QPen(orange, 1))
            painter.drawLine(x + width, 30, x + width, 175)

            painter.setFont(QFont("Georgia", 11))
            painter.setPen(QPen(green, 1))
            painter.drawText(290, top - 5, f"ascent() -> {metrics.ascent()}")
            painter.setPen(QPen(red, 1))
            painter.drawText(290, baseline - 5, f"ligne de base : y = {baseline}")
            painter.setPen(QPen(blue, 1))
            painter.drawText(290, bottom + 17, f"descent() -> {metrics.descent()}")
            painter.setPen(QPen(orange, 1))
            painter.drawText(x + width + 6, 172, f"horizontalAdvance() -> {width}")
        self.canvas.setImage(self.image)

    def drawRulerNumbers(self) -> None:
        """Trace une règle de 0 à 100 cm, puis centre chaque nombre sous sa graduation."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(29, 53, 87), 1))
            painter.setFont(QFont("Georgia", 12))
            metrics = painter.fontMetrics()
            painter.drawLine(40, 205, 400, 205)
            for index in range(11):
                x = 40 + index * 36
                painter.drawLine(x, 205, x, 215)
                text = str(index * 10)
                left = x - metrics.horizontalAdvance(text) / 2
                baseline = 215 + metrics.ascent()
                painter.drawText(round(left), baseline, text)
            painter.drawText(420, 215 + metrics.ascent(), "cm")
        self.canvas.setImage(self.image)

    def drawElided(self) -> None:
        """Écrit un titre en entier, en gris, puis raccourci pour tenir dans un cadre de 200 pixels."""
        with QPainter(self.image) as painter:
            painter.setFont(QFont("Georgia", 13))
            metrics = painter.fontMetrics()
            title = "Rapport final du projet de session, version révisée"
            shortTitle = metrics.elidedText(title, Qt.TextElideMode.ElideRight, 200)

            painter.setPen(QPen(QColor(149, 165, 166), 1))
            painter.drawRect(40, 270, 200, 30)
            painter.drawText(40, 330, title)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawText(QRect(40, 270, 200, 30), Qt.AlignmentFlag.AlignVCenter, shortTitle)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie les deux listes déroulantes et le sélecteur numérique au slot qui redessine."""
        self.textCombo.currentIndexChanged.connect(self.redrawTextSample)
        self.sizeSlider.valueChanged.connect(self.redrawTextSample)
        self.alignmentCombo.currentIndexChanged.connect(self.redrawTextSample)

    @Slot()
    def redrawTextSample(self) -> None:
        """Lit les trois contrôles, puis redessine."""
        self.drawTextSample(self.textCombo.currentData(), self.sizeSlider.value(),
                            self.alignmentCombo.currentData())

    def drawTextSample(self, text: str, pointSize: int, alignment: Qt.AlignmentFlag) -> None:
        """Repart d'une image blanche, écrit le texte dans un cadre gris, et encadre en rouge sa place."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            box = QRect(40, 40, 400, 280)
            painter.setPen(QPen(QColor(149, 165, 166), 1))
            painter.drawRect(box)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setFont(QFont("Georgia", pointSize))
            flags = alignment | Qt.TextFlag.TextWordWrap
            usedRect = painter.drawText(box, flags, text)
            painter.setPen(QPen(QColor(231, 76, 60), 1, Qt.PenStyle.DashLine))
            painter.drawRect(usedRect)
        self.canvas.setImage(self.image)

    def _exploreText(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine avec leurs valeurs de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawTextSample()

    def _recap(self) -> None:
        """Crée la surface, puis trace la ligne rouge du récapitulatif."""
        self.createSurface()
        self.drawGuideLine()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : une surface, une grille, un trait",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée l'image blanche et "
                    "affiche la grille du canevas, qui aide à lire les coordonnées (notion 1.1). "
                    "Un stylo rouge d'un pixel trace une ligne à y = 60 (notion 2.1)."
                    "<br><br>Cette ligne sert de repère : le texte de l'étape suivante est écrit "
                    "dessus."
                ),
                run=self._recap,
                codeSource=(self.createSurface, self.drawGuideLine),
                references=[("QPainter.drawLine", qtDocUrl("QtGui", "QPainter", "drawLine"))],
            ),
            QStepWalkthrough.Step(
                title="drawText() : y est la ligne de base",
                explanation=(
                    "<code>drawText(40, 60, texte)</code> écrit une chaîne de caractères. Le "
                    "point (40, 60) n'est pas le haut du texte. C'est le début de sa <b>ligne de "
                    "base</b> : les lettres reposent sur la ligne rouge, comme sur une ligne de "
                    "cahier."
                    "<br><br>Le texte prend la couleur du stylo, ici le noir. La police par "
                    "défaut est petite : l'étape suivante la change."
                ),
                run=self.drawOnBaseline,
                references=[("QPainter.drawText", qtDocUrl("QtGui", "QPainter", "drawText"))],
            ),
            QStepWalkthrough.Step(
                title="QFont : famille et taille",
                explanation=(
                    "<code>QFont(\"Georgia\", 28)</code>, de <code>PySide6.QtGui</code>, décrit "
                    "une police : sa famille, puis sa "
                    "taille en points. <code>setFont()</code> la donne au peintre, pour tous les "
                    "textes qui suivent. Si la famille manque sur l'ordinateur, Qt en prend une "
                    "autre : le texte s'écrit quand même, avec une autre allure."
                    "<br><br>Le point est une unité d'imprimerie : 1/72 de pouce. L'image compte "
                    "96 pixels par pouce. Une police de 28 points mesure donc 28 × 96 / 72, "
                    "environ 37 pixels. C'est la taille de la police, et non la hauteur de chaque "
                    "lettre."
                    "<br><br>Le y et le p de « Typographie » descendent sous la ligne de base. "
                    "Les autres lettres reposent dessus."
                ),
                run=self.drawWithFont,
                references=[
                    ("QFont", qtDocUrl("QtGui", "QFont")),
                    ("QPainter.setFont", qtDocUrl("QtGui", "QPainter", "setFont")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Gras et italique",
                explanation=(
                    "<code>setBold(True)</code> et <code>setItalic(True)</code> modifient l'objet "
                    "<code>font</code>. Mais <code>setFont()</code> donne au peintre une copie de "
                    "la police, comme <code>setPen()</code> pour le stylo (notion 2.1). Après "
                    "chaque modification, la police est donc redonnée au peintre."
                    "<br><br>Les trois mots sont noirs : ce peintre est neuf, et il a le stylo "
                    "par défaut (notion 2.1)."
                ),
                run=self.drawBoldItalic,
                references=[
                    ("QFont.setBold", qtDocUrl("QtGui", "QFont", "setBold")),
                    ("QFont.setItalic", qtDocUrl("QtGui", "QFont", "setItalic")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Un texte lisse : la police décide de l'anticrénelage",
                explanation=(
                    "Le texte a son propre anticrénelage, actif par défaut : les bords des "
                    "lettres prennent des teintes intermédiaires, comme un trait anticrénelé "
                    "(notion 1.3). Ce qui le décide n'est pas <code>setRenderHint()</code>, "
                    "mais la police. Sa <b>stratégie de style</b>, une constante de "
                    "<code>QFont.StyleStrategy</code>, se règle par "
                    "<code>setStyleStrategy()</code>."
                    "<br><br>Ici, le canevas agrandit le bas de l'image, quatre fois (notion "
                    "1.3). Le même mot y est écrit deux fois, de la même police :"
                    "<ul>"
                    "<li><code>NoAntialias</code>, en haut, demande un texte sans "
                    "anticrénelage : chaque pixel est plein ou vide, et les courbes des lettres "
                    "avancent par marches ;</li>"
                    "<li><code>PreferDefault</code>, la stratégie par défaut, en bas, rétablit "
                    "le texte lisse.</li></ul>"
                    "Il n'y a donc rien à faire pour un texte lisse. Qt garde aussi une "
                    "indication <code>QPainter.RenderHint.TextAntialiasing</code>, active dans "
                    "tout peintre neuf. Sur une image, elle ne change rien : seule la police "
                    "compte. Pour les traits et les formes, en revanche, l'anticrénelage reste à "
                    "activer soi-même."
                ),
                run=self.drawTextAntialiasing,
                references=[
                    ("QFont.setStyleStrategy", qtDocUrl("QtGui", "QFont", "setStyleStrategy")),
                    ("QFont.StyleStrategy", qtDocUrl("QtGui", "QFont", "StyleStrategy")),
                ],
            ),
            QStepWalkthrough.Step(
                title="drawText() dans un rectangle : l'alignement",
                explanation=(
                    "Le canevas montre de nouveau toute l'image. <code>setViewRect()</code> "
                    "(notion 1.3) reçoit ici <code>None</code> au lieu d'un rectangle : il n'y a "
                    "plus de zone agrandie. L'image repart du blanc. Avec un "
                    "rectangle au lieu d'un point, "
                    "<code>drawText()</code> place le texte à l'intérieur selon des drapeaux "
                    "d'alignement, des constantes de <code>Qt.AlignmentFlag</code>. On en "
                    "choisit un pour l'horizontale (<code>AlignLeft</code>, "
                    "<code>AlignRight</code>) et un pour la verticale (<code>AlignTop</code>, "
                    "<code>AlignBottom</code>). <code>AlignCenter</code> centre dans les deux "
                    "sens."
                    "<br><br>Les deux drapeaux, réunis par <code>|</code>, gardent les deux choix. "
                    "Plus besoin de penser à la ligne de base : Qt la "
                    "calcule."
                ),
                run=self.drawAlignedInRect,
                references=[
                    ("QPainter.drawText", qtDocUrl("QtGui", "QPainter", "drawText")),
                    ("Qt.AlignmentFlag", qtDocUrl("QtCore", "Qt", "AlignmentFlag")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Un texte trop long est coupé",
                explanation=(
                    "Rien ne dépasse du rectangle donné à <code>drawText()</code>. Avec un "
                    "alignement seul, le texte reste sur une ligne : trop long, il est coupé net "
                    "au bord droit du rectangle. Ici, le cadre de gauche ne fait que 210 pixels "
                    "de large. Son seul drapeau est <code>AlignLeft</code> : sans drapeau "
                    "vertical, le texte se place en haut, le choix par défaut."
                ),
                run=self.drawTooLong,
                references=[("QPainter.drawText", qtDocUrl("QtGui", "QPainter", "drawText"))],
            ),
            QStepWalkthrough.Step(
                title="TextWordWrap : le retour à la ligne",
                explanation=(
                    "À droite, le même texte, avec un drapeau de plus : "
                    "<code>Qt.TextFlag.TextWordWrap</code>. Il vient d'une autre famille de "
                    "drapeaux, <code>Qt.TextFlag</code>, mais <code>|</code> le réunit aux "
                    "drapeaux d'alignement de la même façon. Le texte passe à la ligne entre "
                    "deux mots. Un <code>\\n</code> dans le texte force aussi un passage à la "
                    "ligne dans un rectangle. Avec <code>drawText(x, y, texte)</code>, il est "
                    "ignoré : cette forme écrit toujours une seule ligne."
                    "<br><br><code>drawText()</code> rend le rectangle (<code>QRect</code>) "
                    "réellement occupé par le texte, encadré en tirets rouges. Il est plus "
                    "petit que le cadre donné : de quoi ajuster un cadre autour du texte, ou "
                    "placer la suite juste dessous."
                ),
                run=self.drawWordWrap,
                references=[
                    ("Qt.TextFlag", qtDocUrl("QtCore", "Qt", "TextFlag")),
                    ("QPainter.drawText", qtDocUrl("QtGui", "QPainter", "drawText")),
                ],
            ),
            QStepWalkthrough.Step(
                title="QFontMetrics : les mesures d'une police",
                explanation=(
                    "L'image repart du blanc. <code>painter.fontMetrics()</code> rend un objet "
                    "<code>QFontMetrics</code> : les mesures de la police du peintre, en pixels. "
                    "<code>ascent()</code> rend la hauteur au-dessus de la ligne de base (ligne "
                    "verte). Elle passe un peu au-dessus du haut des lettres : la police réserve "
                    "de la place pour les accents et les signes les plus hauts. "
                    "<code>descent()</code> rend la profondeur dessous (ligne bleue). "
                    "<code>horizontalAdvance(texte)</code> rend la largeur du texte (ligne "
                    "orange)."
                    "<br><br>Les nombres écrits à côté des lignes sont ces valeurs, lues par le "
                    "code puis écrites par <code>drawText()</code>, en Georgia 11. L'objet "
                    "<code>metrics</code> est une copie des mesures, prise au moment de l'appel : "
                    "il décrit toujours la police de 48 points, même après "
                    "<code>setFont(QFont(\"Georgia\", 11))</code>."
                ),
                run=self.drawMetrics,
                references=[
                    ("QPainter.fontMetrics", qtDocUrl("QtGui", "QPainter", "fontMetrics")),
                    ("QFontMetrics.ascent", qtDocUrl("QtGui", "QFontMetrics", "ascent")),
                    ("QFontMetrics.descent", qtDocUrl("QtGui", "QFontMetrics", "descent")),
                    ("QFontMetrics.horizontalAdvance",
                     qtDocUrl("QtGui", "QFontMetrics", "horizontalAdvance")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Centrer un texte soi-même : une règle graduée",
                explanation=(
                    "Pour centrer un texte sous un point, on le décale de la moitié de sa "
                    "largeur, que les mesures de la police donnent. Ici, une règle de 0 à 100 cm, "
                    "une graduation tous les 36 pixels. Chaque nombre doit être centré sous sa "
                    "graduation. Or « 0 », « 10 » et « 100 » n'ont pas la même largeur."
                    "<br><br>À l'horizontale, le texte commence à x moins la moitié de sa "
                    "largeur : <code>x - horizontalAdvance(text) / 2</code>. Ce calcul donne un "
                    "nombre décimal, et <code>drawText(x, y, texte)</code> attend des entiers : "
                    "<code>round()</code> l'arrondit. À la verticale, la ligne de base est posée "
                    "à <code>215 + ascent()</code>. Le haut de la police, <code>ascent()</code> "
                    "pixels au-dessus de la ligne de base, touche alors le bas des graduations, "
                    "à y = 215. Les chiffres sont un peu moins hauts que la police : un petit "
                    "espace reste au-dessus d'eux."
                    "<br><br>Dans un rectangle, le drapeau <code>AlignHCenter</code> centre à "
                    "l'horizontale seulement : il fait ce calcul à notre place (étape "
                    "« drawText() dans un rectangle : l'alignement »)."
                ),
                run=self.drawRulerNumbers,
                references=[
                    ("QFontMetrics.horizontalAdvance",
                     qtDocUrl("QtGui", "QFontMetrics", "horizontalAdvance")),
                    ("QFontMetrics.ascent", qtDocUrl("QtGui", "QFontMetrics", "ascent")),
                ],
            ),
            QStepWalkthrough.Step(
                title="elidedText() : raccourcir avec des points de suspension",
                explanation=(
                    "<code>elidedText(texte, mode, largeur)</code> raccourcit un texte trop long. "
                    "Plutôt que de le couper au milieu d'une lettre (étape « Un texte trop long "
                    "est coupé »), il retire des caractères et ajoute « … ». Il rend la chaîne "
                    "raccourcie, qui tient dans la largeur donnée en pixels. Ici, un titre trop "
                    "long pour un cadre de 200 pixels. Il est écrit en entier, en gris, sous le "
                    "cadre. La chaîne raccourcie est écrite dans le cadre avec "
                    "<code>AlignVCenter</code>, qui centre à la verticale seulement."
                    "<br><br>Le mode est une constante de <code>Qt.TextElideMode</code>. "
                    "<code>ElideRight</code> coupe la fin. <code>ElideMiddle</code> coupe le "
                    "milieu, pratique pour un chemin de fichier. <code>ElideLeft</code> coupe le "
                    "début."
                ),
                run=self.drawElided,
                references=[
                    ("QFontMetrics.elidedText", qtDocUrl("QtGui", "QFontMetrics", "elidedText")),
                    ("Qt.TextElideMode", qtDocUrl("QtCore", "Qt", "TextElideMode")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : texte, taille et alignement",
                explanation=(
                    "Trois contrôles paraissent sous le canevas :"
                    "<ul>"
                    "<li>la liste déroulante <code>textCombo</code> choisit le texte : un mot, une "
                    "phrase ou un paragraphe (au départ). <code>currentData()</code> rend la "
                    "chaîne choisie ;</li>"
                    "<li>le sélecteur numérique <code>sizeSlider</code> règle la taille de 6 à "
                    "72 points (20 au départ) ;</li>"
                    "<li>la liste déroulante <code>alignmentCombo</code> choisit l'alignement "
                    "parmi cinq : en haut à gauche, en haut centré, au centre (au départ), en bas "
                    "à droite, justifié. Chaque choix porte ses drapeaux, écrits entre "
                    "parenthèses, et <code>currentData()</code> les rend.</li></ul>"
                    "Seul <code>AlignJustify</code> est nouveau : il étire chaque ligne jusqu'aux "
                    "deux bords, sauf la dernière."
                    "<br><br><code>connectControls()</code> relie les trois signaux au slot "
                    "<code>redrawTextSample()</code>, qui lit les contrôles et appelle "
                    "<code>drawTextSample()</code>. Celle-ci repart d'une image blanche, écrit le "
                    "texte dans le cadre gris avec <code>TextWordWrap</code>, puis encadre en "
                    "rouge le rectangle rendu."
                    "<br><br>Essayer 40 points : le texte ne tient plus. Il est coupé aux bords "
                    "du cadre, et le rectangle rouge dépasse le cadre : c'est la place que le "
                    "texte aurait voulue. Essayer « Justifié » sur le paragraphe."
                ),
                run=self._exploreText,
                codeSource=(self.connectControls, self.redrawTextSample, self.drawTextSample),
                references=[
                    ("QPainter.drawText", qtDocUrl("QtGui", "QPainter", "drawText")),
                    ("Qt.AlignmentFlag", qtDocUrl("QtCore", "Qt", "AlignmentFlag")),
                ],
            ),
        ]
