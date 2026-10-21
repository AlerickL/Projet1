"""Démo : `QRangeSliderSpinBox` et `QRealRangeSliderSpinBox` dans une même fenêtre, avec chaque
réglage public exposé à côté, l'état du widget choisi et le journal de leurs signaux.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QLocale, Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from ...core.q_interval_format import QIntervalFormat
from ..q_range_slider_spin_box import QAbstractRangeSliderSpinBox, QRangeSliderSpinBox, QRealRangeSliderSpinBox

type Box = QRangeSliderSpinBox | QRealRangeSliderSpinBox


def main() -> int:
    app = QApplication(sys.argv)
    Mode = QAbstractRangeSliderSpinBox.CollisionMode

    intBox = QRangeSliderSpinBox()
    intBox.setLimits(-100, 100)
    intBox.setRange(-20, 60)
    realBox = QRealRangeSliderSpinBox()
    realBox.setLimits(-10.0, 10.0)
    realBox.setRange(-2.5, 3.75)
    realBox.setSuffix(" m")
    boxes: list[tuple[str, Box]] = [("int", intBox), ("real", realBox)]

    # -- Displays ------------------------------------------------------------
    stateLabels: dict[str, QLabel] = {key: QLabel() for key in ("range", "limits", "steps", "ticks", "format", "flags")}
    textLabels: dict[str, QLabel] = {name: QLabel() for name, _ in boxes}
    for label in textLabels.values():
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
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

    minSpin, maxSpin, lowerSpin, upperSpin = newSpin(), newSpin(), newSpin(), newSpin()
    lengthSpin, centerSpin = newSpin(), newSpin()
    singleStepSpin, pageStepSpin, tickIntervalSpin = newSpin(), newSpin(1e-9), newSpin(0.0)
    tickIntervalSpin.setSpecialValueText("0 (automatic)")
    numberSpins: tuple[QDoubleSpinBox, ...] = (minSpin, maxSpin, lowerSpin, upperSpin, lengthSpin, singleStepSpin,
                                               pageStepSpin, tickIntervalSpin)
    decimalsSpin = QSpinBox()
    decimalsSpin.setRange(0, 15)

    prefixEdit, suffixEdit = QLineEdit(), QLineEdit()
    openingEdit, closingEdit, separatorEdit = QLineEdit(), QLineEdit(), QLineEdit()
    separatorEdit.setPlaceholderText("automatic (', ' or '; ')")
    textEdits: tuple[QLineEdit, ...] = (prefixEdit, suffixEdit, openingEdit, closingEdit, separatorEdit)

    localeCombo = QComboBox()
    for name, locale in (("System", QLocale()), ("C (1.5, separator ',')", QLocale.c()),
                         ("French, Canada (1,5, separator ';')", QLocale(QLocale.Language.French, QLocale.Country.Canada)),
                         ("English, United States", QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))):
        localeCombo.addItem(name, locale)
    collisionCombo = QComboBox()
    for mode in Mode:
        collisionCombo.addItem(mode.name, mode)
    orientationCombo = QComboBox()
    orientationCombo.addItem("Horizontal", Qt.Orientation.Horizontal)
    orientationCombo.addItem("Vertical", Qt.Orientation.Vertical)
    tickPositionCombo = QComboBox()
    for position in QSlider.TickPosition:
        tickPositionCombo.addItem(position.name, position)

    overlapCheck = QCheckBox("Overlap allowed (the bounds may be equal)")
    trackingCheck = QCheckBox("Tracking (the range follows the drag and each typed key)")
    freeEntryCheck = QCheckBox("Free entry (select all, then type any notation)")
    enabledCheck = QCheckBox("Enabled")
    checks: tuple[QCheckBox, ...] = (overlapCheck, trackingCheck, freeEntryCheck, enabledCheck)

    # -- Refreshing ----------------------------------------------------------
    def refreshState() -> None:
        for name, box in boxes:
            textLabels[name].setText(f"text() = {box.text()!r}")
        b = target()
        lower, upper = b.range()
        stateLabels["range"].setText(f"({lower:.15g}, {upper:.15g}),  length() = {b.length():.15g},  "
                                     f"center() = {b.center():.15g}")
        stateLabels["limits"].setText(f"[{b.minimum():.15g}, {b.maximum():.15g}]")
        extra = f"   /   decimals() = {b.decimals()}, resolution() = {b.resolution():.15g}" if isinstance(b, QRealRangeSliderSpinBox) else ""
        stateLabels["steps"].setText(f"single {b.singleStep():.15g},  page {b.pageStep():.15g}{extra}")
        stateLabels["ticks"].setText(f"{b.tickPosition().name},  tickInterval() = {b.tickInterval():.15g}")
        stateLabels["format"].setText(f"intervalFormat() = {b.intervalFormat()!r},  locale() = {b.locale().name()}")
        stateLabels["flags"].setText(f"collisionMode() = {b.collisionMode().name},  overlapAllowed() = {b.overlapAllowed()},  "
                                     f"hasTracking() = {b.hasTracking()},  isEnabled() = {b.isEnabled()}")

    def refreshControls() -> None:
        """Brings the configuration widgets back in step with the target (after a rounding, a clamping...)."""
        b = target()
        isReal = isinstance(b, QRealRangeSliderSpinBox)
        widgets: tuple[QWidget, ...] = (*numberSpins, centerSpin, decimalsSpin, *textEdits, localeCombo, collisionCombo,
                                        orientationCombo, tickPositionCombo, *checks)
        for w in widgets:
            w.blockSignals(True)
        decimals = b.decimals() if isinstance(b, QRealRangeSliderSpinBox) else 0
        for spin in numberSpins:
            spin.setDecimals(decimals)
            spin.setSingleStep(10 ** -decimals)
        decimalsSpin.setEnabled(isReal)
        decimalsSpin.setValue(decimals)
        minSpin.setValue(b.minimum())
        maxSpin.setValue(b.maximum())
        lowerSpin.setValue(b.lowerValue())
        upperSpin.setValue(b.upperValue())
        lengthSpin.setValue(b.length())
        centerSpin.setDecimals(decimals + 1)          # a centre may fall between two steps
        centerSpin.setSingleStep(10 ** -decimals)
        centerSpin.setValue(b.center())
        singleStepSpin.setValue(b.singleStep())
        pageStepSpin.setValue(b.pageStep())
        tickIntervalSpin.setValue(b.tickInterval())
        prefixEdit.setText(b.prefix())
        suffixEdit.setText(b.suffix())
        fmt = b.intervalFormat()
        openingEdit.setText(fmt.openingDelimiter())
        closingEdit.setText(fmt.closingDelimiter())
        separatorEdit.setText(fmt.separator() or "")
        localeCombo.setCurrentIndex(max(0, localeCombo.findData(b.locale())))
        collisionCombo.setCurrentIndex(collisionCombo.findData(b.collisionMode()))
        orientationCombo.setCurrentIndex(orientationCombo.findData(b.orientation()))
        tickPositionCombo.setCurrentIndex(tickPositionCombo.findData(b.tickPosition()))
        overlapCheck.setChecked(b.overlapAllowed())
        trackingCheck.setChecked(b.hasTracking())
        freeEntryCheck.setChecked(b.isFreeEntryEnabled())
        enabledCheck.setChecked(b.isEnabled())
        for w in widgets:
            w.blockSignals(False)
        refreshState()

    def number(v: float) -> float:
        """The value in the target's own kind of number."""
        return round(v) if isinstance(target(), QRangeSliderSpinBox) else v

    # The actions take the target as Any: one action serves the int and the real widget alike.
    def attempt(action: Callable[[Any], object]) -> Callable[[], None]:
        """Runs a change on the target, showing the error if it is rejected, then refreshes the interface."""
        def run() -> None:
            errorLabel.clear()
            try:
                action(target())
            except (ValueError, TypeError) as error:
                errorLabel.setText(f"Rejected ({type(error).__name__}): {error}")
            refreshControls()
        return run

    # -- Signals of the boxes: log ---------------------------------------------
    def logLine(name: str, text: str) -> None:
        log.appendPlainText(f"{name:5} {text}")

    def connectBox(name: str, box: Box) -> None:
        def logValue(signal: str) -> Callable[[float], None]:
            def write(value: float) -> None:
                logLine(name, f"{signal}({value:.15g})")
            return write

        def logPair(signal: str, refresh: bool) -> Callable[[float, float], None]:
            def write(first: float, second: float) -> None:
                logLine(name, f"{signal}({first:.15g}, {second:.15g})")
                if refresh:
                    refreshControls()
            return write

        def logFinished() -> None:
            logLine(name, "editingFinished()")

        box.lowerValueChanged.connect(logValue("lowerValueChanged"))
        box.upperValueChanged.connect(logValue("upperValueChanged"))
        box.rangeChanged.connect(logPair("rangeChanged", True))
        box.limitsChanged.connect(logPair("limitsChanged", False))
        box.editingFinished.connect(logFinished)
        if isinstance(box, QRealRangeSliderSpinBox):
            def logDecimals(digits: int) -> None:
                logLine(name, f"decimalsChanged({digits})")
            box.decimalsChanged.connect(logDecimals)

    for name, box in boxes:
        connectBox(name, box)

    # -- Configuration -> target ----------------------------------------------
    def bindNumber(spin: QDoubleSpinBox, apply: Callable[[Any, float], object]) -> None:
        """Applies each new value of a spin box to the target."""
        def run(value: float) -> None:
            attempt(lambda b: apply(b, value))()
        spin.valueChanged.connect(run)

    def bindText(edit: QLineEdit, apply: Callable[[Any, str], object]) -> None:
        def run(text: str) -> None:
            attempt(lambda b: apply(b, text))()
        edit.textEdited.connect(run)

    def bindCheck(check: QCheckBox, apply: Callable[[Any, bool], object]) -> None:
        def run(on: bool) -> None:
            attempt(lambda b: apply(b, on))()
        check.toggled.connect(run)

    def bindCombo(combo: QComboBox, apply: Callable[[Any, Any], object]) -> None:
        """Applies the data of the chosen item to the target."""
        def run(_: int) -> None:
            attempt(lambda b: apply(b, combo.currentData()))()
        combo.currentIndexChanged.connect(run)

    def applyFormat(b: Any, _: str) -> None:
        fmt = QIntervalFormat(openingEdit.text(), closingEdit.text())
        if separatorEdit.text():
            fmt.setSeparator(separatorEdit.text())
        b.setIntervalFormat(fmt)

    def applyDecimals(digits: int) -> None:
        attempt(lambda b: b.setDecimals(digits) if isinstance(b, QRealRangeSliderSpinBox) else None)()

    def retarget(_: int) -> None:
        errorLabel.clear()
        refreshControls()

    targetCombo.currentIndexChanged.connect(retarget)
    bindNumber(minSpin, lambda b, v: b.setMinimum(number(v)))
    bindNumber(maxSpin, lambda b, v: b.setMaximum(number(v)))
    bindNumber(lowerSpin, lambda b, v: b.setLowerValue(number(v)))
    bindNumber(upperSpin, lambda b, v: b.setUpperValue(number(v)))
    bindNumber(lengthSpin, lambda b, v: b.setLength(number(v)))
    bindNumber(centerSpin, lambda b, v: b.moveCenter(v))
    bindNumber(singleStepSpin, lambda b, v: b.setSingleStep(number(v)))
    bindNumber(pageStepSpin, lambda b, v: b.setPageStep(number(v)))
    bindNumber(tickIntervalSpin, lambda b, v: b.setTickInterval(number(v)))
    decimalsSpin.valueChanged.connect(applyDecimals)
    bindText(prefixEdit, lambda b, t: b.setPrefix(t))
    bindText(suffixEdit, lambda b, t: b.setSuffix(t))
    for edit in (openingEdit, closingEdit, separatorEdit):
        bindText(edit, applyFormat)
    bindCombo(localeCombo, lambda b, locale: b.setLocale(locale))
    bindCombo(collisionCombo, lambda b, mode: b.setCollisionMode(mode))
    bindCombo(orientationCombo, lambda b, orientation: b.setOrientation(orientation))
    bindCombo(tickPositionCombo, lambda b, position: b.setTickPosition(position))
    bindCheck(overlapCheck, lambda b, on: b.setOverlapAllowed(on))
    bindCheck(trackingCheck, lambda b, on: b.setTracking(on))
    bindCheck(freeEntryCheck, lambda b, on: b.setFreeEntryEnabled(on))
    bindCheck(enabledCheck, lambda b, on: b.setEnabled(on))

    # -- Scenarios -------------------------------------------------------------
    def presetButton(text: str, action: Callable[[Any], object]) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(attempt(action))
        return button

    def frequencyBand(b: Any) -> None:
        b.setLimits(number(20), number(20000))
        b.setRange(number(300), number(3400))
        b.setPageStep(number(1000))
        b.setSuffix(" Hz")
        b.setTickPosition(QSlider.TickPosition.TicksBelow)
        b.setTickInterval(number(2000))

    def openInterval(b: Any) -> None:
        b.setIntervalFormat(QIntervalFormat("]", "[", " ; "))

    def clearLog(_: Any) -> None:
        log.clear()

    scenarios: list[QPushButton] = [
        presetButton("Telephone band: [300, 3400] Hz in [20, 20000], a tick every 2000", frequencyBand),
        presetButton("French open interval ]a ; b[", openInterval),
        presetButton("Shift by +1 single step (moves the whole interval)", lambda b: b.shiftBy(1)),
        presetButton("Widen by +1 single step (keeps the center)", lambda b: b.widenBy(1)),
        presetButton("Narrow by 1 single step (keeps the center)", lambda b: b.widenBy(-1)),
        presetButton("Move center to 0 (keeps the length)", lambda b: b.moveCenter(0)),
        presetButton("Pushing, overlap forbidden", lambda b: (b.setCollisionMode(Mode.Pushing), b.setOverlapAllowed(False))),
        presetButton("Range (8, 2) (sorted)", lambda b: b.setRange(number(8), number(2))),
        presetButton("Limits [2, 2] (zero width)", lambda b: b.setLimits(number(2), number(2))),
        presetButton("Upper value 2.675 (the float is 2.67499...)", lambda b: b.setUpperValue(number(2.675))),
        presetButton("Upper value NaN (rejected: ValueError in real, TypeError in int)", lambda b: b.setUpperValue(float("nan"))),
        presetButton("Limits [0, 1e12] (rejected: too many steps for the slider)", lambda b: b.setLimits(number(0), number(1e12))),
        presetButton("Clear log", clearLog),
    ]

    # -- Layout --------------------------------------------------------------
    stage = QVBoxLayout()
    for name, box in boxes:
        group = QGroupBox(f"{type(box).__name__} ({name})")
        groupLayout = QVBoxLayout(group)
        groupLayout.addWidget(box)
        groupLayout.addWidget(textLabels[name])
        stage.addWidget(group)
    stage.addStretch(1)
    stageBox = QGroupBox("Widgets")
    stageBox.setLayout(stage)

    hint = QLabel(
        "Drag a handle, or the segment between them, to move the range; the box follows. "
        "In the box, each bound is edited alone; select all, then type any notation: '-2.5, 3.75' or "
        "'0.625 ± 3.125'. Shift + arrow widens or narrows the range in both; Ctrl + A then arrows "
        "shifts it in the box, as Space (both handles) then arrows in the slider.")
    hint.setWordWrap(True)

    stateBox = QGroupBox("State (read from the target)")
    stateLayout = QFormLayout(stateBox)
    for label, key in (("range():", "range"), ("limits():", "limits"), ("Steps:", "steps"), ("Ticks:", "ticks"),
                       ("Format:", "format"), ("Flags:", "flags")):
        stateLayout.addRow(label, stateLabels[key])

    configBox = QGroupBox("Configuration (applied to the target)")
    configLayout = QFormLayout(configBox)
    configLayout.addRow("target:", targetCombo)
    configLayout.addRow("minimum:", minSpin)
    configLayout.addRow("maximum:", maxSpin)
    configLayout.addRow("lowerValue:", lowerSpin)
    configLayout.addRow("upperValue:", upperSpin)
    configLayout.addRow("length (lower kept):", lengthSpin)
    configLayout.addRow("center (moveCenter):", centerSpin)
    configLayout.addRow("singleStep:", singleStepSpin)
    configLayout.addRow("pageStep:", pageStepSpin)
    configLayout.addRow("decimals (real):", decimalsSpin)
    configLayout.addRow("collisionMode:", collisionCombo)
    configLayout.addRow("prefix:", prefixEdit)
    configLayout.addRow("suffix:", suffixEdit)
    configLayout.addRow("opening delimiter:", openingEdit)
    configLayout.addRow("separator:", separatorEdit)
    configLayout.addRow("closing delimiter:", closingEdit)
    configLayout.addRow("locale:", localeCombo)
    configLayout.addRow("orientation:", orientationCombo)
    configLayout.addRow("tickPosition:", tickPositionCombo)
    configLayout.addRow("tickInterval:", tickIntervalSpin)
    for check in checks:
        configLayout.addRow(check)
    configLayout.addRow(errorLabel)

    scenariosBox = QGroupBox("Scenarios (applied to the target)")
    scenariosLayout = QVBoxLayout(scenariosBox)
    for button in scenarios:
        scenariosLayout.addWidget(button)

    leftColumn = QVBoxLayout()
    leftColumn.addWidget(stageBox, 2)
    leftColumn.addWidget(hint)
    leftColumn.addWidget(stateBox)
    leftColumn.addWidget(QLabel("Log:"))
    leftColumn.addWidget(log, 1)

    rightPanel = QWidget()
    rightColumn = QVBoxLayout(rightPanel)
    rightColumn.addWidget(configBox)
    rightColumn.addWidget(scenariosBox)
    rightColumn.addStretch(1)
    rightScroll = QScrollArea()                   # the settings are taller than a laptop screen
    rightScroll.setWidget(rightPanel)
    rightScroll.setWidgetResizable(True)

    mainWindow = QWidget()
    mainLayout = QHBoxLayout(mainWindow)
    mainLayout.addLayout(leftColumn, 3)
    mainLayout.addWidget(rightScroll, 2)

    refreshControls()
    mainWindow.setWindowTitle("QRangeSliderSpinBox / QRealRangeSliderSpinBox Demo")
    mainWindow.resize(1150, 860)
    mainWindow.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
