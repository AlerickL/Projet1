"""Notion 2.4 : dégradés.

Contexte : un pinceau peut porter un dégradé plutôt qu'une couleur unie. Qt
en propose trois : linéaire (entre deux points), radial (autour d'un
centre) et conique (autour d'un centre, selon l'angle). Leurs couleurs se
placent sur des points d'arrêt, entre 0 et 1.

Étapes couvertes : le récapitulatif de la surface, un dégradé linéaire, ses
coordonnées fixées dans l'image, des coordonnées relatives à la forme,
plusieurs points d'arrêt,
le dégradé radial, son point focal, le dégradé conique, l'étalement au-delà
des extrémités, la distance et l'angle de deux points (`QLineF`, vu en 1.2),
puis un constructeur de dégradés : type, étalement, deux points, et des
points d'arrêt qu'on ajoute, retire, place et colore ; le code du dégradé
obtenu s'écrit sous les contrôles.

Chaque étape est une méthode de `QTopicGradientsTab`. Les étapes dessinent
dans la même image, `self.image`. Celles qui comparent repartent d'une image
blanche (`fill`).
"""

from __future__ import annotations

from PySide6.QtCore import SIGNAL, QLineF, QPointF, Qt, Slot
from PySide6.QtGui import (
    QBrush, QColor, QConicalGradient, QGradient, QImage, QLinearGradient, QPainter, QPen, QRadialGradient,
)
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas
from .q_gradient_code_view import QGradientCodeView
from .q_gradient_stops_editor import QGradientStopsEditor

# Les points d'arrêt du constructeur de dégradé à son apparition : bleu, jaune, rouge.
_BuilderStartStops = [(0.0, QColor("#2e86de")), (0.5, QColor("#f6d365")), (1.0, QColor("#e74c3c"))]


class QTopicGradientsTab(QWidget):
    """Onglet de la notion 2.4 : dégradés linéaire, radial et conique, points d'arrêt, étalement.

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
        kindCombo, spreadCombo, startSlider, endSlider: Type de dégradé,
            étalement, et position horizontale de ses deux points.
        stopsEditor: L'éditeur des points d'arrêt du constructeur (outil
            présenté à l'étape « À vous »).
        gradientCode: Le code du dégradé construit (outil d'observation
            présenté à l'étape « À vous »).
        image: La surface de la notion, ou None avant la première étape.
    """

    TabTitle = "Dégradés"
    TabToolTip = "QLinearGradient, QRadialGradient, QConicalGradient : points d'arrêt et étalement"
    RecommendedPanelWidth = 600
    Objective = (
        "Remplir une forme d'un dégradé linéaire, radial ou conique, placer ses couleurs avec des "
        "points d'arrêt, et choisir ce qui se passe au-delà de ses extrémités."
    )
    KeyConcepts = [
        "Un dégradé se pose dans un pinceau, comme une couleur.",
        "Ses couleurs se placent sur des points d'arrêt, de 0 (début) à 1 (fin).",
        "Par défaut, ses coordonnées sont celles de l'image, pas celles de la forme remplie.",
        "Radial : un centre, un rayon, et un point focal d'où la lumière semble venir.",
        "Conique : les couleurs tournent autour d'un centre, à partir d'un angle.",
        "Entre deux points d'arrêt, les couleurs se mélangent en RGB, composante par composante.",
        "L'étalement décide de ce qui se passe au-delà de la fin : prolonger, répéter ou "
        "refléter.",
    ]
    KeyApis = [
        "QLinearGradient", "QRadialGradient", "QConicalGradient", "QGradient.setColorAt",
        "QGradient.setCoordinateMode", "QGradient.setSpread", "QGradient.setStops",
        "QLineF.length", "QLineF.angle",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.kindCombo = self.controls.addComboBox(
            "Type", [("Linéaire", "linear"), ("Radial", "radial"), ("Conique", "conical")])
        self.spreadCombo = self.controls.addComboBox("Étalement", [
            ("Prolonger (PadSpread)", QGradient.Spread.PadSpread),
            ("Répéter (RepeatSpread)", QGradient.Spread.RepeatSpread),
            ("Refléter (ReflectSpread)", QGradient.Spread.ReflectSpread),
        ])
        self.startSlider = self.controls.addSlider("Départ, x", 0, 480, 160, suffix="px")
        self.endSlider = self.controls.addSlider("Arrivée, x", 0, 480, 320, suffix="px")
        self.controls.setMaximumWidth(480)
        self.stopsEditor = QGradientStopsEditor(_BuilderStartStops)
        self.stopsEditor.setMaximumWidth(480)
        self.gradientCode = QGradientCodeView()
        self.gradientCode.setMaximumWidth(480)

        self.walkthrough = QStepWalkthrough(
            self._buildSteps(), self._resetState,
            objective=self.Objective, keyConcepts=self.KeyConcepts, keyApis=self.KeyApis,
        )

        contentColumn = QWidget()
        contentLayout = QVBoxLayout(contentColumn)
        contentLayout.addWidget(self.canvas)
        contentLayout.addWidget(self.readout)
        contentLayout.addWidget(self.controls)
        contentLayout.addWidget(self.stopsEditor)
        contentLayout.addWidget(self.gradientCode)
        contentLayout.addStretch(1)
        createSplitterLayout(self, contentColumn, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Ramène le canevas, la lecture et les contrôles à leur état de départ, avant chaque rejeu."""
        self.controls.resetControls()
        # L'éditeur n'est pas un contrôle du panneau : sa connexion et ses points d'arrêt sont remis ici.
        if self.stopsEditor.receivers(SIGNAL("stopsChanged()")) > 0:
            self.stopsEditor.stopsChanged.disconnect()
        self.stopsEditor.setStops(_BuilderStartStops)
        self.stopsEditor.setVisible(False)
        self.gradientCode.setVisible(False)
        self.readout.clear()
        self.canvas.setImage(QImage())
        self.image = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface blanche de 480 × 360 pixels, et la montre."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setImage(self.image)

    def drawLinearGradient(self) -> None:
        """Remplit un rectangle d'un dégradé linéaire, du jaune au rouge, de x = 40 à x = 440."""
        gradient = QLinearGradient(QPointF(40, 0), QPointF(440, 0))
        gradient.setColorAt(0, QColor("#f6d365"))
        gradient.setColorAt(1, QColor("#e74c3c"))
        with QPainter(self.image) as painter:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRect(40, 20, 400, 120)
        self.canvas.setImage(self.image)

    def drawInImageCoordinates(self) -> None:
        """Remplit quatre disques avec le même dégradé : chacun en reçoit une portion différente."""
        gradient = QLinearGradient(QPointF(40, 0), QPointF(440, 0))
        gradient.setColorAt(0, QColor("#f6d365"))
        gradient.setColorAt(1, QColor("#e74c3c"))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            for index in range(4):
                painter.drawEllipse(45 + index * 105, 165, 80, 80)
        self.canvas.setImage(self.image)

    def drawInShapeCoordinates(self) -> None:
        """Remplit quatre autres disques d'un dégradé relatif à chaque forme : tous identiques."""
        gradient = QLinearGradient(QPointF(0, 0), QPointF(1, 0))
        gradient.setCoordinateMode(QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0, QColor("#f6d365"))
        gradient.setColorAt(1, QColor("#e74c3c"))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            for index in range(4):
                painter.drawEllipse(45 + index * 105, 265, 80, 80)
        self.canvas.setImage(self.image)

    def drawEveningSky(self) -> None:
        """Remplit toute l'image d'un ciel du soir : un dégradé vertical à quatre points d'arrêt."""
        sky = QLinearGradient(QPointF(0, 0), QPointF(0, 360))
        sky.setColorAt(0, QColor("#0b1d51"))
        sky.setColorAt(0.45, QColor("#725ac1"))
        sky.setColorAt(0.75, QColor("#f7797d"))
        sky.setColorAt(1, QColor("#fbd786"))
        with QPainter(self.image) as painter:
            painter.fillRect(0, 0, 480, 360, QBrush(sky))
        self.canvas.setImage(self.image)

    def drawSun(self) -> None:
        """Ajoute un soleil qui rayonne : un dégradé radial, opaque au centre, transparent au bord."""
        sun = QRadialGradient(QPointF(240, 280), 110)
        sun.setColorAt(0, QColor(255, 255, 230))
        sun.setColorAt(0.3, QColor(255, 214, 110))
        sun.setColorAt(1, QColor(255, 180, 90, 0))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(sun))
            painter.drawEllipse(QPointF(240, 280), 110, 110)
        self.canvas.setImage(self.image)

    def drawPlanets(self) -> None:
        """Ajoute deux planètes : sans point focal (à gauche), puis avec un point focal tourné vers le soleil."""
        flat = QRadialGradient(QPointF(90, 80), 50)
        lit = QRadialGradient(QPointF(390, 80), 50, QPointF(375, 100))
        for gradient in (flat, lit):
            gradient.setColorAt(0, QColor("#ffffff"))
            gradient.setColorAt(0.3, QColor("#a9cce3"))
            gradient.setColorAt(1, QColor("#1b4f72"))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(flat))
            painter.drawEllipse(QPointF(90, 80), 50, 50)
            painter.setBrush(QBrush(lit))
            painter.drawEllipse(QPointF(390, 80), 50, 50)
        self.canvas.setImage(self.image)

    def drawHueRing(self) -> None:
        """Repart d'une image blanche ; un anneau de teintes : un dégradé conique autour du centre."""
        self.image.fill(Qt.GlobalColor.white)
        wheel = QConicalGradient(QPointF(240, 180), 0)
        for index in range(7):
            wheel.setColorAt(index / 6, QColor.fromHsv(index * 60 % 360, 220, 255))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(wheel))
            painter.drawEllipse(QPointF(240, 180), 160, 160)
            painter.setBrush(QBrush(QColor("white")))
            painter.drawEllipse(QPointF(240, 180), 80, 80)
        self.canvas.setImage(self.image)

    def drawSpreads(self) -> None:
        """Repart d'une image blanche ; un dégradé court, de x = 190 à x = 290, avec trois étalements."""
        self.image.fill(Qt.GlobalColor.white)
        spreads = [QGradient.Spread.PadSpread, QGradient.Spread.RepeatSpread,
                   QGradient.Spread.ReflectSpread]
        with QPainter(self.image) as painter:
            for index in range(3):
                gradient = QLinearGradient(QPointF(190, 0), QPointF(290, 0))
                gradient.setColorAt(0, QColor("#2e86de"))
                gradient.setColorAt(1, QColor("#f6d365"))
                gradient.setSpread(spreads[index])
                painter.fillRect(20, 30 + index * 110, 440, 80, QBrush(gradient))
            painter.setPen(QPen(QColor("#34495e"), 2, Qt.PenStyle.DashLine))
            painter.drawLine(190, 10, 190, 350)
            painter.drawLine(290, 10, 290, 350)
        self.canvas.setImage(self.image)

    def measureTwoPoints(self) -> None:
        """Repart d'une image blanche ; deux points reliés, et la distance et l'angle que rend QLineF."""
        self.image.fill(Qt.GlobalColor.white)
        start = QPointF(160, 250)
        end = QPointF(320, 110)
        line = QLineF(start, end)
        self.readout.setText(f"line.length() -> {round(line.length(), 1)}\n"
                             f"line.angle() -> {round(line.angle(), 1)}")
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#95a5a6"), 1, Qt.PenStyle.DashLine))
            painter.drawLine(start, QPointF(400, 250))  # 0° : vers trois heures
            painter.setPen(QPen(QColor("#34495e"), 2))
            painter.drawLine(start, end)
            painter.setBrush(QBrush(QColor("#34495e")))
            painter.drawEllipse(start, 7, 7)
            painter.drawEllipse(end, 7, 7)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie les listes déroulantes, les sélecteurs numériques et l'éditeur au slot qui redessine."""
        self.kindCombo.currentIndexChanged.connect(self.redrawGradient)
        self.spreadCombo.currentIndexChanged.connect(self.redrawGradient)
        self.startSlider.valueChanged.connect(self.redrawGradient)
        self.endSlider.valueChanged.connect(self.redrawGradient)
        self.stopsEditor.stopsChanged.connect(self.redrawGradient)

    @Slot()
    def redrawGradient(self) -> None:
        """Lit les contrôles et les points d'arrêt, puis redessine."""
        self.drawChosenGradient(self.kindCombo.currentData(), self.spreadCombo.currentData(),
                                self.startSlider.value(), self.endSlider.value(), self.stopsEditor.stops())

    def drawChosenGradient(self, kind: str, spread: QGradient.Spread, startX: int, endX: int,
                           stops: list[tuple[float, QColor]]) -> None:
        """Vide la lecture, remplit toute l'image du dégradé décrit, marque ses deux points, puis écrit son code."""
        self.readout.clear()
        start = QPointF(startX, 250)
        end = QPointF(endX, 110)
        line = QLineF(start, end)
        if kind == "linear":
            gradient = QLinearGradient(start, end)
        elif kind == "radial":
            gradient = QRadialGradient(start, line.length())
        else:
            gradient = QConicalGradient(start, line.angle())
        gradient.setStops(stops)
        gradient.setSpread(spread)
        with QPainter(self.image) as painter:
            painter.fillRect(0, 0, 480, 360, QBrush(gradient))
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("white"), 2, Qt.PenStyle.DashLine))
            painter.drawLine(start, end)
            painter.setBrush(QBrush(QColor("#34495e")))
            painter.drawEllipse(start, 7, 7)
            painter.drawEllipse(end, 7, 7)
        self.canvas.setImage(self.image)
        self.gradientCode.setGradient(gradient)

    def _exploreGradient(self) -> None:
        """Connecte les contrôles, les révèle, puis dessine le dégradé de départ."""
        self.connectControls()
        self.controls.reveal()
        self.stopsEditor.setVisible(True)
        self.gradientCode.setVisible(True)
        self.redrawGradient()

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
                title="Un dégradé linéaire",
                explanation=(
                    "<code>QLinearGradient(début, fin)</code> fait varier la couleur le long du segment qui "
                    "relie deux points. <code>setColorAt(0, …)</code> fixe la couleur du début, "
                    "<code>setColorAt(1, …)</code> celle de la fin : ce sont des <b>points "
                    "d'arrêt</b>. Le dégradé se pose dans un pinceau, "
                    "<code>QBrush(gradient)</code>, comme une couleur. Sans aucun point d'arrêt, "
                    "il irait du noir au blanc. Les classes de dégradés de cette notion viennent "
                    "toutes de <code>PySide6.QtGui</code>."
                    "<br><br>Ici, le segment est horizontal, sur y = 0, et le rectangle est plus "
                    "bas. La couleur ne change que dans la direction du segment : un point hors "
                    "du segment prend la couleur du point du segment qui a le même x. Le "
                    "rectangle a donc les mêmes couleurs à toute hauteur."
                ),
                run=self.drawLinearGradient,
                references=[
                    ("QLinearGradient", qtDocUrl("QtGui", "QLinearGradient")),
                    ("QBrush", qtDocUrl("QtGui", "QBrush")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Des coordonnées fixées dans l'image",
                explanation=(
                    "Les coordonnées d'un dégradé sont celles du repère du peintre, pas celles "
                    "de la forme remplie. Ici, ce repère est celui de l'image. Même dégradé, de "
                    "x = 40 à x = 440, pour quatre disques. Chacun reçoit la couleur qui se "
                    "trouve à sa place dans l'image : le premier est jaune, le dernier rouge. La "
                    "notion 3.2 montrera qu'on peut déplacer ce repère, et la notion 4.2 y verra "
                    "un dégradé se déplacer avec lui."
                ),
                run=self.drawInImageCoordinates,
                references=[("QLinearGradient", qtDocUrl("QtGui", "QLinearGradient"))],
            ),
            QStepWalkthrough.Step(
                title="Des coordonnées relatives à la forme",
                explanation=(
                    "Les trois sortes de dégradés partagent une classe commune, "
                    "<code>QGradient</code> : <code>QLinearGradient</code>, "
                    "<code>QRadialGradient</code> et <code>QConicalGradient</code>, présentés aux "
                    "étapes 7 et 9, en héritent "
                    "(prérequis « héritage »). Ses méthodes valent donc pour les trois. Elle "
                    "définit leurs réglages, comme "
                    "<code>setColorAt()</code> et <code>setCoordinateMode()</code>. "
                    "<code>QGradient.CoordinateMode.ObjectBoundingMode</code> compte les "
                    "coordonnées du dégradé dans le rectangle englobant de chaque forme : (0, 0) "
                    "en haut à gauche, (1, 1) en bas à droite. Le dégradé va donc de 0 à 1 en x. "
                    "Les quatre disques du bas reçoivent chacun le dégradé complet."
                ),
                run=self.drawInShapeCoordinates,
                references=[
                    ("QGradient", qtDocUrl("QtGui", "QGradient")),
                    ("QGradient.setCoordinateMode", qtDocUrl("QtGui", "QGradient", "setCoordinateMode")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Plusieurs points d'arrêt",
                explanation=(
                    "Un dégradé accepte autant de points d'arrêt qu'on veut, chacun entre 0 et 1. "
                    "Ici, un ciel du soir de haut en bas : bleu nuit, violet, rose, puis jaune "
                    "pâle à l'horizon. Un point hors de 0 à 1 est ignoré en silence. "
                    "<code>fillRect()</code> (notion 2.2) accepte aussi ce pinceau : le ciel "
                    "couvre toute l'image."
                    "<br><br>Entre deux points d'arrêt, Qt mélange les deux couleurs en RGB "
                    "(notion 2.3), composante par composante : à mi-chemin, chaque composante "
                    "vaut la moyenne des deux. Ce mélange ne passe pas par la roue des teintes. "
                    "Entre deux couleurs opposées sur la roue, comme le rouge (255, 0, 0) et le "
                    "cyan (0, 255, 255), le milieu est un gris (128, 128, 128). Pour garder un "
                    "passage vif, on ajoute un point d'arrêt intermédiaire, comme le violet et le "
                    "rose de ce ciel."
                ),
                run=self.drawEveningSky,
                references=[("QGradient.setColorAt", qtDocUrl("QtGui", "QGradient", "setColorAt"))],
            ),
            QStepWalkthrough.Step(
                title="Un dégradé radial",
                explanation=(
                    "<code>QRadialGradient(centre, rayon)</code> fait varier la couleur du centre "
                    "(0) jusqu'au cercle du rayon (1). Le dernier point d'arrêt a un alpha de 0 "
                    "(notion 2.3) : le soleil se fond dans le ciel, sans bord net. Le disque est "
                    "dessiné par son centre et ses rayons (notion 1.2)."
                ),
                run=self.drawSun,
                references=[("QRadialGradient", qtDocUrl("QtGui", "QRadialGradient"))],
            ),
            QStepWalkthrough.Step(
                title="Le point focal",
                explanation=(
                    "Un troisième argument, le point focal, déplace l'origine des couleurs sans "
                    "déplacer le cercle. À gauche, sans point focal : la couleur 0 est au centre. "
                    "À droite, le point focal, <code>QPointF(375, 100)</code>, est 25 pixels plus "
                    "près du soleil, en bas à gauche de la planète : sa face tournée vers le "
                    "soleil paraît éclairée. Un point focal hors du cercle est ramené sur son "
                    "bord."
                ),
                run=self.drawPlanets,
                references=[
                    ("QRadialGradient", qtDocUrl("QtGui", "QRadialGradient")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Un dégradé conique",
                explanation=(
                    "<code>QConicalGradient(centre, angle)</code> fait tourner les couleurs autour "
                    "du centre, de 0 à 1 sur un tour complet. L'angle de départ suit la "
                    "convention de <code>drawPie()</code> : 0 à trois heures, en sens inverse des "
                    "aiguilles d'une montre. Sept points d'arrêt en HSV (notion 2.3) donnent une "
                    "roue de teintes continue : aux positions 0, 1/6, …, 1, les teintes 0, 60, …, "
                    "300, puis 360. <code>% 360</code> ramène 360 à 0 : le septième point revient "
                    "au rouge du premier, et la roue se ferme sans cassure. Un disque blanc la "
                    "creuse en anneau."
                ),
                run=self.drawHueRing,
                references=[("QConicalGradient", qtDocUrl("QtGui", "QConicalGradient"))],
            ),
            QStepWalkthrough.Step(
                title="L'étalement, au-delà des extrémités",
                explanation=(
                    "Au-delà des extrémités d'un dégradé, <code>setSpread()</code> décide de la "
                    "couleur, avec une constante de <code>QGradient.Spread</code>. Ici, le "
                    "dégradé ne couvre que x = 190 à 290 (lignes en tirets). De haut en bas :"
                    "<ul>"
                    "<li><code>PadSpread</code>, le défaut, prolonge la couleur de chaque "
                    "extrémité ;</li>"
                    "<li><code>RepeatSpread</code> répète le dégradé ;</li>"
                    "<li><code>ReflectSpread</code> le répète en miroir, sans cassure.</li></ul>"
                    "Un dégradé conique ignore l'étalement."
                ),
                run=self.drawSpreads,
                references=[
                    ("QGradient.setSpread", qtDocUrl("QtGui", "QGradient", "setSpread")),
                    ("QGradient.Spread", qtDocUrl("QtGui", "QGradient", "Spread")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Distance et angle de deux points",
                explanation=(
                    "Deux mesures, dont l'étape « À vous » aura besoin : le rayon d'un dégradé "
                    "radial et l'orientation d'un dégradé conique se tirent de deux points. "
                    "Le segment <code>QLineF</code> (notion 1.2) sait aussi se mesurer. "
                    "<code>length()</code> rend sa longueur, en pixels. <code>angle()</code> rend "
                    "sa direction, en degrés, dans la convention du dégradé conique : 0 vers "
                    "trois heures (ligne en tirets), sens inverse des aiguilles d'une montre. "
                    "<code>round()</code> arrondit les deux mesures au dixième."
                    "<br><br>Ici, le second point est 160 pixels à droite et 140 plus haut : une "
                    "longueur d'environ 212,6 et un angle d'environ 41,2°. L'étape suivante "
                    "emploie ces deux mesures."
                ),
                run=self.measureTwoPoints,
                references=[
                    ("QLineF.length", qtDocUrl("QtCore", "QLineF", "length")),
                    ("QLineF.angle", qtDocUrl("QtCore", "QLineF", "angle")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : le constructeur de dégradés",
                explanation=(
                    "Un constructeur de dégradés paraît sous le canevas. Il montre ce que "
                    "permettent les dégradés, et sert aussi d'outil : le code du dégradé obtenu "
                    "se copie dans un programme hors de ce guide."
                    "<ul>"
                    "<li>La liste <code>kindCombo</code> choisit le type : chaque choix porte une "
                    "chaîne, <code>\"linear\"</code>, <code>\"radial\"</code> ou "
                    "<code>\"conical\"</code>. Elle part de « Linéaire ».</li>"
                    "<li>La liste <code>spreadCombo</code> choisit l'étalement : chaque choix "
                    "porte sa constante de <code>QGradient.Spread</code>. Elle part de "
                    "<code>PadSpread</code>.</li>"
                    "<li>Deux sélecteurs numériques, <code>startSlider</code> et "
                    "<code>endSlider</code>, placent en x le point de départ (en bas) et le point "
                    "d'arrivée (en haut), de 0 à 480 pixels. Ils partent de 160 et de 320.</li>"
                    "<li>L'éditeur des points d'arrêt, <code>stopsEditor</code>, est un outil de "
                    "ce guide. Chaque rangée règle un point d'arrêt : sa couleur, par un clic sur son "
                    "bouton, et sa position, affichée de 0 à 100 %. Au départ, trois points : "
                    "bleu à 0 %, jaune à 50 %, rouge à 100 %. « Ajouter un point d'arrêt » en "
                    "ajoute un au milieu du plus grand écart, « Retirer » en retire un. Sa "
                    "méthode <code>stops()</code> rend les points triés, sous la forme d'une "
                    "liste de paires (position, couleur), la position de 0 à 1, comme pour "
                    "<code>setColorAt()</code>. Son signal "
                    "<code>stopsChanged</code> est émis à chaque changement.</li></ul>"
                    "<code>drawChosenGradient()</code> construit le dégradé. Linéaire : du "
                    "départ à l'arrivée. Radial : centré sur le départ, de rayon la distance "
                    "entre les deux points. Conique : centré sur le départ, orienté vers "
                    "l'arrivée. Nouveau : <code>setStops(stops)</code> pose d'un coup toute la liste des "
                    "points d'arrêt, dans la forme que rend l'éditeur : c'est l'équivalent d'un "
                    "<code>setColorAt()</code> par point."
                    "<br><br>Sous l'éditeur, <code>self.gradientCode</code>, un autre outil de "
                    "ce guide, reçoit le dégradé par <code>setGradient(gradient)</code>. Il écrit "
                    "le code Python qui le recrée, non modifiable, avec un bouton pour le copier."
                    "<br><br>Ajouter un point d'arrêt, le rendre cyan, "
                    "puis le rapprocher d'une extrémité. Essayer chaque étalement avec le départ "
                    "et l'arrivée rapprochés."
                ),
                run=self._exploreGradient,
                codeSource=(self.connectControls, self.redrawGradient, self.drawChosenGradient),
                references=[
                    ("QGradient.setStops", qtDocUrl("QtGui", "QGradient", "setStops")),
                    ("QGradient.Spread", qtDocUrl("QtGui", "QGradient", "Spread")),
                    ("QLineF.angle", qtDocUrl("QtCore", "QLineF", "angle")),
                ],
            ),
        ]
