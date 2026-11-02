"""La surface d'affichage partagée par toutes les notions de qpainter : `QDrawingCanvas`.

Outil d'observation. L'apprenant ne
peint jamais de widget : il crée sa propre `QImage`, y dessine avec un
`QPainter`, puis la donne au canevas par `setImage()`. Le canevas l'affiche
telle quelle, à l'échelle 1, sur un damier visible là où l'image est
transparente, avec une grille graduée en option (le repère : origine en
haut à gauche, y vers le bas). Il peut aussi agrandir une portion de
l'image, pixel par pixel, pour observer l'anticrénelage ou un trait d'un
pixel.

Le code de ce module n'est jamais montré. Son rôle et ses méthodes visibles
sont présentés à l'apprenant avant usage (règle I4 du skill
`interactive-walkthrough-app`). Texte d'interface en français, sans `tr()`
(même skill, §10).
"""

from __future__ import annotations

from typing import override

from PySide6.QtCore import QRect, QRectF, Qt, Slot
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget


class QDrawingCanvas(QWidget):
    """Affiche l'image de l'apprenant, avec une grille graduée et un agrandissement optionnels.

    Image:
        `setImage(image)` reçoit une `QImage`, en garde une copie et
        redessine le canevas. La copie ne suit pas les dessins faits
        ensuite sur l'image d'origine : il faut redonner l'image au canevas
        après chaque dessin. Le canevas a une taille fixe, 480 × 360 px par
        défaut. Une image d'une autre taille s'affiche à l'échelle 1, dans
        le coin supérieur gauche : coupée si elle est plus grande, entourée
        du damier si elle est plus petite. Avant le premier `setImage()`,
        le canevas affiche une image blanche de sa taille.

    Grille:
        `setGridVisible(True)` superpose une grille fine tous les 20 px, plus
        marquée et graduée tous les 100 px. Elle n'est jamais dessinée dans
        l'image : c'est une surimpression d'affichage. `gridVisible()` la lit.
        `setGridColor(QColor)` choisit sa couleur, `DefaultGridColor` au
        départ : les lignes la reprennent en transparence (plus marquée tous
        les 100 px), les graduations en plus foncé et opaque. L'alpha de la
        couleur reçue est ignoré. `gridColor()` la lit.

    Agrandissement:
        `setViewRect(QRect)` affiche seulement cette portion de l'image,
        exprimée dans le repère de l'image, agrandie pour remplir le
        canevas, sans lissage : chaque pixel devient un carré, séparé des
        autres par une grille au-delà d'un facteur 6. La partie de la
        portion qui sort de l'image montre le damier. `setViewRect(None)`,
        ou un rectangle vide, revient à l'image entière. `viewRect()` la
        lit.

    Slots:
        setImage(QImage), setGridVisible(bool), setGridColor(QColor),
        setViewRect(object).
    """

    DefaultGridColor = QColor(90, 110, 130)

    def __init__(self, width: int = 480, height: int = 360, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.__image: QImage = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        self.__image.fill(QColor("white"))
        self.__gridVisible: bool = False
        self.__gridColor: QColor = QColor(self.DefaultGridColor)
        self.__viewRect: QRect | None = None
        self.setFixedSize(width, height)

    # ====== API : image ======

    @Slot(QImage)
    def setImage(self, image: QImage) -> None:
        """Garde une copie de l'image et redessine le canevas."""
        self.__image = QImage(image)
        self.update()

    # ====== API : affichage ======

    def gridVisible(self) -> bool:
        """`True` si la grille graduée est superposée à l'image."""
        return self.__gridVisible

    @Slot(bool)
    def setGridVisible(self, visible: bool) -> None:
        """Affiche ou cache la grille graduée."""
        self.__gridVisible = visible
        self.update()

    def gridColor(self) -> QColor:
        """La couleur de la grille, opaque."""
        return QColor(self.__gridColor)

    @Slot(QColor)
    def setGridColor(self, color: QColor) -> None:
        """Choisit la couleur de la grille ; son alpha est ignoré."""
        self.__gridColor = QColor(color.red(), color.green(), color.blue())
        self.update()

    def viewRect(self) -> QRect | None:
        """La portion agrandie de l'image, ou `None` si l'image entière est affichée."""
        return QRect(self.__viewRect) if self.__viewRect is not None else None

    @Slot(object)
    def setViewRect(self, rect: QRect | None) -> None:
        """Agrandit une portion de l'image pour remplir le canevas, ou revient à l'image entière."""
        self.__viewRect = QRect(rect) if rect is not None and not rect.isEmpty() else None
        self.update()

    # ====== Événements ======

    @override
    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: D102 (Qt override)
        painter = QPainter(self)
        self.__paintCheckerboard(painter)
        if self.__viewRect is None:
            painter.drawImage(0, 0, self.__image)
            if self.__gridVisible:
                self.__paintGrid(painter)
        else:
            self.__paintMagnified(painter)
        painter.setPen(QColor("#9aa7b1"))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    # ====== Privé ======

    def __paintCheckerboard(self, painter: QPainter) -> None:
        painter.fillRect(self.rect(), QColor("#ffffff"))
        square = 10
        for y in range(0, self.height(), square):
            for x in range((y // square) % 2 * square, self.width(), 2 * square):
                painter.fillRect(x, y, square, square, QColor("#e4e8ec"))

    def __paintGrid(self, painter: QPainter) -> None:
        width, height = self.width(), self.height()
        painter.save()
        major = QColor(self.__gridColor)
        major.setAlpha(110)
        minor = QColor(self.__gridColor)
        minor.setAlpha(45)
        for x in range(0, width, 20):
            painter.setPen(major if x % 100 == 0 else minor)
            painter.drawLine(x, 0, x, height)
        for y in range(0, height, 20):
            painter.setPen(major if y % 100 == 0 else minor)
            painter.drawLine(0, y, width, y)
        font = QFont(painter.font())
        font.setPointSizeF(7.5)
        painter.setFont(font)
        painter.setPen(self.__gridColor.darker(130))
        for x in range(100, width, 100):
            painter.drawText(x + 3, 11, str(x))
        for y in range(100, height, 100):
            painter.drawText(3, y - 3, str(y))
        painter.drawText(3, 11, "(0, 0)  x →")
        painter.drawText(3, 24, "y ↓")
        painter.restore()

    def __paintMagnified(self, painter: QPainter) -> None:
        source = self.__viewRect
        if source is None:
            return
        scale = min(self.width() / source.width(), self.height() / source.height())
        target = QRectF(0, 0, source.width() * scale, source.height() * scale)
        painter.save()
        # No smoothing: each image pixel must stay a sharp square. Qt clips a source rectangle
        # that leaves the image without changing the scale, so the checkerboard shows there.
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawImage(target, self.__image, QRectF(source))
        if scale >= 6:
            painter.setPen(QPen(QColor(90, 110, 130, 90), 1))
            for column in range(source.width() + 1):
                x = round(column * scale)
                painter.drawLine(x, 0, x, round(target.height()))
            for row in range(source.height() + 1):
                y = round(row * scale)
                painter.drawLine(0, y, round(target.width()), y)
        font = QFont(painter.font())
        font.setPointSizeF(8)
        painter.setFont(font)
        painter.setPen(QColor(70, 85, 100))
        painter.drawText(QRectF(4, self.height() - 16, self.width() - 8, 14), Qt.AlignmentFlag.AlignRight,
                         f"agrandi ×{scale:g} : x {source.left()} à {source.right()}, "
                         f"y {source.top()} à {source.bottom()}")
        painter.restore()
