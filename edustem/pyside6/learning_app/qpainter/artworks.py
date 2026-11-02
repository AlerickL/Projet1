"""Les œuvres de l'application qpainter : treize petits programmes de dessin.

Chaque œuvre est un programme de l'atelier (notion 5.2) : un texte Python
exécuté par `runDrawingProgram`, avec un peintre actif sur une image blanche
de 480 × 360 pixels. La même source sert deux fois : l'image d'illustration
de sa page (l'introduction d'un chapitre, sa synthèse, ou l'introduction du
guide), et une œuvre de l'atelier, pour lire le programme, l'exécuter et le
modifier. Toutes les images d'illustration sont donc produites par QPainter.

Chaque chapitre a deux œuvres : celle de son introduction, puis celle de sa
synthèse. Deux autres n'illustrent aucune page : elles ne vivent que dans
l'atelier. Chacune n'emploie que les techniques de son chapitre et des
précédents : elle montre ce qu'on sait faire à la fin du chapitre. La
dernière illustre la page « Introduction » : plus audacieuse et plus
abstraite, elle montre où mène le guide entier.

L'application ne recalcule pas les images de ses pages : elle les lit
(`artworkImage`), pré-générées en PNG dans `assets/images/qpainter/` par
`render_artwork_images.py`. Le manifeste `artworks.json` y associe chaque
titre à l'empreinte de son programme (`artworkFingerprint`). Un test
signale toute image manquante ou périmée : l'image affichée reste celle que
produit le programme lisible dans l'atelier.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter

from ..common.image_assets import ImagesRoot
from .drawing_sandbox import runDrawingProgram

# The pre-rendered images of the artworks that illustrate a page, and their manifest. Both are
# written by render_artwork_images.py.
ImagesFolder = ImagesRoot / "qpainter"
ManifestPath = ImagesFolder / "artworks.json"


@dataclass(frozen=True)
class Artwork:
    """Une œuvre : son titre, son chapitre (None : l'introduction), son programme, et sa page.

    `synthesis` est vrai pour l'œuvre de la page de synthèse du chapitre,
    faux pour celle de sa page d'introduction. `illustrates` est faux pour
    une œuvre qui n'illustre aucune page et ne vit que dans l'atelier ; son
    chapitre dit alors seulement quelles techniques elle emploie.
    """

    title: str
    chapter: int | None
    code: str
    synthesis: bool = False
    illustrates: bool = True

    def pageTitle(self) -> str:
        """Le nom de la page qu'elle illustre, tel que l'affiche le menu des œuvres de l'atelier."""
        if not self.illustrates:
            return "Atelier"
        if self.chapter is None:
            return "Introduction"
        return f"Synthèse du chapitre {self.chapter}" if self.synthesis else f"Chapitre {self.chapter}"


Artworks: list[Artwork] = [
    Artwork("Fils tendus", 1, '''\
# Fils tendus : chaque fil est un simple segment.
# Leurs enveloppes dessinent des courbes.
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
left, top, size = 90, 30, 300
for index in range(31):
    step = index * 10
    painter.setPen(QPen(QColor(230 - index * 5, 70 + index * 3, 90 + index * 5), 1))
    painter.drawLine(QPointF(left, top + step), QPointF(left + step, top + size))
    painter.drawLine(QPointF(left + step, top), QPointF(left + size, top + step))
    painter.setPen(QPen(QColor(40 + index * 5, 120 + index * 3, 200 - index * 4), 1))
    painter.drawLine(QPointF(left + size - step, top), QPointF(left, top + step))
    painter.drawLine(QPointF(left + size, top + step), QPointF(left + size - step, top + size))
painter.setPen(QPen(QColor(45, 52, 54), 2))
painter.drawRect(QRectF(left, top, size, size))
'''),
    Artwork("Moiré", 1, '''\
# Moiré : deux familles de cercles concentriques, aux centres voisins.
# Chaque cercle est un simple trait ; leurs croisements font naître des franges.
painter.fillRect(0, 0, 480, 360, QColor("#fbfaf6"))
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
for center, color in ((QPointF(205, 180), QColor(20, 70, 140)), (QPointF(275, 180), QColor(190, 40, 70))):
    painter.setPen(QPen(color, 2.2))
    for radius in range(8, 300, 10):
        painter.drawEllipse(center, radius, radius)
painter.setPen(QPen(QColor(45, 52, 54), 3))
painter.drawRect(QRectF(1.5, 1.5, 477, 357))
''', synthesis=True),
    Artwork("Bulles", 2, '''\
# Bulles : un fond en dégradé, puis des disques translucides placés au hasard,
# chacun éclairé par un dégradé radial décentré.
night = QLinearGradient(QPointF(0, 0), QPointF(0, 360))
night.setColorAt(0, QColor("#0b1d51"))
night.setColorAt(1, QColor("#3a0f4f"))
painter.fillRect(0, 0, 480, 360, QBrush(night))
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
generator = random.Random(11)
for index in range(32):
    x = generator.uniform(15, 465)
    y = generator.uniform(15, 345)
    radius = generator.uniform(8, 48)
    hue = generator.randrange(360)
    bubble = QRadialGradient(QPointF(x, y), radius, QPointF(x - radius / 3, y - radius / 3))
    bubble.setColorAt(0, QColor(255, 255, 255, 230))
    bubble.setColorAt(0.35, QColor.fromHsv(hue, 150, 255, 150))
    bubble.setColorAt(1, QColor.fromHsv(hue, 220, 200, 50))
    painter.setPen(QPen(QColor.fromHsv(hue, 90, 255, 200), 1.5))
    painter.setBrush(QBrush(bubble))
    painter.drawEllipse(QPointF(x, y), radius, radius)
'''),
    Artwork("Écailles", 2, '''\
# Écailles : des rangées de disques qui se chevauchent, de la plus haute à la plus basse.
# Chaque disque est rempli d'un dégradé linéaire, de sa teinte à une nuance plus sombre,
# et bordé d'un trait clair.
painter.fillRect(0, 0, 480, 360, QColor("#10202b"))
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
radius = 30
for row in range(-1, 17):
    y = row * radius * 0.75
    shift = radius if row % 2 else 0
    for column in range(-1, 10):
        x = column * 2 * radius + shift
        hue = (170 + row * 8 + column * 5) % 360
        color = QColor.fromHsv(hue, 150, 225)
        scale = QLinearGradient(QPointF(x, y - radius), QPointF(x, y + radius))
        scale.setColorAt(0, color.lighter(130))
        scale.setColorAt(1, color.darker(220))
        painter.setBrush(QBrush(scale))
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1.5))
        painter.drawEllipse(QPointF(x, y), radius, radius)
''', synthesis=True),
    Artwork("Rosace de mots", 3, '''\
# Rosace de mots : un même mot, tourné et agrandi pas à pas autour du centre.
# Le dernier, le plus grand, se pose à l'horizontale, comme un texte ordinaire.
painter.fillRect(0, 0, 480, 360, QColor("#fdf6e3"))
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.translate(240, 180)
painter.setFont(QFont("Georgia", 11))
count = 40
first, last = 0.45, 2.2
for index in range(count):
    painter.save()
    painter.rotate((index - (count - 1)) * 27)
    size = first + (last - first) * index / (count - 1)
    painter.scale(size, size)
    painter.setPen(QPen(QColor.fromHsv((index * 15) % 360, 200, 170), 1))
    painter.drawText(QPointF(18, 0), "QPainter")
    painter.restore()
'''),
    Artwork("Cadran", 3, '''\
# Cadran : des graduations posées par rotation du repère, puis des chiffres
# centrés sur leur place grâce aux mesures de la police.
painter.fillRect(0, 0, 480, 360, QColor("#2b2d42"))
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.translate(240, 180)
painter.setPen(QPen(QColor("#8d99ae"), 6))
painter.setBrush(QColor("#edf2f4"))
painter.drawEllipse(QPointF(0, 0), 160, 160)
for minute in range(60):
    painter.save()
    painter.rotate(minute * 6)
    if minute % 5 == 0:
        painter.setPen(QPen(QColor("#2b2d42"), 4))
        painter.drawLine(QPointF(0, -148), QPointF(0, -128))
    else:
        painter.setPen(QPen(QColor("#8d99ae"), 1.5))
        painter.drawLine(QPointF(0, -148), QPointF(0, -140))
    painter.restore()
font = QFont("Georgia", 20)
painter.setFont(font)
metrics = QFontMetricsF(font)
painter.setPen(QColor("#2b2d42"))
for hour in range(1, 13):
    angle = math.radians(hour * 30)
    x = 105 * math.sin(angle)
    y = -105 * math.cos(angle)
    text = str(hour)
    width = metrics.horizontalAdvance(text)
    painter.drawText(QPointF(x - width / 2, y + (metrics.ascent() - metrics.descent()) / 2), text)
for angle, length, width, color in ((300, 70, 8, "#2b2d42"), (60, 115, 5, "#2b2d42"), (200, 125, 2, "#d90429")):
    painter.save()
    painter.rotate(angle)
    pen = QPen(QColor(color), width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(QPointF(0, 18), QPointF(0, -length))
    painter.restore()
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(QColor("#d90429"))
painter.drawEllipse(QPointF(0, 0), 7, 7)
''', synthesis=True),
    Artwork("Hublot", 4, '''\
# Hublot : des vagues faites de courbes cubiques, un soleil en mode Screen,
# le tout découpé par un disque.
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.fillRect(0, 0, 480, 360, QColor("#1b1b2f"))
porthole = QPainterPath()
porthole.addEllipse(QPointF(240, 180), 160, 160)
painter.setClipPath(porthole)
sky = QLinearGradient(QPointF(0, 20), QPointF(0, 200))
sky.setColorAt(0, QColor("#f8b195"))
sky.setColorAt(1, QColor("#f67280"))
painter.fillRect(0, 0, 480, 360, QBrush(sky))
sun = QRadialGradient(QPointF(300, 150), 90)
sun.setColorAt(0, QColor(255, 236, 160))
sun.setColorAt(0.4, QColor(255, 200, 120, 200))
sun.setColorAt(1, QColor(255, 160, 120, 0))
painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(QBrush(sun))
painter.drawEllipse(QPointF(300, 150), 90, 90)
painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
for layer in range(5):
    y = 175 + layer * 34
    wave = QPainterPath()
    wave.moveTo(0, y)
    for k in range(6):
        x = k * 96 - layer * 19
        wave.cubicTo(x + 32, y - 20, x + 64, y + 20, x + 96, y)
    wave.lineTo(480, 360)
    wave.lineTo(0, 360)
    wave.closeSubpath()
    painter.setBrush(QColor.fromHsv(205 + layer * 5, 170, 220 - layer * 38))
    painter.drawPath(wave)
painter.setClipping(False)
painter.setBrush(Qt.BrushStyle.NoBrush)
painter.setPen(QPen(QColor("#c9a227"), 12))
painter.drawPath(porthole)
'''),
    Artwork("Pétales de lumière", 4, '''\
# Pétales de lumière : seize pétales sur un fond de nuit,
# longs et courts en alternance. Chacun est rempli d'un dégradé, sombre au
# cœur et lumineux à la pointe, et bordé d'un trait fin. En mode Screen,
# leurs recouvrements s'éclaircissent.
painter.fillRect(0, 0, 480, 360, QColor("#14112a"))
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
painter.translate(240, 180)
for index in range(16):
    length = 165 if index % 2 == 0 else 110
    hue = (180 + index * 9) % 360
    painter.save()
    painter.rotate(index * 22.5)
    petal = QLinearGradient(QPointF(0, 0), QPointF(length, 0))
    petal.setColorAt(0, QColor.fromHsv(hue, 200, 120, 30))
    petal.setColorAt(0.75, QColor.fromHsv(hue, 170, 255, 150))
    petal.setColorAt(1, QColor.fromHsv(hue, 90, 255, 200))
    painter.setBrush(QBrush(petal))
    painter.setPen(QPen(QColor.fromHsv(hue, 120, 255, 160), 1))
    painter.drawEllipse(QRectF(0, -length / 7, length, 2 * length / 7))
    painter.restore()
''', synthesis=True),
    Artwork("Nuit en montagne", 5, '''\
# Nuit en montagne : un ciel, des étoiles au hasard, une lune,
# des montagnes et des sapins, du plus loin au plus proche.
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
sky = QLinearGradient(QPointF(0, 0), QPointF(0, 360))
sky.setColorAt(0, QColor("#020111"))
sky.setColorAt(0.7, QColor("#20124d"))
sky.setColorAt(1, QColor("#3d2c8d"))
painter.fillRect(0, 0, 480, 360, QBrush(sky))
generator = random.Random(4)
painter.setPen(Qt.PenStyle.NoPen)
for index in range(90):
    painter.setBrush(QColor(255, 255, 255, generator.randint(60, 255)))
    painter.drawEllipse(QPointF(generator.uniform(0, 480), generator.uniform(0, 230)), 1.2, 1.2)
glow = QRadialGradient(QPointF(370, 80), 60)
glow.setColorAt(0, QColor(255, 250, 220))
glow.setColorAt(0.45, QColor(255, 250, 220))
glow.setColorAt(0.5, QColor(255, 250, 220, 90))
glow.setColorAt(1, QColor(255, 250, 220, 0))
painter.setBrush(QBrush(glow))
painter.drawEllipse(QPointF(370, 80), 60, 60)
for layer in range(3):
    ridge = QPainterPath()
    ridge.moveTo(0, 360)
    for index in range(13):
        x = index * 40
        height = 70 + 45 * math.sin(index * 1.3 + layer * 2.1) + layer * 40
        ridge.lineTo(x, 300 - height + layer * 25)
    ridge.lineTo(480, 360)
    ridge.closeSubpath()
    painter.setBrush(QColor.fromHsv(255, 90, 125 - layer * 40))
    painter.drawPath(ridge)
tree = QPolygonF([QPointF(0, -46), QPointF(14, -16), QPointF(7, -16), QPointF(20, 8),
                  QPointF(-20, 8), QPointF(-7, -16), QPointF(-14, -16)])
painter.setBrush(QColor("#0b0b1a"))
for index in range(9):
    painter.save()
    painter.translate(30 + index * 55, 340 - (index % 3) * 6)
    painter.scale(1 + (index % 2) * 0.4, 1 + (index % 2) * 0.4)
    painter.drawPolygon(tree)
    painter.restore()
'''),
    Artwork("Arbre", 5, '''\
# Arbre : une fonction qui dessine une branche, puis s'appelle elle-même
# pour deux branches plus courtes, chacune dans un repère tourné.
painter.fillRect(0, 0, 480, 360, QColor("#f3efe0"))
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
generator = random.Random(3)


def branch(length, depth):
    """Une branche de longueur donnée, vers le haut du repère ; puis ses deux branches filles."""
    pen = QPen(QColor.fromHsv(25 + (9 - depth) * 9, 160, 90 + (9 - depth) * 15), max(1, depth * 1.4))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(QPointF(0, 0), QPointF(0, -length))
    if depth == 0:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor.fromHsv(generator.randint(330, 370) % 360, 140, 240, 170))
        painter.drawEllipse(QPointF(0, -length), 5, 5)
        return
    painter.translate(0, -length)
    for angle in (-generator.uniform(15, 35), generator.uniform(15, 35)):
        painter.save()
        painter.rotate(angle)
        branch(length * generator.uniform(0.68, 0.8), depth - 1)
        painter.restore()


painter.translate(240, 350)
branch(85, 9)
''', synthesis=True),
    Artwork("Ville au crépuscule", 5, '''\
# Ville au crépuscule : un ciel, un soleil bas, des immeubles et leurs fenêtres,
# puis leur reflet dans l'eau, du plus loin au plus proche.
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
sky = QLinearGradient(QPointF(0, 0), QPointF(0, 250))
sky.setColorAt(0, QColor("#1d2b64"))
sky.setColorAt(0.6, QColor("#c0587e"))
sky.setColorAt(1, QColor("#fca96b"))
painter.fillRect(0, 0, 480, 250, QBrush(sky))
sun = QRadialGradient(QPointF(330, 235), 70)
sun.setColorAt(0, QColor(255, 240, 200))
sun.setColorAt(0.3, QColor(255, 220, 150, 220))
sun.setColorAt(1, QColor(255, 180, 120, 0))
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(QBrush(sun))
painter.drawEllipse(QPointF(330, 235), 70, 70)


def city(painter, generator):
    """Les immeubles, posés sur la ligne y = 250, et leurs fenêtres éclairées au hasard."""
    x = 0
    while x < 480:
        width = generator.randint(28, 60)
        height = generator.randint(50, 170)
        painter.setBrush(QColor.fromHsv(250, 60, generator.randint(40, 70)))
        painter.drawRect(QRectF(x, 250 - height, width - 2, height))
        painter.setBrush(QColor(255, 214, 120))
        for wy in range(int(250 - height + 8), 242, 12):
            for wx in range(x + 5, x + width - 9, 9):
                if generator.random() < 0.35:
                    painter.drawRect(QRectF(wx, wy, 4, 6))
        x += width


city(painter, random.Random(5))
water = QLinearGradient(QPointF(0, 250), QPointF(0, 360))
water.setColorAt(0, QColor("#3b2b5a"))
water.setColorAt(1, QColor("#0d1430"))
painter.fillRect(0, 250, 480, 110, QBrush(water))
painter.save()
painter.setClipRect(QRectF(0, 250, 480, 110))
painter.translate(0, 500)
painter.scale(1, -1)
painter.setOpacity(0.3)
city(painter, random.Random(5))
painter.restore()
painter.setPen(QPen(QColor(255, 220, 170, 160), 1))
for k in range(14):
    y = 256 + k * 7.5
    painter.drawLine(QPointF(300 - k * 3, y), QPointF(360 + k * 3, y))
''', illustrates=False),
    Artwork("Tuiles de Truchet", 5, '''\
# Tuiles de Truchet : chaque case tire au hasard l'une de deux tuiles,
# deux quarts de cercle. Ensemble, ils tracent un labyrinthe de courbes.
painter.fillRect(0, 0, 480, 360, QColor("#f4f1de"))
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
generator = random.Random(7)
size = 40
half = size / 2
for row in range(9):
    for column in range(12):
        x = column * size
        y = row * size
        pen = QPen(QColor.fromHsv((column * 14 + row * 22) % 360, 170, 200), 7)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        if generator.random() < 0.5:
            painter.drawArc(QRectF(x - half, y - half, size, size), 270 * 16, 90 * 16)
            painter.drawArc(QRectF(x + half, y + half, size, size), 90 * 16, 90 * 16)
        else:
            painter.drawArc(QRectF(x + half, y - half, size, size), 180 * 16, 90 * 16)
            painter.drawArc(QRectF(x - half, y + half, size, size), 0, 90 * 16)
''', illustrates=False),
    Artwork("Rubans de lumière", None, '''\
# Rubans de lumière : une tresse désordonnée de cinquante-six faisceaux.
# La plupart des rubans forment une tresse : ils se
# croisent une première fois vers x = 130, s'écartent en fuseau, puis se
# recroisent à droite. Les autres ignorent le premier nœud : ils sortent par le
# haut ou le bas de l'image et y reviennent avant de la quitter à gauche. Le
# hasard décale les nœuds, les croisements et les écarts de chaque ruban.
# Chaque ruban suit un polynôme de degré 3, celui qui passe par 4 points : la
# courbe est lisse partout. L'épaisseur pulse, à un rythme propre à chaque
# ruban. Le halo : des traits larges et transparents sous un cœur fin et
# lumineux, superposés en mode Screen ; il s'atténue quand les rubans sont
# nombreux.
night = QLinearGradient(QPointF(0, 0), QPointF(0, 360))
night.setColorAt(0, QColor("#070a18"))
night.setColorAt(1, QColor("#150a24"))
painter.fillRect(0, 0, 480, 360, QBrush(night))
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)


def polynomial(knotsX, knotsY, x):
    """La valeur en x du polynôme qui passe par les points (knotsX, knotsY), selon Lagrange."""
    total = 0
    for i in range(len(knotsX)):
        term = knotsY[i]
        for j in range(len(knotsX)):
            if j != i:
                term *= (x - knotsX[j]) / (knotsX[i] - knotsX[j])
        total += term
    return total


def light(hue, saturation, alpha):
    """Un pinceau horizontal : la couleur s'allume de gauche à droite, puis pâlit un peu au bord."""
    gradient = QLinearGradient(QPointF(0, 0), QPointF(480, 0))
    gradient.setColorAt(0, QColor.fromHsv(hue, saturation, 255, alpha // 4))
    gradient.setColorAt(0.7, QColor.fromHsv(hue, saturation, 255, alpha))
    gradient.setColorAt(1, QColor.fromHsv(hue, saturation, 255, alpha // 2))
    return QBrush(gradient)


generator = random.Random(38)
count = 56
fade = min(1, 30 / count)
halos = ((22, int(30 * fade)), (12, int(60 * fade)), (5, int(120 * fade)))
for index in range(count):
    offset = 2 * index / (count - 1) - 1
    crossX = 350 + 10 * offset + generator.uniform(-25, 25)
    crossY = 176 + 18 * offset + generator.uniform(-20, 20)
    if generator.random() < 0.3:
        # Ce ruban sort par le bord le plus proche, puis revient avant de quitter l'image à gauche.
        # Son dernier point, hors de l'image à x = 600, garde la droite sans retour en arrière.
        left = 180 + 100 * offset + generator.uniform(-30, 30)
        edge = generator.uniform(-35, -10) if offset < 0 else generator.uniform(370, 395)
        right = 180 - 260 * offset * generator.uniform(0.7, 1.3)
        knotsX = [-20, generator.uniform(100, 180), crossX, 600]
        knotsY = [left, edge, crossY, crossY + 1.7 * (right - crossY)]
    else:
        # Un premier nœud, lâche et désordonné, vers x = 130.
        left = 180 + 195 * offset + generator.uniform(-45, 45)
        right = 180 + 230 * offset * generator.uniform(0.7, 1.3)
        knotsX = [-20, 130 + generator.uniform(-35, 35), crossX, 500]
        knotsY = [left, 180 - 28 * offset + generator.uniform(-30, 30), crossY, right]
    frequency = generator.uniform(8, 20)
    phase = generator.uniform(0, 2 * math.pi)
    points = [QPointF(x, polynomial(knotsX, knotsY, x)) for x in range(-20, 503, 3)]
    middle = QPainterPath()
    middle.addPolygon(QPolygonF(points))
    hue = int(188 + index * 128 / (count - 1))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for width, alpha in halos:
        glow = QPen(light((hue + 45) % 360, 200, alpha), width)
        glow.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(glow)
        painter.drawPath(middle)
    upper = []
    lower = []
    for k in range(len(points)):
        share = k / (len(points) - 1)
        half = 0.15 + 1.2 * (0.5 + 0.5 * math.sin(share * frequency + phase)) ** 2
        direction = points[min(k + 1, len(points) - 1)] - points[max(k - 1, 0)]
        length = math.hypot(direction.x(), direction.y())
        normal = QPointF(-direction.y(), direction.x()) * (half / length)
        upper.append(points[k] + normal)
        lower.insert(0, points[k] - normal)
    core = QPainterPath()
    core.addPolygon(QPolygonF(upper + lower))
    core.closeSubpath()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(light(hue, 70, 255))
    painter.drawPath(core)
'''),
]


def renderArtwork(artwork: Artwork) -> QImage:
    """L'image d'une œuvre : son programme exécuté sur une image blanche de 480 × 360.

    Raises:
        RuntimeError: Le programme s'est terminé sur une erreur.
    """
    image = QImage(480, 360, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)
    with QPainter(image) as painter:
        report = runDrawingProgram(artwork.code, painter)
    if not report.succeeded():
        raise RuntimeError(f"artwork {artwork.title!r}, line {report.errorLine}: {report.errorMessage}")
    return image


def artworkFingerprint(artwork: Artwork) -> str:
    """L'empreinte sha256 du programme d'une œuvre, en hexadécimal : elle change avec le programme."""
    return hashlib.sha256(artwork.code.encode("utf-8")).hexdigest()


def artworkImage(artwork: Artwork) -> QImage:
    """L'image pré-générée d'une œuvre qui illustre une page, lue dans `assets/images/qpainter/`.

    Raises:
        FileNotFoundError: Le manifeste, son entrée pour cette œuvre, ou son
            image manque.
    """
    entries = json.loads(ManifestPath.read_text(encoding="utf-8"))
    if artwork.title not in entries:
        raise FileNotFoundError(f"{ManifestPath}: no entry for artwork {artwork.title!r}")
    path = ImagesFolder / entries[artwork.title]["file"]
    image = QImage(str(path))
    if image.isNull():
        raise FileNotFoundError(path)
    return image


def artworkOfChapter(chapter: int, *, synthesis: bool = False) -> Artwork:
    """L'œuvre d'un chapitre, numéroté à partir de 1 : celle de son introduction, ou de sa synthèse.

    Raises:
        LookupError: Aucune œuvre pour ce chapitre et cette page.
    """
    for artwork in Artworks:
        if artwork.illustrates and artwork.chapter == chapter and artwork.synthesis == synthesis:
            return artwork
    raise LookupError(f"no artwork for chapter {chapter} (synthesis: {synthesis})")


def introductionArtwork() -> Artwork:
    """L'œuvre de la page « Introduction », la dernière de la liste."""
    return next(artwork for artwork in Artworks if artwork.chapter is None)
