"""Notion 4.2 : découpage et composition.

Contexte : jusqu'ici, chaque forme dessinée recouvre simplement ce qui est
déjà dans l'image. Deux outils changent cette règle. Le découpage limite la
zone où le `QPainter` a le droit de dessiner. Le mode de composition décide
comment chaque nouveau pixel se combine avec celui qui est déjà là : le
recouvrir, passer derrière, l'effacer, l'assombrir...

Étapes couvertes : récapitulatif (un cadre en tirets), un découpage
rectangulaire (`setClipRect`), un découpage de forme quelconque
(`setClipPath`, un trou de serrure), la destination et la source en mode
`SourceOver`, puis cinq autres modes, une case chacun (DestinationOver,
Clear, DestinationOut, Multiply, Screen), et enfin les 24 modes au choix.

Chaque étape est une méthode de `QTopicClippingTab`. Les étapes dessinent
dans la même image, `self.image`. Celles qui changent de sujet repartent
d'une image blanche ou transparente (`fill`).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Slot
from PySide6.QtGui import (
    QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient,
)
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


# Les 24 modes de composition de Qt, dans l'ordre de l'étape « À vous » : les modes déjà vus, puis
# ceux qui décident par les alphas ce qui reste de chacun, puis ceux qui mélangent les couleurs.
_ModeNames = [
    "SourceOver", "DestinationOver", "Clear", "DestinationOut", "Multiply", "Screen",
    "Source", "Destination", "SourceIn", "DestinationIn", "SourceOut", "SourceAtop", "DestinationAtop", "Xor",
    "Plus", "Darken", "Lighten", "Overlay", "HardLight", "SoftLight", "ColorDodge", "ColorBurn",
    "Difference", "Exclusion",
]


class QTopicClippingTab(QWidget):
    """Onglet de la notion 4.2 : limiter la zone de dessin, puis choisir comment les pixels se combinent.

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
        modeCombo: La liste des 24 modes de composition de Qt.
        image: La surface de la notion, ou None avant le récapitulatif.
    """

    TabTitle = "Découpage et composition"
    TabToolTip = "setClipRect, setClipPath et modes de composition (QPainter.CompositionMode)"
    RecommendedPanelWidth = 600
    Objective = (
        "Limiter le dessin à une zone rectangulaire ou de forme quelconque, puis choisir comment "
        "chaque nouvelle forme se combine avec ce que l'image contient déjà : la recouvrir, passer "
        "derrière, l'effacer, l'assombrir ou l'éclaircir."
    )
    KeyConcepts = [
        "Le découpage est un pochoir : tout ce qui tombe hors de la zone est ignoré.",
        "Le découpage dure jusqu'à la fin du peintre, ou jusqu'à <code>setClipping(False)</code> ; "
        "un peintre neuf n'en a aucun.",
        "La destination est ce que l'image contient déjà ; la source est ce qu'on dessine.",
        "Le mode de composition combine source et destination, pixel par pixel, alpha compris. "
        "Les mélanges de couleurs calculent sur les composantes RGB.",
        "Certains modes effacent : le fond devient transparent, et le damier apparaît.",
    ]
    KeyApis = [
        "QPainter.setClipRect", "QPainter.setClipping", "QPainter.setClipPath",
        "QPainter.setCompositionMode",
        "QPainter.CompositionMode",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.controls = QControlPanel()
        self.modeCombo = self.controls.addComboBox(
            "Mode", [(name, getattr(QPainter.CompositionMode, f"CompositionMode_{name}")) for name in _ModeNames])
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
        self.canvas.setViewRect(None)
        self.image = None

    # -- Étapes -------------------------------------------------------------------------------

    def createSurface(self) -> None:
        """Crée la surface blanche de 480 × 360 pixels, et la montre."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setImage(self.image)

    def drawFrame(self) -> None:
        """Trace un cadre gris en tirets : le rectangle (30, 40, 180, 280)."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(99, 110, 114), 1, Qt.PenStyle.DashLine))
            painter.drawRect(30, 40, 180, 280)
        self.canvas.setImage(self.image)

    def drawClippedStripes(self) -> None:
        """Trace des rayures que setClipRect() limite au cadre, puis, sans découpage, une ligne qui déborde."""
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setClipRect(30, 40, 180, 280)
            painter.setPen(QPen(QColor(225, 112, 85), 8))
            for x in range(-360, 480, 24):
                painter.drawLine(x, 0, x + 360, 360)
            painter.setClipping(False)
            painter.setPen(QPen(QColor(9, 132, 227), 4))
            painter.drawLine(0, 340, 240, 340)
        self.canvas.setImage(self.image)

    def drawKeyhole(self) -> None:
        """Peint une porte, puis un paysage que setClipPath() ne laisse voir que par le trou de serrure."""
        hole = QPainterPath()
        hole.addEllipse(QPointF(350, 130), 42, 42)
        trapezoid = QPainterPath()
        trapezoid.moveTo(330, 150)
        trapezoid.lineTo(370, 150)
        trapezoid.lineTo(395, 290)
        trapezoid.lineTo(305, 290)
        trapezoid.closeSubpath()
        keyhole = hole.united(trapezoid)

        sky = QLinearGradient(0, 80, 0, 290)
        sky.setColorAt(0, QColor(116, 185, 255))
        sky.setColorAt(1, QColor(255, 234, 167))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(250, 30, 200, 300, QColor(141, 110, 99))
            painter.setClipPath(keyhole)
            painter.fillRect(0, 0, 480, 360, QBrush(sky))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(253, 203, 110))
            painter.drawEllipse(QPointF(372, 120), 22, 22)
            painter.setBrush(QColor(0, 184, 148))
            painter.drawEllipse(QPointF(320, 320), 130, 80)
        self.canvas.setImage(self.image)

    def drawSourceOver(self) -> None:
        """Repart d'une image transparente ; un carré bleu, puis un disque orange à bord flou par-dessus."""
        self.image.fill(Qt.GlobalColor.transparent)
        orange = QRadialGradient(QPointF(100, 100), 50)
        orange.setColorAt(0.0, QColor(243, 156, 18))
        orange.setColorAt(0.6, QColor(243, 156, 18))
        orange.setColorAt(1.0, QColor(243, 156, 18, 0))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(20, 30, 90, 90, QColor(9, 132, 227))  # la destination
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(orange))
            painter.drawEllipse(QPointF(100, 100), 50, 50)  # la source
            painter.setPen(QPen(QColor(45, 52, 54), 1))
            painter.drawText(10, 170, "SourceOver")
        self.canvas.setImage(self.image)

    def composeInCell(self, left: int, top: int, mode: QPainter.CompositionMode,
                      label: str) -> None:
        """Dans une case de 160 × 180 pixels : le carré bleu, puis le disque orange composé selon mode, et le libellé."""
        orange = QRadialGradient(QPointF(100, 100), 50)
        orange.setColorAt(0.0, QColor(243, 156, 18))
        orange.setColorAt(0.6, QColor(243, 156, 18))
        orange.setColorAt(1.0, QColor(243, 156, 18, 0))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(left, top)
            painter.fillRect(20, 30, 90, 90, QColor(9, 132, 227))  # la destination
            painter.setCompositionMode(mode)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(orange))
            painter.drawEllipse(QPointF(100, 100), 50, 50)  # la source
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(45, 52, 54), 1))
            painter.drawText(10, 170, label)
        self.canvas.setImage(self.image)

    def drawDestinationOver(self) -> None:
        """Compose la deuxième case en mode DestinationOver."""
        self.composeInCell(160, 0, QPainter.CompositionMode.CompositionMode_DestinationOver,
                           "DestinationOver")

    def drawClear(self) -> None:
        """Compose la troisième case en mode Clear."""
        self.composeInCell(320, 0, QPainter.CompositionMode.CompositionMode_Clear, "Clear")

    def drawDestinationOut(self) -> None:
        """Compose la quatrième case en mode DestinationOut."""
        self.composeInCell(0, 180, QPainter.CompositionMode.CompositionMode_DestinationOut,
                           "DestinationOut")

    def drawMultiply(self) -> None:
        """Compose la cinquième case en mode Multiply."""
        self.composeInCell(160, 180, QPainter.CompositionMode.CompositionMode_Multiply,
                           "Multiply")

    def drawScreen(self) -> None:
        """Compose la sixième case en mode Screen."""
        self.composeInCell(320, 180, QPainter.CompositionMode.CompositionMode_Screen, "Screen")

    def connectControls(self) -> None:
        """Relie la liste déroulante au slot qui redessine."""
        self.modeCombo.currentIndexChanged.connect(self.redrawModeTest)

    @Slot()
    def redrawModeTest(self) -> None:
        """Repart d'une image transparente, puis dessine l'essai avec le mode choisi."""
        self.image.fill(Qt.GlobalColor.transparent)
        self.drawModeTest(self.modeCombo.currentData(), self.modeCombo.currentText())

    def drawModeTest(self, mode: QPainter.CompositionMode, label: str) -> None:
        """Dessine une destination variée, puis un grand disque à bord flou composé selon mode."""
        rainbow = QLinearGradient(QPointF(20, 0), QPointF(460, 0))
        for index in range(7):
            rainbow.setColorAt(index / 6, QColor.fromHsv(index * 60 % 360, 230, 240))
        disc = QRadialGradient(QPointF(240, 180), 140)
        disc.setColorAt(0.0, QColor(243, 156, 18))
        disc.setColorAt(0.7, QColor(243, 156, 18))
        disc.setColorAt(1.0, QColor(243, 156, 18, 0))
        with QPainter(self.image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(20, 40, 440, 110, QBrush(rainbow))  # la destination : des teintes,
            painter.fillRect(20, 190, 140, 110, QColor(0, 0, 0))  # du noir,
            painter.fillRect(170, 190, 140, 110, QColor(128, 128, 128))  # du gris
            painter.fillRect(320, 190, 140, 110, QColor(255, 255, 255))  # et du blanc
            painter.setCompositionMode(mode)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(disc))
            painter.drawEllipse(QPointF(240, 180), 140, 140)  # la source
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(45, 52, 54), 1))
            painter.drawText(20, 345, label)
        self.canvas.setImage(self.image)

    def _exploreModes(self) -> None:
        """Connecte la liste, la révèle, puis dessine avec le premier mode."""
        self.connectControls()
        self.controls.reveal()
        self.redrawModeTest()

    def _recap(self) -> None:
        """Crée la surface, puis trace le cadre du récapitulatif."""
        self.createSurface()
        self.drawFrame()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        mode = qtDocUrl("QtGui", "QPainter", "CompositionMode")
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : un cadre en tirets",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée l'image blanche (notion "
                    "1.1). Un stylo gris à tirets (notion 2.1) trace un rectangle (notion "
                    "1.2)."
                    "<br><br>Ce cadre marque la zone de l'étape suivante : le seul endroit où le "
                    "peintre aura le droit de dessiner."
                ),
                run=self._recap,
                codeSource=(self.createSurface, self.drawFrame),
                references=[("QPainter.drawRect", qtDocUrl("QtGui", "QPainter", "drawRect"))],
            ),
            QStepWalkthrough.Step(
                title="Un découpage rectangulaire : setClipRect()",
                explanation=(
                    "<code>setClipRect(x, y, largeur, hauteur)</code> reçoit le rectangle du "
                    "cadre. Ensuite, le peintre ne dessine plus qu'à l'intérieur. Les rayures "
                    "traversent pourtant toute l'image : tout ce qui tombe hors du cadre est "
                    "simplement ignoré, comme avec un pochoir."
                    "<br><br>Le découpage dure jusqu'à la fin du bloc <code>with</code>, ou "
                    "jusqu'à <code>setClipping(False)</code>, qui le désactive tout de suite. La "
                    "ligne bleue du bas, tracée après, déborde du cadre : plus rien ne la limite. "
                    "Un peintre neuf n'a aucun découpage : l'étape suivante le montre."
                ),
                run=self.drawClippedStripes,
                references=[
                    ("QPainter.setClipRect", qtDocUrl("QtGui", "QPainter", "setClipRect")),
                    ("QPainter.setClipping", qtDocUrl("QtGui", "QPainter", "setClipping")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Une zone de forme quelconque : setClipPath()",
                explanation=(
                    "<code>setClipPath(chemin)</code> limite le dessin à l'intérieur d'un "
                    "chemin : une zone de forme quelconque. Ici, un trou de serrure : un disque "
                    "et un trapèze, réunis par "
                    "<code>united()</code> (notion 4.1). Simplement ajoutées au même chemin, les "
                    "deux formes laisseraient un trou dans leur zone commune (règle "
                    "<code>OddEvenFill</code>, notion 4.1)."
                    "<br><br>Ce peintre est neuf : il peint d'abord la porte brune, sans "
                    "découpage, et elle n'est pas coupée par le cadre de l'étape précédente. "
                    "Après <code>setClipPath(chemin)</code>, le ciel en dégradé (notion 2.4), le "
                    "soleil et la colline couvrent pourtant toute l'image : on ne les voit qu'à "
                    "travers la serrure. <code>QLinearGradient(0, 80, 0, 290)</code> reçoit ses "
                    "deux points en quatre nombres, x1, y1, x2, y2, au lieu de deux "
                    "<code>QPointF</code>."
                ),
                run=self.drawKeyhole,
                references=[
                    ("QPainter.setClipPath", qtDocUrl("QtGui", "QPainter", "setClipPath")),
                    ("QPainterPath.united", qtDocUrl("QtGui", "QPainterPath", "united")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Destination, source et SourceOver",
                explanation=(
                    "Chaque forme dessinée, la <b>source</b>, se combine avec ce que l'image "
                    "contient déjà, la <b>destination</b>. "
                    "<code>setCompositionMode(mode)</code> choisit comment, pixel par pixel."
                    "<br><br>L'image repart entièrement transparente (notion 2.3) : le damier du "
                    "canevas la montre. Ici, un carré bleu est dessiné d'abord : c'est la "
                    "destination. Puis un disque orange : c'est la source. Son bord est flou : "
                    "le dégradé radial (notion 2.4) est opaque au centre et transparent au bord."
                    "<br><br>Le mode est une constante de "
                    "<code>QPainter.CompositionMode</code>. <code>SourceOver</code>, le mode par "
                    "défaut, pose la source par-dessus en respectant son alpha : c'est ce qu'on a "
                    "toujours fait jusqu'ici. Le texte « SourceOver » nomme le mode. Dans le code, "
                    "chaque mode porte le préfixe <code>CompositionMode_</code>, comme "
                    "<code>CompositionMode_SourceOver</code> ; le texte l'omet."
                ),
                run=self.drawSourceOver,
                references=[
                    ("QPainter.setCompositionMode",
                     qtDocUrl("QtGui", "QPainter", "setCompositionMode")),
                    ("QPainter.CompositionMode", mode),
                ],
            ),
            QStepWalkthrough.Step(
                title="DestinationOver : dessiner derrière",
                explanation=(
                    "<code>DestinationOver</code> inverse les rôles : ce qui est déjà dessiné "
                    "reste devant. Le disque, dessiné après le carré, passe derrière lui. Il "
                    "n'apparaît que là où l'image était transparente. Utile pour ajouter un fond "
                    "après coup."
                    "<br><br><i>Pour l'exemple</i> : les cinq modes suivants se comparent côte à "
                    "côte, une case de 160 × 180 pixels chacun. "
                    "<code>composeInCell(gauche, haut, mode, libellé)</code> répète le dessin de "
                    "l'étape précédente dans une case, placée par <code>translate()</code> "
                    "(notion 3.2). Le dégradé suit ce repère déplacé, comme toute coordonnée du "
                    "peintre (notion 2.4) : son centre, (100, 100), est celui de la case. Elle "
                    "reçoit le mode et le texte à écrire, et ne rend rien. Le texte est écrit en "
                    "<code>SourceOver</code>, pour rester lisible."
                ),
                run=self.drawDestinationOver,
                codeSource=(self.composeInCell, self.drawDestinationOver),
                references=[("QPainter.CompositionMode", mode)],
            ),
            QStepWalkthrough.Step(
                title="Clear : effacer",
                explanation=(
                    "<code>Clear</code> rend transparent chaque pixel couvert par la forme. La "
                    "couleur du pinceau ne compte pas, ni son alpha. Le bord flou du disque ne "
                    "compte donc pas : le trou a un bord net, et le damier apparaît. Même un "
                    "pinceau entièrement transparent efface. Avec "
                    "<code>Qt.BrushStyle.NoBrush</code> (notion 2.2), en revanche, rien n'est "
                    "rempli, donc rien n'est effacé."
                ),
                run=self.drawClear,
                references=[("QPainter.CompositionMode", mode)],
            ),
            QStepWalkthrough.Step(
                title="DestinationOut : percer selon l'alpha",
                explanation=(
                    "<code>DestinationOut</code> retire de la destination l'alpha de la source. "
                    "Là où le disque est opaque, le carré disparaît complètement. Sur son bord "
                    "flou, le carré ne devient que partiellement transparent : le trou a un bord "
                    "doux, contrairement à <code>Clear</code>. La couleur de la source, elle, ne "
                    "compte pas. C'est le mode d'une gomme à bord doux."
                ),
                run=self.drawDestinationOut,
                references=[("QPainter.CompositionMode", mode)],
            ),
            QStepWalkthrough.Step(
                title="Multiply : assombrir",
                explanation=(
                    "<code>Multiply</code> multiplie les composantes des deux couleurs, ramenées "
                    "entre 0 et 1. Le calcul porte sur les composantes <b>RGB</b> (notion 2.3), "
                    "chacune à part : rouge par rouge, vert par vert, bleu par bleu. Jamais sur la "
                    "teinte ni sur la luminosité. Multiplier par 1, le blanc, ne change rien. "
                    "Multiplier par 0, le noir, donne du noir. Entre les deux, le résultat est "
                    "toujours plus sombre que chacune des couleurs. Orange (243, 156, 18) sur bleu "
                    "(9, 132, 227) : 243 × 9 / 255 ≈ 9, 156 × 132 / 255 ≈ 81, "
                    "18 × 227 / 255 ≈ 16. Le résultat, (9, 81, 16), est un vert très foncé."
                    "<br><br>Sur la partie transparente de l'image, il n'y a rien à multiplier : "
                    "la source apparaît telle quelle."
                ),
                run=self.drawMultiply,
                references=[("QPainter.CompositionMode", mode)],
            ),
            QStepWalkthrough.Step(
                title="Screen : éclaircir",
                explanation=(
                    "<code>Screen</code> fait l'inverse, lui aussi sur les composantes RGB, "
                    "chacune à part. Il multiplie les compléments des couleurs, 1 moins chaque "
                    "composante, puis prend le complément du résultat. Le noir ne change rien, le "
                    "blanc donne du blanc. Le mélange est toujours plus clair que chacune des "
                    "deux couleurs : orange sur bleu donne (243, 207, 229), un rose pâle. Comme "
                    "deux projecteurs braqués sur le même écran."
                ),
                run=self.drawScreen,
                references=[("QPainter.CompositionMode", mode)],
            ),
            QStepWalkthrough.Step(
                title="À vous : les 24 modes de composition",
                explanation=(
                    "La liste déroulante <code>modeCombo</code> paraît sous le canevas. Elle "
                    "propose les 24 modes de <code>QPainter.CompositionMode</code>, en trois "
                    "familles :"
                    "<ul>"
                    "<li>les six modes déjà vus, de <code>SourceOver</code> à "
                    "<code>Screen</code> ;</li>"
                    "<li>huit modes qui ne mélangent pas les couleurs : selon les alphas, ils "
                    "décident ce qui reste de la source et de la destination. Par exemple, "
                    "<code>SourceIn</code> ne garde le disque que là où la destination existe, "
                    "<code>SourceOut</code> que là où elle n'existe pas, et <code>Xor</code> "
                    "garde chacun là où l'autre est absent ;</li>"
                    "<li>dix modes qui mélangent les couleurs, composante RGB par composante RGB : "
                    "<code>Plus</code> les additionne, <code>Darken</code> et "
                    "<code>Lighten</code> gardent la plus sombre ou la plus claire, "
                    "<code>Difference</code> soustrait la plus petite de la plus grande… La "
                    "<a href=\"" + mode + "\">liste des modes de la documentation</a> donne la "
                    "règle de chacun.</li></ul>"
                    "La documentation liste aussi des modes <code>RasterOp_…</code> : des "
                    "opérations logiques sur les bits des pixels (et, ou…), sans rapport avec "
                    "l'alpha. Ils sortent du sujet de cette notion, et la liste ne les reprend "
                    "pas."
                    "<br><br>La destination est variée pour que chaque mode montre ce qu'il fait : des "
                    "teintes en haut, du noir, du gris et du blanc en bas, et du transparent "
                    "entre les deux, où paraît le damier. La source est un grand disque orange, "
                    "opaque au centre, à bord flou. Dans tous les modes, seuls les pixels couverts "
                    "par le disque changent."
                    "<br><br><code>currentData()</code> rend la constante du mode, "
                    "<code>currentText()</code> son nom. <code>connectControls()</code> relie la "
                    "liste au slot <code>redrawModeTest()</code>. Il repart d'une image "
                    "transparente, puis appelle <code>drawModeTest()</code>. Celle-ci dessine la "
                    "destination en <code>SourceOver</code>, puis le disque dans le mode choisi, "
                    "et écrit le nom du mode en bas."
                    "<br><br>Comparer <code>Multiply</code> et <code>Screen</code> sur le noir et "
                    "sur le blanc, puis <code>Difference</code> sur les teintes."
                ),
                run=self._exploreModes,
                codeSource=(self.connectControls, self.redrawModeTest, self.drawModeTest),
                references=[
                    ("QPainter.CompositionMode", mode),
                    ("QComboBox.currentText", qtDocUrl("QtWidgets", "QComboBox", "currentText")),
                ],
            ),
        ]
