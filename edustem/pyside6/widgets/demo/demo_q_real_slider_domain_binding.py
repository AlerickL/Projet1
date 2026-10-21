"""Démo : `QRealSliderDomainBinding`, un `QDomainExplorerBox` qui pilote un contrôle réel
(`QRealSlider`, `QRealScrollBar` ou `QRealDial`).

Le domaine compte une position par pas du contrôle (`resolution()`) : changer la plage ou les
décimales change sa taille, que l'explorateur relit à chaque usage.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from ..q_domain_explorer_box import QDomainExplorerBox
from ..q_real_slider import QRealControl, QRealDial, QRealScrollBar, QRealSlider
from ..q_real_slider_domain_binding import QRealSliderDomainBinding


def main() -> int:
    app = QApplication(sys.argv)

    controls: list[QRealControl] = [QRealSlider(Qt.Orientation.Horizontal), QRealScrollBar(Qt.Orientation.Horizontal),
                                    QRealDial()]
    stack = QStackedWidget()
    for control in controls:
        control.setDecimals(1)
        control.setRange(-5.0, 5.0)
        stack.addWidget(control)

    explorer = QDomainExplorerBox()
    stateLabel = QLabel()
    stateLabel.setWordWrap(True)
    errorLabel = QLabel()
    errorLabel.setStyleSheet("color: firebrick;")
    errorLabel.setWordWrap(True)
    log = QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumBlockCount(300)

    controlCombo = QComboBox()
    for control in controls:
        controlCombo.addItem(type(control).__name__)

    def newSpin() -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(-1e6, 1e6)
        spin.setDecimals(3)
        spin.setKeyboardTracking(False)
        return spin

    minSpin, maxSpin, defaultSpin = newSpin(), newSpin(), newSpin()
    minSpin.setValue(-5.0)
    maxSpin.setValue(5.0)
    defaultSpin.setValue(1.25)
    decimalsSpin = QSpinBox()
    decimalsSpin.setRange(0, 6)
    decimalsSpin.setValue(1)
    setDefaultButton = QPushButton("setDefaultValue")
    unsetDefaultButton = QPushButton("unsetDefaultValue")

    def current() -> QRealControl:
        return controls[controlCombo.currentIndex()]

    def binding() -> QRealSliderDomainBinding:
        bound = explorer.binding()
        assert isinstance(bound, QRealSliderDomainBinding)
        return bound

    def refreshState() -> None:
        c, b = current(), binding()
        stateLabel.setText(
            f"value() = {c.value():.15g},  range [{c.minimum():.15g}, {c.maximum():.15g}],  "
            f"decimals() = {c.decimals()},  resolution() = {c.resolution():.15g}\n"
            f"binding: size() = {b.size()},  index() = {b.index()},  defaultValue() = {b.defaultValue():.15g},  "
            f"defaultIndex() = {b.defaultIndex()}")

    def attempt() -> None:
        """Applies the settings to the current control, showing the error if one is rejected."""
        errorLabel.clear()
        try:
            c = current()
            c.setDecimals(decimalsSpin.value())
            c.setRange(minSpin.value(), maxSpin.value())
        except (ValueError, TypeError) as error:
            errorLabel.setText(f"Rejected ({type(error).__name__}): {error}")
        refreshState()

    def attach(_: int) -> None:
        """Binds the explorer to the chosen control."""
        stack.setCurrentIndex(controlCombo.currentIndex())
        explorer.setBinding(QRealSliderDomainBinding(current()))
        attempt()

    def applyNumber(_: float) -> None:
        attempt()

    def applyDecimals(_: int) -> None:
        attempt()

    def setDefault() -> None:
        binding().setDefaultValue(defaultSpin.value())
        refreshState()

    def unsetDefault() -> None:
        binding().unsetDefaultValue()
        refreshState()

    for index, control in enumerate(controls):
        def logValue(value: float, name: str = type(control).__name__, position: int = index) -> None:
            log.appendPlainText(f"{name}.valueChanged({value:.15g})")
            if position == controlCombo.currentIndex():
                refreshState()
        control.valueChanged.connect(logValue)

    controlCombo.currentIndexChanged.connect(attach)
    for spin in (minSpin, maxSpin):
        spin.valueChanged.connect(applyNumber)
    decimalsSpin.valueChanged.connect(applyDecimals)
    setDefaultButton.clicked.connect(setDefault)
    unsetDefaultButton.clicked.connect(unsetDefault)

    stageBox = QGroupBox("Explorer and bound control")
    stage = QVBoxLayout(stageBox)
    stage.addWidget(explorer)
    stage.addWidget(stack)

    configBox = QGroupBox("Configuration")
    config = QFormLayout(configBox)
    config.addRow("control:", controlCombo)
    config.addRow("minimum:", minSpin)
    config.addRow("maximum:", maxSpin)
    config.addRow("decimals:", decimalsSpin)
    config.addRow("default value:", defaultSpin)
    defaultButtons = QHBoxLayout()
    defaultButtons.addWidget(setDefaultButton)
    defaultButtons.addWidget(unsetDefaultButton)
    config.addRow(defaultButtons)
    config.addRow(errorLabel)

    hint = QLabel("One position per step of the control: 101 positions on [-5, 5] at 1 decimal. Reset goes to the "
                  "default value (the first position while it is undefined); a default between two positions goes "
                  "to the value the control would retain.")
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
    mainWindow.setWindowTitle("QRealSliderDomainBinding Demo")
    mainWindow.resize(950, 600)
    mainWindow.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
