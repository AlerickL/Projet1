"""Démo : les trois contrôles réels (QRealSlider, QRealScrollBar, QRealDial)
dans une même fenêtre, avec chaque réglage du mixin exposé à côté.

Un réglage commun, l'espacement des repères, pilote à la fois les graduations du
curseur (`tickInterval`) et les crans du cadran (`notchSize`).
"""

from __future__ import annotations

import math
import random
import sys
from collections.abc import Callable
from typing import override

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QAbstractSlider, QApplication, QBoxLayout, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from ..q_real_slider import QRealControl, QRealDial, QRealScrollBar, QRealSlider, QRealSliderMixin


def main() -> int:
    app = QApplication(sys.argv)

    slider = QRealSlider(Qt.Orientation.Horizontal)
    slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    scrollBar = QRealScrollBar(Qt.Orientation.Horizontal)
    dial = QRealDial()
    dial.setNotchesVisible(True)
    controls: list[tuple[str, QRealControl]] = [("slider", slider), ("scrollBar", scrollBar), ("dial", dial)]
    allControls: list[QRealControl] = [control for _, control in controls]

    # -- Displays ------------------------------------------------------------
    stateLabels: dict[str, QLabel] = {key: QLabel() for key in (
        "value", "position", "range", "resolution", "steps", "marks", "down")}
    log = QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumBlockCount(300)
    errorLabel = QLabel()
    errorLabel.setStyleSheet("color: firebrick;")
    errorLabel.setWordWrap(True)

    # -- Configuration widgets ------------------------------------------------
    decimalsSpin = QSpinBox()
    decimalsSpin.setRange(0, 15)
    decimalsSpin.setValue(slider.decimals())

    def newSpin(low: float = -1e9, high: float = 1e9) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(low, high)
        spin.setKeyboardTracking(False)
        return spin

    minSpin, maxSpin, valueSpin, positionSpin = newSpin(), newSpin(), newSpin(), newSpin()
    singleStepSpin, pageStepSpin = newSpin(1e-9), newSpin(1e-9)
    valueSpins: tuple[QDoubleSpinBox, ...] = (minSpin, maxSpin, valueSpin, positionSpin, singleStepSpin, pageStepSpin)

    # Fixed decimals, not those of the controls: the slider remembers the requested spacing
    # across a change of decimals, and this spin box must keep showing that request.
    markSpacingSpin = newSpin(0.0)
    markSpacingSpin.setDecimals(6)
    markSpacingSpin.setSingleStep(0.01)
    markSpacingSpin.setSpecialValueText("0 (automatic)")
    markSpacingSpin.setValue(0.1)
    markSpacingLabel = QLabel("mark spacing:")
    markSpacingTip = (
        "Spacing between two marks, in value units (0: automatic).\n\n"
        "QRealSlider: tickInterval() / setTickInterval(float).\n"
        "  Qt draws a tick every tickInterval. tickPosition must show them.\n\n"
        "QRealDial: notchSize(), read only, a non-zero multiple of singleStep().\n"
        "  Qt derives it from notchTarget() / setNotchTarget(float), a target in pixels.\n"
        "  This demo converts the spacing to pixels for the dial's current size;\n"
        "  Qt then rounds it. notchesVisible must show them.")
    markSpacingSpin.setToolTip(markSpacingTip)
    markSpacingLabel.setToolTip(markSpacingTip)
    defaultNotchTarget: float = dial.notchTarget()

    tickPositionCombo = QComboBox()
    for position in QSlider.TickPosition:
        tickPositionCombo.addItem(position.name, position)
    tickPositionCombo.setCurrentIndex(tickPositionCombo.findData(slider.tickPosition()))

    orientationCombo = QComboBox()
    orientationCombo.addItem("Horizontal", Qt.Orientation.Horizontal)
    orientationCombo.addItem("Vertical", Qt.Orientation.Vertical)
    actionCombo = QComboBox()
    for action in QAbstractSlider.SliderAction:
        actionCombo.addItem(action.name, action)

    enabledCheck = QCheckBox("Enabled")
    enabledCheck.setChecked(True)
    trackingCheck = QCheckBox("Tracking (value follows the drag)")
    trackingCheck.setChecked(True)
    invertedAppearanceCheck = QCheckBox("Inverted appearance")
    invertedControlsCheck = QCheckBox("Inverted controls")
    wrappingCheck = QCheckBox("Dial wrapping")
    notchesCheck = QCheckBox("Dial notches visible")
    notchesCheck.setChecked(True)
    sliderDownCheck = QCheckBox("Slider down (slider only)")

    # -- Refreshing ----------------------------------------------------------
    def refreshState() -> None:
        s = slider
        stateLabels["value"].setText(f"{s.value():.15g}")
        stateLabels["position"].setText(f"{s.sliderPosition():.15g}")
        stateLabels["range"].setText(f"[{s.minimum():.15g}, {s.maximum():.15g}]")
        stateLabels["resolution"].setText(f"{s.resolution():.15g}   /   stepCount() = {s.stepCount()}   /   decimals() = {s.decimals()}")
        stateLabels["steps"].setText(f"single {s.singleStep():.15g},  page {s.pageStep():.15g}")
        interval = s.tickInterval()
        stateLabels["marks"].setText(
            f"slider tickInterval() = {interval:.15g}" + (" (automatic)" if interval == 0 else "")
            + f"   /   dial notchSize() = {dial.notchSize():.15g}   (notchTarget() = {dial.notchTarget():.3g} px)")
        stateLabels["down"].setText(str(s.isSliderDown()))

    def refreshControls() -> None:
        """Brings the configuration widgets back in step with the controls (after a rounding, a clamping...)."""
        widgets: tuple[QWidget, ...] = (decimalsSpin, *valueSpins)
        for w in widgets:
            w.blockSignals(True)
        decimalsSpin.setValue(slider.decimals())
        for spin in valueSpins:
            spin.setDecimals(slider.decimals())
            spin.setSingleStep(slider.resolution())
        minSpin.setValue(slider.minimum())
        maxSpin.setValue(slider.maximum())
        valueSpin.setValue(slider.value())
        positionSpin.setValue(slider.sliderPosition())
        singleStepSpin.setValue(slider.singleStep())
        pageStepSpin.setValue(slider.pageStep())
        for w in widgets:
            w.blockSignals(False)
        applyDialNotchTarget()                   # the range, the steps or the decimals may have changed
        refreshState()

    def dialPixelsPerSingleStep() -> int:
        """La longueur en pixels d'un pas simple sur l'arc du cadran, calculée comme `QDial::notchSize()`.

        Qt travaille en entiers internes et arrondit à chaque étape : l'arc couvre 5/6 du tour
        (6/6 avec le bouclage), puis Qt en déduit la part d'un pas de page, puis celle d'un pas
        simple, par division entière. Reproduire ces arrondis est ce qui rend la conversion
        exacte (vérifié contre Qt sur des milliers de cadrans aléatoires).
        """
        lo, hi = dial.baseFromValue(dial.minimum()), dial.baseFromValue(dial.maximum())
        page, single = dial.baseFromValue(dial.pageStep()), dial.baseFromValue(dial.singleStep())
        radius = min(dial.width(), dial.height()) / 2
        length = int(radius * (6 if dial.wrapping() else 5) * math.pi / 6 + 0.5)
        if hi > lo + page:
            length = int(length * page / (hi - lo) + 0.5)
        return max(1, length * single // page)

    def dialNotchTargetFor(spacing: float) -> float:
        """La cible en pixels qui donne au cadran, à sa taille actuelle, des crans espacés de `spacing`.

        Qt arrondit l'écart obtenu au multiple le plus proche du pas simple (au moins un pas).
        """
        if spacing == 0:
            return defaultNotchTarget
        return spacing / dial.singleStep() * dialPixelsPerSingleStep()

    def applyDialNotchTarget() -> None:
        dial.setNotchTarget(dialNotchTargetFor(markSpacingSpin.value()))

    def setMarkSpacing(spacing: float) -> None:
        slider.setTickInterval(spacing)
        applyDialNotchTarget()

    def attempt(action: Callable[[], object]) -> None:
        """Runs a change, showing the error if the mixin rejects it, then refreshes the interface."""
        errorLabel.clear()
        try:
            action()
        except (ValueError, TypeError) as error:
            errorLabel.setText(f"Rejected: {error}")
        refreshControls()

    def forAll(method: Callable[[QRealControl], object]) -> Callable[[], None]:
        def run() -> None:
            for control in allControls:
                method(control)
        return run

    # -- Signals of the controls: log, and value kept in step -----------------
    def logLine(name: str, text: str) -> None:
        log.appendPlainText(f"{name:9} {text}")

    def connectControl(name: str, control: QRealControl) -> None:
        def onValueChanged(v: float) -> None:
            logLine(name, f"valueChanged({v:.15g})")
            for other in allControls:
                if other is not control:
                    other.setValue(v)          # emits only if it changes: no feedback loop
            refreshControls()
        control.valueChanged.connect(onValueChanged)
        control.sliderMoved.connect(lambda v: (logLine(name, f"sliderMoved({v:.15g})"), refreshState()))
        control.rangeChanged.connect(lambda lo, hi: (logLine(name, f"rangeChanged({lo:.15g}, {hi:.15g})"), refreshControls()))
        control.decimalsChanged.connect(lambda d: logLine(name, f"decimalsChanged({d})"))
        control.sliderPressed.connect(lambda: (logLine(name, "sliderPressed()"), refreshState()))
        control.sliderReleased.connect(lambda: (logLine(name, "sliderReleased()"), refreshState()))
        control.actionTriggered.connect(lambda a: logLine(name, f"actionTriggered({a})"))

    for name, control in controls:
        connectControl(name, control)

    # -- Configuration -> controls --------------------------------------------
    decimalsSpin.valueChanged.connect(lambda d: attempt(forAll(lambda c: c.setDecimals(d))))
    minSpin.valueChanged.connect(lambda v: attempt(forAll(lambda c: c.setMinimum(v))))
    maxSpin.valueChanged.connect(lambda v: attempt(forAll(lambda c: c.setMaximum(v))))
    valueSpin.valueChanged.connect(lambda v: attempt(forAll(lambda c: c.setValue(v))))
    positionSpin.valueChanged.connect(lambda v: attempt(lambda: slider.setSliderPosition(v)))
    singleStepSpin.valueChanged.connect(lambda v: attempt(forAll(lambda c: c.setSingleStep(v))))
    pageStepSpin.valueChanged.connect(lambda v: attempt(forAll(lambda c: c.setPageStep(v))))
    markSpacingSpin.valueChanged.connect(lambda v: attempt(lambda: setMarkSpacing(v)))
    tickPositionCombo.currentIndexChanged.connect(lambda _: slider.setTickPosition(tickPositionCombo.currentData()))

    enabledCheck.toggled.connect(lambda on: forAll(lambda c: c.setEnabled(on))())
    trackingCheck.toggled.connect(lambda on: forAll(lambda c: c.setTracking(on))())
    invertedAppearanceCheck.toggled.connect(lambda on: forAll(lambda c: c.setInvertedAppearance(on))())
    invertedControlsCheck.toggled.connect(lambda on: forAll(lambda c: c.setInvertedControls(on))())
    wrappingCheck.toggled.connect(lambda on: (dial.setWrapping(on), applyDialNotchTarget(), refreshState()))
    _QResizeFollower(dial, lambda: (applyDialNotchTarget(), refreshState()))
    notchesCheck.toggled.connect(dial.setNotchesVisible)
    sliderDownCheck.toggled.connect(lambda on: (slider.setSliderDown(on), refreshState()))

    stage = QBoxLayout(QBoxLayout.Direction.TopToBottom)

    def setOrientation() -> None:
        orientation: Qt.Orientation = orientationCombo.currentData()
        slider.setOrientation(orientation)
        scrollBar.setOrientation(orientation)
        stage.setDirection(QBoxLayout.Direction.TopToBottom if orientation == Qt.Orientation.Horizontal
                           else QBoxLayout.Direction.LeftToRight)
    orientationCombo.currentIndexChanged.connect(lambda _: setOrientation())

    def triggerAction() -> None:
        slider.triggerAction(actionCombo.currentData())   # on the slider only: the others follow its value
        refreshControls()

    def presetButton(text: str, action: Callable[[], object]) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(lambda: attempt(action))
        return button

    def setRange(lo: float, hi: float) -> Callable[[], None]:
        return forAll(lambda c: c.setRange(lo, hi))

    def randomValue() -> None:
        v = random.uniform(slider.minimum(), slider.maximum())
        for c in allControls:
            c.setValue(v)

    triggerButton = QPushButton("triggerAction (slider)")
    triggerButton.clicked.connect(triggerAction)
    scenarios: list[QPushButton] = [
        presetButton("Range [0, 1]", setRange(0.0, 1.0)),
        presetButton("Range [-10, 10]", setRange(-10.0, 10.0)),
        presetButton("Range [0.1055, 1.0044] (rounded to the decimals)", setRange(0.1055, 1.0044)),
        presetButton("Range [2, 2] (degenerate)", setRange(2.0, 2.0)),
        presetButton("Range [5, 2] (max below min)", setRange(5.0, 2.0)),
        presetButton("Range [0, largest that fits the decimals]", lambda: setRange(0.0, QRealSliderMixin._IntMax * slider.resolution())()),
        presetButton("Range [0, twice that] (too many steps)", lambda: setRange(0.0, 2 * QRealSliderMixin._IntMax * slider.resolution())()),
        presetButton("Value 1/3 (rounded)", forAll(lambda c: c.setValue(1 / 3))),
        presetButton("Value 0.1255 (rounded to the decimals)", forAll(lambda c: c.setValue(0.1255))),
        presetButton("Value 0.285 (the float is 0.28499..., rounded like QDoubleSpinBox)", forAll(lambda c: c.setValue(0.285))),
        presetButton("Value NaN (rejected)", forAll(lambda c: c.setValue(float("nan")))),
        presetButton("Mark spacing 0.05 (then change the decimals: the slider keeps the request)",
                     lambda: markSpacingSpin.setValue(0.05)),
        presetButton("Mark spacing 0.001 (below one step: one step)", lambda: markSpacingSpin.setValue(0.001)),
        presetButton("Mark spacing 0 (automatic)", lambda: markSpacingSpin.setValue(0.0)),
        presetButton("Random value", randomValue),
        presetButton("Clear log", log.clear),
    ]

    # -- Layout --------------------------------------------------------------
    for title, control in (("QRealSlider", slider), ("QRealScrollBar", scrollBar), ("QRealDial", dial)):
        box = QGroupBox(title)
        QVBoxLayout(box).addWidget(control)
        stage.addWidget(box)
    stageBox = QGroupBox("Controls (kept in step through valueChanged)")
    stageBox.setLayout(stage)

    stateBox = QGroupBox("State (read from the slider)")
    stateLayout = QFormLayout(stateBox)
    for label, key in (("value():", "value"), ("sliderPosition():", "position"), ("Range:", "range"),
                       ("resolution():", "resolution"), ("Steps:", "steps"), ("Marks:", "marks"),
                       ("isSliderDown():", "down")):
        stateLayout.addRow(label, stateLabels[key])

    configBox = QGroupBox("Configuration (applied to the three controls)")
    configLayout = QFormLayout(configBox)
    configLayout.addRow("decimals:", decimalsSpin)
    configLayout.addRow("minimum:", minSpin)
    configLayout.addRow("maximum:", maxSpin)
    configLayout.addRow("value:", valueSpin)
    configLayout.addRow("sliderPosition (slider):", positionSpin)
    configLayout.addRow("singleStep:", singleStepSpin)
    configLayout.addRow("pageStep:", pageStepSpin)
    configLayout.addRow("tickPosition (slider):", tickPositionCombo)
    configLayout.addRow(markSpacingLabel, markSpacingSpin)
    configLayout.addRow("orientation:", orientationCombo)
    configLayout.addRow("action:", actionCombo)
    configLayout.addRow(triggerButton)
    for check in (enabledCheck, trackingCheck, invertedAppearanceCheck, invertedControlsCheck, wrappingCheck,
                  notchesCheck, sliderDownCheck):
        configLayout.addRow(check)
    configLayout.addRow(errorLabel)

    scenariosBox = QGroupBox("Scenarios")
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

    slider.setTickInterval(markSpacingSpin.value())
    refreshControls()
    mainWindow.setWindowTitle("QRealSlider / QRealScrollBar / QRealDial Demo")
    mainWindow.resize(1000, 800)
    mainWindow.show()

    return app.exec()


class _QResizeFollower(QObject):
    """Appelle `callback` à chaque redimensionnement de `widget`, dont il devient l'enfant Qt."""

    def __init__(self, widget: QWidget, callback: Callable[[], object]) -> None:
        super().__init__(widget)
        self.__callback: Callable[[], object] = callback
        widget.installEventFilter(self)

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Resize:
            self.__callback()
        return False


if __name__ == "__main__":
    sys.exit(main())
