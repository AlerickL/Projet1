"""Démo : `QRangeSlider` et `QRealRangeSlider` côte à côte, avec chaque réglage exposé à côté.

Les réglages communs s'appliquent aux deux curseurs. Les valeurs tapées sont exprimées dans
l'unité du curseur réel ; le curseur entier les reçoit multipliées par cent.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QBoxLayout, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QSlider, QSpinBox, QStyleFactory, QVBoxLayout, QWidget,
)

from ..q_range_slider import QAbstractRangeSlider, QRangeSlider, QRealRangeSlider

_IntegerScale = 100     # the integer slider shows the real one's values, in hundredths


def main() -> int:
    app = QApplication(sys.argv)
    Handle, Mode = QAbstractRangeSlider.Handle, QAbstractRangeSlider.CollisionMode

    integer = QRangeSlider()
    integer.setLimits(0, _IntegerScale)
    integer.setRange(20, 60)
    real = QRealRangeSlider()
    real.setRange(0.2, 0.6)
    sliders: tuple[QRangeSlider, QRealRangeSlider] = (integer, real)

    # -- Displays ------------------------------------------------------------
    stateLabels: dict[str, QLabel] = {key: QLabel(wordWrap=True) for key in (
        "integer", "real", "positions", "steps", "handles")}
    log = QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumBlockCount(300)
    errorLabel = QLabel()
    errorLabel.setStyleSheet("color: firebrick;")
    errorLabel.setWordWrap(True)

    # -- Configuration widgets ------------------------------------------------
    def newSpin() -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(-1e6, 1e6)
        spin.setSingleStep(0.05)
        spin.setKeyboardTracking(False)
        return spin

    minimumSpin, maximumSpin, lowerSpin, upperSpin = newSpin(), newSpin(), newSpin(), newSpin()
    singleStepSpin, pageStepSpin, tickIntervalSpin = newSpin(), newSpin(), newSpin()
    valueSpins: tuple[QDoubleSpinBox, ...] = (minimumSpin, maximumSpin, lowerSpin, upperSpin, singleStepSpin,
                                              pageStepSpin, tickIntervalSpin)
    decimalsSpin = QSpinBox()
    decimalsSpin.setRange(0, 15)

    def combo(items: list[tuple[str, object]]) -> QComboBox:
        box = QComboBox()
        for text, data in items:
            box.addItem(text, data)
        return box

    orientationCombo = combo([(o.name, o) for o in Qt.Orientation])
    tickPositionCombo = combo([(p.name, p) for p in QSlider.TickPosition])
    collisionCombo = combo([(m.name, m) for m in Mode])
    currentCombo = combo([(h.name, h) for h in (Handle.Lower, Handle.Upper, Handle.Both)])
    styleCombo = combo([(name, name) for name in QStyleFactory.keys()])
    styleCombo.setCurrentIndex(styleCombo.findText(app.style().objectName(), Qt.MatchFlag.MatchFixedString))

    overlapCheck = QCheckBox("Overlap allowed (the bounds may be equal)")
    overlapCheck.setChecked(True)
    trackingCheck = QCheckBox("Tracking (values follow the drag)")
    trackingCheck.setChecked(True)
    invertedAppearanceCheck = QCheckBox("Inverted appearance")
    invertedControlsCheck = QCheckBox("Inverted controls")
    rightToLeftCheck = QCheckBox("Right-to-left layout")
    enabledCheck = QCheckBox("Enabled")
    enabledCheck.setChecked(True)

    # -- Refreshing ----------------------------------------------------------
    def refreshState() -> None:
        stateLabels["integer"].setText(f"limits {integer.limits()}   range {integer.range()}   text() = {integer.text()!r}")
        stateLabels["real"].setText(
            f"limits {real.limits()}   range {real.range()}   decimals() = {real.decimals()}   "
            f"resolution() = {real.resolution():.15g}   stepCount() = {real.stepCount()}   text() = {real.text()!r}")
        stateLabels["positions"].setText(
            f"integer ({integer.lowerSliderPosition()}, {integer.upperSliderPosition()})   "
            f"real ({real.lowerSliderPosition():.15g}, {real.upperSliderPosition():.15g})")
        stateLabels["steps"].setText(
            f"integer single {integer.singleStep()}, page {integer.pageStep()}, tick {integer.tickInterval()}   "
            f"real single {real.singleStep():.15g}, page {real.pageStep():.15g}, tick {real.tickInterval():.15g}")
        stateLabels["handles"].setText(
            f"integer current {integer.currentHandle().name}, pressed {integer.pressedHandle().name}   "
            f"real current {real.currentHandle().name}, pressed {real.pressedHandle().name}")

    def refreshControls() -> None:
        """Brings the configuration widgets back in step with the real slider (after a rounding, a clamping...)."""
        widgets: tuple[QWidget, ...] = (decimalsSpin, currentCombo, *valueSpins)
        for w in widgets:
            w.blockSignals(True)
        decimalsSpin.setValue(real.decimals())
        for spin in valueSpins:
            spin.setDecimals(max(2, real.decimals()))
        minimumSpin.setValue(real.minimum())
        maximumSpin.setValue(real.maximum())
        lowerSpin.setValue(real.lowerValue())
        upperSpin.setValue(real.upperValue())
        singleStepSpin.setValue(real.singleStep())
        pageStepSpin.setValue(real.pageStep())
        tickIntervalSpin.setValue(real.tickInterval())
        currentCombo.setCurrentIndex(currentCombo.findData(real.currentHandle()))
        for w in widgets:
            w.blockSignals(False)
        refreshState()

    def attempt(action: Callable[[], object]) -> None:
        """Runs a change, showing the error if a slider rejects it, then refreshes the interface."""
        errorLabel.clear()
        try:
            action()
        except (ValueError, TypeError) as error:
            errorLabel.setText(f"Rejected: {error}")
        refreshControls()

    def scaled(v: float) -> int:
        return round(v * _IntegerScale)

    def forBoth(method: Callable[[QRangeSlider | QRealRangeSlider], object]) -> Callable[[], None]:
        def run() -> None:
            for slider in sliders:
                method(slider)
        return run

    def forEach(onInteger: Callable[[], object], onReal: Callable[[], object]) -> Callable[[], None]:
        return lambda: (onReal(), onInteger(), None)[2]

    # -- Signals of the sliders: log ------------------------------------------
    def logLine(name: str, text: str) -> None:
        log.appendPlainText(f"{name:8} {text}")

    def connectSlider(name: str, slider: QRangeSlider | QRealRangeSlider) -> None:
        slider.lowerValueChanged.connect(lambda v: logLine(name, f"lowerValueChanged({v:.15g})"))
        slider.upperValueChanged.connect(lambda v: logLine(name, f"upperValueChanged({v:.15g})"))
        slider.rangeChanged.connect(lambda lo, up: (logLine(name, f"rangeChanged({lo:.15g}, {up:.15g})"), refreshControls()))
        slider.limitsChanged.connect(lambda lo, hi: (logLine(name, f"limitsChanged({lo:.15g}, {hi:.15g})"), refreshControls()))
        slider.sliderMoved.connect(lambda lo, up: (logLine(name, f"sliderMoved({lo:.15g}, {up:.15g})"), refreshState()))
        slider.sliderPressed.connect(lambda h: (logLine(name, f"sliderPressed({h.name})"), refreshControls()))
        slider.sliderReleased.connect(lambda h: (logLine(name, f"sliderReleased({h.name})"), refreshState()))

    connectSlider("integer", integer)
    connectSlider("real", real)
    real.decimalsChanged.connect(lambda d: logLine("real", f"decimalsChanged({d})"))

    # -- Configuration -> sliders ---------------------------------------------
    decimalsSpin.valueChanged.connect(lambda d: attempt(lambda: real.setDecimals(d)))
    minimumSpin.valueChanged.connect(lambda v: attempt(forEach(lambda: integer.setMinimum(scaled(v)), lambda: real.setMinimum(v))))
    maximumSpin.valueChanged.connect(lambda v: attempt(forEach(lambda: integer.setMaximum(scaled(v)), lambda: real.setMaximum(v))))
    lowerSpin.valueChanged.connect(lambda v: attempt(forEach(lambda: integer.setLowerValue(scaled(v)), lambda: real.setLowerValue(v))))
    upperSpin.valueChanged.connect(lambda v: attempt(forEach(lambda: integer.setUpperValue(scaled(v)), lambda: real.setUpperValue(v))))
    singleStepSpin.valueChanged.connect(lambda v: attempt(forEach(lambda: integer.setSingleStep(scaled(v)), lambda: real.setSingleStep(v))))
    pageStepSpin.valueChanged.connect(lambda v: attempt(forEach(lambda: integer.setPageStep(scaled(v)), lambda: real.setPageStep(v))))
    tickIntervalSpin.valueChanged.connect(lambda v: attempt(forEach(lambda: integer.setTickInterval(scaled(v)), lambda: real.setTickInterval(v))))

    tickPositionCombo.currentIndexChanged.connect(lambda _: forBoth(lambda s: s.setTickPosition(tickPositionCombo.currentData()))())
    collisionCombo.currentIndexChanged.connect(lambda _: forBoth(lambda s: s.setCollisionMode(collisionCombo.currentData()))())
    currentCombo.currentIndexChanged.connect(lambda _: (forBoth(lambda s: s.setCurrentHandle(currentCombo.currentData()))(), refreshState()))
    overlapCheck.toggled.connect(lambda on: attempt(forBoth(lambda s: s.setOverlapAllowed(on))))
    trackingCheck.toggled.connect(lambda on: forBoth(lambda s: s.setTracking(on))())
    invertedAppearanceCheck.toggled.connect(lambda on: forBoth(lambda s: s.setInvertedAppearance(on))())
    invertedControlsCheck.toggled.connect(lambda on: forBoth(lambda s: s.setInvertedControls(on))())
    enabledCheck.toggled.connect(lambda on: forBoth(lambda s: s.setEnabled(on))())
    rightToLeftCheck.toggled.connect(lambda on: forBoth(lambda s: s.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft if on else Qt.LayoutDirection.LeftToRight))())

    def setStyle() -> None:
        for slider in sliders:
            slider.setStyle(QStyleFactory.create(styleCombo.currentData()))   # one instance each: the slider does not own it
            slider.updateGeometry()
    styleCombo.currentIndexChanged.connect(lambda _: setStyle())

    stage = QBoxLayout(QBoxLayout.Direction.TopToBottom)

    def setOrientation() -> None:
        orientation: Qt.Orientation = orientationCombo.currentData()
        for slider in sliders:
            slider.setOrientation(orientation)
        stage.setDirection(QBoxLayout.Direction.TopToBottom if orientation == Qt.Orientation.Horizontal
                           else QBoxLayout.Direction.LeftToRight)
    orientationCombo.currentIndexChanged.connect(lambda _: setOrientation())

    def presetButton(text: str, action: Callable[[], object]) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(lambda: attempt(action))
        return button

    def setLimits(lo: float, hi: float) -> Callable[[], None]:
        return forEach(lambda: integer.setLimits(scaled(lo), scaled(hi)), lambda: real.setLimits(lo, hi))

    def setRange(lo: float, up: float) -> Callable[[], None]:
        return forEach(lambda: integer.setRange(scaled(lo), scaled(up)), lambda: real.setRange(lo, up))

    scenarios: list[QPushButton] = [
        presetButton("Limits [0, 1]", setLimits(0.0, 1.0)),
        presetButton("Limits [-10, 10]", setLimits(-10.0, 10.0)),
        presetButton("Limits [2, 2] (zero width)", setLimits(2.0, 2.0)),
        presetButton("Limits [5, 2] (maximum below minimum)", setLimits(5.0, 2.0)),
        presetButton("Limits [0, 1e12] (too many steps)", setLimits(0.0, 1e12)),
        presetButton("Range (0.8, 0.3) (sorted)", setRange(0.8, 0.3)),
        presetButton("Range (0.5, 0.5) (equal bounds)", setRange(0.5, 0.5)),
        presetButton("Range = limits", lambda: forBoth(lambda s: s.setRange(*s.limits()))()),
        presetButton("Lower value above the upper one (blocks or pushes)",
                     forEach(lambda: integer.setLowerValue(integer.upperValue() + 10),
                             lambda: real.setLowerValue(real.upperValue() + 0.1))),
        presetButton("Lower value 0.2675 (real: rounded like QDoubleSpinBox)",
                     forEach(lambda: integer.setLowerValue(27), lambda: real.setLowerValue(0.2675))),
        presetButton("Lower value NaN (real: rejected)", lambda: real.setLowerValue(float("nan"))),
        presetButton("Clear log", log.clear),
    ]

    # -- Layout --------------------------------------------------------------
    for title, slider in (("QRangeSlider (hundredths)", integer), ("QRealRangeSlider", real)):
        box = QGroupBox(title)
        QVBoxLayout(box).addWidget(slider)
        stage.addWidget(box)
    reference = QSlider(Qt.Orientation.Horizontal)
    reference.setValue(40)
    referenceBox = QGroupBox("QSlider (reference for the appearance)")
    QVBoxLayout(referenceBox).addWidget(reference)
    stageBox = QGroupBox("Sliders")
    stageBox.setLayout(stage)

    stateBox = QGroupBox("State")
    stateLayout = QFormLayout(stateBox)
    for label, stateKey in (("QRangeSlider:", "integer"), ("QRealRangeSlider:", "real"), ("Slider positions:", "positions"),
                            ("Steps:", "steps"), ("Handles:", "handles")):
        stateLayout.addRow(label, stateLabels[stateKey])

    configBox = QGroupBox("Configuration (in the real slider's unit, applied to both)")
    configLayout = QFormLayout(configBox)
    configLayout.addRow("minimum:", minimumSpin)
    configLayout.addRow("maximum:", maximumSpin)
    configLayout.addRow("lowerValue:", lowerSpin)
    configLayout.addRow("upperValue:", upperSpin)
    configLayout.addRow("decimals (real):", decimalsSpin)
    configLayout.addRow("singleStep:", singleStepSpin)
    configLayout.addRow("pageStep:", pageStepSpin)
    configLayout.addRow("tickInterval:", tickIntervalSpin)
    configLayout.addRow("tickPosition:", tickPositionCombo)
    configLayout.addRow("collisionMode:", collisionCombo)
    configLayout.addRow("currentHandle:", currentCombo)
    configLayout.addRow("orientation:", orientationCombo)
    configLayout.addRow("style:", styleCombo)
    for check in (overlapCheck, trackingCheck, invertedAppearanceCheck, invertedControlsCheck, rightToLeftCheck,
                  enabledCheck):
        configLayout.addRow(check)
    configLayout.addRow(errorLabel)

    scenariosBox = QGroupBox("Scenarios")
    scenariosLayout = QVBoxLayout(scenariosBox)
    for button in scenarios:
        scenariosLayout.addWidget(button)

    hint = QLabel("Drag a handle, or the segment between the two. Keyboard: arrows, Page Up, Page Down, Home, "
                  "End; Space picks the next handle (lower, upper, both).")
    hint.setWordWrap(True)

    leftColumn = QVBoxLayout()
    leftColumn.addWidget(stageBox, 2)
    leftColumn.addWidget(referenceBox)
    leftColumn.addWidget(hint)
    leftColumn.addWidget(stateBox)
    leftColumn.addWidget(QLabel("Log:"))
    leftColumn.addWidget(log, 1)

    # Two side columns rather than one: stacked, they would be taller than a laptop screen.
    sideColumns: list[QVBoxLayout] = []
    for box in (configBox, scenariosBox):
        column = QVBoxLayout()
        column.addWidget(box)
        column.addStretch(1)
        sideColumns.append(column)

    mainWindow = QWidget()
    mainLayout = QHBoxLayout(mainWindow)
    mainLayout.addLayout(leftColumn, 3)
    for column in sideColumns:
        mainLayout.addLayout(column, 1)

    refreshControls()
    mainWindow.setWindowTitle("QRangeSlider / QRealRangeSlider Demo")
    mainWindow.resize(1300, 760)
    mainWindow.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
