"""Notion 5.1 : une illustration interactive.

Contexte : un paysage de village, construit couche par couche, du fond vers
l'avant. Chaque couche est une méthode de dessin, et chacune réemploie une
technique d'une notion précédente : dégradés (2.4), points et transparence
(1.2, 2.3), chemins (4.1), formes de base (1.2), transformations (3.2),
découpage (4.2), opacité (4.3), texte mesuré (3.1). Rien de nouveau sur le
peintre : la notion apprend à décomposer un dessin.

Étapes couvertes : les neuf couches, toutes écrites pour 19 h 45, leurs
valeurs en clair ; puis les couleurs du ciel, la course du soleil et la
tombée de la nuit, calculées à partir de l'heure ; enfin l'heure réglée à la
main.

Chaque étape est une méthode de `QTopicIllustrationTab`, sauf les calculs
liés à l'heure et le sapin, des fonctions du module. Les couches dessinent
toutes dans la même image, `self.image`.
"""

from __future__ import annotations

import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt, Slot
from PySide6.QtGui import (
    QBrush, QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient,
)
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


def drawPine(painter: QPainter) -> None:
    """Dessine un sapin de 110 pixels de haut, le pied du tronc au point (0, 0)."""
    painter.setBrush(QColor(107, 79, 58))
    painter.drawRect(QRectF(-5, -20, 10, 20))
    painter.setBrush(QColor(45, 90, 61))
    tiers = [(-15, 30, -60), (-45, 24, -88), (-72, 17, -110)]  # (bas, demi-largeur, sommet)
    for bottom, halfWidth, top in tiers:
        painter.drawPolygon([QPointF(-halfWidth, bottom), QPointF(halfWidth, bottom),
                             QPointF(0, top)])


def mixColors(first: QColor, second: QColor, t: float) -> QColor:
    """Rend la couleur à la fraction t entre first (t = 0) et second (t = 1)."""
    red = round(first.red() + (second.red() - first.red()) * t)
    green = round(first.green() + (second.green() - first.green()) * t)
    blue = round(first.blue() + (second.blue() - first.blue()) * t)
    return QColor(red, green, blue)


def skyColors(hour: float) -> tuple[QColor, QColor]:
    """Rend les couleurs du haut et du bas du ciel à une heure de 0 à 24."""
    keys = [  # (heure clé, haut du ciel, bas du ciel)
        (0, QColor(13, 19, 48), QColor(31, 42, 82)),  # nuit
        (4.5, QColor(13, 19, 48), QColor(31, 42, 82)),
        (6, QColor(53, 71, 125), QColor(244, 162, 97)),  # aube
        (8, QColor(74, 137, 212), QColor(207, 232, 245)),  # jour
        (17.5, QColor(61, 124, 201), QColor(191, 224, 242)),
        (19.75, QColor(44, 58, 120), QColor(240, 132, 60)),  # coucher
        (21, QColor(20, 27, 64), QColor(91, 63, 110)),
        (22.5, QColor(13, 19, 48), QColor(31, 42, 82)),  # nuit
        (24, QColor(13, 19, 48), QColor(31, 42, 82)),
    ]
    for index in range(len(keys) - 1):
        hour0, top0, bottom0 = keys[index]
        hour1, top1, bottom1 = keys[index + 1]
        if hour0 <= hour <= hour1:
            t = (hour - hour0) / (hour1 - hour0)
            return mixColors(top0, top1, t), mixColors(bottom0, bottom1, t)


def sunPosition(hour: float) -> QPointF:
    """Rend le centre du soleil : levé à 5 h 30 à gauche, couché à 21 h à droite."""
    progress = (hour - 5.5) / 15.5  # 0 au lever, 1 au coucher
    x = 30 + 420 * progress
    y = 260 - 220 * math.sin(math.pi * progress)  # 260 : l'horizon
    return QPointF(x, y)


def nightAmount(hour: float) -> float:
    """Rend 0 en plein jour, 1 en pleine nuit, une valeur entre les deux sinon."""
    if hour >= 12:  # le soir : la nuit tombe de 18 h 30 à 21 h
        amount = (hour - 18.5) / 2.5
    else:  # le matin : la nuit se retire de 5 h à 7 h
        amount = (7 - hour) / 2
    return min(1.0, max(0.0, amount))


class QTopicIllustrationTab(QWidget):
    """Onglet de la notion 5.1 : un paysage complet, une technique par couche.

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
        hourSlider: L'heure, en minutes depuis minuit.
        image: La surface de la notion, ou None avant la première étape.
        windowRects: Les fenêtres des maisons, remplies par `drawHouses()`.
    """

    TabTitle = "Une illustration interactive"
    TabToolTip = "Un paysage construit couche par couche, une technique du guide à chaque couche"
    RecommendedPanelWidth = 620
    Objective = (
        "Décomposer une illustration complète en couches dessinées du fond vers l'avant, et "
        "choisir pour chacune la technique qui convient. Puis rendre tout le dessin dépendant "
        "d'un seul nombre : l'heure de la journée."
    )
    KeyConcepts = [
        "On dessine du fond vers l'avant : chaque couche recouvre les précédentes.",
        "Une méthode de dessin par couche, chacune avec son propre peintre.",
        "Chaque technique a son usage : dégradé pour le ciel, chemin pour un relief, "
        "transformations pour une forme répétée, découpage pour une fenêtre.",
        "Les valeurs écrites en clair pour une heure précise deviennent ensuite des calculs "
        "qui dépendent de l'heure.",
    ]
    KeyApis = [
        "QLinearGradient", "QRadialGradient", "QPainter.drawPoints", "QPainterPath",
        "QPainter.translate", "QPainter.save", "QPainter.setClipRect", "QPainter.setOpacity",
        "QFontMetrics",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None
        self.windowRects: list[QRectF] = []

        self.canvas = QDrawingCanvas()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.hourSlider = self.controls.addSlider("Heure", 0, 24 * 60 - 1, 19 * 60 + 45, suffix="min")
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
        """Ramène canevas, lecture et contrôle à leur état de départ, avant chaque rejeu."""
        self.controls.resetControls()
        self.readout.clear()
        self.canvas.setImage(QImage())
        self.image = None
        self.windowRects = []

    # -- Les couches du paysage, du fond vers l'avant -----------------------------------------

    def drawSky(self, top: QColor, bottom: QColor) -> None:
        """Remplit l'image d'un dégradé vertical : top en haut, bottom à l'horizon (y = 260)."""
        gradient = QLinearGradient(QPointF(0, 0), QPointF(0, 260))
        gradient.setColorAt(0, top)
        gradient.setColorAt(1, bottom)
        with QPainter(self.image) as painter:
            painter.fillRect(0, 0, 480, 360, QBrush(gradient))
        self.canvas.setImage(self.image)

    def drawStars(self, alpha: int) -> None:
        """Sème 90 étoiles blanches dans le haut du ciel, toutes du même alpha (0 à 255)."""
        generator = random.Random(7)
        stars = []
        for index in range(90):
            stars.append(QPointF(generator.uniform(0, 480), generator.uniform(0, 170)))
        pen = QPen(QColor(255, 255, 255, alpha), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(pen)
            painter.drawPoints(stars)
        self.canvas.setImage(self.image)

    def drawSunAndMoon(self, sun: QPointF, moon: QPointF) -> None:
        """Dessine la lune, puis le soleil et son halo, à leurs centres sun et moon."""
        halo = QRadialGradient(sun, 70)
        halo.setColorAt(0.0, QColor(255, 251, 230))
        halo.setColorAt(0.28, QColor(255, 214, 102))
        halo.setColorAt(0.33, QColor(255, 183, 77, 140))
        halo.setColorAt(1.0, QColor(255, 160, 60, 0))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(248, 246, 232))
            painter.drawEllipse(moon, 13, 13)
            painter.setBrush(QBrush(halo))
            painter.drawEllipse(sun, 70, 70)
        self.canvas.setImage(self.image)

    def drawMountains(self) -> None:
        """Dessine trois reliefs, du plus lointain au plus proche, chacun un chemin fermé."""
        far = QPainterPath()
        far.moveTo(0, 205)
        for x, y in [(60, 160), (115, 195), (175, 135), (240, 190), (290, 165), (350, 215),
                     (400, 238), (440, 226), (480, 240)]:
            far.lineTo(x, y)
        hills = QPainterPath()
        hills.moveTo(0, 250)
        hills.cubicTo(QPointF(90, 215), QPointF(170, 270), QPointF(260, 245))
        hills.cubicTo(QPointF(340, 222), QPointF(400, 262), QPointF(480, 250))
        meadow = QPainterPath()
        meadow.moveTo(0, 300)
        meadow.cubicTo(QPointF(120, 275), QPointF(260, 318), QPointF(480, 285))
        layers = [(far, QColor(129, 148, 184)), (hills, QColor(79, 125, 98)),
                  (meadow, QColor(111, 157, 79))]
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            for path, color in layers:
                path.lineTo(480, 360)
                path.lineTo(0, 360)
                path.closeSubpath()
                painter.setBrush(color)
                painter.drawPath(path)
        self.canvas.setImage(self.image)

    def drawHouses(self) -> None:
        """Dessine deux maisons, et retient leurs fenêtres dans self.windowRects."""
        self.windowRects = []
        ground = 308
        houses = [  # (gauche, largeur, hauteur, murs, toit)
            (60, 100, 62, QColor(241, 227, 198), QColor(181, 82, 59)),
            (205, 124, 78, QColor(233, 216, 184), QColor(140, 59, 46)),
        ]
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(61, 44, 36), 1.5))
            for left, width, height, wall, roof in houses:
                top = ground - height
                right = left + width
                painter.setBrush(wall)
                painter.drawRect(QRectF(left, top, width, height))
                painter.setBrush(roof)
                ridge = QPointF(left + width / 2, top - width * 0.45)
                painter.drawPolygon([QPointF(left - 10, top), QPointF(right + 10, top), ridge])
                painter.setBrush(QColor(107, 79, 58))
                painter.drawRect(QRectF(left + width / 2 - 11, ground - 38, 22, 38))
                for windowLeft in [left + 12, right - 12 - 26]:
                    window = QRectF(windowLeft, top + 14, 26, 24)
                    painter.setBrush(QColor(169, 199, 223))
                    painter.drawRect(window)
                    self.windowRects.append(window)
        self.canvas.setImage(self.image)

    def drawTrees(self) -> None:
        """Plante le même sapin à sept endroits, chacun dans son propre repère."""
        trees = [  # (x et y du pied, échelle, inclinaison en degrés)
            (20, 262, 0.4, 0), (355, 252, 0.35, 0), (365, 256, 0.45, 0), (183, 306, 0.6, -2),
            (372, 310, 0.95, 3), (30, 345, 1.25, -3), (445, 350, 1.45, 2),
        ]
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            for x, y, size, lean in trees:
                painter.save()
                painter.translate(x, y)
                painter.rotate(lean)
                painter.scale(size, size)
                drawPine(painter)
                painter.restore()
        self.canvas.setImage(self.image)

    def drawNightVeil(self, alpha: int) -> None:
        """Recouvre l'image d'un voile bleu nuit : alpha 0 en haut, alpha donné en bas."""
        veil = QLinearGradient(QPointF(0, 100), QPointF(0, 260))
        veil.setColorAt(0, QColor(10, 16, 48, 0))
        veil.setColorAt(1, QColor(10, 16, 48, alpha))
        with QPainter(self.image) as painter:
            painter.fillRect(0, 0, 480, 360, QBrush(veil))
        self.canvas.setImage(self.image)

    def drawLitWindows(self, opacity: float) -> None:
        """Éclaire chaque fenêtre avec l'opacité donnée, puis y dessine deux rideaux."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            for window in self.windowRects:
                painter.save()
                painter.setClipRect(window)
                light = QRadialGradient(window.center(), window.width())
                light.setColorAt(0, QColor(255, 230, 150))
                light.setColorAt(1, QColor(240, 150, 60))
                painter.setOpacity(opacity)
                painter.fillRect(window, QBrush(light))
                painter.setOpacity(1.0)
                painter.setBrush(QColor(160, 45, 50, 230))
                w = window.width()
                h = window.height()
                top = window.top() - h * 0.4
                leftCurtain = QRectF(window.left() - w * 0.55, top, w * 0.85, h * 1.8)
                rightCurtain = QRectF(window.right() - w * 0.3, top, w * 0.85, h * 1.8)
                painter.drawEllipse(leftCurtain)
                painter.drawEllipse(rightCurtain)
                painter.restore()
        self.canvas.setImage(self.image)

    def drawCaption(self, text: str) -> None:
        """Écrit le texte dans un cartouche translucide, mesuré d'après la police."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            font = QFont("Georgia", 13)
            font.setItalic(True)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            width = metrics.horizontalAdvance(text) + 24
            height = metrics.ascent() + metrics.descent() + 12
            box = QRectF(14, 14, width, height)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.drawRoundedRect(box, 8, 8)
            painter.setPen(QPen(QColor(43, 45, 66), 1))
            painter.drawText(box, Qt.AlignmentFlag.AlignCenter, text)
        self.canvas.setImage(self.image)

    # -- Étapes -------------------------------------------------------------------------------

    def addSky(self) -> None:
        """Crée la surface, puis y dessine le ciel de 19 h 45."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.drawSky(QColor(44, 58, 120), QColor(240, 132, 60))

    def addStars(self) -> None:
        """Les étoiles de 19 h 45 : la nuit est à moitié tombée, alpha 128."""
        self.drawStars(128)

    def addSunAndMoon(self) -> None:
        """Le soleil et la lune à leurs positions de 19 h 45, arrondies au pixel."""
        self.drawSunAndMoon(QPointF(416, 205), QPointF(91, 163))

    def addNightVeil(self) -> None:
        """Le voile de 19 h 45 : alpha 95 en bas."""
        self.drawNightVeil(95)

    def addLitWindows(self) -> None:
        """Les fenêtres de 19 h 45 : lumière pleinement allumée."""
        self.drawLitWindows(1.0)

    def addCaption(self) -> None:
        """La légende de 19 h 45."""
        self.drawCaption("Saint-Pixel, 19 h 45")

    def drawSkyOfEachHour(self) -> None:
        """Remplace le paysage par 24 bandes : le ciel de chaque heure, de 0 h à 23 h."""
        with QPainter(self.image) as painter:
            for hour in range(24):
                top, bottom = skyColors(hour)
                gradient = QLinearGradient(QPointF(0, 0), QPointF(0, 260))
                gradient.setColorAt(0, top)
                gradient.setColorAt(1, bottom)
                painter.fillRect(hour * 20, 0, 20, 360, QBrush(gradient))
        self.canvas.setImage(self.image)

    def drawLandscape(self, hour: float, caption: str) -> None:
        """Dessine les neuf couches dans l'ordre, avec les valeurs de l'heure donnée."""
        top, bottom = skyColors(hour)
        night = nightAmount(hour)
        self.drawSky(top, bottom)
        self.drawStars(round(255 * night))
        self.drawSunAndMoon(sunPosition(hour), sunPosition((hour + 12) % 24))
        self.drawMountains()
        self.drawHouses()
        self.drawTrees()
        self.drawNightVeil(round(190 * night))
        self.drawLitWindows(min(1.0, 2 * night))
        self.drawCaption(caption)

    def drawLandscapeAt1945(self) -> None:
        """Écrit les valeurs calculées pour 19 h 45, puis redessine le paysage avec elles."""
        sun = sunPosition(19.75)
        self.readout.setText(f"sunPosition(19.75) -> ({round(sun.x(), 1)}, {round(sun.y(), 1)})\n"
                             f"nightAmount(19.75) -> {nightAmount(19.75)}")
        self.drawLandscape(19.75, "Saint-Pixel, 19 h 45")

    def connectControls(self) -> None:
        """Relie le sélecteur numérique de l'heure au slot qui redessine."""
        self.hourSlider.valueChanged.connect(self.redrawLandscape)

    @Slot()
    def redrawLandscape(self) -> None:
        """Lit l'heure en minutes, prépare la légende et la lecture, puis redessine."""
        minutes = self.hourSlider.value()
        hour = minutes / 60
        rest = minutes % 60
        caption = f"Saint-Pixel, {minutes // 60} h {rest // 10}{rest % 10}"
        night = round(nightAmount(hour), 2)
        self.readout.setText(f"hour -> {round(hour, 2)}, nightAmount(hour) -> {night}")
        self.drawLandscape(hour, caption)

    def _exploreHour(self) -> None:
        """Connecte le contrôle, le révèle, puis dessine avec sa valeur de départ."""
        self.connectControls()
        self.controls.reveal()
        self.redrawLandscape()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        fillRectUrl = qtDocUrl("QtGui", "QPainter", "fillRect")
        radialUrl = qtDocUrl("QtGui", "QRadialGradient")
        return [
            QStepWalkthrough.Step(
                title="Le ciel de 19 h 45 : un dégradé linéaire",
                explanation=(
                    "Pas de récapitulatif : chaque couche du paysage reprend elle-même des gestes "
                    "déjà vus, et dit d'où ils viennent. "
                    "<br><br>Le paysage se dessine du fond vers l'avant, une couche par méthode. Chaque "
                    "couche a son propre peintre, et finit par <code>setImage()</code> (notion "
                    "1.1). Toutes les couches sont d'abord écrites pour une heure précise, 19 h "
                    "45. Leurs valeurs sont en clair."
                    "<br><br>D'abord la surface, puis le ciel : un dégradé linéaire vertical "
                    "(notion 2.4). <code>drawSky()</code> reçoit ses deux couleurs, celle du haut "
                    "et celle de l'horizon, à y = 260. Plus bas, la dernière couleur se prolonge "
                    "(étalement par défaut, notion 2.4). Le pré la cachera."
                ),
                run=self.addSky,
                codeSource=(self.drawSky, self.addSky),
                references=[
                    ("QLinearGradient", qtDocUrl("QtGui", "QLinearGradient")),
                    ("QPainter.fillRect", fillRectUrl),
                ],
            ),
            QStepWalkthrough.Step(
                title="Les étoiles : des points et de la transparence",
                explanation=(
                    "Quatre-vingt-dix points, dessinés par <code>drawPoints()</code> (notion 1.2). "
                    "Un stylo de 2 pixels à extrémités rondes fait de chaque point un petit "
                    "disque (notion 2.1)."
                    "<br><br>Les positions sont tirées par <code>uniform()</code> d'un générateur à "
                    "graine fixe, <code>random.Random(7)</code> : les mêmes étoiles à chaque dessin. "
                    "Le module <code>random</code> de Python est importé en tête du fichier, par "
                    "<code>import random</code> (prérequis)."
                    "<br><br>L'alpha de la couleur règle l'éclat (notion 2.3). À 19 h 45, la nuit "
                    "est à moitié tombée : alpha 128, la moitié de 255. Les étoiles paraissent à "
                    "peine."
                ),
                run=self.addStars,
                codeSource=(self.drawStars, self.addStars),
                references=[
                    ("QPainter.drawPoints", qtDocUrl("QtGui", "QPainter", "drawPoints")),
                    ("QPen.setCapStyle", qtDocUrl("QtGui", "QPen", "setCapStyle")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le soleil et la lune : un dégradé radial",
                explanation=(
                    "La lune est un disque crème de 13 pixels de rayon. Le soleil est un seul "
                    "disque de 70 pixels de rayon, rempli d'un dégradé radial (notion 2.4). Ses "
                    "points d'arrêt donnent un cœur clair, un bord net vers 30 % du rayon, puis un "
                    "halo qui s'efface jusqu'à l'alpha 0."
                    "<br><br><code>drawSunAndMoon()</code> reçoit les deux centres. Ici, leurs "
                    "positions de 19 h 45, arrondies au pixel : le soleil est bas, à droite ; la "
                    "lune est haute, à gauche."
                ),
                run=self.addSunAndMoon,
                codeSource=(self.drawSunAndMoon, self.addSunAndMoon),
                references=[("QRadialGradient", radialUrl)],
            ),
            QStepWalkthrough.Step(
                title="Les montagnes : des chemins",
                explanation=(
                    "Trois reliefs, chacun un chemin (notion 4.1). Les montagnes lointaines sont "
                    "une ligne brisée, faite de <code>lineTo()</code>. Les collines et le pré sont "
                    "des courbes de Bézier, faites de <code>cubicTo()</code>. La boucle ferme "
                    "ensuite chaque chemin par les deux coins du bas de l'image, puis le remplit."
                    "<br><br>Plus un relief est lointain, plus il est pâle et bleuté : c'est la "
                    "perspective atmosphérique. Le bas du soleil disparaît derrière les "
                    "montagnes."
                ),
                run=self.drawMountains,
                references=[
                    ("QPainterPath", qtDocUrl("QtGui", "QPainterPath")),
                    ("QPainter.drawPath", qtDocUrl("QtGui", "QPainter", "drawPath")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Les maisons : des formes de base",
                explanation=(
                    "Chaque maison n'est faite que de formes de base (notion 1.2) : un rectangle "
                    "pour les murs, un triangle pour le toit, un rectangle pour la porte et un "
                    "pour chaque fenêtre. Le même stylo foncé les contourne. Un pinceau différent "
                    "remplit chaque partie (notions 2.1 et 2.2). Le stylo a une épaisseur "
                    "décimale, 1,5 pixel : comme toute coordonnée, une épaisseur peut être réelle."
                    "<br><br>Les calculs, maison par maison. Chaque tuple de <code>houses</code> "
                    "donne le bord gauche, la largeur, la hauteur des murs, puis les couleurs des "
                    "murs et du toit. Les murs posent leur bas sur le sol, "
                    "<code>ground</code> : leur haut est à <code>ground - height</code>. Le toit "
                    "est un triangle qui déborde de 10 pixels de chaque côté ; son faîte, "
                    "<code>ridge</code>, est au milieu, à 0,45 fois la largeur au-dessus des murs. "
                    "La porte, de 22 × 38, est centrée en bas. Les deux fenêtres sont à 12 pixels "
                    "des bords et à 14 pixels du haut des murs."
                    "<br><br>Chaque fenêtre est un <code>QRectF</code> (notion 1.2), ajouté à la "
                    "liste <code>self.windowRects</code>. Une couche suivante les éclairera."
                ),
                run=self.drawHouses,
                references=[("QPainter.drawPolygon", qtDocUrl("QtGui", "QPainter", "drawPolygon"))],
            ),
            QStepWalkthrough.Step(
                title="Les sapins : une forme, plusieurs repères",
                explanation=(
                    "<code>drawPine(painter)</code> reçoit un peintre actif et dessine toujours le "
                    "même sapin, le pied sur le point (0, 0). Elle ne rend rien. Pour chaque "
                    "arbre, le repère est déplacé jusqu'au pied par <code>translate()</code>, "
                    "tourné de quelques degrés par <code>rotate()</code>, puis mis à l'échelle "
                    "par <code>scale()</code> (notion 3.2). <code>save()</code> et "
                    "<code>restore()</code> isolent chaque arbre."
                    "<br><br>Petits et hauts dans l'image, les sapins paraissent lointains. "
                    "Grands et bas, ils passent au premier plan. La liste va du plus lointain au "
                    "plus proche : chaque arbre se peint par-dessus les précédents, et les "
                    "maisons, dessinées avant, restent derrière tous les arbres. L'ordre des "
                    "gestes fait la profondeur : un arbre lointain doit donc éviter les maisons, "
                    "sinon il passerait devant elles."
                ),
                run=self.drawTrees,
                codeSource=(drawPine, self.drawTrees),
                references=[
                    ("QPainter.translate", qtDocUrl("QtGui", "QPainter", "translate")),
                    ("QPainter.save", qtDocUrl("QtGui", "QPainter", "save")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La tombée de la nuit : un voile translucide",
                explanation=(
                    "Plutôt que de foncer chaque couleur une à une, un seul rectangle recouvre "
                    "toute l'image. Son pinceau est un dégradé bleu nuit, d'alpha 0 jusqu'à y = "
                    "100, puis de plus en plus opaque jusqu'à y = 260 (notions 2.3 et 2.4). Le "
                    "haut du ciel, déjà sombre, n'est pas voilé. La lune et les étoiles les plus "
                    "basses, vers y = 165, le sont à peine : l'alpha y est encore faible. Le bas "
                    "du paysage s'assombrit d'un coup."
                    "<br><br>À 19 h 45, l'alpha du bas vaut 95, la moitié de 190, l'alpha de la "
                    "pleine nuit."
                ),
                run=self.addNightVeil,
                codeSource=(self.drawNightVeil, self.addNightVeil),
                references=[("QPainter.fillRect", fillRectUrl)],
            ),
            QStepWalkthrough.Step(
                title="Les fenêtres éclairées : le découpage",
                explanation=(
                    "Dessinées après le voile, les fenêtres restent vives. Un <code>QRectF</code> "
                    "rend ses mesures par ses accesseurs :"
                    "<ul>"
                    "<li>ses bords : <code>left()</code>, <code>right()</code> et "
                    "<code>top()</code> ;</li>"
                    "<li>sa taille : <code>width()</code> et <code>height()</code> ;</li>"
                    "<li>son centre : <code>center()</code>, un <code>QPointF</code>.</li></ul>"
                    "<br><br><code>fillRect()</code> reçoit ici le rectangle en un seul objet, la "
                    "fenêtre, au lieu de quatre nombres : une autre écriture de la même méthode "
                    "(notion 1.2)."
                    "<br><br>Dans chaque fenêtre : une lumière chaude en dégradé radial, puis deux "
                    "rideaux. Chaque rideau est une grande ellipse, plus large que la fenêtre. "
                    "<code>setClipRect(window)</code> (notion 4.2) limite tout dessin au cadre : "
                    "seul l'arrondi du rideau reste visible. <code>setOpacity()</code> (notion "
                    "4.3) dose la lumière ; à 19 h 45, elle est pleine (1,0). "
                    "<code>restore()</code> rend l'état mémorisé par <code>save()</code> : le "
                    "découpage et l'opacité disparaissent avant la fenêtre suivante."
                ),
                run=self.addLitWindows,
                codeSource=(self.drawLitWindows, self.addLitWindows),
                references=[
                    ("QPainter.setClipRect", qtDocUrl("QtGui", "QPainter", "setClipRect")),
                    ("QRectF", qtDocUrl("QtCore", "QRectF")),
                ],
            ),
            QStepWalkthrough.Step(
                title="La légende : du texte mesuré",
                explanation=(
                    "Le nom du village et l'heure, dans un cartouche blanc translucide aux coins "
                    "arrondis. Sa taille n'est pas écrite à la main : les mesures de la police "
                    "la donnent (notion 3.1). La largeur est <code>horizontalAdvance(text)</code>, "
                    "la hauteur <code>ascent() + descent()</code>, plus une marge. "
                    "<code>AlignCenter</code> centre le texte dans le cartouche (notion 3.1)."
                    "<br><br>L'illustration de 19 h 45 est complète."
                ),
                run=self.addCaption,
                codeSource=(self.drawCaption, self.addCaption),
                references=[
                    ("QPainter.drawText", qtDocUrl("QtGui", "QPainter", "drawText")),
                    ("QFontMetrics", qtDocUrl("QtGui", "QFontMetrics")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Le ciel suit l'heure",
                explanation=(
                    "Les couleurs du ciel vont maintenant dépendre de l'heure. "
                    "<code>skyColors(hour)</code> reçoit une heure de 0 à 24, en nombre réel : "
                    "19,75 pour 19 h 45. Elle rend deux couleurs, le haut et le bas du ciel. "
                    "La liste <code>keys</code> donne neuf heures clés, chacune avec ses deux "
                    "couleurs. 19 h 45 en est une : ses couleurs sont celles de l'étape « Le ciel "
                    "de 19 h 45 »."
                    "<br><br>La boucle parcourt les heures clés deux par deux, et s'arrête sur "
                    "celles qui encadrent l'heure demandée. <code>t</code> est la fraction du "
                    "chemin parcouru de "
                    "l'une à l'autre : 0 à la première, 1 à la seconde. "
                    "<code>mixColors(first, second, t)</code> mélange les deux couleurs, composante "
                    "par composante : <code>first + (second - first) * t</code>, arrondi à l'entier."
                    "<br><br>Pour le voir, le paysage est remplacé par 24 bandes : le ciel de "
                    "chaque heure, de 0 h à gauche à 23 h à droite."
                ),
                run=self.drawSkyOfEachHour,
                codeSource=(mixColors, skyColors, self.drawSkyOfEachHour),
                references=[("QColor", qtDocUrl("QtGui", "QColor"))],
            ),
            QStepWalkthrough.Step(
                title="Le soleil et la nuit suivent l'heure",
                explanation=(
                    "<code>sunPosition(hour)</code> rend le centre du soleil, un "
                    "<code>QPointF</code>. Sa course va de 5 h 30 à 21 h ; "
                    "<code>progress</code> passe de 0 au lever à 1 au coucher. Le soleil avance "
                    "de gauche à droite. Sa hauteur au-dessus de l'horizon vaut 220 × sin(π × "
                    "progress) pixels : 0 au lever et au coucher, 220 à mi-course. La nuit, "
                    "progress sort de 0 à 1 et le sinus devient négatif : le soleil passe sous "
                    "l'horizon. <code>math.sin()</code> et <code>math.pi</code> viennent du "
                    "module <code>math</code> de Python, importé en tête du fichier (prérequis). "
                    "La lune suit la même course, douze heures plus tard : "
                    "<code>(hour + 12) % 24</code>."
                    "<br><br><code>nightAmount(hour)</code> rend 0 le jour, 1 la nuit, et une "
                    "valeur entre les deux pendant les transitions. Les étoiles reçoivent 255 fois "
                    "cette valeur, le voile 190 fois. La lumière des fenêtres en reçoit le "
                    "double, plafonné à 1,0 : les lampes s'allument dès le crépuscule."
                    "<br><br><code>drawLandscape()</code> dessine les neuf couches avec ces "
                    "valeurs. La lecture montre celles de 19 h 45 : <code>x()</code> et "
                    "<code>y()</code> rendent les coordonnées du point. Le paysage remplace les "
                    "bandes. Il est identique à celui de l'étape « La légende » : les valeurs "
                    "calculées pour 19 h 45 sont celles écrites en clair, à une fraction de pixel "
                    "près pour le soleil et la lune."
                ),
                run=self.drawLandscapeAt1945,
                codeSource=(sunPosition, nightAmount, self.drawLandscape, self.drawLandscapeAt1945),
                references=[("QPointF", qtDocUrl("QtCore", "QPointF"))],
            ),
            QStepWalkthrough.Step(
                title="À vous : l'heure de la journée",
                explanation=(
                    "Un contrôle paraît sous le canevas et la lecture. Le sélecteur numérique "
                    "<code>hourSlider</code> règle l'heure en minutes depuis minuit, de 0 à "
                    "1439 (1185 au départ, soit 19 h 45)."
                    "<br><br><code>connectControls()</code> relie son signal au slot "
                    "<code>redrawLandscape()</code>. Il divise les minutes par 60 pour obtenir "
                    "l'heure. <code>minutes // 60</code> donne les heures entières, et "
                    "<code>minutes % 60</code> les minutes restantes. Celles-ci s'écrivent en "
                    "deux chiffres : <code>rest // 10</code>, puis <code>rest % 10</code>. Ainsi "
                    "5 minutes s'écrivent « 05 »."
                    "<br><br>Faire glisser le sélecteur : l'aube orangée, le plein jour, le "
                    "coucher, puis la nuit, ses étoiles et sa lune."
                ),
                run=self._exploreHour,
                codeSource=(self.connectControls, self.redrawLandscape),
                references=[("QPainter", qtDocUrl("QtGui", "QPainter"))],
            ),
        ]
