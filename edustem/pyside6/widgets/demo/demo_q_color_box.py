"""Démo : deux QColorBox synchronisées, avec les réglages de la seconde."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QWidget,
)

from ..q_color_box import QColorBox


def _withAlpha(color: QColor, alpha: int) -> QColor:
    """Renvoie une copie de `color` avec l'alpha donné."""
    result = QColor(color)
    result.setAlpha(alpha)
    return result


def main() -> int:
    app = QApplication(sys.argv)

    colorBox1 = QColorBox()
    colorBox2 = QColorBox()
    colorBox1.setColor(QColor(255, 0, 255, 128))
    colorBox2.setColor(QColor(64, 96, 222, 128))
    colorBox2.setUseAlpha(False)
    colorBox1.colorChanged.connect(colorBox2.setColor)

    window = QWidget()
    leftLayout = QFormLayout()
    leftLayout.addRow("Color box 1:", colorBox1)
    leftLayout.addRow("Color box 2:", colorBox2)

    # Box 2's own settings only.
    enabledCheck = QCheckBox("Enabled")
    enabledCheck.setChecked(colorBox2.isEnabled())
    enabledCheck.toggled.connect(colorBox2.setEnabled)

    alphaCheck = QCheckBox("Use alpha")
    alphaCheck.setChecked(colorBox2.useAlpha())
    alphaCheck.toggled.connect(colorBox2.setUseAlpha)

    eyedropperCombo = QComboBox()
    eyedropperCombo.setToolTip("Click the eyedropper, or press it, drag to a colour and release.")
    for button in QColorBox.EyedropperButton:
        eyedropperCombo.addItem(button.name, button)
    eyedropperCombo.setCurrentIndex(eyedropperCombo.findData(colorBox2.eyedropperButton()))

    def setEyedropperButton(_: int) -> None:
        colorBox2.setEyedropperButton(eyedropperCombo.currentData())
    eyedropperCombo.currentIndexChanged.connect(setEyedropperButton)
    pickButton = QPushButton("Pick a screen colour (pickScreenColor)")
    pickButton.clicked.connect(colorBox2.pickScreenColor)

    alphaSlider = QSlider(Qt.Orientation.Horizontal)
    alphaSlider.setRange(0, 255)
    alphaSlider.valueChanged.connect(lambda value: colorBox2.setColor(_withAlpha(colorBox2.color(), value)))
    alphaCheck.toggled.connect(alphaSlider.setEnabled)

    colorLabel = QLabel()

    def syncBox2Info(color: QColor) -> None:
        """Garde le curseur et l'étiquette synchronisés avec la couleur de la
        boîte 2 (aussi modifiée par la boîte 1 ou le sélecteur)."""
        alphaSlider.blockSignals(True)
        alphaSlider.setValue(color.alpha())
        alphaSlider.blockSignals(False)
        colorLabel.setText(color.name(QColor.NameFormat.HexArgb))

    colorBox2.colorChanged.connect(syncBox2Info)
    syncBox2Info(colorBox2.color())

    leftLayout.addRow("Box 2:", enabledCheck)
    leftLayout.addRow("", alphaCheck)
    leftLayout.addRow("Box 2 eyedropper:", eyedropperCombo)
    leftLayout.addRow("", pickButton)
    leftLayout.addRow("Box 2 alpha:", alphaSlider)
    leftLayout.addRow("Box 2 color:", colorLabel)

    mainLayout = QHBoxLayout(window)
    mainLayout.addLayout(leftLayout)
    mainLayout.addWidget(QColorBox())

    window.setWindowTitle("QColorBox Demo")
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
