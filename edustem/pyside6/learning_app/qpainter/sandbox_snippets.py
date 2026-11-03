"""Les fragments de code de l'atelier de dessin (notion 5.2).

Chaque fragment est un court extrait, prêt à insérer dans l'éditeur puis à
adapter : un geste vu dans une notion du cours, avec des valeurs lisibles
sur le canevas de 480 × 360. Les fragments sont regroupés par notion, dans
l'ordre du cours.

Chaque fragment s'exécute seul, sans erreur, avec les noms fournis par
`drawing_sandbox.ProvidedNames` : c'est vérifié par
`learning_app/tests/test_drawing_sandbox.py`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Snippet:
    """Un fragment : son titre dans le menu, et son code."""

    title: str
    code: str


# (titre du groupe, fragments), dans l'ordre du cours.
SnippetGroups: list[tuple[str, list[Snippet]]] = [
    ("1.2 Formes de base", [
        Snippet("Ligne", "painter.drawLine(40, 40, 200, 120)"),
        Snippet("Rectangle", "painter.drawRect(40, 40, 160, 100)"),
        Snippet("Rectangle arrondi", "painter.drawRoundedRect(40, 40, 160, 100, 16, 16)"),
        Snippet("Ellipse (centre et rayons)", "painter.drawEllipse(QPointF(240, 180), 80, 50)"),
        Snippet("Arc (angles en 16es de degré)",
                "painter.drawArc(QRectF(160, 100, 160, 160), 30 * 16, 120 * 16)"),
        Snippet("Part de tarte", "painter.drawPie(QRectF(160, 100, 160, 160), 30 * 16, 120 * 16)"),
        Snippet("Polygone", "painter.drawPolygon([QPointF(240, 60), QPointF(340, 240), QPointF(140, 240)])"),
        Snippet("Points",
                "points = []\n"
                "for index in range(15):\n"
                "    points.append(QPointF(100 + 20 * index, 180))\n"
                "painter.drawPoints(points)"),
    ]),
    ("1.3 Qualité du trait", [
        Snippet("Anticrénelage", "painter.setRenderHint(QPainter.RenderHint.Antialiasing)"),
    ]),
    ("2.1 Le stylo", [
        Snippet("Stylo : couleur et épaisseur", 'painter.setPen(QPen(QColor("#2b2d42"), 4))'),
        Snippet("Stylo à tirets", 'painter.setPen(QPen(QColor("#2b2d42"), 2, Qt.PenStyle.DashLine))'),
        Snippet("Extrémités et jonctions arrondies",
                'pen = QPen(QColor("#2b2d42"), 12)\n'
                "pen.setCapStyle(Qt.PenCapStyle.RoundCap)\n"
                "pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)\n"
                "painter.setPen(pen)"),
        Snippet("Sans contour", "painter.setPen(Qt.PenStyle.NoPen)"),
    ]),
    ("2.2 Le pinceau", [
        Snippet("Pinceau : couleur pleine", 'painter.setBrush(QColor("#8ecae6"))'),
        Snippet("Pinceau à motif", 'painter.setBrush(QBrush(QColor("#219ebc"), Qt.BrushStyle.DiagCrossPattern))'),
        Snippet("Sans remplissage", "painter.setBrush(Qt.BrushStyle.NoBrush)"),
        Snippet("Remplir tout le fond", 'painter.fillRect(0, 0, 480, 360, QColor("#fdf6e3"))'),
    ]),
    ("2.3 Couleurs et transparence", [
        Snippet("Couleur RGB translucide", "color = QColor(230, 57, 70, 128)  # rouge, vert, bleu, alpha"),
        Snippet("Couleur HSV", "color = QColor.fromHsv(200, 180, 230)  # teinte, saturation, valeur"),
        Snippet("Nuances d'une couleur",
                'color = QColor("#219ebc")\n'
                "light = color.lighter(150)\n"
                "dark = color.darker(150)"),
    ]),
    ("2.4 Dégradés", [
        Snippet("Dégradé linéaire",
                "gradient = QLinearGradient(QPointF(0, 0), QPointF(0, 360))\n"
                'gradient.setColorAt(0, QColor("#8ecae6"))\n'
                'gradient.setColorAt(1, QColor("#023047"))\n'
                "painter.fillRect(0, 0, 480, 360, QBrush(gradient))"),
        Snippet("Dégradé radial",
                "gradient = QRadialGradient(QPointF(240, 180), 100)\n"
                'gradient.setColorAt(0, QColor("#ffb703"))\n'
                'gradient.setColorAt(1, QColor("#fb8500"))\n'
                "painter.setBrush(QBrush(gradient))\n"
                "painter.drawEllipse(QPointF(240, 180), 100, 100)"),
        Snippet("Dégradé conique",
                "gradient = QConicalGradient(QPointF(240, 180), 0)\n"
                "for i in range(7):\n"
                "    gradient.setColorAt(i / 6, QColor.fromHsv(i * 60 % 360, 200, 240))\n"
                "painter.setBrush(QBrush(gradient))\n"
                "painter.drawEllipse(QPointF(240, 180), 100, 100)"),
    ]),
    ("3.1 Le texte", [
        Snippet("Texte (y : ligne de base)",
                'painter.setFont(QFont("Arial", 20))\n'
                'painter.drawText(40, 60, "Bonjour")'),
        Snippet("Texte centré dans un rectangle",
                'painter.setFont(QFont("Arial", 20))\n'
                'painter.drawText(QRectF(0, 0, 480, 360), Qt.AlignmentFlag.AlignCenter, "Au centre")'),
        Snippet("Mesurer un texte",
                'painter.setFont(QFont("Arial", 20))\n'
                "metrics = painter.fontMetrics()\n"
                'print("largeur :", metrics.horizontalAdvance("Bonjour"))\n'
                'print("hauteur :", metrics.ascent() + metrics.descent())'),
    ]),
    ("3.2 Transformations", [
        Snippet("Déplacer, tourner, isoler",
                "painter.save()\n"
                "painter.translate(240, 180)\n"
                "painter.rotate(30)\n"
                "painter.drawRect(-50, -30, 100, 60)\n"
                "painter.restore()"),
        Snippet("Une rosace (boucle de rotations)",
                "painter.translate(240, 180)\n"
                "for index in range(12):\n"
                "    painter.drawEllipse(QRect(10, -16, 150, 32))\n"
                "    painter.rotate(30)"),
        Snippet("Mise à l'échelle", "painter.scale(1.5, 1.5)"),
    ]),
    ("4.1 Chemins", [
        Snippet("Chemin de droites et de courbe",
                "path = QPainterPath()\n"
                "path.moveTo(60, 280)\n"
                "path.lineTo(160, 120)\n"
                "path.cubicTo(QPointF(220, 40), QPointF(320, 200), QPointF(420, 100))\n"
                "path.lineTo(420, 280)\n"
                "path.closeSubpath()\n"
                "painter.drawPath(path)"),
        Snippet("Opération entre chemins",
                "disk = QPainterPath()\n"
                "disk.addEllipse(QPointF(220, 180), 100, 100)\n"
                "hole = QPainterPath()\n"
                "hole.addEllipse(QPointF(270, 150), 70, 70)\n"
                "painter.drawPath(disk.subtracted(hole))"),
    ]),
    ("4.2 Découpage et composition", [
        Snippet("Découper par un rectangle", "painter.setClipRect(100, 80, 280, 200)"),
        Snippet("Découper par un chemin",
                "clip = QPainterPath()\n"
                "clip.addEllipse(QPointF(240, 180), 120, 120)\n"
                "painter.setClipPath(clip)"),
        Snippet("Mode de composition : multiplier",
                "painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)"),
    ]),
    ("4.3 Images", [
        Snippet("Dessiner dans une image à part",
                "tile = QImage(60, 60, QImage.Format.Format_ARGB32)\n"
                "tile.fill(Qt.GlobalColor.transparent)\n"
                "with QPainter(tile) as tilePainter:\n"
                '    tilePainter.setBrush(QColor("#e76f51"))\n'
                "    tilePainter.drawEllipse(10, 10, 40, 40)\n"
                "painter.drawImage(40, 40, tile)"),
        Snippet("Opacité", "painter.setOpacity(0.5)"),
    ]),
    ("Python", [
        Snippet("Boucle sur une grille",
                "for row in range(6):\n"
                "    for column in range(8):\n"
                "        painter.drawRect(20 + column * 55, 20 + row * 55, 40, 40)"),
        Snippet("Hasard reproductible",
                "generator = random.Random(1)  # graine fixe : le même dessin à chaque fois\n"
                "x = generator.uniform(0, 480)"),
        Snippet("Point sur un cercle",
                "angle = math.radians(45)\n"
                "point = QPointF(240 + 100 * math.cos(angle), 180 - 100 * math.sin(angle))"),
    ]),
]
