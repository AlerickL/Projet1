"""Notion 2.3 : couleurs et transparence.

Contexte : jusqu'ici, les couleurs s'écrivaient `QColor(r, g, b)`. Cette
notion présente d'abord ce que disent ces trois nombres (l'espace RGB), puis
les autres écritures d'une couleur (nom, hexadécimal), son canal alpha,
l'image transparente, les deux autres espaces de couleur de Qt (HSV et HSL)
et des nuances dérivées d'une même couleur.

Étapes couvertes : récapitulatif (une forme pleine), RGB et ses accesseurs,
une couleur par son nom, en hexadécimal, le canal alpha, une image
transparente, HSV (teinte, puis saturation et valeur V), HSL et sa
luminosité, deux roues de teintes (HSV et HSL), `lighter()` et `darker()`,
les composantes réelles (méthodes en F). Trois boutons radio choisissent
ensuite l'espace, deux autres les nombres (entiers de 0 à 255 ou réels de
0 à 1), et quatre sélecteurs numériques règlent une couleur et son alpha ;
la lecture l'écrit dans les trois espaces.

Chaque étape est une méthode de `QTopicColorsTab`. Les étapes dessinent
dans la même image, `self.image`. Celles qui comparent repartent d'une image
blanche (`fill`).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSignalBlocker, Qt, Slot
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas

# Liens ciblés des explications (skill, §12.4) : une section d'article par espace de couleurs.
_RgbArticleUrl = "https://fr.wikipedia.org/wiki/Rouge_vert_bleu#Description"
_HsvArticleUrl = "https://fr.wikipedia.org/wiki/Teinte_Saturation_Valeur#Description_des_composantes"
_HslArticleUrl = "https://fr.wikipedia.org/wiki/Teinte_saturation_lumi%C3%A8re#Système_HSL_ou_TSL"


def realText(value: float) -> str:
    """Un réel écrit à trois décimales, avec la virgule décimale : 0.3882 donne « 0,388 »."""
    return f"{value:.3f}".replace(".", ",")


class QTopicColorsTab(QWidget):
    """Onglet de la notion 2.3 : décrire une couleur (`QColor`), sa transparence, ses nuances.

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
        controls: Les contrôles de l'étape « À vous » (plomberie ; seuls
            `setCaption()` et `setDivisor()` sont cités, et présentés à cette étape).
        spaceGroup: Le groupe des trois boutons radio : RGB, HSV ou HSL.
        numberGroup: Le groupe des deux boutons radio : entiers de 0 à 255,
            ou réels de 0 à 1.
        firstSlider, secondSlider, thirdSlider, alphaSlider: Les trois
            composantes de la couleur choisie, dans l'espace et les nombres
            cochés, et son alpha.
        image: La surface de la notion, ou None avant le récapitulatif.
        color: La couleur choisie à l'étape « À vous », ou None avant.
    """

    TabTitle = "Couleurs et transparence"
    TabToolTip = "QColor : les espaces RGB, HSV et HSL, nom, hexadécimal, canal alpha, lighter() et darker()"
    RecommendedPanelWidth = 640
    Objective = (
        "Comprendre ce que décrivent les trois nombres d'une couleur dans chacun des espaces RGB, "
        "HSV et HSL, et écrire une couleur (<code>QColor</code>) de plusieurs façons. La rendre "
        "translucide avec son canal alpha, et en dériver des nuances cohérentes."
    )
    KeyConcepts = [
        "RGB décrit une couleur comme un écran la produit : trois lumières, rouge, vert et bleu, "
        "de 0 à 255, qui s'additionnent.",
        "Le nom et l'hexadécimal sont deux autres écritures d'une couleur RGB.",
        "Le canal alpha règle l'opacité : 255 opaque, 0 invisible. Une image peut elle-même être "
        "transparente.",
        "HSV et HSL réarrangent les trois mêmes nombres : une teinte (un angle), une saturation, "
        "puis la valeur V (le plus grand des trois) ou la luminosité L (la moyenne du plus grand "
        "et du plus petit).",
        "La couleur la plus vive d'une teinte est en haut de V, mais au milieu de L : en HSL, le "
        "haut est toujours le blanc.",
        "Ni V ni L ne mesurent la clarté que l'œil perçoit : à valeur égale, un jaune paraît plus "
        "clair qu'un bleu.",
        "Les accesseurs de <code>QColor</code> rendent une même couleur dans chaque espace.",
        "Chaque composante s'écrit aussi en réel, de 0 à 1 : les méthodes en F, comme "
        "<code>fromRgbF()</code> et <code>redF()</code>.",
        "<code>lighter()</code> et <code>darker()</code> dérivent des nuances d'une même "
        "teinte.",
    ]
    KeyApis = [
        "QColor", "QColor.red", "QColor.green", "QColor.blue", "Qt.GlobalColor", "QColor.name",
        "QColor.alpha", "QColor.fromHsv", "QColor.hsvHue", "QColor.hsvSaturation", "QColor.value",
        "QColor.fromHsl", "QColor.lightness", "QColor.lighter", "QColor.darker", "QColor.fromRgbF",
        "QColor.redF",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None
        self.color: QColor | None = None

        self.canvas = QDrawingCanvas()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.spaceGroup = self.controls.addRadioGroup("Espace", ["RGB", "HSV", "HSL"], checked=1)
        self.numberGroup = self.controls.addRadioGroup("Nombres", ["entiers de 0 à 255", "réels de 0 à 1"],
                                                       checked=0)
        self.firstSlider = self.controls.addSlider("Teinte H", 0, 359, 210)
        self.secondSlider = self.controls.addSlider("Saturation S", 0, 255, 180)
        self.thirdSlider = self.controls.addSlider("Valeur V", 0, 255, 220)
        self.alphaSlider = self.controls.addSlider("Alpha", 0, 255, 160)
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
        self.color = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface blanche de 480 × 360 pixels, et la montre."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setImage(self.image)

    def drawReminder(self) -> None:
        """Comme en 2.2 : une forme pleine, sans contour."""
        with QPainter(self.image) as painter:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(46, 134, 222)))
            painter.drawRoundedRect(140, 150, 200, 60, 12, 12)
        self.canvas.setImage(self.image)

    def drawRgbPlanes(self) -> None:
        """Repart d'une image blanche ; deux grilles de 8 × 8 couleurs, le bleu à 0 puis à 255."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            for row in range(8):
                for column in range(8):
                    red = column * 255 // 7
                    green = row * 255 // 7
                    painter.fillRect(16 + column * 26, 76 + row * 26, 26, 26, QColor(red, green, 0))
                    painter.fillRect(256 + column * 26, 76 + row * 26, 26, 26, QColor(red, green, 255))
        blue = QColor(46, 134, 222)
        self.readout.setText(f"red() -> {blue.red()}, green() -> {blue.green()}, blue() -> {blue.blue()}")
        self.canvas.setImage(self.image)

    def drawNamedColors(self) -> None:
        """Repart d'une image blanche ; six échantillons de couleurs désignées par leur nom."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.fillRect(15, 15, 70, 50, QColor("tomato"))
            painter.fillRect(91, 15, 70, 50, QColor("gold"))
            painter.fillRect(167, 15, 70, 50, QColor("mediumseagreen"))
            painter.fillRect(243, 15, 70, 50, QColor("steelblue"))
            painter.fillRect(319, 15, 70, 50, QColor("orchid"))
            painter.fillRect(395, 15, 70, 50, QColor(Qt.GlobalColor.darkCyan))
        tomato = QColor("tomato")
        self.readout.setText(f"tomato : red() -> {tomato.red()}, green() -> {tomato.green()}, "
                             f"blue() -> {tomato.blue()}")
        self.canvas.setImage(self.image)

    def drawHexColors(self) -> None:
        """La même couleur, écrite de trois façons : nom, composantes, hexadécimal."""
        with QPainter(self.image) as painter:
            painter.fillRect(15, 85, 146, 50, QColor("tomato"))
            painter.fillRect(167, 85, 146, 50, QColor(255, 99, 71))
            painter.fillRect(319, 85, 146, 50, QColor("#ff6347"))
        self.readout.setText(f"QColor(255, 99, 71).name() -> {QColor(255, 99, 71).name()}")
        self.canvas.setImage(self.image)

    def drawTranslucentDiscs(self) -> None:
        """Trois disques d'alpha 128, sur du blanc à gauche, sur un fond sombre à droite ; l'alpha du rouge, écrit."""
        red = QColor(231, 76, 60, 128)
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(240, 0, 240, 360, QColor(52, 73, 94))
            painter.setPen(Qt.PenStyle.NoPen)
            for left in [0, 240]:
                painter.setBrush(QBrush(red))
                painter.drawEllipse(left + 30, 90, 120, 120)
                painter.setBrush(QBrush(QColor(46, 204, 113, 128)))
                painter.drawEllipse(left + 90, 90, 120, 120)
                painter.setBrush(QBrush(QColor(52, 152, 219, 128)))
                painter.drawEllipse(left + 60, 150, 120, 120)
        self.readout.setText(f"alpha() -> {red.alpha()}, name(QColor.NameFormat.HexArgb) -> "
                             f"{red.name(QColor.NameFormat.HexArgb)}")
        self.canvas.setImage(self.image)

    def drawOnTransparentImage(self) -> None:
        """Vide la lecture ; remplit l'image d'une couleur transparente, puis y redessine les trois disques, en grand."""
        self.readout.clear()
        self.image.fill(Qt.GlobalColor.transparent)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(231, 76, 60, 128)))
            painter.drawEllipse(100, 20, 180, 180)
            painter.setBrush(QBrush(QColor(46, 204, 113, 128)))
            painter.drawEllipse(200, 20, 180, 180)
            painter.setBrush(QBrush(QColor(52, 152, 219, 128)))
            painter.drawEllipse(150, 160, 180, 180)
        self.canvas.setImage(self.image)

    def drawHues(self) -> None:
        """Repart d'une image blanche ; douze teintes HSV, de 0 à 330, à saturation et valeur égales."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            for index in range(12):
                painter.fillRect(15 + index * 38, 30, 34, 70, QColor.fromHsv(index * 30, 200, 230))
        tomato = QColor("tomato")
        gray = QColor(128, 128, 128)
        self.readout.setText(f"tomato : hsvHue() -> {tomato.hsvHue()}\n"
                             f"gris : hsvHue() -> {gray.hsvHue()}")
        self.canvas.setImage(self.image)

    def drawSaturationAndValue(self) -> None:
        """Pour la teinte 210, fait varier la saturation (rangée du milieu), puis la valeur V (bas)."""
        with QPainter(self.image) as painter:
            for index in range(12):
                x = 15 + index * 38
                level = index * 23
                painter.fillRect(x, 140, 34, 70, QColor.fromHsv(210, level, 230))
                painter.fillRect(x, 250, 34, 70, QColor.fromHsv(210, 200, level))
        tomato = QColor("tomato")
        self.readout.setText(f"tomato : hsvSaturation() -> {tomato.hsvSaturation()}, "
                             f"value() -> {tomato.value()}")
        self.canvas.setImage(self.image)

    def drawLightness(self) -> None:
        """Repart d'une image blanche ; même teinte et saturation : la valeur V en haut, la luminosité HSL en bas."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            for index in range(12):
                x = 15 + index * 38
                level = round(index * 255 / 11)
                painter.fillRect(x, 50, 34, 110, QColor.fromHsv(210, 200, level))
                painter.fillRect(x, 200, 34, 110, QColor.fromHsl(210, 200, level))
        tomato = QColor("tomato")
        self.readout.setText(f"tomato : hslHue() -> {tomato.hslHue()}, "
                             f"hslSaturation() -> {tomato.hslSaturation()}, "
                             f"lightness() -> {tomato.lightness()}")
        self.canvas.setImage(self.image)

    def drawHueWheels(self) -> None:
        """Vide la lecture, repart d'une image blanche ; deux roues de teintes : HSV à gauche, HSL à droite."""
        self.readout.clear()
        self.image.fill(Qt.GlobalColor.white)
        rings = [[110, 255, 128], [80, 185, 180], [50, 115, 225]]
        with QPainter(self.image) as painter:
            painter.setPen(Qt.PenStyle.NoPen)
            for ring in rings:
                radius = ring[0]
                hsvBounds = QRectF(120 - radius, 180 - radius, 2 * radius, 2 * radius)
                hslBounds = QRectF(360 - radius, 180 - radius, 2 * radius, 2 * radius)
                for hue in range(0, 360, 10):
                    painter.setBrush(QBrush(QColor.fromHsv(hue, 255, ring[1])))
                    painter.drawPie(hsvBounds, hue * 16, 10 * 16)
                    painter.setBrush(QBrush(QColor.fromHsl(hue, 255, ring[2])))
                    painter.drawPie(hslBounds, hue * 16, 10 * 16)
        self.canvas.setImage(self.image)

    def drawShades(self) -> None:
        """Repart d'une image blanche ; sept nuances d'un bleu, puis trois pastilles."""
        self.image.fill(Qt.GlobalColor.white)
        base = QColor(46, 134, 222)
        shades = [base.darker(200), base.darker(150), base.darker(120), base,
                  base.lighter(120), base.lighter(150), base.lighter(180)]
        with QPainter(self.image) as painter:
            for index, shade in enumerate(shades):
                painter.fillRect(15 + index * 65, 40, 60, 100, shade)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            colors = [QColor("tomato"), QColor("mediumseagreen"), QColor("steelblue")]
            for index, color in enumerate(colors):
                painter.setPen(QPen(color.darker(150), 4))
                painter.setBrush(QBrush(color.lighter(130)))
                painter.drawRoundedRect(25 + index * 150, 210, 130, 80, 16, 16)
        self.canvas.setImage(self.image)

    def mixBlueAndGold(self) -> None:
        """Repart d'une image blanche ; un bleu, un or, et leur mélange à parts égales, calculé en réels."""
        self.image.fill(Qt.GlobalColor.white)
        blue = QColor(46, 134, 222)
        gold = QColor("gold")
        mixture = QColor.fromRgbF((blue.redF() + gold.redF()) / 2,
                                  (blue.greenF() + gold.greenF()) / 2,
                                  (blue.blueF() + gold.blueF()) / 2)
        colors = [blue, mixture, gold]
        names = ["bleu", "mélange", "or"]
        text = ""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            for index, color in enumerate(colors):
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QPointF(100 + index * 140, 180), 60, 60)
                text += (f"{names[index]} : redF() vaut {realText(color.redF())}, "
                         f"greenF() vaut {realText(color.greenF())}, blueF() vaut {realText(color.blueF())}\n")
        self.readout.setText(text)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie les deux groupes de boutons radio et les quatre sélecteurs numériques à leurs slots."""
        self.spaceGroup.idClicked.connect(self.setNotation)
        self.numberGroup.idClicked.connect(self.setNotation)
        self.firstSlider.valueChanged.connect(self.redrawColor)
        self.secondSlider.valueChanged.connect(self.redrawColor)
        self.thirdSlider.valueChanged.connect(self.redrawColor)
        self.alphaSlider.valueChanged.connect(self.redrawColor)

    @Slot()
    def redrawColor(self) -> None:
        """Construit la couleur décrite par les sélecteurs, dans l'espace et les nombres cochés, puis la dessine."""
        space = self.spaceGroup.checkedId()
        first = self.firstSlider.value()
        second = self.secondSlider.value()
        third = self.thirdSlider.value()
        alpha = self.alphaSlider.value()
        if self.numberGroup.checkedId() == 0:
            if space == 0:
                self.color = QColor(first, second, third, alpha)
            elif space == 1:
                self.color = QColor.fromHsv(first, second, third, alpha)
            else:
                self.color = QColor.fromHsl(first, second, third, alpha)
        else:
            first = first / 1000
            second = second / 1000
            third = third / 1000
            alpha = alpha / 1000
            if space == 0:
                self.color = QColor.fromRgbF(first, second, third, alpha)
            elif space == 1:
                self.color = QColor.fromHsvF(first, second, third, alpha)
            else:
                self.color = QColor.fromHslF(first, second, third, alpha)
        self.drawChosenColor(self.color)

    @Slot()
    def setNotation(self) -> None:
        """Réécrit la couleur courante dans l'espace et les nombres cochés : libellés, bornes et valeurs."""
        color = self.color
        space = self.spaceGroup.checkedId()
        if space == 0:
            captions = ["Rouge R", "Vert G", "Bleu B"]
            integers = [color.red(), color.green(), color.blue()]
            reals = [color.redF(), color.greenF(), color.blueF()]
            firstMaximum = 255
        elif space == 1:
            captions = ["Teinte H", "Saturation S", "Valeur V"]
            integers = [max(color.hsvHue(), 0), color.hsvSaturation(), color.value()]
            reals = [max(color.hsvHueF(), 0), color.hsvSaturationF(), color.valueF()]
            firstMaximum = 359
        else:
            captions = ["Teinte H", "Saturation S", "Luminosité L"]
            integers = [max(color.hslHue(), 0), color.hslSaturation(), color.lightness()]
            reals = [max(color.hslHueF(), 0), color.hslSaturationF(), color.lightnessF()]
            firstMaximum = 359
        if self.numberGroup.checkedId() == 0:
            values = integers + [color.alpha()]
            maxima = [firstMaximum, 255, 255, 255]
            divisor = 1
        else:
            values = []
            for real in reals + [color.alphaF()]:
                values.append(round(real * 1000))
            maxima = [1000, 1000, 1000, 1000]
            divisor = 1000
        sliders = [self.firstSlider, self.secondSlider, self.thirdSlider, self.alphaSlider]
        for slider, maximum, value in zip(sliders, maxima, values):
            with QSignalBlocker(slider):
                slider.setMaximum(maximum)
                slider.setValue(value)
            self.controls.setDivisor(slider, divisor)
        for slider, caption in zip(sliders, captions):
            self.controls.setCaption(slider, caption)
        self.redrawColor()

    def drawChosenColor(self, color: QColor) -> None:
        """Dessine deux disques de cette couleur, sur du blanc et sur un fond sombre, puis l'écrit dans les nombres cochés."""
        self.image.fill(Qt.GlobalColor.white)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(240, 0, 240, 360, QColor(52, 73, 94))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(120, 180), 95, 95)
            painter.drawEllipse(QPointF(360, 180), 95, 95)
        if self.numberGroup.checkedId() == 0:
            components = (
                f"RGB : {color.red()} ; {color.green()} ; {color.blue()}\n"
                f"HSV : {color.hsvHue()} ; {color.hsvSaturation()} ; {color.value()}\n"
                f"HSL : {color.hslHue()} ; {color.hslSaturation()} ; {color.lightness()}\n"
                f"alpha : {color.alpha()}\n"
            )
        else:
            components = (
                f"RGB : {realText(color.redF())} ; {realText(color.greenF())} ; {realText(color.blueF())}\n"
                f"HSV : {realText(color.hsvHueF())} ; {realText(color.hsvSaturationF())} ; "
                f"{realText(color.valueF())}\n"
                f"HSL : {realText(color.hslHueF())} ; {realText(color.hslSaturationF())} ; "
                f"{realText(color.lightnessF())}\n"
                f"alpha : {realText(color.alphaF())}\n"
            )
        self.readout.setText(
            components
            + f"hexadécimal, en RGB : {color.name()} ; avec l'alpha en tête : "
            f"{color.name(QColor.NameFormat.HexArgb)}"
        )
        self.canvas.setImage(self.image)

    def _exploreColor(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine la couleur de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawColor()

    def _recap(self) -> None:
        """Crée la surface, puis dessine la forme du récapitulatif."""
        self.createSurface()
        self.drawReminder()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : une forme pleine",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée l'image blanche. Un "
                    "pinceau bleu, <code>QColor(46, 134, 222)</code>, remplit un rectangle "
                    "arrondi, sans contour (notions 1.2 et 2.2). Seule l'écriture change : "
                    "<code>drawRoundedRect()</code> reçoit ici les nombres un à un, x, y, largeur "
                    "et hauteur, puis les deux rayons des coins, au lieu d'un "
                    "<code>QRectF</code>. Cette notion explique ce que "
                    "disent ces trois nombres, puis montre les autres façons d'écrire une couleur."
                ),
                run=self._recap,
                codeSource=(self.createSurface, self.drawReminder),
                references=[("QColor", qtDocUrl("QtGui", "QColor"))],
            ),
            QStepWalkthrough.Step(
                title="RGB : trois lumières qui s'additionnent",
                explanation=(
                    "<code>QColor(r, g, b)</code> décrit une couleur comme un écran la produit. "
                    "Chaque pixel de l'écran a trois petites sources de lumière, rouge, verte et "
                    "bleue, d'intensité 0 à 255. Leurs lumières s'additionnent : rouge et vert "
                    "donnent du jaune, les trois au maximum du blanc, les trois éteintes du noir. "
                    "Le <a href=\"" + _RgbArticleUrl + "\">début de l'article « Rouge vert bleu » "
                    "de Wikipédia</a> décrit ce mélange de lumières, si on veut aller plus loin. "
                    "Wikipédia en français écrit RVB, et plus loin TSV et TSL pour HSV et HSL : "
                    "les mêmes sigles, traduits."
                    "<br><br>Les trois composantes peuvent servir d'axes : R, G et B, de 0 à 255 "
                    "chacun, forment un cube, dont chaque point est une couleur. Les deux grilles "
                    "en montrent deux faces. Le rouge "
                    "augmente vers la droite, le vert vers le bas. À gauche, le bleu est à 0 : "
                    "noir, rouge, vert et jaune aux quatre coins. À droite, le bleu est à 255 : "
                    "bleu, magenta, cyan et blanc. RGB est l'écriture de la machine. Elle se "
                    "prête mal aux retouches : pour pâlir un orange, il faut changer les trois "
                    "nombres à la fois."
                    "<br><br>Une couleur garde ses trois composantes. Ses accesseurs "
                    "<code>red()</code>, <code>green()</code> et <code>blue()</code> les rendent, "
                    "ici pour le bleu du récapitulatif."
                    "<br><br><i>Pour l'exemple</i> : <code>column * 255 // 7</code> répartit "
                    "les huit colonnes de 0 à 255."
                ),
                run=self.drawRgbPlanes,
                references=[
                    ("QColor", qtDocUrl("QtGui", "QColor")),
                    ("QColor.red", qtDocUrl("QtGui", "QColor", "red")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une couleur par son nom",
                explanation=(
                    "<code>QColor(\"tomato\")</code> accepte l'un des 148 noms de couleur du web : "
                    "<code>\"gold\"</code>, <code>\"steelblue\"</code>… "
                    "<code>Qt.GlobalColor</code> offre en plus une vingtaine de couleurs "
                    "prédéfinies, comme <code>Qt.GlobalColor.darkCyan</code>, le dernier "
                    "échantillon. <code>QColor()</code> accepte aussi une de ces constantes : "
                    "<code>QColor(Qt.GlobalColor.darkCyan)</code>. Un nom n'est qu'une autre "
                    "écriture d'une couleur RGB : « tomato » vaut (255, 99, 71)."
                    "<br><br><i>Pour l'exemple</i> : chaque échantillon est un "
                    "<code>fillRect()</code> (notion 2.2)."
                ),
                run=self.drawNamedColors,
                references=[
                    ("QColor", qtDocUrl("QtGui", "QColor")),
                    ("Qt.GlobalColor", qtDocUrl("QtCore", "Qt", "GlobalColor")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une couleur en hexadécimal",
                explanation=(
                    "Une couleur s'écrit aussi en hexadécimal, comme "
                    "<code>\"#ff6347\"</code>. L'hexadécimal compte en base 16 : après 9 "
                    "viennent a (10), b, c, d, e et f (15). Chaque composante s'écrit en deux "
                    "chiffres, de 00 à ff. Ici, la même couleur est écrite de trois façons : par "
                    "son nom, par ses composantes, puis en hexadécimal. Ainsi ff = 15 × 16 + 15 = 255, "
                    "63 = 6 × 16 + 3 = 99 et 47 = 4 × 16 + 7 = 71 : rouge 255, vert 99, bleu 71. "
                    "C'est toujours du RGB, écrit autrement."
                    "<br><br><code>name()</code> rend l'écriture hexadécimale d'une couleur, "
                    "<code>\"#ff6347\"</code> pour celle-ci."
                ),
                run=self.drawHexColors,
                references=[("QColor.name", qtDocUrl("QtGui", "QColor", "name"))],
            ),
            QStepWalkthrough.Step(
                title="Le canal alpha",
                explanation=(
                    "Un quatrième nombre, alpha, règle l'opacité : 255 opaque, 0 invisible. "
                    "<code>QColor(231, 76, 60, 128)</code>, rangé dans <code>red</code>, est un "
                    "rouge à moitié opaque. Son accesseur <code>alpha()</code> rend 128."
                    "<br><br>Les mêmes trois disques, à gauche sur du blanc, à droite sur un fond "
                    "sombre. Chaque disque laisse voir ce qui est dessous : le fond, puis les "
                    "autres disques. La même couleur translucide change donc d'aspect selon le "
                    "fond. Sur le blanc, le rouge à moitié opaque devient un rose ; sur le fond "
                    "sombre, un rouge terne."
                    "<br><br>L'hexadécimal peut aussi porter l'alpha. "
                    "<code>name(QColor.NameFormat.HexArgb)</code> l'écrit en tête, avant le "
                    "rouge : <code>\"#80e74c3c\"</code> pour ce rouge, où 80 vaut 128."
                    "<br><br><i>Pour l'exemple</i> : la boucle dessine le groupe deux fois, "
                    "décalé de <code>left</code>, 0 puis 240 pixels."
                ),
                run=self.drawTranslucentDiscs,
                references=[("QColor.alpha", qtDocUrl("QtGui", "QColor", "alpha"))],
            ),
            QStepWalkthrough.Step(
                title="Une image transparente",
                explanation=(
                    "<code>Qt.GlobalColor.transparent</code> est une couleur d'alpha 0. "
                    "<code>fill()</code> en remplit l'image : l'image elle-même devient "
                    "transparente, et le <b>damier</b> du canevas se voit à travers. Chaque pixel "
                    "garde sa propre opacité : c'est ce que dit le format "
                    "<code>Format_ARGB32</code> de la notion 1.1, A pour alpha."
                    "<br><br>Là où deux disques se chevauchent, l'image est plus opaque. Soit a "
                    "et b les opacités des deux disques. Le premier couvre la fraction a du "
                    "pixel ; il en laisse 1 − a. Le second couvre la fraction b de ce reste. "
                    "L'opacité finale vaut donc a + b × (1 − a). "
                    "Chaque opacité va ici de 0 à 1 : c'est l'alpha divisé par 255, et 128 donne "
                    "environ 0,5. Pour deux couches à 0,5 : 0,5 + 0,5 × 0,5 = 0,75, soit 192 sur "
                    "255. Ce nombre se calcule, la lecture ne l'affiche pas : à l'œil, le "
                    "chevauchement paraît plus foncé."
                ),
                run=self.drawOnTransparentImage,
                references=[
                    ("Qt.GlobalColor", qtDocUrl("QtCore", "Qt", "GlobalColor")),
                    ("QImage.Format", qtDocUrl("QtGui", "QImage", "Format")),
                ],
            ),
            QStepWalkthrough.Step(
                title="HSV : la teinte",
                explanation=(
                    "HSV réarrange les trois nombres de RGB pour répondre à trois questions "
                    "plus proches de notre façon de parler d'une couleur : quelle teinte, à quel "
                    "point vive, à quel point lumineuse. Ce n'est qu'un autre calcul sur R, G et B, "
                    "pas une mesure de ce que l'œil perçoit. Wikipédia décrit les "
                    "<a href=\"" + _HsvArticleUrl + "\">trois composantes</a>, si on veut aller "
                    "plus loin."
                    "<br><br><code>QColor.fromHsv(teinte, saturation, valeur)</code> crée une "
                    "couleur HSV. Elle s'appelle sur la classe <code>QColor</code> elle-même, et "
                    "non sur une couleur : c'est une <b>méthode statique</b>, qui crée et rend une "
                    "couleur neuve. La <b>teinte</b> est un angle sur le cercle des couleurs, de 0 "
                    "à 359 : 0 rouge, 120 vert, 240 bleu. Ici, sur une image redevenue blanche, "
                    "douze teintes espacées de 30°. Les deux autres nombres, 200 et 230, restent "
                    "fixes : l'étape suivante les explique."
                    "<br><br><code>hsvHue()</code> rend la teinte d'une couleur : 9 pour "
                    "« tomato », un rouge orangé. Un gris n'a pas de teinte : Qt rend −1."
                ),
                run=self.drawHues,
                references=[
                    ("QColor.fromHsv", qtDocUrl("QtGui", "QColor", "fromHsv")),
                    ("QColor.hsvHue", qtDocUrl("QtGui", "QColor", "hsvHue")),
                ],
            ),
            QStepWalkthrough.Step(
                title="HSV : saturation et valeur V",
                explanation=(
                    "Même teinte, 210, un bleu. Les deux autres composantes vont de 0 à 255 :"
                    "<ul>"
                    "<li>la <b>saturation</b>, au milieu, va du gris (0) à la couleur la plus vive "
                    "(255) ;</li>"
                    "<li>la <b>valeur V</b>, en bas, va du noir à la couleur la plus lumineuse. "
                    "C'est simplement le plus grand des trois nombres R, G et B.</li></ul>"
                    "Changer une seule composante donne une gamme cohérente, bien plus facilement "
                    "qu'en RGB. Mais V n'est pas la clarté perçue : à V = 255, un jaune pur "
                    "paraît bien plus clair qu'un bleu pur. Le bord de la roue HSV, deux étapes "
                    "plus loin, le montre."
                    "<br><br><code>hsvSaturation()</code> et <code>value()</code> rendent ces deux "
                    "composantes : 184 et 255 pour « tomato », (255, 99, 71) en RGB. La "
                    "saturation HSV est l'écart entre le plus grand et le plus petit des trois "
                    "nombres, rapporté au plus grand : (255 − 71) / 255, soit 184 sur 255. Ce <code>value()</code> est celui "
                    "de <code>QColor</code>, la valeur V. Il ne faut pas le confondre avec "
                    "l'accesseur <code>value()</code> d'un sélecteur numérique."
                ),
                run=self.drawSaturationAndValue,
                references=[
                    ("QColor.hsvSaturation", qtDocUrl("QtGui", "QColor", "hsvSaturation")),
                    ("QColor.value", qtDocUrl("QtGui", "QColor", "value")),
                ],
            ),
            QStepWalkthrough.Step(
                title="HSL : la luminosité",
                explanation=(
                    "HSL garde la teinte et une saturation, mais remplace la valeur V par la "
                    "<b>luminosité</b> L : la moyenne du plus grand et du plus petit des trois "
                    "nombres R, G et B. <code>QColor.fromHsl(teinte, saturation, "
                    "luminosité)</code> crée une couleur HSL. L'"
                    "<a href=\"" + _HslArticleUrl + "\">article de Wikipédia sur HSL</a> compare "
                    "les deux espaces, si on veut aller plus loin."
                    "<br><br>Même teinte (210), même saturation (200), et le dernier nombre de 0 "
                    "à 255 dans les deux rangées :"
                    "<ul>"
                    "<li>en haut, la valeur V va du noir à la couleur la plus lumineuse de cette "
                    "saturation, atteinte à 255 ;</li>"
                    "<li>en bas, la luminosité L va du noir à cette même couleur, atteinte au "
                    "milieu, vers 128, puis de cette couleur au blanc.</li></ul>"
                    "En HSL, la luminosité maximale donne donc toujours le blanc. En HSV, le blanc "
                    "demande une valeur maximale <i>et</i> une saturation nulle."
                    "<br><br><code>hslHue()</code>, <code>hslSaturation()</code> et "
                    "<code>lightness()</code> rendent les composantes HSL. Pour « tomato », la "
                    "saturation vaut 255 en HSL, mais 184 en HSV : un même mot n'a pas le même "
                    "calcul d'un espace à l'autre. En HSL, le même écart, 184, est rapporté à ce "
                    "que la luminosité permet : 255 − |255 + 71 − 255| = 184. Le rapport vaut 1, "
                    "soit 255."
                ),
                run=self.drawLightness,
                references=[
                    ("QColor.fromHsl", qtDocUrl("QtGui", "QColor", "fromHsl")),
                    ("QColor.lightness", qtDocUrl("QtGui", "QColor", "lightness")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Deux roues de teintes : HSV et HSL",
                explanation=(
                    "Chaque part est un <code>drawPie()</code> (notion 1.2) de 10°, remplie de la "
                    "teinte qui porte le même angle. Les angles de <code>drawPie()</code> et ceux "
                    "des teintes suivent la même convention : 0 à trois heures, sens inverse des "
                    "aiguilles d'une montre. Le rouge est donc à droite, "
                    "le vert en haut à gauche, le bleu en bas à gauche."
                    "<br><br>Les deux roues ont la même saturation, 255, et le même bord : la "
                    "<b>couleur pure</b> de chaque teinte, la plus vive qui soit, qui s'écrit "
                    "V = 255 en HSV et L = 128 en HSL. Sur ce bord, comparer le jaune et le bleu : "
                    "à V = 255 tous deux, le jaune paraît bien plus clair. Vers le centre, "
                    "chaque anneau change la troisième composante. Chaque part va jusqu'au centre, "
                    "mais les anneaux sont dessinés du plus grand au plus petit : un disque plus "
                    "petit recouvre le centre du précédent, et il ne reste de chacun qu'un "
                    "anneau :"
                    "<ul>"
                    "<li>à gauche, V diminue : la roue HSV fonce vers le noir ;</li>"
                    "<li>à droite, L augmente : la roue HSL pâlit vers le blanc.</li></ul>"
                    "Chaque espace va dans les deux sens. Pour pâlir en HSV, on baisse la "
                    "saturation. Pour foncer en HSL, on baisse L sous 128."
                    "<br><br><i>Pour l'exemple</i> : chaque élément de <code>rings</code> donne "
                    "le rayon d'un anneau, sa valeur V, puis sa luminosité L. Les deux rectangles "
                    "englobants, <code>hsvBounds</code> et <code>hslBounds</code>, sont centrés en "
                    "(120, 180) et en (360, 180)."
                ),
                run=self.drawHueWheels,
                references=[
                    ("QColor.fromHsv", qtDocUrl("QtGui", "QColor", "fromHsv")),
                    ("QColor.fromHsl", qtDocUrl("QtGui", "QColor", "fromHsl")),
                    ("QPainter.drawPie", qtDocUrl("QtGui", "QPainter", "drawPie")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Des nuances : lighter() et darker()",
                explanation=(
                    "<code>darker(150)</code> divise la valeur V par 1,5, sans changer la teinte. "
                    "<code>lighter(150)</code> la multiplie par 1,5. Mais la valeur V ne dépasse "
                    "jamais 255 : l'excédent est retiré de la saturation, et la couleur pâlit "
                    "vers le blanc. L'argument est un pourcentage : 150 multiplie par 1,5, 120 par "
                    "1,2, et <code>darker(200)</code> divise par 2. Pour ce bleu, de valeur 222 et "
                    "de saturation 202, <code>lighter(150)</code> donne 333. La valeur reste à "
                    "255, et l'excédent, 333 − 255 = 78, est retiré de la saturation : "
                    "202 − 78 = 124."
                    "<br><br>En haut, sept nuances d'un même bleu. En bas, chaque pastille tire "
                    "son remplissage et son contour d'une seule couleur. Le noir, non dessiné ici, "
                    "ne s'éclaircit pas : sa valeur V est nulle, et 0 × 1,5 reste 0."
                ),
                run=self.drawShades,
                references=[
                    ("QColor.lighter", qtDocUrl("QtGui", "QColor", "lighter")),
                    ("QColor.darker", qtDocUrl("QtGui", "QColor", "darker")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Des composantes réelles : les méthodes en F",
                explanation=(
                    "<code>QColor</code> accepte aussi des réels de 0 à 1 : "
                    "<code>fromRgbF()</code>, <code>fromHsvF()</code> et <code>fromHslF()</code>, "
                    "le F pour <i>float</i>, le réel de Python. 0 vaut 0, et 1 vaut 255. Chaque "
                    "accesseur a sa version réelle : <code>redF()</code>, <code>hsvHueF()</code>, "
                    "<code>lightnessF()</code>, <code>alphaF()</code>… La teinte aussi va de 0 à 1 : "
                    "0,5 vaut 180°, et 1 vaut 360°, le rouge de départ."
                    "<br><br>Les réels servent quand une couleur se calcule : mélanger, assombrir "
                    "d'un facteur, ou échanger avec une bibliothèque qui compte de 0 à 1. Ici, le "
                    "disque du milieu mélange le bleu et l'or à parts égales : chaque composante "
                    "est la moyenne des deux, et <code>fromRgbF()</code> en fait une couleur. Ce "
                    "sont deux lumières qui se mélangent, pas deux peintures : le résultat est un "
                    "vert-jaune terne. La lecture n'affiche que ses composantes RGB ; "
                    "<code>hsvHue()</code> et <code>hsvSaturation()</code> rendraient 82° et 93 "
                    "sur 255."
                    "<br><br><i>Pour l'exemple</i> : <code>realText()</code> écrit un réel à trois "
                    "décimales, avec la virgule décimale. Dans la f-string, <code>:.3f</code> après "
                    "le nom demande trois décimales. <code>replace(\".\", \",\")</code>, une "
                    "méthode des chaînes de Python, remplace ensuite le point par une virgule."
                ),
                run=self.mixBlueAndGold,
                codeSource=(self.mixBlueAndGold, realText),
                references=[
                    ("QColor.fromRgbF", qtDocUrl("QtGui", "QColor", "fromRgbF")),
                    ("QColor.redF", qtDocUrl("QtGui", "QColor", "redF")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : une couleur, trois espaces",
                explanation=(
                    "Neuf contrôles paraissent sous le canevas, sur quatre rangées :"
                    "<ul>"
                    "<li>trois boutons radio (<code>QRadioButton</code>), RGB, HSV et HSL, "
                    "réunis dans un groupe exclusif (<code>QButtonGroup</code>), "
                    "<code>spaceGroup</code> : cocher l'un décoche les autres ;</li>"
                    "<li>deux autres boutons radio, dans un second groupe, "
                    "<code>numberGroup</code> : des entiers de 0 à 255, ou des réels de 0 à 1 ;"
                    "</li>"
                    "<li>trois sélecteurs numériques, <code>firstSlider</code>, "
                    "<code>secondSlider</code> et <code>thirdSlider</code>, pour les trois "
                    "composantes dans l'espace coché ;</li>"
                    "<li><code>alphaSlider</code> pour l'alpha.</li></ul>"
                    "Au départ, HSV et les entiers sont cochés : teinte 210, saturation 180, "
                    "valeur 220, alpha 160."
                    "<br><br><b>Le but.</b> Passer d'un espace ou d'une sorte de nombres à "
                    "l'autre : les deux disques gardent leur couleur, les sélecteurs sautent. "
                    "Une même couleur s'écrit donc de plusieurs façons. Baisser l'alpha : le "
                    "fond paraît à travers les disques. En HSL, monter L au maximum : du blanc, "
                    "quelle que soit la teinte."
                    "<br><br>La suite explique le code affiché. Nouveau : il emploie des "
                    "éléments propres à ses contrôles, le groupe de boutons, "
                    "<code>setMaximum()</code> et <code>QSignalBlocker</code>. Ils servent "
                    "l'interaction, pas le dessin : les lire une fois suffit."
                    "<br><br><b>1. Les groupes.</b> Un groupe numérote ses boutons : <code>addButton(bouton, numéro)</code> "
                    "de <code>QButtonGroup</code> donne le sien à chacun. Ici, ils sont numérotés "
                    "dans l'ordre, à partir de 0 : RGB 0, HSV 1, HSL 2 ; entiers 0, réels 1. "
                    "<code>checkedId()</code> rend le numéro du bouton coché, et le signal "
                    "<code>idClicked</code> est émis à chaque clic."
                    "<br><br><b>2. Construire la couleur.</b> <code>redrawColor()</code> construit la couleur dans l'espace et "
                    "les nombres cochés, avec l'alpha en quatrième argument. Un sélecteur "
                    "numérique n'a que des positions entières : en réels, il va de 0 à 1000, et sa "
                    "valeur est divisée par 1000. Le slot garde la couleur dans "
                    "<code>self.color</code>, puis appelle <code>drawChosenColor()</code>. "
                    "Celle-ci dessine la couleur sur du blanc et sur un fond sombre, puis l'écrit "
                    "dans les trois espaces, avec son alpha, puis en hexadécimal, avec et sans "
                    "l'alpha. À l'arrivée sur l'étape, le guide appelle "
                    "<code>redrawColor()</code> une fois : <code>self.color</code> existe donc "
                    "avant le premier clic."
                    "<br><br><b>3. Changer de notation.</b> <code>integers + [color.alpha()]</code> "
                    "colle deux listes en une seule : les trois composantes, suivies de l'alpha. "
                    "<code>setNotation()</code> réécrit <code>self.color</code> dans "
                    "la nouvelle <b>notation</b> : l'espace et les nombres cochés. La couleur ne "
                    "change pas, seuls ses nombres changent. Le slot lit les composantes de la "
                    "couleur, puis règle chaque sélecteur. <code>setMaximum()</code> fixe sa borne "
                    "haute : 255 pour le rouge, 359 pour une teinte, 1000 en réels. "
                    "<code>setValue()</code> fixe sa position. Pour un gris, sans teinte (−1), "
                    "<code>max(…, 0)</code> ramène la teinte à 0. Chaque passage arrondit les "
                    "nombres : après plusieurs allers-retours, une composante peut s'écarter de "
                    "quelques unités sur 255, un écart à peine visible."
                    "<br><br>Pendant la boucle, les sélecteurs mêlent l'ancienne notation et la "
                    "nouvelle. Or <code>setValue()</code> émet <code>valueChanged</code> dès que "
                    "la valeur change, et <code>setMaximum()</code> aussi, quand il ramène une "
                    "valeur trop grande sous la nouvelle borne. Chaque émission appelle "
                    "<code>redrawColor()</code>, qui construirait alors une couleur fausse, "
                    "parfois hors des bornes de <code>fromHsv()</code> : Qt l'écrirait dans la "
                    "console. <code>QSignalBlocker(sélecteur)</code>, de "
                    "<code>PySide6.QtCore</code>, l'empêche : pendant son bloc <code>with</code>, "
                    "le sélecteur n'émet aucun signal, et ceux qu'il aurait émis sont perdus. À la "
                    "sortie du bloc, il en émet de nouveau. Après la boucle, un seul appel reconstruit la couleur, avec les "
                    "quatre nouvelles valeurs."
                    "<br><br><b>4. Deux méthodes des contrôles.</b> Les contrôles, rangés sous le canevas (<code>self.controls</code>), "
                    "sont un outil de ce guide, qui ne fait pas partie de Qt. Deux de ses "
                    "méthodes servent ici :"
                    "<ul>"
                    "<li><code>setCaption(contrôle, texte)</code> change le libellé affiché "
                    "devant un contrôle ;</li>"
                    "<li><code>setDivisor(sélecteur, diviseur)</code> change la valeur affichée "
                    "à côté d'un sélecteur : avec 1000, la position 725 s'affiche « 0,725 ». Elle "
                    "ne change que l'affichage, jamais la valeur du sélecteur, et met cet "
                    "affichage à jour : appelée après le bloc, elle montre la nouvelle "
                    "valeur.</li></ul>"
                ),
                run=self._exploreColor,
                codeSource=(self.connectControls, self.redrawColor, self.setNotation,
                            self.drawChosenColor),
                references=[
                    ("QButtonGroup", qtDocUrl("QtWidgets", "QButtonGroup")),
                    ("QColor.fromRgbF", qtDocUrl("QtGui", "QColor", "fromRgbF")),
                    ("QColor.redF", qtDocUrl("QtGui", "QColor", "redF")),
                    ("QColor.name", qtDocUrl("QtGui", "QColor", "name")),
                    ("QSlider", qtDocUrl("QtWidgets", "QSlider")),
                ],
            ),
        ]
