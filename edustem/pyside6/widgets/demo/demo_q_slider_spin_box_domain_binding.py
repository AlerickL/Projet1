"""Démo : `QSliderSpinBoxDomainBinding`, un `QDomainExplorerBox` qui pilote un curseur-boîte
numérique (`QSliderSpinBox` ou `QRealSliderSpinBox`).

Le domaine compte une position par valeur représentable : par entier, ou par pas de
10**-decimals en réel. Changer la plage ou les décimales change sa taille, que l'explorateur
relit à chaque usage.
"""

from __future__ import annotations

import sys
from typing import Any

from PySide6.QtWidgets import (
    QApplication, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from ..q_domain_explorer_box import QDomainExplorerBox
from ..q_slider_spin_box import QRealSliderSpinBox, QSliderSpinBox
from ..q_slider_spin_box_domain_binding import QSliderSpinBoxDomainBinding

type Box = QSliderSpinBox | QRealSliderSpinBox


def main() -> int:
    app = QApplication(sys.argv)

    intBox = QSliderSpinBox()
    intBox.setRange(-20, 20)
    realBox = QRealSliderSpinBox()
    realBox.setDecimals(1)
    realBox.setRange(-5.0, 5.0)
    realBox.setSuffix(" V")
    boxes: list[Box] = [intBox, realBox]
    stack = QStackedWidget()
    for box in boxes:
        stack.addWidget(box)

    explorer = QDomainExplorerBox()
    stateLabel = QLabel()
    stateLabel.setWordWrap(True)
    errorLabel = QLabel()
    errorLabel.setStyleSheet("color: firebrick;")
    errorLabel.setWordWrap(True)
    log = QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumBlockCount(300)

    boxCombo = QComboBox()
    for box in boxes:
        boxCombo.addItem(type(box).__name__)

    def newSpin() -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(-1e6, 1e6)
        spin.setDecimals(3)
        spin.setKeyboardTracking(False)
        return spin

    minSpin, maxSpin, defaultSpin = newSpin(), newSpin(), newSpin()
    defaultSpin.setValue(1.25)
    decimalsSpin = QSpinBox()
    decimalsSpin.setRange(0, 6)
    decimalsSpin.setValue(1)
    setDefaultButton = QPushButton("setDefaultValue")
    unsetDefaultButton = QPushButton("unsetDefaultValue")

    def current() -> Box:
        return boxes[boxCombo.currentIndex()]

    def binding() -> QSliderSpinBoxDomainBinding:
        bound = explorer.binding()
        assert isinstance(bound, QSliderSpinBoxDomainBinding)
        return bound

    def number(value: float) -> Any:
        """A value in the current box's own kind of number."""
        return round(value) if isinstance(current(), QSliderSpinBox) else value

    def refreshState() -> None:
        c, b = current(), binding()
        extra = f",  decimals() = {c.decimals()},  resolution() = {c.resolution():.15g}" if isinstance(c, QRealSliderSpinBox) else ""
        stateLabel.setText(
            f"value() = {c.value():.15g},  range [{c.minimum():.15g}, {c.maximum():.15g}]{extra}\n"
            f"binding: size() = {b.size()},  index() = {b.index()},  defaultValue() = {b.defaultValue():.15g},  "
            f"defaultIndex() = {b.defaultIndex()}")

    def attempt() -> None:
        """Applies the settings to the current box, showing the error if one is rejected."""
        errorLabel.clear()
        try:
            c = current()
            if isinstance(c, QRealSliderSpinBox):
                c.setDecimals(decimalsSpin.value())
            c.setRange(number(minSpin.value()), number(maxSpin.value()))
        except (ValueError, TypeError, OverflowError) as error:
            errorLabel.setText(f"Rejected ({type(error).__name__}): {error}")
        refreshState()

    def attach(_: int) -> None:
        """Binds the explorer to the chosen box, and shows its settings."""
        c = current()
        stack.setCurrentIndex(boxCombo.currentIndex())
        explorer.setBinding(QSliderSpinBoxDomainBinding(c))
        for spin in (minSpin, maxSpin):
            spin.blockSignals(True)
        minSpin.setValue(c.minimum())
        maxSpin.setValue(c.maximum())
        for spin in (minSpin, maxSpin):
            spin.blockSignals(False)
        decimalsSpin.setEnabled(isinstance(c, QRealSliderSpinBox))
        refreshState()

    def applyNumber(_: float) -> None:
        attempt()

    def applyDecimals(_: int) -> None:
        attempt()

    def setDefault() -> None:
        binding().setDefaultValue(number(defaultSpin.value()))
        refreshState()

    def unsetDefault() -> None:
        binding().unsetDefaultValue()
        refreshState()

    for index, box in enumerate(boxes):
        def logValue(value: float, name: str = type(box).__name__, position: int = index) -> None:
            log.appendPlainText(f"{name}.valueChanged({value:.15g})")
            if position == boxCombo.currentIndex():
                refreshState()
        box.valueChanged.connect(logValue)

    boxCombo.currentIndexChanged.connect(attach)
    for spin in (minSpin, maxSpin):
        spin.valueChanged.connect(applyNumber)
    decimalsSpin.valueChanged.connect(applyDecimals)
    setDefaultButton.clicked.connect(setDefault)
    unsetDefaultButton.clicked.connect(unsetDefault)

    stageBox = QGroupBox("Explorer and bound box")
    stage = QVBoxLayout(stageBox)
    stage.addWidget(explorer)
    stage.addWidget(stack)

    configBox = QGroupBox("Configuration")
    config = QFormLayout(configBox)
    config.addRow("box:", boxCombo)
    config.addRow("minimum:", minSpin)
    config.addRow("maximum:", maxSpin)
    config.addRow("decimals (real):", decimalsSpin)
    config.addRow("default value:", defaultSpin)
    defaultButtons = QHBoxLayout()
    defaultButtons.addWidget(setDefaultButton)
    defaultButtons.addWidget(unsetDefaultButton)
    config.addRow(defaultButtons)
    config.addRow(errorLabel)

    hint = QLabel("One position per representable value: 41 positions on [-20, 20] for the integer box, 101 on "
                  "[-5, 5] at 1 decimal for the real one. Each move is a single setValue: the box emits one "
                  "valueChanged and no editingFinished.")
    hint.setWordWrap(True)

    column = QVBoxLayout()
    column.addWidget(stageBox)
    column.addWidget(stateLabel)
    column.addWidget(hint)
    column.addWidget(QLabel("Log:"))
    column.addWidget(log, 1)

    side = QVBoxLayout()
    side.addWidget(configBox)
    side.addStretch(1)

    mainWindow = QWidget()
    mainLayout = QHBoxLayout(mainWindow)
    mainLayout.addLayout(column, 3)
    mainLayout.addLayout(side, 2)

    attach(0)
    mainWindow.setWindowTitle("QSliderSpinBoxDomainBinding Demo")
    mainWindow.resize(950, 560)
    mainWindow.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
