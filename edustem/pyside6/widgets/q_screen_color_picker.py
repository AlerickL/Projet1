"""Pipette d'écran : `QScreenColorPicker`.

Prend une couleur n'importe où à l'écran. Au lancement, chaque écran est capturé, puis
recouvert de sa capture figée. Un réticule suit le pointeur ; un panneau, à côté, grossit les
pixels visés et décrit la couleur. Un clic retient la couleur du pixel visé.

    picker = QScreenColorPicker(widget)
    picker.setReferenceColor(widget.color())
    picker.colorSelected.connect(widget.setColor)
    picker.start()

Voir `QScreenColorPicker` pour la documentation complète. `EyedropperButton` choisit comment
un widget de couleur montre la commande qui la lance.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import ClassVar, Final, override

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import (QClipboard, QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QImage, QKeyEvent, QMouseEvent,
                           QPainter, QPainterPath, QPaintEvent, QPalette, QPen, QPixmap, QScreen, QWheelEvent)
from PySide6.QtWidgets import QApplication, QFrame, QStyle, QStyleOptionFrame, QWidget


class QScreenColorPicker(QObject):
    """Pipette : prend la couleur d'un pixel n'importe où à l'écran.

    Déroulement
    -----------
    `start` attend un court instant, le temps que l'appelant se redessine (un widget peut
    masquer ce qui gênerait la prise, comme ses poignées), puis capture chaque écran. Une
    fenêtre sans bord recouvre alors chaque écran de sa capture : l'écran paraît figé. Le
    pointeur disparaît, remplacé par un réticule : deux lignes qui traversent l'écran,
    dégagées autour du pixel visé.

    La couleur prise est celle d'un pixel de l'écran, en pixels physiques : à une échelle
    d'affichage de 150 %, chaque pixel de l'écran se vise. Elle est opaque.

    Le panneau
    ----------
    Un panneau suit le réticule, décalé pour ne pas le cacher. De haut en bas :

    - **Avant, après** : la couleur de référence (`referenceColor`), celle que la prise
      remplacerait, puis la couleur qui serait retenue.
    - **La loupe** : les pixels voisins, grossis (`zoom`), le pixel visé encadré au centre.
      Son côté (`loupeSize`) se règle entre 4 et 16 fois la hauteur d'un `QLineEdit`, comme
      la fenêtre du plan de `QColorEdit`. Le cadre garde sa taille : le zoom change le
      nombre de pixels montrés.
    - **L'aperçu** (`previewWidget`), s'il y en a un : un widget rendu tel quel dans le
      panneau, par exemple un éditeur qui montre la couleur visée.
    - **La couleur écrite** (`_colorText`), la taille de la moyenne et le mode de prise.
    - **Le contraste** entre la couleur visée et la référence, au sens des WCAG, avec les
      seuils AA (4,5:1) et AAA (7:1).
    - **L'historique** : les dernières couleurs prises, toutes pipettes confondues.
    - **Les gestes**, en petit.

    Gestes
    ------
    - Clic gauche, Entrée ou Espace : retient la couleur (`colorSelected`).
    - Échap ou clic droit : abandonne (`canceled`). Quitter les fenêtres de la pipette
      (Alt+Tab) abandonne aussi.
    - Flèches : déplacent le réticule d'un pixel de l'écran ; avec Maj, de dix.
    - Maj pendant un déplacement de la souris : verrouille l'axe dominant, à partir du
      point où Maj a été enfoncée.
    - Alt : ne prend que la teinte ; Ctrl : ne prend que la luminosité (`PickMode`). Le reste
      vient de la référence.
    - 1 à 9 : la zone moyennée (`sampleSize`, `sampleShape`). Un chiffre impair moyenne un
      carré de ce côté (1, le pixel seul) ; un chiffre pair, un disque de ce rayon.
    - Molette : règle le grossissement de la loupe (`zoom`).
    - Tab, Maj+Tab : parcourent l'historique ; un déplacement revient à l'écran.
    - Ctrl+C : copie la couleur écrite, sans quitter la pipette (`copy`).

    Pilotage par programme
    ----------------------
    `moveTo` place le réticule sur un point de l'écran, `select` retient la couleur. Un
    widget s'en sert pour un geste d'un seul tenant : appuyer sur sa pipette, glisser
    jusqu'à la couleur, relâcher.

    Personnalisation
    ----------------
    `_colorText` écrit une couleur (`#RRGGBB` par défaut) : pour le panneau et pour la copie.
    `_paintPointer` dessine le réticule et le panneau. `paintIcon` dessine l'icône de la
    pipette, pour le bouton qui la lance.

    Propriétés:
        zoom (int): Le grossissement de la loupe : un pixel de l'écran y occupe un carré de
            ce côté, en pixels de l'écran. Accesseur `zoom()`, mutateur `setZoom()`.
        sampleSize (int): La zone moyennée, de 1 à 9 : impair, le côté d'un carré ; pair, le
            rayon d'un disque. Accesseur `sampleSize()`, mutateur `setSampleSize()` ; sa forme
            se lit par `sampleShape()`.
        loupeSize (int): Le côté de la loupe, en pixels. Accesseur `loupeSize()`, mutateur
            `setLoupeSize()`.
        referenceColor (QColor): La couleur qu'une prise remplacerait ; invalide pour
            aucune. Accesseur `referenceColor()`, mutateur `setReferenceColor()`.
        previewWidget (QWidget): Le widget d'aperçu ; None pour aucun. Accesseur
            `previewWidget()`, mutateur `setPreviewWidget()`.

    Signaux:
        currentColorChanged: Signal(QColor). Émis quand la couleur qui serait retenue change.
        colorSelected: Signal(QColor). Émis quand une couleur est retenue.
        canceled: Signal(). Émis quand la prise est abandonnée.
        activeChanged: Signal(bool). Émis quand la pipette s'active ou se termine.

    Slots:
        start(): Lance une prise.
        cancel(): Abandonne la prise en cours.
        select(): Retient la couleur visée.
        copy(): Copie la couleur visée, écrite.
        moveTo(QPoint): Place le réticule sur un point de l'écran.
        setZoom(int): Fixe le grossissement de la loupe.
        setSampleSize(int): Fixe le côté du carré moyenné.
        setLoupeSize(int): Fixe le côté de la loupe.
        setReferenceColor(QColor): Fixe la couleur qu'une prise remplacerait.
        setPreviewWidget(object): Fixe le widget d'aperçu.
    """

    class PickMode(Enum):
        """Ce que la prise retient de la couleur visée, d'après les touches enfoncées.

        Attributs:
            Color: Toute la couleur.
            Hue: La teinte seule (Alt) ; la saturation et la luminosité viennent de la référence.
            Lightness: La luminosité seule (Ctrl) ; la teinte et la saturation viennent de la référence.
        """

        Color = 0
        Hue = 1
        Lightness = 2

    class SampleShape(Enum):
        """La forme de la zone moyennée, d'après la parité de `sampleSize`.

        Attributs:
            Square: Un carré, de côté `sampleSize` (impair).
            Disc: Un disque, de rayon `sampleSize` (pair).
        """

        Square = 0
        Disc = 1

    currentColorChanged = Signal(QColor)
    colorSelected = Signal(QColor)
    canceled = Signal()
    activeChanged = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        """Construit une pipette inactive.

        Args:
            parent: Objet parent, ou None.
        """
        super().__init__(parent)
        self.__active: bool = False
        self.__overlays: list[QScreenColorPicker._Overlay] = []
        self.__target: QScreenColorPicker._Overlay | None = None
        self.__pendingPosition: QPoint | None = None
        self.__current: QColor = QColor()
        self.__zoom: int = self._DefaultZoom
        self.__sampleSize: int = 1
        self.__loupeSize: int = 0                     # 0: the default
        self.__referenceColor: QColor = QColor()
        self.__preview: QWidget | None = None
        self.__historyIndex: int = -1                 # -1: the colour on screen; else a rank in the history
        self.__lockAnchor: QPoint | None = None
        self.__lockAxis: Qt.Orientation | None = None
        self.__copied: bool = False
        self.__grabTimer: QTimer = QTimer(self)
        self.__grabTimer.setSingleShot(True)
        self.__grabTimer.timeout.connect(self.__grab)
        self.__copiedTimer: QTimer = QTimer(self)
        self.__copiedTimer.setSingleShot(True)
        self.__copiedTimer.timeout.connect(self.__clearCopied)

    # ================================================================== state

    def isActive(self) -> bool:
        """Indique si une prise est en cours, de `start` jusqu'à la prise ou l'abandon."""
        return self.__active

    def currentColor(self) -> QColor:
        """La couleur qui serait retenue, mode de prise compris ; invalide hors d'une prise."""
        return QColor(self.__current)

    def pickMode(self) -> PickMode:
        """Le mode de prise, d'après les touches enfoncées : Alt, la teinte ; Ctrl, la luminosité."""
        modifiers = _heldModifiers()
        if modifiers & Qt.KeyboardModifier.AltModifier:
            return QScreenColorPicker.PickMode.Hue
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            return QScreenColorPicker.PickMode.Lightness
        return QScreenColorPicker.PickMode.Color

    def zoom(self) -> int:
        """Le grossissement de la loupe (8 par défaut)."""
        return self.__zoom

    @Slot(int)
    def setZoom(self, zoom: int) -> None:
        """Fixe le grossissement de la loupe, ramené entre 2 et 24."""
        self.__zoom = max(self._ZoomRange[0], min(self._ZoomRange[1], zoom))
        self.__refresh()

    def sampleSize(self) -> int:
        """La zone moyennée, en pixels de l'écran : impair, le côté d'un carré ; pair, le rayon d'un disque (1 par défaut)."""
        return self.__sampleSize

    def sampleShape(self) -> SampleShape:
        """La forme de la zone moyennée : un carré pour une taille impaire, un disque pour une taille paire."""
        return QScreenColorPicker.SampleShape.Square if self.__sampleSize % 2 else QScreenColorPicker.SampleShape.Disc

    @Slot(int)
    def setSampleSize(self, size: int) -> None:
        """Fixe la zone moyennée, ramenée entre 1 et 9 : impair, un carré de ce côté ; pair, un disque de ce rayon."""
        self.__sampleSize = max(self._SampleRange[0], min(self._SampleRange[1], size))
        self.__updateCurrent()

    def loupeSize(self) -> int:
        """Le côté de la loupe, en pixels : huit fois la hauteur d'un `QLineEdit` par défaut."""
        if self.__loupeSize > 0:
            return self.__loupeSize
        return self._DefaultLoupeSize * _lineEditHeight()

    @Slot(int)
    def setLoupeSize(self, size: int) -> None:
        """Fixe le côté de la loupe, ramené entre `minimumLoupeSize` et `maximumLoupeSize` ; 0 redonne le défaut."""
        self.__loupeSize = 0 if size <= 0 else max(self.minimumLoupeSize(), min(self.maximumLoupeSize(), size))
        self.__refresh()

    def minimumLoupeSize(self) -> int:
        """Le plus petit côté permis : quatre fois la hauteur d'un `QLineEdit`."""
        return self._LoupeSizeRange[0] * _lineEditHeight()

    def maximumLoupeSize(self) -> int:
        """Le plus grand côté permis : seize fois la hauteur d'un `QLineEdit`."""
        return self._LoupeSizeRange[1] * _lineEditHeight()

    def referenceColor(self) -> QColor:
        """La couleur qu'une prise remplacerait ; invalide par défaut."""
        return QColor(self.__referenceColor)

    @Slot(QColor)
    def setReferenceColor(self, color: QColor) -> None:
        """Fixe la couleur qu'une prise remplacerait ; une couleur invalide n'en montre aucune.

        Sans référence, Alt et Ctrl prennent toute la couleur, et le contraste n'est pas montré.
        """
        self.__referenceColor = QColor(color)
        self.__updateCurrent()

    def previewWidget(self) -> QWidget | None:
        """Le widget d'aperçu rendu dans le panneau ; None par défaut."""
        return self.__preview

    @Slot(object)
    def setPreviewWidget(self, widget: QWidget | None) -> None:
        """Fixe le widget d'aperçu, rendu dans le panneau, sous la loupe.

        Le widget n'est jamais montré : il est rendu à sa hauteur recommandée, à la largeur du
        panneau. La pipette ne le prend pas en charge ; à l'appelant de le tenir à jour, par
        exemple en reliant `currentColorChanged` à son `setColor`.

        Args:
            widget: Le widget, ou None pour aucun.
        """
        self.__preview = widget
        self.__refresh()

    @staticmethod
    def history() -> list[QColor]:
        """Les dernières couleurs prises, la plus récente d'abord, toutes pipettes confondues (huit au plus)."""
        return [QColor(color) for color in QScreenColorPicker._history]

    @staticmethod
    def clearHistory() -> None:
        """Vide l'historique."""
        QScreenColorPicker._history.clear()

    # ================================================================ actions

    @Slot()
    def start(self) -> None:
        """Lance une prise ; sans effet si une prise est déjà en cours."""
        if self.__active:
            return
        self.__active = True
        self.__pendingPosition = None
        self.__historyIndex = -1
        self.activeChanged.emit(True)
        self.__grabTimer.start(self._GrabDelay)

    @Slot()
    def cancel(self) -> None:
        """Abandonne la prise en cours ; sans effet hors d'une prise."""
        if self.__active:
            self.__finish()
            self.canceled.emit()
            self.activeChanged.emit(False)

    @Slot()
    def select(self) -> None:
        """Retient la couleur visée et l'ajoute à l'historique ; abandonne si rien n'est encore visé."""
        if not self.__active:
            return
        self.__updateCurrent()
        if not self.__current.isValid():
            self.cancel()
            return
        color = QColor(self.__current)
        history = QScreenColorPicker._history
        history[:] = [color] + [kept for kept in history if kept != color][:self._HistoryLength - 1]
        self.__finish()
        self.colorSelected.emit(QColor(color))
        self.activeChanged.emit(False)

    @Slot()
    def copy(self) -> None:
        """Copie dans le presse-papiers la couleur visée, écrite par `_colorText` ; la prise continue."""
        if self.__active and self.__current.isValid():
            _clipboard().setText(self._colorText(self.__current))
            self.__copied = True
            self.__copiedTimer.start(self._CopiedDelay)
            self.__refresh()

    @Slot(QPoint)
    def moveTo(self, position: QPoint) -> None:
        """Place le réticule sur un point de l'écran, en coordonnées globales.

        Avant la capture, le point est retenu pour le premier réticule.
        """
        if not self.__active:
            return
        if not self.__overlays:
            self.__pendingPosition = QPoint(position)
            return
        overlay = self.__overlayAt(position)
        if overlay is not None:
            self.__aim(overlay, overlay.mapFromGlobal(QPointF(position)))

    # ============================================================ presentation

    @staticmethod
    def paintIcon(painter: QPainter, rect: QRectF, color: QColor) -> None:
        """Dessine l'icône de la pipette, centrée dans un rectangle, d'une seule couleur.

        La pipette est couchée en diagonale : la pointe en bas à gauche, la poire en haut à
        droite. Elle occupe le plus grand carré du rectangle.

        Args:
            painter: Le peintre.
            rect: Le rectangle.
            color: La couleur de l'icône.
        """
        side = min(rect.width(), rect.height())
        if side <= 0:
            return
        # Along the pipette, from the tip (-0.5) to the end of the bulb (+0.5), on a unit length.
        shape = QPainterPath()
        shape.moveTo(-0.5, 0.0)
        shape.lineTo(-0.36, -0.065)
        shape.lineTo(0.1, -0.065)
        shape.lineTo(0.1, -0.17)
        shape.lineTo(0.2, -0.17)
        shape.lineTo(0.2, 0.17)
        shape.lineTo(0.1, 0.17)
        shape.lineTo(0.1, 0.065)
        shape.lineTo(-0.36, 0.065)
        shape.closeSubpath()
        shape.addRoundedRect(QRectF(0.18, -0.115, 0.32, 0.23), 0.115, 0.115)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(rect.center())
        painter.rotate(-45)
        painter.scale(side * math.sqrt(2) * 0.92, side * math.sqrt(2) * 0.92)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPath(shape.simplified())
        painter.restore()

    # ================================================================= events

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not isinstance(watched, QScreenColorPicker._Overlay):
            return super().eventFilter(watched, event)
        kind = event.type()
        if kind == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
            self.__historyIndex = -1
            self.__aim(watched, event.position())
        elif kind == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent):
            if event.button() == Qt.MouseButton.LeftButton:
                if self.__historyIndex < 0:
                    self.__aim(watched, event.position())
                self.select()
            elif event.button() == Qt.MouseButton.RightButton:
                self.cancel()
        elif kind == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            self.__press(event)
        elif kind == QEvent.Type.KeyRelease and isinstance(event, QKeyEvent):
            self.__updateCurrent()              # Alt or Ctrl released: the pick mode changes
        elif kind == QEvent.Type.Wheel and isinstance(event, QWheelEvent):
            delta = event.angleDelta().y() or event.angleDelta().x()
            if delta:
                self.setZoom(self.__zoom + (1 if delta > 0 else -1))
        elif kind == QEvent.Type.Enter:
            watched.activateWindow()
        elif kind == QEvent.Type.WindowDeactivate:
            QTimer.singleShot(0, self.__cancelIfLeft)
            return False
        else:
            return kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick, QEvent.Type.ShortcutOverride)
        return True

    # ============================================================== protected

    _history: ClassVar[list[QColor]] = []

    _GrabDelay: Final[int] = 120             # ms for the caller to repaint before the screens are captured
    _CopiedDelay: Final[int] = 1200          # ms the panel says the colour was copied
    _DefaultZoom: Final[int] = 8
    _ZoomRange: Final[tuple[int, int]] = (2, 24)
    _SampleRange: Final[tuple[int, int]] = (1, 9)
    _HistoryLength: Final[int] = 8
    _LockThreshold: Final[int] = 3           # screen pixels from the anchor before the dominant axis is chosen
    _DefaultLoupeSize: Final[int] = 8        # side of the loupe, in line-edit heights, as the plane's popup of QColorEdit
    _LoupeSizeRange: Final[tuple[int, int]] = (4, 16)
    _PanelOffset: Final[int] = 2             # distance from the crosshair to the panel, in text lines
    _GapLines: Final[float] = 1.0            # the crosshair's clear centre, in text lines from the pixel
    _SmallFontScale: Final[float] = 0.8
    _AaRatio: Final[float] = 4.5
    _AaaRatio: Final[float] = 7.0
    # Fixed whatever the theme: the crosshair must read on any colour, as the grips of QColorEdit.
    _CoreColor: Final[QColor] = QColor(250, 250, 250)
    _EdgeColor: Final[QColor] = QColor(24, 24, 24)

    def _grabScreen(self, screen: QScreen) -> QPixmap:
        """Capture un écran, en pixels physiques ; point d'extension.

        Retourne:
            La capture, avec son facteur d'échelle ; une image nulle si l'écran ne se capture pas.
        """
        return _captureScreen(screen)

    def _colorText(self, color: QColor) -> str:
        """Une couleur écrite, pour le panneau et pour la copie ; `#RRGGBB` par défaut. Point d'extension."""
        return color.name(QColor.NameFormat.HexRgb).upper()

    def _paintPointer(self, painter: QPainter, area: QRectF, scale: float, image: QImage, pixel: QPoint) -> None:
        """Dessine le réticule et le panneau sur la capture d'un écran ; point d'extension.

        Args:
            painter: Le peintre, sur la fenêtre de la pipette de cet écran.
            area: Le rectangle de cette fenêtre, en pixels logiques.
            scale: Le nombre de pixels de l'écran par pixel logique.
            image: La capture de cet écran, en pixels de l'écran.
            pixel: Le pixel visé, en pixels de l'écran.
        """
        palette = QGuiApplication.palette()
        metrics = QFontMetrics(painter.font())
        line = metrics.height()
        self._paintCrosshair(painter, area, scale, pixel, self._GapLines * line, self.__lockAxis)

        small = QFont(painter.font())
        small.setPointSizeF(painter.font().pointSizeF() * self._SmallFontScale)
        smallMetrics = QFontMetrics(small)
        smallLine = smallMetrics.height()
        hints = (self.tr("Click · Enter: pick    Esc: cancel    Ctrl+C: copy"),
                 self.tr("Alt: hue only    Ctrl: lightness only    Shift: lock axis"),
                 self.tr("Arrows: 1 px    1 3 5 7 9: square    2 4 6 8: disc    Wheel: zoom"),
                 self.tr("Tab: history"))
        preview = self.__preview
        side = self._loupeSide(scale, self.loupeSize())
        width = max(side, max(smallMetrics.horizontalAdvance(hint) for hint in hints) + line)
        previewHeight = 0
        if preview is not None:
            width = max(width, preview.minimumSizeHint().width())
            previewHeight = preview.sizeHint().height()
        pad = round(line / 3)
        reference = self.__referenceColor
        history = QScreenColorPicker._history
        heights = [round(1.6 * line), side, previewHeight, line, line if reference.isValid() else 0,
                   line if history else 0, 4 * smallLine]
        height = pad + sum(part + pad for part in heights if part)
        outer = width + 2 * pad

        centre = QPointF((pixel.x() + 0.5) / scale, (pixel.y() + 0.5) / scale)
        offset = self._PanelOffset * line
        x = centre.x() + offset if centre.x() + offset + outer <= area.right() else centre.x() - offset - outer
        y = centre.y() + offset if centre.y() + offset + height <= area.bottom() else centre.y() - offset - height
        panel = QRectF(round(max(area.left(), x) * scale) / scale, round(max(area.top(), y) * scale) / scale, outer, height)
        painter.fillRect(panel.adjusted(-1, -1, 1, 1), palette.color(QPalette.ColorRole.Mid))
        painter.fillRect(panel, palette.color(QPalette.ColorRole.Window))
        left = panel.left() + pad
        top = panel.top() + pad

        # Before | after.
        strip = round(1.6 * line)
        current = self.__current
        mode = self.pickMode() if reference.isValid() else QScreenColorPicker.PickMode.Color
        after = {QScreenColorPicker.PickMode.Color: self.tr("After"), QScreenColorPicker.PickMode.Hue: self.tr("Hue"),
                 QScreenColorPicker.PickMode.Lightness: self.tr("Lightness")}[mode]
        halves = [(QRectF(left, top, width / 2, strip), reference, self.tr("Before")),
                  (QRectF(left + width / 2, top, width / 2, strip), current, after)]
        if not reference.isValid():
            halves = [(QRectF(left, top, width, strip), current, after)]
        for rect, color, word in halves:
            if not color.isValid():
                continue
            painter.fillRect(rect, color)
            painter.setPen(_ink(color))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{word}  {color.name().upper()}")
        top += strip + pad

        loupe = QRectF(round((left + (width - side) / 2) * scale) / scale, top, side, side)
        self._paintMagnified(painter, loupe, scale, image, pixel)
        top += side + pad

        if preview is not None:
            preview.resize(round(width), previewHeight)
            preview.render(painter, QPoint(round(left), round(top)))
            top += previewHeight + pad

        painter.setPen(palette.color(QPalette.ColorRole.WindowText))
        if self.__copied:
            text = self.tr("Copied: {0}").format(self._colorText(current))
        else:
            text = self._colorText(current) if current.isValid() else ""
            if self.sampleShape() == QScreenColorPicker.SampleShape.Disc:
                text += "   " + self.tr("disc r {0}").format(self.__sampleSize)
            elif self.__sampleSize > 1:
                text += f"   {self.__sampleSize}×{self.__sampleSize}"
        painter.drawText(QRectF(left, top, width, line), Qt.AlignmentFlag.AlignCenter, text)
        top += line + pad

        if reference.isValid() and current.isValid():
            ratio = _contrastRatio(current, reference)
            marks = "  ".join(f"{name} {'✓' if ratio >= threshold else '✗'}"
                              for name, threshold in (("AA", self._AaRatio), ("AAA", self._AaaRatio)))
            painter.drawText(QRectF(left, top, width, line), Qt.AlignmentFlag.AlignCenter,
                             self.tr("Contrast {0}:1").format(f"{ratio:.2f}") + f"   {marks}")
            top += line + pad

        if history:
            chip = line * 0.8
            gap = line / 4
            start = left + (width - len(history) * (chip + gap) + gap) / 2
            for rank, color in enumerate(history):
                rect = QRectF(start + rank * (chip + gap), top + (line - chip) / 2, chip, chip)
                if rank == self.__historyIndex:
                    painter.fillRect(rect.adjusted(-2, -2, 2, 2), palette.color(QPalette.ColorRole.Highlight))
                painter.fillRect(rect.adjusted(-1, -1, 1, 1), palette.color(QPalette.ColorRole.Mid))
                painter.fillRect(rect, color)
            top += line + pad

        painter.setFont(small)
        painter.setPen(palette.color(QPalette.ColorRole.PlaceholderText))
        painter.drawText(QRectF(left, top, width, 4 * smallLine), Qt.AlignmentFlag.AlignCenter, "\n".join(hints))

    def _paintCrosshair(self, painter: QPainter, area: QRectF, scale: float, pixel: QPoint, gap: float,
                        locked: Qt.Orientation | None = None) -> None:
        """Dessine deux lignes qui traversent la fenêtre par le pixel visé, dégagées autour de lui.

        Chaque ligne est claire, bordée de sombre, d'un pixel de l'écran chacun : lisible sur
        toute couleur. La ligne d'un axe verrouillé prend la couleur d'accent.

        Args:
            painter: Le peintre.
            area: Le rectangle de la fenêtre, en pixels logiques.
            scale: Le nombre de pixels de l'écran par pixel logique.
            pixel: Le pixel visé, en pixels de l'écran.
            gap: Le rayon du centre dégagé, en pixels logiques.
            locked: L'axe verrouillé, ou None.
        """
        clear = math.ceil(gap * scale)
        unit = 1 / scale
        accent = QGuiApplication.palette().color(QPalette.ColorRole.Highlight)
        x, y = pixel.x() / scale, pixel.y() / scale
        top, bottom = (pixel.y() - clear) / scale, (pixel.y() + 1 + clear) / scale
        left, right = (pixel.x() - clear) / scale, (pixel.x() + 1 + clear) / scale
        for extra, color in ((unit, self._EdgeColor), (0.0, self._CoreColor)):
            vertical = accent if extra == 0 and locked == Qt.Orientation.Vertical else color
            horizontal = accent if extra == 0 and locked == Qt.Orientation.Horizontal else color
            for first, last in ((area.top(), top), (bottom, area.bottom() + 1)):
                painter.fillRect(QRectF(x - extra, first, unit + 2 * extra, max(0.0, last - first)), vertical)
            for first, last in ((area.left(), left), (right, area.right() + 1)):
                painter.fillRect(QRectF(first, y - extra, max(0.0, last - first), unit + 2 * extra), horizontal)

    def _loupeSide(self, scale: float, wanted: float) -> float:
        """Le côté d'une loupe proche de `wanted`, calé sur les pixels de l'écran ; il ne dépend pas du zoom."""
        return max(3, round(wanted * scale)) / scale

    def _paintMagnified(self, painter: QPainter, rect: QRectF, scale: float, image: QImage, pixel: QPoint) -> None:
        """Dessine les pixels voisins du pixel visé, grossis, dans un carré, avec le carré moyenné encadré.

        Le carré garde sa taille : le zoom change le nombre de pixels montrés, rognés aux bords.
        Le pixel visé reste au centre.

        Args:
            painter: Le peintre.
            rect: Le carré, d'un côté donné par `_loupeSide`.
            scale: Le nombre de pixels de l'écran par pixel logique.
            image: La capture, en pixels de l'écran.
            pixel: Le pixel visé.
        """
        zoom = self.__zoom
        side = round(rect.width() * scale)
        half = (side // zoom) // 2 + 1                      # enough cells to cover the square, cut at its edges
        cells = 2 * half + 1
        source = image.copy(QRect(pixel.x() - half, pixel.y() - half, cells, cells))
        unit = 1 / scale
        cell = zoom * unit
        centre = QPointF(round(rect.left() * scale + (side - zoom) // 2) / scale,
                         round(rect.top() * scale + (side - zoom) // 2) / scale)
        size = self.__sampleSize
        painter.save()
        painter.setClipRect(rect)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawImage(QRectF(centre.x() - half * cell, centre.y() - half * cell, cells * cell, cells * cell), source)
        if self.sampleShape() == QScreenColorPicker.SampleShape.Disc:
            # A circle through the outer edges of the pixels at the radius, light inside dark.
            middle = centre + QPointF(cell / 2, cell / 2)
            radius = (size + 0.5) * cell
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for extra, color, width in ((0.0, self._EdgeColor, 3 * unit), (0.0, self._CoreColor, unit)):
                painter.setPen(QPen(color, width))
                painter.drawEllipse(middle, radius + extra, radius + extra)
            painter.restore()
            return
        for inset, color in ((0.0, self._EdgeColor), (unit, self._CoreColor)):
            box = QRectF(centre.x() - (size // 2) * cell - unit + inset, centre.y() - (size // 2) * cell - unit + inset,
                         size * cell + 2 * unit - 2 * inset, size * cell + 2 * unit - 2 * inset)
            for edge in (QRectF(box.left(), box.top(), box.width(), unit), QRectF(box.left(), box.bottom() - unit, box.width(), unit),
                         QRectF(box.left(), box.top(), unit, box.height()), QRectF(box.right() - unit, box.top(), unit, box.height())):
                painter.fillRect(edge, color)
        painter.restore()

    # ================================================================ private

    @Slot()
    def __grab(self) -> None:
        if not self.__active:
            return
        for screen in QGuiApplication.screens():
            pixmap = self._grabScreen(screen)
            if pixmap.isNull():
                continue
            overlay = QScreenColorPicker._Overlay(self, screen, pixmap)
            overlay.installEventFilter(self)
            self.__overlays.append(overlay)
        if not self.__overlays:
            self.cancel()
            return
        for overlay in self.__overlays:
            overlay.show()
        position = self.__pendingPosition if self.__pendingPosition is not None else QCursor.pos()
        overlay = self.__overlayAt(position) or self.__overlays[0]
        overlay.activateWindow()
        overlay.setFocus()
        self.__aim(overlay, overlay.mapFromGlobal(QPointF(position)))

    def __overlayAt(self, position: QPoint) -> QScreenColorPicker._Overlay | None:
        screen = QGuiApplication.screenAt(position)
        return next((overlay for overlay in self.__overlays if overlay.screen() is screen), None)

    def __aim(self, overlay: _Overlay, position: QPointF) -> None:
        """Vise le pixel de l'écran sous un point d'une fenêtre de la pipette, axe verrouillé compris."""
        image = overlay.image
        pixel = QPoint(math.floor(position.x() * overlay.scale), math.floor(position.y() * overlay.scale))
        if _heldModifiers() & Qt.KeyboardModifier.ShiftModifier and overlay is self.__target:
            if self.__lockAnchor is None and overlay.pixel is not None:
                self.__lockAnchor = QPoint(overlay.pixel)
            anchor = self.__lockAnchor
            if anchor is not None:
                dx, dy = abs(pixel.x() - anchor.x()), abs(pixel.y() - anchor.y())
                if self.__lockAxis is None and max(dx, dy) >= self._LockThreshold:
                    self.__lockAxis = Qt.Orientation.Horizontal if dx >= dy else Qt.Orientation.Vertical
                if self.__lockAxis == Qt.Orientation.Horizontal:
                    pixel.setY(anchor.y())
                elif self.__lockAxis == Qt.Orientation.Vertical:
                    pixel.setX(anchor.x())
        else:
            self.__lockAnchor = self.__lockAxis = None
        pixel = QPoint(max(0, min(image.width() - 1, pixel.x())), max(0, min(image.height() - 1, pixel.y())))
        self.__setTarget(overlay, pixel)

    def __setTarget(self, overlay: _Overlay, pixel: QPoint) -> None:
        if self.__target is not None and self.__target is not overlay:
            self.__target.pixel = None
            self.__target.update()
        self.__target = overlay
        overlay.pixel = pixel
        self.__updateCurrent()

    def __updateCurrent(self) -> None:
        """Recompose la couleur qui serait retenue : la couleur visée, ou celle de l'historique, selon le mode."""
        if self.__target is None or self.__target.pixel is None:
            return
        history = QScreenColorPicker._history
        if 0 <= self.__historyIndex < len(history):
            picked = QColor(history[self.__historyIndex])
        else:
            picked = _averageColor(self.__target.image, self.__target.pixel, self.__sampleSize)
        color = _blend(picked, self.__referenceColor, self.pickMode())
        self.__target.update()
        if color != self.__current:
            self.__current = color
            self.currentColorChanged.emit(QColor(color))

    def __press(self, event: QKeyEvent) -> None:
        key = Qt.Key(event.key())
        modifiers = event.modifiers()
        steps = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0), Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        samples = {Qt.Key(Qt.Key.Key_0.value + digit): digit for digit in range(1, 10)}
        history = QScreenColorPicker._history
        if key == Qt.Key.Key_Escape:
            self.cancel()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.select()
        elif key == Qt.Key.Key_C and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.copy()
        elif key in samples:
            self.setSampleSize(samples[key])
        elif key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab) and history:
            forward = key == Qt.Key.Key_Tab and not modifiers & Qt.KeyboardModifier.ShiftModifier
            if self.__historyIndex < 0:
                self.__historyIndex = 0 if forward else len(history) - 1
            else:
                self.__historyIndex = (self.__historyIndex + (1 if forward else -1)) % len(history)
            self.__updateCurrent()
        elif key in steps and self.__target is not None and self.__target.pixel is not None:
            factor = 10 if modifiers & Qt.KeyboardModifier.ShiftModifier else 1
            dx, dy = steps[key]
            image = self.__target.image
            pixel = self.__target.pixel
            self.__historyIndex = -1
            self.__setTarget(self.__target, QPoint(max(0, min(image.width() - 1, pixel.x() + dx * factor)),
                                                   max(0, min(image.height() - 1, pixel.y() + dy * factor))))
        else:
            self.__updateCurrent()              # Alt or Ctrl pressed: the pick mode changes

    @Slot()
    def __cancelIfLeft(self) -> None:
        if self.__active and self.__overlays and not any(overlay.isActiveWindow() for overlay in self.__overlays):
            self.cancel()

    @Slot()
    def __clearCopied(self) -> None:
        self.__copied = False
        self.__refresh()

    def __refresh(self) -> None:
        if self.__target is not None:
            self.__target.update()

    def __finish(self) -> None:
        self.__active = False
        self.__grabTimer.stop()
        self.__copiedTimer.stop()
        self.__copied = False
        for overlay in self.__overlays:
            overlay.removeEventFilter(self)
            overlay.hide()
            overlay.deleteLater()
        self.__overlays.clear()
        self.__target = None
        self.__current = QColor()
        self.__historyIndex = -1
        self.__lockAnchor = self.__lockAxis = None

    # ============================================================== overlay

    class _Overlay(QWidget):
        """Fenêtre sans bord qui recouvre un écran de sa capture, et y dessine le réticule et le panneau."""

        def __init__(self, picker: QScreenColorPicker, screen: QScreen, pixmap: QPixmap) -> None:
            super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                             | Qt.WindowType.Tool)
            self.picker: QScreenColorPicker = picker
            self.pixmap: QPixmap = pixmap
            self.image: QImage = pixmap.toImage()
            self.scale: float = pixmap.devicePixelRatio()
            self.pixel: QPoint | None = None
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.setCursor(Qt.CursorShape.BlankCursor)
            self.setMouseTracking(True)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setScreen(screen)
            self.setGeometry(screen.geometry())
            picker.destroyed.connect(self.close)      # a window without parent would outlive a destroyed picker

        @override
        def paintEvent(self, event: QPaintEvent) -> None:
            with QPainter(self) as painter:
                painter.drawPixmap(0, 0, self.pixmap)
                if self.pixel is not None:
                    self.picker._paintPointer(painter, QRectF(self.rect()), self.scale, self.image, self.pixel)  # pyright: ignore[reportPrivateUsage]


class EyedropperButton(Enum):
    """La commande qui lance la pipette dans un widget de couleur (`QColorBox`, `QColorEdit`).

    Quelle qu'elle soit, la pipette se lance aussi par programme (`pickScreenColor`).

    Attributs:
        Hidden: Aucune commande.
        Corner: Un coin replié sur la couleur, en bas, à son bout ; il ne prend aucune place.
        Section: Une section à part, juste après la couleur, comme les autres bascules.
    """

    Hidden = 0
    Corner = 1
    Section = 2


_LineEditVerticalMargin: Final[int] = 1      # both as QLineEdit::sizeHint, to get its exact height
_LineEditMinimumTextHeight: Final[int] = 14


def _lineEditHeight() -> int:
    """La hauteur d'un `QLineEdit` du style de l'application, pour sa police : l'unité des tailles de la loupe."""
    style = QApplication.style()
    option = QStyleOptionFrame()
    option.lineWidth = style.pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
    option.frameShape = QFrame.Shape.StyledPanel
    metrics = QFontMetrics(QApplication.font())
    iconSize = style.pixelMetric(QStyle.PixelMetric.PM_SmallIconSize)
    content = max(metrics.height(), _LineEditMinimumTextHeight, iconSize - 2) + 2 * _LineEditVerticalMargin
    return style.sizeFromContents(QStyle.ContentsType.CT_LineEdit, option, QSize(0, content)).height()


def _averageColor(image: QImage, pixel: QPoint, size: int) -> QColor:
    """La couleur moyenne d'une zone centrée sur un pixel, rognée aux bords de l'image ; opaque.

    Une taille impaire est le côté d'un carré ; une taille paire, le rayon d'un disque : les
    pixels dont le centre est à cette distance au plus.
    """
    disc = size % 2 == 0
    half = size if disc else size // 2
    red = green = blue = count = 0
    for y in range(max(0, pixel.y() - half), min(image.height(), pixel.y() + half + 1)):
        for x in range(max(0, pixel.x() - half), min(image.width(), pixel.x() + half + 1)):
            if disc and (x - pixel.x()) ** 2 + (y - pixel.y()) ** 2 > size * size:
                continue
            color = image.pixelColor(x, y)
            red, green, blue, count = red + color.red(), green + color.green(), blue + color.blue(), count + 1
    if count == 0:
        return QColor()
    return QColor(round(red / count), round(green / count), round(blue / count))


def _captureScreen(screen: QScreen) -> QPixmap:
    """La capture d'un écran entier ; les tests remplacent cette fonction, jamais une classe de Qt."""
    return screen.grabWindow(0)


def _heldModifiers() -> Qt.KeyboardModifier:
    """Les touches de modification enfoncées, lues sur le système : un geste peut se finir dans un autre widget."""
    return QGuiApplication.queryKeyboardModifiers()


def _clipboard() -> QClipboard:
    """Le presse-papiers de l'application."""
    return QGuiApplication.clipboard()


def _blend(picked: QColor, reference: QColor, mode: QScreenColorPicker.PickMode) -> QColor:
    """La couleur retenue : la couleur prise, ou un seul de ses canaux TSL posé sur la référence (opaque).

    Une teinte prise sur un gris n'existe pas : la référence est alors gardée telle quelle.
    """
    Mode = QScreenColorPicker.PickMode
    if not picked.isValid() or not reference.isValid() or mode == Mode.Color:
        return QColor(picked)
    hue, saturation, lightness = reference.hslHueF(), reference.hslSaturationF(), reference.lightnessF()
    if mode == Mode.Hue:
        if picked.hslHueF() < 0:
            return QColor.fromHslF(max(0.0, hue), saturation, lightness, 1.0)
        hue = picked.hslHueF()
    else:
        lightness = picked.lightnessF()
    return QColor.fromHslF(max(0.0, hue), saturation, lightness, 1.0)


def _relativeLuminance(color: QColor) -> float:
    """La luminance relative d'une couleur sRGB, au sens des WCAG."""
    def linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return 0.2126 * linear(color.redF()) + 0.7152 * linear(color.greenF()) + 0.0722 * linear(color.blueF())


def _contrastRatio(first: QColor, second: QColor) -> float:
    """Le rapport de contraste WCAG de deux couleurs, de 1 à 21."""
    lighter, darker = sorted((_relativeLuminance(first), _relativeLuminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _ink(color: QColor) -> QColor:
    """Une encre lisible sur une couleur : presque noire sur une couleur claire, presque blanche sinon."""
    return QColor(24, 24, 24) if _relativeLuminance(color) > 0.18 else QColor(250, 250, 250)
