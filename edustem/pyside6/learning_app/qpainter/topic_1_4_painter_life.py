"""Notion 1.4 : la vie du peintre.

Contexte : les notions 1.1 à 1.3 ont toujours dessiné dans un bloc `with`.
Celle-ci montre ce qui se passe hors de ce cadre : un peintre terminé, deux
peintres sur une même image, et l'écriture explicite avec `end()`, qu'on
croise dans bien des exemples.

Étapes couvertes : récapitulatif (une surface, un trait), un trait demandé
après le bloc, un second peintre refusé, les deux écritures (`end()`
explicite ou bloc `with`). Une case à cocher déplace ensuite l'appel
`end()` dans un code écrit sans bloc `with`.

Chaque étape est une méthode de `QTopicPainterLifeTab`. Les étapes
dessinent dans la même image, `self.image`, et la redonnent au canevas à la
fin.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_canvas import QDrawingCanvas


class QTopicPainterLifeTab(QWidget):
    """Onglet de la notion 1.4 : quand un peintre est actif, et pourquoi le bloc `with`.

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
        endEarlyCheck: La case « terminer avant le second trait ».
        image: La surface de la notion, ou None avant le récapitulatif.
    """

    TabTitle = "La vie du peintre"
    TabToolTip = "Peintre actif ou terminé (isActive), un seul peintre par image, end() ou bloc with"
    RecommendedPanelWidth = 640
    Objective = (
        "Savoir quand un peintre (<code>QPainter</code>) est actif, ce qui se passe quand il ne "
        "l'est pas, et pourquoi on préfère le bloc <code>with</code> à l'appel explicite de "
        "<code>end()</code>."
    )
    KeyConcepts = [
        "Un peintre terminé ignore tout dessin, sans aucun message d'erreur.",
        "Une image n'accepte qu'un seul peintre actif à la fois : le second est refusé.",
        "Deux écritures du même geste : <code>end()</code> appelé soi-même, ou le bloc "
        "<code>with</code>, qui l'appelle toujours à sa sortie.",
        "Recommandation : toujours le bloc <code>with</code>.",
    ]
    KeyApis = ["QPainter.isActive", "QPainter.end", "QPainter.begin"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image: QImage | None = None

        self.canvas = QDrawingCanvas()
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.endEarlyCheck = self.controls.addCheckBox("Terminer avant le second trait")
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
        """Crée la surface blanche de 480 × 360 pixels, et montre la grille du repère."""
        self.image = QImage(480, 360, QImage.Format.Format_ARGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.canvas.setGridVisible(True)
        self.canvas.setImage(self.image)

    def drawReminder(self) -> None:
        """Comme en 1.1 : un peintre actif dans le bloc with, un trait bleu de 3 pixels."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(29, 53, 87), 3))
            painter.drawLine(40, 60, 200, 60)
        self.canvas.setImage(self.image)

    def drawAfterTheBlock(self) -> None:
        """Trace un trait dans le bloc, puis en demande un second après le bloc."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(29, 53, 87), 3))
            painter.drawLine(40, 120, 200, 120)
        self.readout.setText(f"painter.isActive() -> {painter.isActive()}")
        painter.drawLine(40, 160, 200, 160)  # ignoré, sans message
        self.canvas.setImage(self.image)

    def drawWithTwoPainters(self) -> None:
        """Met un second peintre sur l'image, pendant que le premier est encore actif."""
        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(29, 53, 87), 3))
            painter.drawLine(40, 200, 200, 200)
            with QPainter(self.image) as secondPainter:
                self.readout.setText(f"secondPainter.isActive() -> {secondPainter.isActive()}")
                secondPainter.drawLine(40, 240, 200, 240)  # ignoré
            painter.drawLine(40, 280, 200, 280)
        self.canvas.setImage(self.image)

    def drawBothWays(self) -> None:
        """Le même geste écrit deux fois : end() appelé soi-même, puis le bloc with."""
        painter = QPainter(self.image)
        painter.setPen(QPen(QColor(228, 87, 46), 3))
        painter.drawLine(280, 120, 440, 120)
        finished = painter.end()
        self.readout.setText(f"painter.end() -> {finished}")

        with QPainter(self.image) as painter:
            painter.setPen(QPen(QColor(228, 87, 46), 3))
            painter.drawLine(280, 160, 440, 160)
        self.canvas.setImage(self.image)

    def connectControls(self) -> None:
        """Relie la case à cocher au slot qui redessine."""
        self.endEarlyCheck.toggled.connect(self.redrawTwoLines)

    @Slot()
    def redrawTwoLines(self) -> None:
        """Lit la case à cocher, puis redessine les deux traits."""
        self.drawTwoLines(self.endEarlyCheck.isChecked())

    def drawTwoLines(self, endEarly: bool) -> None:
        """Repart d'une image blanche, puis trace deux traits sans bloc with ; end() avant le second si endEarly."""
        self.image.fill(Qt.GlobalColor.white)
        painter = QPainter(self.image)
        painter.setPen(QPen(QColor(228, 87, 46), 6))
        activeBeforeFirst = painter.isActive()
        painter.drawLine(60, 120, 420, 120)
        if endEarly:
            painter.end()
        activeBeforeSecond = painter.isActive()
        painter.drawLine(60, 240, 420, 240)
        if not endEarly:
            painter.end()
        self.readout.setText(f"avant le premier trait : isActive() -> {activeBeforeFirst}\n"
                             f"avant le second trait : isActive() -> {activeBeforeSecond}")
        self.canvas.setImage(self.image)

    def _exploreEnd(self) -> None:
        """Connecte la case à cocher, la révèle, puis dessine les deux traits."""
        self.connectControls()
        self.controls.reveal()
        self.redrawTwoLines()

    def _recap(self) -> None:
        """Crée la surface, puis trace le trait du récapitulatif."""
        self.createSurface()
        self.drawReminder()

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit la séquence d'étapes de la notion, dans l'ordre."""
        return [
            QStepWalkthrough.Step(
                title="Récapitulatif : une surface, un trait",
                explanation=(
                    "Rien de nouveau : <code>createSurface()</code> crée l'image blanche et "
                    "montre la grille. Un peintre, actif dans le bloc <code>with</code>, trace un "
                    "trait bleu de 3 pixels. À la sortie du bloc, le peintre termine. Cette "
                    "notion regarde ce qui se passe hors de ce cadre."
                ),
                run=self._recap,
                codeSource=(self.createSurface, self.drawReminder),
                references=[("QPainter", qtDocUrl("QtGui", "QPainter"))],
            ),
            QStepWalkthrough.Step(
                title="Après le bloc, le peintre a terminé",
                explanation=(
                    "<code>isActive()</code> rend <code>True</code> si le peintre est actif, "
                    "<code>False</code> sinon. La variable <code>painter</code> existe encore "
                    "après le bloc : un bloc <code>with</code> ne supprime pas ses noms. Mais "
                    "<code>isActive()</code> rend maintenant <code>False</code> : le peintre a "
                    "terminé."
                    "<br><br>Le trait demandé après le bloc, à y = 160, n'apparaît pas. Un peintre "
                    "terminé ignore tout dessin, sans aucun message, ni dans l'application ni "
                    "dans la console. Tout dessin se fait donc à l'intérieur du bloc."
                ),
                run=self.drawAfterTheBlock,
                references=[("QPainter.isActive", qtDocUrl("QtGui", "QPainter", "isActive"))],
            ),
            QStepWalkthrough.Step(
                title="Un seul peintre à la fois",
                explanation=(
                    "Une image n'accepte qu'un peintre actif à la fois. Le second peintre est "
                    "refusé : son <code>isActive()</code> rend <code>False</code>, et son trait, à y = 240, est "
                    "ignoré. Le premier peintre, lui, continue : son trait à y = 280 paraît."
                    "<br><br>Qt écrit un avertissement dans la console : <code>QPainter::begin: "
                    "A paint device can only be painted by one painter at a time.</code> On ne "
                    "le voit que si l'application est lancée depuis un terminal. "
                    "<code>begin()</code> est la méthode qui fait commencer un peintre : "
                    "<code>QPainter(image)</code> l'appelle pour nous."
                    "<br><br>C'est pourquoi un peintre doit toujours terminer. Un peintre resté "
                    "actif bloquerait tous les suivants sur la même image."
                ),
                run=self.drawWithTwoPainters,
                references=[
                    ("QPainter.begin", qtDocUrl("QtGui", "QPainter", "begin")),
                    ("QPainter.isActive", qtDocUrl("QtGui", "QPainter", "isActive")),
                ],
            ),
            QStepWalkthrough.Step(
                title="Deux écritures : end() explicite ou bloc with",
                explanation=(
                    "Dans la documentation et dans bien des exemples en ligne, on croise une "
                    "autre écriture. On crée le peintre, on dessine, puis on appelle soi-même "
                    "<code>painter.end()</code> pour qu'il termine. <code>end()</code> rend "
                    "<code>True</code> quand le peintre termine bien. Les "
                    "deux traits orange sont identiques : c'est le même geste, écrit de deux "
                    "façons."
                    "<br><br>La différence : avec <code>end()</code>, c'est à nous de ne jamais "
                    "l'oublier. Si le programme s'arrête en chemin sur une erreur, "
                    "<code>end()</code> n'est pas appelé. Le peintre reste actif, et l'image "
                    "refuse ensuite tout autre peintre. Le bloc <code>with</code>, lui, termine "
                    "toujours le peintre à sa sortie, même dans ce cas."
                    "<br><br><b>Recommandation : toujours le bloc <code>with</code>.</b> Un code "
                    "lu ailleurs avec <code>end()</code> fait la même chose, écrit à la main."
                ),
                run=self.drawBothWays,
                references=[
                    ("QPainter.end", qtDocUrl("QtGui", "QPainter", "end")),
                    ("QPainter.isActive", qtDocUrl("QtGui", "QPainter", "isActive")),
                ],
            ),
            QStepWalkthrough.Step(
                title="À vous : terminer trop tôt",
                explanation=(
                    "Une case à cocher, <code>endEarlyCheck</code>, paraît sous le canevas : "
                    "« Terminer avant le second trait », décochée au départ."
                    "<br><br><code>connectControls()</code> relie son signal "
                    "<code>toggled</code> au slot <code>redrawTwoLines()</code>, qui appelle "
                    "<code>drawTwoLines()</code>. Celle-ci emploie l'écriture explicite de "
                    "l'étape précédente, sans bloc <code>with</code>. La case déplace l'appel "
                    "<code>end()</code> : avant le second trait, ou après. La lecture affiche "
                    "<code>isActive()</code> juste avant chaque trait."
                    "<br><br>Cocher la case : le second trait disparaît, sans message d'erreur."
                ),
                run=self._exploreEnd,
                codeSource=(self.connectControls, self.redrawTwoLines, self.drawTwoLines),
                references=[
                    ("QPainter.end", qtDocUrl("QtGui", "QPainter", "end")),
                    ("QPainter.isActive", qtDocUrl("QtGui", "QPainter", "isActive")),
                ],
            ),
        ]
