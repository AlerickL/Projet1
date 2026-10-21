"""Bouton de couleur : `QColorBox`.

Dépendance locale : la pipette, `QScreenColorPicker` et `EyedropperButton`
(`q_screen_color_picker.py`), un outil partagé avec `QColorEdit`.
"""

from __future__ import annotations

from typing import Final, override

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, QSize, Qt, Signal, Slot
from PySide6.QtGui import (QColor, QEnterEvent, QHelpEvent, QKeyEvent, QMouseEvent, QPainter, QPainterPath, QPaintEvent, QPalette,
                           qGray)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QColorDialog, QSizePolicy, QStyle, QStyleOptionFocusRect,
                               QStyleOptionFrame, QToolTip, QWidget)

from .q_screen_color_picker import EyedropperButton, QScreenColorPicker


class QColorBox(QAbstractButton):
    """Petit bouton affichant une couleur, qui ouvre un sélecteur de couleur au clic.

    Hérite de `QAbstractButton`, qui fournit gratuitement le signal `clicked`,
    le focus clavier, l'activation par la barre d'espace et l'état désactivé.

    Quand le canal alpha n'est pas utilisé (`useAlpha()` vaut False), la
    couleur est affichée opaque et le sélecteur n'offre pas de canal alpha ;
    l'alpha de la couleur stockée n'est pas modifié pour autant.

    Quand le widget est désactivé, l'utilisateur ne peut plus changer la
    couleur (comme pour tout widget Qt), mais le programme le peut toujours
    via `setColor()`. La couleur est l'information que ce widget affiche :
    elle reste donc affichée telle quelle, et l'état désactivé se signale par
    le cadre qui devient gris (ainsi que, comme pour tout widget Qt,
    l'absence de focus clavier). Seul le survol d'un widget désactivé désature
    et assombrit la couleur affichée, pour rappeler qu'elle ne peut pas être
    changée depuis là ; la couleur stockée n'est elle-même jamais modifiée.

    La pipette
    ----------
    La commande de la pipette prend l'une des formes de `EyedropperButton`
    (`eyedropperButton`, `Corner` par défaut) :

    - `Corner` : un coin replié, en bas à droite de la couleur, porte l'icône
      d'une pipette. Il ne prend aucune place en plus. Sa taille est fixe,
      tirée de la hauteur d'un `QLineEdit`.
    - `Section` : une section à part, à droite de la couleur, dans le même
      cadre. Le widget s'élargit d'autant.
    - `Hidden` : aucune commande.

    Un clic sur la commande lance la pipette (`screenColorPicker`) : l'écran se
    fige, et un clic y prend une couleur. On peut aussi appuyer sur la commande,
    glisser jusqu'à la couleur et relâcher. Quand le widget a le focus, la
    touche I la lance aussi. `pickScreenColor` la lance par programme, quelle
    que soit la commande. La couleur prise garde l'alpha de
    la couleur courante. Un clic sur la couleur ouvre toujours le dialogue
    (`clicked`).

    Signaux:
        colorChanged: Signal(QColor). Émis quand la couleur change.

    Slots:
        setUseAlpha(bool): Active ou désactive le canal alpha.
        setColor(QColor): Définit la couleur affichée.
        setEyedropperButton(EyedropperButton): Choisit la commande de la pipette.
        pickScreenColor(): Lance la pipette.
    """

    EyedropperButton = EyedropperButton

    colorChanged = Signal(QColor)

    def __init__(self, initColor: QColor | None = None, useAlpha: bool = True,
                 parent: QWidget | None = None, *,
                 eyedropperButton: EyedropperButton = EyedropperButton.Corner) -> None:
        """Initialise le widget.

        Args:
            initColor: Couleur initiale, ou None pour le blanc opaque par défaut.
            useAlpha: Valeur initiale de `useAlpha()`.
            parent: Widget parent, ou None.
            eyedropperButton: La commande de la pipette.
        """
        super().__init__(parent)
        self.__useAlpha: bool = True
        self.__color: QColor = QColor(255, 255, 255)
        self.__eyedropperButton: EyedropperButton = eyedropperButton
        self.__picker: QScreenColorPicker | None = None
        self.__picking: bool = False
        self.__buttonHovered: bool = False
        self.__buttonPressed: bool = False
        self.__dragging: bool = False
        self.__pressPosition: QPoint = QPoint()

        # Proper initialization via mutators (keeps their own logic, e.g. update()).
        self.setUseAlpha(useAlpha)
        if initColor is not None:
            self.setColor(initColor)

        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.clicked.connect(self.__chooseColor)

    # =================================================================== state

    def useAlpha(self) -> bool:
        """Indique si le canal alpha est pris en compte.

        Retourne:
            True si le canal alpha est utilisé.
        """
        return self.__useAlpha

    @Slot(bool)
    def setUseAlpha(self, value: bool) -> None:
        """Active ou désactive le canal alpha.

        Args:
            value: True pour utiliser le canal alpha, False pour l'ignorer.
        """
        if self.__useAlpha != value:
            self.__useAlpha = value
            self.update()

    def color(self) -> QColor:
        """Renvoie une copie de la couleur actuelle.

        Retourne:
            La couleur affichée.
        """
        return QColor(self.__color)

    @Slot(QColor)
    def setColor(self, newColor: QColor) -> None:
        """Définit la couleur affichée.

        Args:
            newColor: Nouvelle couleur. Copiée : l'appelant peut continuer à
                modifier son propre `QColor` sans effet sur celle stockée ici.
        """
        if self.__color != newColor:
            self.__color = QColor(newColor)
            self.colorChanged.emit(self.color())
            self.update()

    # ============================================================== eyedropper

    def eyedropperButton(self) -> EyedropperButton:
        """La commande de la pipette (`Corner` par défaut)."""
        return self.__eyedropperButton

    @Slot(EyedropperButton)
    def setEyedropperButton(self, button: EyedropperButton) -> None:
        """Choisit la commande de la pipette ; avec `Section`, le widget s'élargit.

        Args:
            button: La commande.
        """
        if button != self.__eyedropperButton:
            self.__eyedropperButton = button
            self.__buttonHovered = False
            self.updateGeometry()
            self.update()

    def screenColorPicker(self) -> QScreenColorPicker:
        """La pipette du widget, créée au besoin : pour en régler le zoom, la moyenne ou la loupe.

        Le widget en reste propriétaire.
        """
        if self.__picker is None:
            self.__picker = QScreenColorPicker(self)
            self.__picker.colorSelected.connect(self.__takeColor)
            self.__picker.activeChanged.connect(self.__showPicking)
        return self.__picker

    @Slot()
    def pickScreenColor(self) -> None:
        """Lance la pipette, quelle que soit sa commande ; sans effet si le widget est désactivé ou si une prise est en cours."""
        picker = self.screenColorPicker()
        if not self.isEnabled() or picker.isActive():
            return
        self.__buttonHovered = False
        QToolTip.hideText()
        self.update()
        picker.setReferenceColor(self.__color)
        picker.start()

    # =================================================================== taille

    @override
    def sizeHint(self) -> QSize:
        """Renvoie la taille par défaut du widget.

        Retourne:
            Une taille à peu près carrée, dérivée de la hauteur d'un `QLineEdit`,
            élargie de la section de la pipette s'il y en a une.
        """
        height = self.__lineEditHeight()
        width = height + self.style().pixelMetric(QStyle.PixelMetric.PM_ButtonMargin)
        if self.__eyedropperButton == EyedropperButton.Section:
            width += self.__sectionWidth() + 1
        return QSize(width, height)

    @override
    def minimumSizeHint(self) -> QSize:
        """Renvoie la taille minimale du widget.

        Retourne:
            `sizeHint()` : ce widget n'a pas de taille plus petite utilisable.
        """
        return self.sizeHint()

    # ==================================================================== events

    @override
    def hitButton(self, pos: QPoint) -> bool:
        """Indique si un point actionne le bouton : partout, sauf sur la commande de la pipette.

        Args:
            pos: Le point, en coordonnées du widget.
        """
        return super().hitButton(pos) and not self.__hitsEyedropper(QPointF(pos))

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        """Redessine le widget à l'entrée du curseur.

        Args:
            event: Événement fourni par Qt.
        """
        super().enterEvent(event)
        self.update()

    @override
    def leaveEvent(self, event: QEvent) -> None:
        """Redessine le widget à la sortie du curseur.

        Args:
            event: Événement fourni par Qt.
        """
        super().leaveEvent(event)
        self.__buttonHovered = False
        self.update()

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Sur la commande de la pipette, la lance ; ailleurs, le comportement d'un bouton."""
        if event.button() == Qt.MouseButton.LeftButton and self.__hitsEyedropper(event.position()) and self.isEnabled():
            event.accept()
            self.__buttonPressed = self.__dragging = True
            self.__pressPosition = event.globalPosition().toPoint()
            self.pickScreenColor()
            self.update()
            return
        super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Pendant un glissement depuis la commande, déplace le réticule ; sinon, suit son survol."""
        if self.__dragging:
            self.screenColorPicker().moveTo(event.globalPosition().toPoint())
            return
        hovered = self.__hitsEyedropper(event.position())
        if hovered != self.__buttonHovered:
            self.__buttonHovered = hovered
            self.update()
        super().mouseMoveEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Au bout d'un glissement depuis la commande, prend la couleur sous le pointeur ; après un simple clic, la pipette reste ouverte."""
        if self.__buttonPressed and event.button() == Qt.MouseButton.LeftButton:
            event.accept()
            self.__buttonPressed = self.__dragging = False
            moved = (event.globalPosition().toPoint() - self.__pressPosition).manhattanLength()
            if moved >= QApplication.startDragDistance():
                picker = self.screenColorPicker()
                picker.moveTo(event.globalPosition().toPoint())
                picker.select()
            self.update()
            return
        super().mouseReleaseEvent(event)

    @override
    def event(self, e: QEvent) -> bool:
        """Donne à la commande de la pipette son infobulle."""
        if e.type() == QEvent.Type.ToolTip and isinstance(e, QHelpEvent) and self.__hitsEyedropper(QPointF(e.pos())):
            QToolTip.showText(e.globalPos(), self.tr("Eyedropper: pick a colour on screen\n\nClick · Press, drag, release · I"),
                              self)
            return True
        return super().event(e)

    @override
    def keyPressEvent(self, e: QKeyEvent) -> None:
        """La touche I lance la pipette ; les autres touches sont celles d'un bouton (Espace ouvre le dialogue)."""
        if e.key() == Qt.Key.Key_I and not e.modifiers() & ~Qt.KeyboardModifier.KeypadModifier:
            self.pickScreenColor()
            return
        super().keyPressEvent(e)

    @override
    def paintEvent(self, _: QPaintEvent) -> None:
        """Dessine la couleur, le damier de transparence si nécessaire, la
        commande de la pipette, le cadre, puis le focus.

        Args:
            _: Événement de peinture fourni par Qt (non utilisé).
        """
        color = QColor(self.__color)  # copy: the caller may keep modifying its own QColor while processing it
        if not self.__useAlpha:
            color.setAlpha(255)

        frame = self.rect().adjusted(0, 0, -1, -1)
        inner = self._colorRect()

        # The color is shown as is, even when disabled (it is the information being displayed),
        # except while hovered when disabled, to tell the user that it cannot be changed.
        dimmed = not self.isEnabled() and self.underMouse()
        if dimmed:
            color = self._desaturated(color, self._DisabledHoverDesaturation)

        with QPainter(self) as painter:
            painter.save()
            painter.setClipRect(inner)
            if dimmed:
                painter.setOpacity(self._DisabledHoverOpacity)
            if color.alpha() < 255:
                self._paintCheckerboard(painter)
            painter.fillRect(inner, color)
            painter.setOpacity(1.0)
            if self.__eyedropperButton == EyedropperButton.Corner:
                self.__paintCorner(painter)
            painter.restore()
            if self.__eyedropperButton == EyedropperButton.Section:
                self.__paintSection(painter)

            painter.setPen(self._frameColor())
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(frame)

            if self.hasFocus():
                focus = QStyleOptionFocusRect()
                focus.initFrom(self)
                focus.rect = inner.toRect()
                focus.backgroundColor = self.palette().color(QPalette.ColorRole.Window)
                self.style().drawPrimitive(QStyle.PrimitiveElement.PE_FrameFocusRect, focus, painter, self)

    # ============================================================= implementation

    _GridSize: Final[int] = 8  # Size of a checkerboard square, in pixels.
    _FrameContrast: Final[float] = 0.65  # Frame color between the background (0) and the text color (1).
    _DisabledHoverDesaturation: Final[float] = 0.5  # Blend toward gray when disabled and hovered (0: none, 1: full gray).
    _DisabledHoverOpacity: Final[float] = 0.8  # Opacity of the color when disabled and hovered.
    _CornerRatio: Final[float] = 1.0  # Side of the eyedropper's corner, from the inner height of a line edit.
    _CornerIconRatio: Final[float] = 0.58  # Side of the icon, from the corner's.
    _CornerIconCentre: Final[float] = 0.64  # Centre of the icon from the corner's top left, along each side.
    _SectionRatio: Final[float] = 0.85  # Width of the eyedropper's section, from the height of a line edit.
    _SectionIconRatio: Final[float] = 0.62  # Side of the icon, from the section's least side.

    @staticmethod
    def _desaturated(color: QColor, amount: float) -> QColor:
        """Renvoie une copie de `color` mélangée vers le gris de même
        luminance (l'alpha est conservé).

        Args:
            color: Couleur à désaturer.
            amount: 0.0 laisse la couleur inchangée, 1.0 donne le gris pur.

        Retourne:
            La couleur désaturée.
        """
        gray = qGray(color.rgb())
        return QColor(
            round(color.red() * (1 - amount) + gray * amount),
            round(color.green() * (1 - amount) + gray * amount),
            round(color.blue() * (1 - amount) + gray * amount),
            color.alpha(),
        )

    def _frameColor(self) -> QColor:
        """Renvoie la couleur du cadre : entre le fond de fenêtre et la
        couleur du texte de la palette, selon `_FrameContrast`.

        Contrairement à des rôles fixes comme `Mid` ou `Shadow`, qui peuvent
        être presque identiques au fond dans certains thèmes (ex. noir sur
        fenêtre sombre), ce calcul contraste avec le fond aussi bien en thème
        clair que sombre. La couleur de palette suit l'état activé/désactivé,
        donc le cadre devient gris quand le widget est désactivé.

        Retourne:
            La couleur du cadre.
        """
        palette = self.palette()
        background = palette.color(QPalette.ColorRole.Window)
        text = palette.color(QPalette.ColorRole.WindowText)
        t = self._FrameContrast
        return QColor(
            round(background.red() + (text.red() - background.red()) * t),
            round(background.green() + (text.green() - background.green()) * t),
            round(background.blue() + (text.blue() - background.blue()) * t),
        )

    def _paintCheckerboard(self, painter: QPainter) -> None:
        """Dessine un damier sur le widget, pour montrer la transparence
        (limité par le clip du painter).

        Args:
            painter: Painter actif, déjà positionné sur ce widget.
        """
        rect = self.rect()
        size = self._GridSize
        painter.fillRect(rect, Qt.GlobalColor.lightGray)
        for row, y in enumerate(range(rect.top(), rect.bottom() + 1, size)):
            for col, x in enumerate(range(rect.left(), rect.right() + 1, size)):
                if (row + col) % 2:
                    painter.fillRect(x, y, size, size, Qt.GlobalColor.darkGray)

    def _colorRect(self) -> QRectF:
        """La place de la couleur, dans le cadre ; la section de la pipette, s'il y en a une, est à sa droite."""
        inner = QRectF(self.rect().adjusted(1, 1, -1, -1))
        if self.__eyedropperButton == EyedropperButton.Section:
            inner.setRight(inner.right() - self.__sectionWidth() - 1)
        return inner

    def _eyedropperRect(self) -> QRectF:
        """La place de la commande de la pipette ; vide avec `Hidden`.

        Avec `Corner`, c'est le carré dont le coin occupe la moitié sous la diagonale qui va
        du haut à droite au bas à gauche. Sa taille est fixe : elle ne suit pas celle du widget.
        """
        inner = QRectF(self.rect().adjusted(1, 1, -1, -1))
        if self.__eyedropperButton == EyedropperButton.Corner:
            side = min(inner.width(), inner.height(), round(self._CornerRatio * (self.__lineEditHeight() - 2)))
            return QRectF(inner.right() - side, inner.bottom() - side, side, side)
        if self.__eyedropperButton == EyedropperButton.Section:
            width = self.__sectionWidth()
            return QRectF(inner.right() - width, inner.top(), width, inner.height())
        return QRectF()

    @Slot()
    def __chooseColor(self) -> None:
        options = QColorDialog.ColorDialogOption.ShowAlphaChannel if self.__useAlpha else QColorDialog.ColorDialogOption(0)
        chosen = QColorDialog.getColor(self.__color, self, "", options)
        if chosen.isValid():
            self.setColor(chosen)

    @Slot(QColor)
    def __takeColor(self, picked: QColor) -> None:
        color = QColor(picked)
        color.setAlpha(self.__color.alpha())
        self.setColor(color)

    @Slot(bool)
    def __showPicking(self, active: bool) -> None:
        self.__picking = active
        if not active:
            self.__dragging = self.__buttonPressed = False
        self.update()

    def __hitsEyedropper(self, point: QPointF) -> bool:
        rect = self._eyedropperRect()
        if not rect.contains(point):
            return False
        if self.__eyedropperButton == EyedropperButton.Corner:
            return (point.x() - rect.left()) + (point.y() - rect.top()) >= rect.width()
        return True

    def __tint(self) -> QColor | None:
        """The tint of the eyedropper's button, when hovered, pressed or picking; None otherwise."""
        if not self.isEnabled() or not (self.__buttonHovered or self.__buttonPressed or self.__picking):
            return None
        tint = QColor(self.palette().color(QPalette.ColorRole.Highlight))
        tint.setAlphaF(0.45 if self.__buttonPressed or self.__picking else 0.25)
        return tint

    def __paintCorner(self, painter: QPainter) -> None:
        corner = self._eyedropperRect()
        if corner.isEmpty():
            return
        palette = self.palette()
        triangle = QPainterPath()
        triangle.moveTo(corner.topRight())
        triangle.lineTo(corner.bottomRight())
        triangle.lineTo(corner.bottomLeft())
        triangle.closeSubpath()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillPath(triangle, palette.color(QPalette.ColorRole.Button))
        tint = self.__tint()
        if tint is not None:
            painter.fillPath(triangle, tint)
        painter.setPen(self._frameColor())
        painter.drawLine(corner.topRight(), corner.bottomLeft())
        painter.restore()
        side = corner.width() * self._CornerIconRatio
        centre = corner.topLeft() + QPointF(corner.width(), corner.height()) * self._CornerIconCentre
        QScreenColorPicker.paintIcon(painter, QRectF(centre.x() - side / 2, centre.y() - side / 2, side, side),
                                     palette.color(QPalette.ColorRole.ButtonText))

    def __paintSection(self, painter: QPainter) -> None:
        section = self._eyedropperRect()
        if section.isEmpty():
            return
        palette = self.palette()
        painter.fillRect(QRectF(section.left() - 1, section.top(), 1, section.height()), self._frameColor())
        painter.fillRect(section, palette.color(QPalette.ColorRole.Button))
        tint = self.__tint()
        if tint is not None:
            painter.fillRect(section, tint)
        side = min(section.width(), section.height()) * self._SectionIconRatio
        centre = section.center()
        QScreenColorPicker.paintIcon(painter, QRectF(centre.x() - side / 2, centre.y() - side / 2, side, side),
                                     palette.color(QPalette.ColorRole.ButtonText))

    def __sectionWidth(self) -> int:
        return round(self._SectionRatio * self.__lineEditHeight())

    def __lineEditHeight(self) -> int:
        """The height of a QLineEdit of the current style, for this widget's font."""
        opt = QStyleOptionFrame()
        opt.initFrom(self)
        return self.style().sizeFromContents(  # like a QLineEdit
            QStyle.ContentsType.CT_LineEdit, opt, QSize(0, self.fontMetrics().height()), self
        ).height()
