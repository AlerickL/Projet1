"""Le code d'un dégradé, écrit pour le constructeur de dégradés (notion 2.4) : `QGradientCodeView`.

Outil d'observation propre à la notion 2.4. Il reçoit un objet du sujet, un
`QGradient`, et affiche le code Python qui le recrée, prêt à copier dans un
programme hors de ce guide. Son code n'est jamais montré. La notion
présente son API visible : `setGradient()`. `gradientCode()` est la
fonction pure qui écrit ce code. Texte d'interface en français, sans `tr()`
(skill `interactive-walkthrough-app`, §10).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Slot
from PySide6.QtGui import QColor, QConicalGradient, QGradient, QGuiApplication, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ...widgets.q_python_code_view import QPythonCodeView


def gradientCode(gradient: QGradient, variable: str = "gradient") -> str:
    """Le code Python qui recrée ce dégradé, puis le pose dans un pinceau.

    Écrit le constructeur (linéaire, radial avec ou sans point focal,
    conique), chaque point d'arrêt, puis l'étalement et le mode de
    coordonnées s'ils ne sont pas ceux par défaut. Une couleur opaque
    s'écrit en hexadécimal, une couleur translucide par ses quatre nombres.

    Args:
        gradient: Le dégradé à décrire.
        variable: Le nom de la variable du dégradé dans le code.

    Raises:
        ValueError: Un dégradé d'un autre type (`QGradient` nu).
    """
    if isinstance(gradient, QLinearGradient):
        lines = [f"{variable} = QLinearGradient({_point(gradient.start())}, {_point(gradient.finalStop())})"]
    elif isinstance(gradient, QRadialGradient):
        arguments = f"{_point(gradient.center())}, {_number(gradient.radius())}"
        if gradient.focalPoint() != gradient.center():
            arguments += f", {_point(gradient.focalPoint())}"
        lines = [f"{variable} = QRadialGradient({arguments})"]
    elif isinstance(gradient, QConicalGradient):
        lines = [f"{variable} = QConicalGradient({_point(gradient.center())}, {_number(gradient.angle())})"]
    else:
        raise ValueError(f"unsupported gradient type {gradient.type()}")
    for position, color in gradient.stops():
        lines.append(f"{variable}.setColorAt({_number(position)}, {_color(color)})")
    if gradient.spread() != QGradient.Spread.PadSpread and not isinstance(gradient, QConicalGradient):
        lines.append(f"{variable}.setSpread(QGradient.Spread.{gradient.spread().name})")
    if gradient.coordinateMode() != QGradient.CoordinateMode.LogicalMode:
        lines.append(f"{variable}.setCoordinateMode(QGradient.CoordinateMode.{gradient.coordinateMode().name})")
    lines.append(f"brush = QBrush({variable})")
    return "\n".join(lines)


class QGradientCodeView(QWidget):
    """Le code Python d'un dégradé, non modifiable, avec un bouton pour le copier.

    Contenu:
        `setGradient()` écrit le code du dégradé reçu (`gradientCode()`) ;
        `code()` le rend. Le bouton « Copier le code » le place dans le
        presse-papiers.

    Slots:
        setGradient(QGradient), copyCode().
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise une vue vide.

        Args:
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self._codeView: QPythonCodeView = QPythonCodeView(showLineNumbers=False)
        self._codeView.setFixedHeight(self._codeView.fontMetrics().lineSpacing() * 9 + 12)

        copyButton = QPushButton("Copier le code")
        copyButton.setToolTip("Copier ce code dans le presse-papiers")
        copyButton.clicked.connect(self.copyCode)
        captionRow = QHBoxLayout()
        captionRow.addWidget(QLabel("Le code de ce dégradé :"))
        captionRow.addStretch(1)
        captionRow.addWidget(copyButton)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(captionRow)
        layout.addWidget(self._codeView)

    # ====== API : contenu ======

    def code(self) -> str:
        """Le code affiché ; vide avant le premier `setGradient()`."""
        return self._codeView.toPlainText()

    @Slot(QGradient)
    def setGradient(self, gradient: QGradient) -> None:
        """Affiche le code qui recrée ce dégradé."""
        self._codeView.setPlainText(gradientCode(gradient))

    @Slot()
    def copyCode(self) -> None:
        """Place le code affiché dans le presse-papiers."""
        QGuiApplication.clipboard().setText(self.code())


# ====== Private ======

def _number(value: float) -> str:
    """Un nombre lisible : entier sans décimale, sinon au plus trois décimales."""
    rounded = round(value, 3)
    return str(int(rounded)) if rounded == int(rounded) else f"{rounded:g}"


def _point(point: QPointF) -> str:
    return f"QPointF({_number(point.x())}, {_number(point.y())})"


def _color(color: QColor) -> str:
    if color.alpha() == 255:
        return f'QColor("{color.name()}")'
    return f"QColor({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
