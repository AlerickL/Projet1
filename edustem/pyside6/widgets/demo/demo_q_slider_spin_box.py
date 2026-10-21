"""Démo : `QSliderSpinBox` et `QRealSliderSpinBox` dans une même fenêtre, avec chaque
réglage public exposé à côté, l'état du widget choisi et le journal de leurs signaux.
"""

from __future__ import annotations

import sys
import warnings
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from ..q_slider_spin_box import QRealSliderSpinBox, QSliderSpinBox

type Box = QSliderSpinBox | QRealSliderSpinBox


def main() -> int:
    app = QApplication(sys.argv)

    intBox = QSliderSpinBox()
    realBox = QRealSliderSpinBox()
    boxes: list[tuple[str, Box]] = [("int", intBox), ("real", realBox)]

    # -- Displays ------------------------------------------------------------
    stateLabels: dict[str, QLabel] = {key: QLabel() for key in ("value", "range", "steps", "ticks", "flags")}
    log = QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumBlockCount(300)
    errorLabel = QLabel()
    errorLabel.setStyleSheet("color: firebrick;")
    errorLabel.setWordWrap(True)

    # -- Configuration widgets ------------------------------------------------
    targetCombo = QComboBox()
    for name, box in boxes:
        targetCombo.addItem(f"{type(box).__name__} ({name})", box)

    def target() -> Box:
        return targetCombo.currentData()

    def newSpin(low: float = -1e9) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(low, 1e9)
        spin.setKeyboardTracking(False)
        return spin

    minSpin, maxSpin, valueSpin = newSpin(), newSpin(), newSpin()
    singleStepSpin, pageStepSpin, tickIntervalSpin = newSpin(), newSpin(1e-9), newSpin(0.0)
    tickIntervalSpin.setSpecialValueText("0 (automatic)")
    numberSpins: tuple[QDoubleSpinBox, ...] = (minSpin, maxSpin, valueSpin, singleStepSpin, pageStepSpin, tickIntervalSpin)
    decimalsSpin = QSpinBox()
    decimalsSpin.setRange(0, 15)

    prefixEdit, suffixEdit, specialEdit = QLineEdit(), QLineEdit(), QLineEdit()
    textEdits: tuple[QLineEdit, ...] = (prefixEdit, suffixEdit, specialEdit)

    orientationCombo = QComboBox()
    orientationCombo.addItem("Horizontal", Qt.Orientation.Horizontal)
    orientationCombo.addItem("Vertical", Qt.Orientation.Vertical)
    tickPositionCombo = QComboBox()
    for position in QSlider.TickPosition:
        tickPositionCombo.addItem(position.name, position)

    trackingCheck = QCheckBox("Tracking (value follows the drag and each typed key)")
    wrappingCheck = QCheckBox("Wrapping (spin box arrows go from one bound to the other)")
    enabledCheck = QCheckBox("Enabled")

    # -- Refreshing ----------------------------------------------------------
    def refreshState() -> None:
        b = target()
        stateLabels["value"].setText(f"{b.value():.15g}")
        stateLabels["range"].setText(f"[{b.minimum():.15g}, {b.maximum():.15g}]")
        extra = f"   /   decimals() = {b.decimals()}, resolution() = {b.resolution():.15g}" if isinstance(b, QRealSliderSpinBox) else ""
        stateLabels["steps"].setText(f"single {b.singleStep():.15g},  page {b.pageStep():.15g}{extra}")
        stateLabels["ticks"].setText(f"{b.tickPosition().name},  tickInterval() = {b.tickInterval():.15g}")
        stateLabels["flags"].setText(f"hasTracking() = {b.hasTracking()},  wrapping() = {b.wrapping()},  "
                                     f"isEnabled() = {b.isEnabled()}")

    def refreshControls() -> None:
        """Brings the configuration widgets back in step with the target (after a rounding, a clamping...)."""
        b = target()
        isReal = isinstance(b, QRealSliderSpinBox)
        widgets: tuple[QWidget, ...] = (*numberSpins, decimalsSpin, *textEdits, orientationCombo, tickPositionCombo,
                                        trackingCheck, wrappingCheck, enabledCheck)
        for w in widgets:
            w.blockSignals(True)
        decimals = b.decimals() if isinstance(b, QRealSliderSpinBox) else 0
        for spin in numberSpins:
            spin.setDecimals(decimals)
            spin.setSingleStep(10 ** -decimals)
        decimalsSpin.setEnabled(isReal)
        decimalsSpin.setValue(decimals)
        minSpin.setValue(b.minimum())
        maxSpin.setValue(b.maximum())
        valueSpin.setValue(b.value())
        singleStepSpin.setValue(b.singleStep())
        pageStepSpin.setValue(b.pageStep())
        tickIntervalSpin.setValue(b.tickInterval())
        prefixEdit.setText(b.prefix())
        suffixEdit.setText(b.suffix())
        specialEdit.setText(b.specialValueText())
        orientationCombo.setCurrentIndex(orientationCombo.findData(b.orientation()))
        tickPositionCombo.setCurrentIndex(tickPositionCombo.findData(b.tickPosition()))
        trackingCheck.setChecked(b.hasTracking())
        wrappingCheck.setChecked(b.wrapping())
        enabledCheck.setChecked(b.isEnabled())
        for w in widgets:
            w.blockSignals(False)
        refreshState()

    def number(v: float) -> float:
        """The value in the target's own kind of number."""
        return round(v) if isinstance(target(), QSliderSpinBox) else v

    def attempt(action: Callable[[Box], object]) -> Callable[[], None]:
        """Runs a change on the target, showing the error if it is rejected, then refreshes the interface."""
        def run() -> None:
            errorLabel.clear()
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)   # PySide6 warns before an OverflowError
                    action(target())
            except (ValueError, TypeError, OverflowError) as error:
                errorLabel.setText(f"Rejected ({type(error).__name__}): {error}")
            refreshControls()
        return run

    # -- Signals of the boxes: log ---------------------------------------------
    def logLine(name: str, text: str) -> None:
        log.appendPlainText(f"{name:5} {text}")

    def connectBox(name: str, box: Box) -> None:
        box.valueChanged.connect(lambda v: (logLine(name, f"valueChanged({v:.15g})"), refreshControls()))
        box.rangeChanged.connect(lambda lo, hi: logLine(name, f"rangeChanged({lo:.15g}, {hi:.15g})"))
        box.editingFinished.connect(lambda: logLine(name, "editingFinished()"))
        if isinstance(box, QRealSliderSpinBox):
            box.decimalsChanged.connect(lambda d: logLine(name, f"decimalsChanged({d})"))

    for name, box in boxes:
        connectBox(name, box)

    # -- Configuration -> target ----------------------------------------------
    targetCombo.currentIndexChanged.connect(lambda _: (errorLabel.clear(), refreshControls()))
    minSpin.valueChanged.connect(lambda v: attempt(lambda b: b.setMinimum(number(v)))())
    maxSpin.valueChanged.connect(lambda v: attempt(lambda b: b.setMaximum(number(v)))())
    valueSpin.valueChanged.connect(lambda v: attempt(lambda b: b.setValue(number(v)))())
    singleStepSpin.valueChanged.connect(lambda v: attempt(lambda b: b.setSingleStep(number(v)))())
    pageStepSpin.valueChanged.connect(lambda v: attempt(lambda b: b.setPageStep(number(v)))())
    tickIntervalSpin.valueChanged.connect(lambda v: attempt(lambda b: b.setTickInterval(number(v)))())
    decimalsSpin.valueChanged.connect(
        lambda d: attempt(lambda b: b.setDecimals(d) if isinstance(b, QRealSliderSpinBox) else None)())
    prefixEdit.textEdited.connect(lambda t: attempt(lambda b: b.setPrefix(t))())
    suffixEdit.textEdited.connect(lambda t: attempt(lambda b: b.setSuffix(t))())
    specialEdit.textEdited.connect(lambda t: attempt(lambda b: b.setSpecialValueText(t))())
    orientationCombo.currentIndexChanged.connect(
        lambda _: attempt(lambda b: b.setOrientation(orientationCombo.currentData()))())
    tickPositionCombo.currentIndexChanged.connect(
        lambda _: attempt(lambda b: b.setTickPosition(tickPositionCombo.currentData()))())
    trackingCheck.toggled.connect(lambda on: attempt(lambda b: b.setTracking(on))())
    wrappingCheck.toggled.connect(lambda on: attempt(lambda b: b.setWrapping(on))())
    enabledCheck.toggled.connect(lambda on: attempt(lambda b: b.setEnabled(on))())

    # -- Scenarios -------------------------------------------------------------
    def presetButton(text: str, action: Callable[[Box], object]) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(attempt(action))
        return button

    def angle(b: Box) -> None:
        b.setRange(0, 360)
        b.setSuffix(" °")
        b.setWrapping(True)
        b.setTickPosition(QSlider.TickPosition.TicksBelow)
        b.setTickInterval(45)

    def percentage(b: Box) -> None:
        b.setRange(0, 100)
        b.setSuffix(" %")
        b.setSpecialValueText("Off")

    def clearTexts(b: Box) -> None:
        b.setPrefix("")
        b.setSuffix("")
        b.setSpecialValueText("")

    scenarios: list[QPushButton] = [
        presetButton("Angle: [0, 360] °, wrapping, a tick every 45", angle),
        presetButton("Percentage: [0, 100] %, \"Off\" at the minimum", percentage),
        presetButton("Clear prefix, suffix and special text", clearTexts),
        presetButton("Range [8, 2] (max below min)", lambda b: b.setRange(number(8), number(2))),
        presetButton("Value 2.675 (the float is 2.67499...)", lambda b: b.setValue(number(2.675))),
        presetButton("Value NaN (rejected: ValueError in real, OverflowError in int)", lambda b: b.setValue(float("nan"))),
        presetButton("Range [0, 1e12] (rejected: too many steps, or beyond a C++ int)", lambda b: b.setRange(number(0), number(1e12))),
        presetButton("Clear log", lambda _: log.clear()),
    ]

    # -- Layout --------------------------------------------------------------
    stage = QVBoxLayout()
    for name, box in boxes:
        group = QGroupBox(f"{type(box).__name__} ({name})")
        QVBoxLayout(group).addWidget(box)
        stage.addWidget(group)
    stage.addStretch(1)
    stageBox = QGroupBox("Widgets")
    stageBox.setLayout(stage)

    stateBox = QGroupBox("State (read from the target)")
    stateLayout = QFormLayout(stateBox)
    for label, key in (("value():", "value"), ("Range:", "range"), ("Steps:", "steps"), ("Ticks:", "ticks"),
                       ("Flags:", "flags")):
        stateLayout.addRow(label, stateLabels[key])

    configBox = QGroupBox("Configuration (applied to the target)")
    configLayout = QFormLayout(configBox)
    configLayout.addRow("target:", targetCombo)
    configLayout.addRow("minimum:", minSpin)
    configLayout.addRow("maximum:", maxSpin)
    configLayout.addRow("value:", valueSpin)
    configLayout.addRow("singleStep:", singleStepSpin)
    configLayout.addRow("pageStep:", pageStepSpin)
    configLayout.addRow("decimals (real):", decimalsSpin)
    configLayout.addRow("prefix:", prefixEdit)
    configLayout.addRow("suffix:", suffixEdit)
    configLayout.addRow("specialValueText:", specialEdit)
    configLayout.addRow("orientation:", orientationCombo)
    configLayout.addRow("tickPosition:", tickPositionCombo)
    configLayout.addRow("tickInterval:", tickIntervalSpin)
    for check in (trackingCheck, wrappingCheck, enabledCheck):
        configLayout.addRow(check)
    configLayout.addRow(errorLabel)

    scenariosBox = QGroupBox("Scenarios (applied to the target)")
    scenariosLayout = QVBoxLayout(scenariosBox)
    for button in scenarios:
        scenariosLayout.addWidget(button)

    leftColumn = QVBoxLayout()
    leftColumn.addWidget(stageBox, 2)
    leftColumn.addWidget(stateBox)
    leftColumn.addWidget(QLabel("Log:"))
    leftColumn.addWidget(log, 1)

    rightColumn = QVBoxLayout()
    rightColumn.addWidget(configBox)
    rightColumn.addWidget(scenariosBox)
    rightColumn.addStretch(1)

    mainWindow = QWidget()
    mainLayout = QHBoxLayout(mainWindow)
    mainLayout.addLayout(leftColumn, 3)
    mainLayout.addLayout(rightColumn, 2)

    refreshControls()
    mainWindow.setWindowTitle("QSliderSpinBox / QRealSliderSpinBox Demo")
    mainWindow.resize(1000, 760)
    mainWindow.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
