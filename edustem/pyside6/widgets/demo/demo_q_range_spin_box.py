"""Démo : `QRangeSpinBox` et `QRealRangeSpinBox`, avec chaque réglage exposé à côté.

La boîte réelle est reliée dans les deux sens à un `QRealRangeSlider` : le curseur pour le
geste, la boîte pour la précision. Les réglages s'appliquent aux deux boîtes ; la boîte
entière reçoit les valeurs arrondies.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from PySide6.QtCore import QLocale, Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ...core.q_interval_format import QIntervalFormat
from ..q_range_slider import QRealRangeSlider
from ..q_range_spin_box import QAbstractRangeSpinBox, QRangeSpinBox, QRealRangeSpinBox

type Box = QRangeSpinBox | QRealRangeSpinBox


def main() -> int:
    app = QApplication(sys.argv)
    Mode = QAbstractRangeSpinBox.CollisionMode

    integer = QRangeSpinBox()
    integer.setLimits(-100, 100)
    integer.setRange(-20, 60)
    real = QRealRangeSpinBox()
    real.setLimits(-10.0, 10.0)
    real.setRange(-2.5, 3.75)
    real.setSuffix(" m")
    boxes: tuple[Box, ...] = (integer, real)

    slider = QRealRangeSlider()
    slider.setLimits(-10.0, 10.0)
    slider.setRange(-2.5, 3.75)
    real.rangeChanged.connect(slider.setRange)      # the two widgets share the rules and the rounding
    slider.rangeChanged.connect(real.setRange)

    # -- Displays ------------------------------------------------------------
    stateLabel = QLabel()
    stateLabel.setWordWrap(True)
    textLabels: dict[str, QLabel] = {name: QLabel() for name in ("integer", "real", "slider")}
    for label in textLabels.values():
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    log = QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumBlockCount(300)
    errorLabel = QLabel()
    errorLabel.setStyleSheet("color: firebrick;")
    errorLabel.setWordWrap(True)

    # -- Configuration widgets ------------------------------------------------
    localeCombo = QComboBox()
    for name, locale in (("C (1.5, separator ',')", QLocale.c()),
                         ("French, Canada (1,5, separator ';')", QLocale(QLocale.Language.French, QLocale.Country.Canada)),
                         ("English, United States", QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)),
                         ("German (1,5, separator ';')", QLocale(QLocale.Language.German, QLocale.Country.Germany))):
        localeCombo.addItem(name, locale)
    collisionCombo = QComboBox()
    for mode in Mode:
        collisionCombo.addItem(mode.name, mode)
    prefixEdit, suffixEdit = QLineEdit(), QLineEdit(" m")
    openingEdit, closingEdit, separatorEdit = QLineEdit("["), QLineEdit("]"), QLineEdit()
    separatorEdit.setPlaceholderText("automatic (', ' or '; ')")
    decimalsSpin = QSpinBox()
    decimalsSpin.setRange(0, 15)
    decimalsSpin.setValue(real.decimals())
    singleStepSpin = QDoubleSpinBox()
    singleStepSpin.setRange(0.0, 1000.0)
    singleStepSpin.setValue(1.0)

    def check(text: str, checked: bool) -> QCheckBox:
        box = QCheckBox(text)
        box.setChecked(checked)
        return box

    overlapCheck = check("Overlap allowed (the bounds may be equal)", True)
    trackCheck = check("Track visible", True)
    trackingCheck = check("Keyboard tracking (typed text applies at each keystroke)", True)
    freeEntryCheck = check("Free entry (select all, then type any notation)", True)
    readOnlyCheck = check("Read-only", False)
    enabledCheck = check("Enabled", True)

    # -- Refreshing ----------------------------------------------------------
    def refreshTexts() -> None:
        """Shows the text each widget produces, as a program would read it."""
        textLabels["integer"].setText(repr(integer.text()))
        textLabels["real"].setText(repr(real.text()))
        textLabels["slider"].setText(repr(slider.text()))

    def refreshState() -> None:
        refreshTexts()
        stateLabel.setText(
            f"QRangeSpinBox: limits {integer.limits()}, range {integer.range()}, section {integer.currentSection().name}\n"
            f"QRealRangeSpinBox: limits {real.limits()}, range {real.range()}, length {real.length():.15g}, "
            f"center {real.center():.15g}, section {real.currentSection().name}, "
            f"decimals {real.decimals()}, singleStep {real.singleStep():.15g}\n"
            f"cleanText: {real.cleanText()!r}   slider.text(): {slider.text()!r}")

    def attempt(action: Callable[[], object]) -> None:
        """Runs a change, showing the error if a box rejects it, then refreshes the state."""
        errorLabel.clear()
        try:
            action()
        except (ValueError, TypeError) as error:
            errorLabel.setText(f"Rejected: {error}")
        refreshState()

    def forBoth(method: Callable[[Box], object]) -> Callable[[], None]:
        def run() -> None:
            for box in boxes:
                method(box)
        return run

    # -- Signals of the boxes: log --------------------------------------------
    def logLine(name: str, text: str) -> None:
        log.appendPlainText(f"{name:8} {text}")

    def connectBox(name: str, box: Box) -> None:
        def logValue(signal: str) -> Callable[[float], None]:
            def write(value: float) -> None:
                logLine(name, f"{signal}({value:.15g})")
            return write

        def logPair(signal: str) -> Callable[[float, float], None]:
            def write(first: float, second: float) -> None:
                logLine(name, f"{signal}({first:.15g}, {second:.15g})")
                refreshState()
            return write

        def logFinished() -> None:
            logLine(name, "editingFinished()")

        def followCursor(old: int, new: int) -> None:
            refreshState()

        box.lowerValueChanged.connect(logValue("lowerValueChanged"))
        box.upperValueChanged.connect(logValue("upperValueChanged"))
        box.rangeChanged.connect(logPair("rangeChanged"))
        box.limitsChanged.connect(logPair("limitsChanged"))
        box.editingFinished.connect(logFinished)
        def showText(_: str) -> None:
            refreshTexts()

        box.textChanged.connect(showText)
        box.lineEdit().cursorPositionChanged.connect(followCursor)

    connectBox("integer", integer)
    connectBox("real", real)

    def logDecimals(digits: int) -> None:
        logLine("real", f"decimalsChanged({digits})")
    real.decimalsChanged.connect(logDecimals)

    # -- Configuration -> boxes -----------------------------------------------
    def applyLocale(_: int) -> None:
        locale: QLocale = localeCombo.currentData()
        forBoth(lambda box: box.setLocale(locale))()

    def applyCollision(_: int) -> None:
        mode: QAbstractRangeSpinBox.CollisionMode = collisionCombo.currentData()
        forBoth(lambda box: box.setCollisionMode(mode))()
        slider.setCollisionMode(mode)           # the linked slider follows the same rules

    def applyPrefix(text: str) -> None:
        forBoth(lambda box: box.setPrefix(text))()

    def applyDecimals(digits: int) -> None:
        attempt(lambda: (slider.setDecimals(digits), real.setDecimals(digits)))

    def applySingleStep(step: float) -> None:
        attempt(lambda: (real.setSingleStep(step), integer.setSingleStep(max(1, round(step)))))

    def applyOverlap(allowed: bool) -> None:
        attempt(lambda: (forBoth(lambda box: box.setOverlapAllowed(allowed))(), slider.setOverlapAllowed(allowed)))

    def applyTrack(visible: bool) -> None:
        forBoth(lambda box: box.setTrackVisible(visible))()

    def applyKeyboardTracking(tracking: bool) -> None:
        forBoth(lambda box: box.setKeyboardTracking(tracking))()

    def applyFormat(_: str) -> None:
        def change() -> None:
            fmt = QIntervalFormat(openingEdit.text(), closingEdit.text())
            if separatorEdit.text():
                fmt.setSeparator(separatorEdit.text())
            for widget in (integer, real, slider):
                widget.setIntervalFormat(fmt)
        attempt(change)

    def applyFreeEntry(enabled: bool) -> None:
        forBoth(lambda box: box.setFreeEntryEnabled(enabled))()

    def applyReadOnly(readOnly: bool) -> None:
        forBoth(lambda box: box.setReadOnly(readOnly))()

    def applyEnabled(enabled: bool) -> None:
        forBoth(lambda box: box.setEnabled(enabled))()

    localeCombo.currentIndexChanged.connect(applyLocale)
    collisionCombo.currentIndexChanged.connect(applyCollision)
    prefixEdit.textChanged.connect(applyPrefix)
    suffixEdit.textChanged.connect(real.setSuffix)
    decimalsSpin.valueChanged.connect(applyDecimals)
    singleStepSpin.valueChanged.connect(applySingleStep)
    overlapCheck.toggled.connect(applyOverlap)
    trackCheck.toggled.connect(applyTrack)
    trackingCheck.toggled.connect(applyKeyboardTracking)
    readOnlyCheck.toggled.connect(applyReadOnly)
    freeEntryCheck.toggled.connect(applyFreeEntry)
    for edit in (openingEdit, closingEdit, separatorEdit):
        edit.textChanged.connect(applyFormat)
    enabledCheck.toggled.connect(applyEnabled)

    def presetButton(text: str, action: Callable[[], object]) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(lambda: attempt(action))
        return button

    scenarios: list[QPushButton] = [
        presetButton("French open interval ]a ; b[",
                 lambda: (openingEdit.setText("]"), separatorEdit.setText(" ; "), closingEdit.setText("["))),
    presetButton("Real limits [0, 1]", lambda: real.setLimits(0.0, 1.0)),
        presetButton("Real limits [-1000, 1000] (wider field)", lambda: real.setLimits(-1000.0, 1000.0)),
        presetButton("Real limits [2, 2] (zero width)", lambda: real.setLimits(2.0, 2.0)),
        presetButton("Real range (3, -1) (sorted)", lambda: real.setRange(3.0, -1.0)),
        presetButton("Real lower value 0.2675 (rounded like QDoubleSpinBox)", lambda: real.setLowerValue(0.2675)),
        presetButton("Shift by +1 step (as the wheel over a whole selection)", forBoth(lambda box: box.shiftBy(1))),
        presetButton("Widen by +1 step (as Shift + wheel)", forBoth(lambda box: box.widenBy(1))),
        presetButton("Narrow by 1 step", forBoth(lambda box: box.widenBy(-1))),
        presetButton("Move center to 0 (keeps the length)", forBoth(lambda box: box.moveCenter(0))),
        presetButton("Length 5 (lower bound kept)", forBoth(lambda box: box.setLength(5))),
        presetButton("Upper section current",
                     forBoth(lambda box: box.setCurrentSection(QAbstractRangeSpinBox.Section.Upper))),
        presetButton("Real upper value NaN (rejected)", lambda: real.setUpperValue(float("nan"))),
        presetButton("Clear log", log.clear),
    ]

    # -- Layout --------------------------------------------------------------
    stageBox = QGroupBox("Boxes")
    stage = QFormLayout(stageBox)
    stage.addRow("QRangeSpinBox:", integer)
    stage.addRow("QRealRangeSpinBox:", real)
    stage.addRow("QRealRangeSlider (linked):", slider)
    reference = QDoubleSpinBox()
    reference.setValue(3.75)
    stage.addRow("QDoubleSpinBox (reference):", reference)

    textBox = QGroupBox("Produced text (text(), as a program reads it)")
    textLayout = QFormLayout(textBox)
    textLayout.addRow("QRangeSpinBox.text():", textLabels["integer"])
    textLayout.addRow("QRealRangeSpinBox.text():", textLabels["real"])
    textLayout.addRow("QRealRangeSlider.text():", textLabels["slider"])

    hint = QLabel(
        "Each bound is edited alone: the delimiters and the separator are protected; typing the separator goes to "
        "the upper bound.\n"
        "Select all, then type any notation: '-2.5, 3.75', '[-2.5; 3.75]', '-2.5 .. 3.75' or '0.625 ± 3.125' "
        "(also '+/-'); Enter writes it back in the format.\n"
        "Arrows and the buttons step the bound under the text cursor; Tab goes from the lower bound to the upper one.\n"
        "Wheel: the bound under the pointer. Ctrl + wheel or Ctrl + arrow: ten steps, as in QSpinBox. "
        "Shift + wheel or Shift + arrow: widen or narrow around the centre. "
        "Select all (Ctrl + A), then arrows or wheel: shift the whole interval.")
    hint.setWordWrap(True)

    configBox = QGroupBox("Configuration (applied to both boxes)")
    configLayout = QFormLayout(configBox)
    configLayout.addRow("locale:", localeCombo)
    configLayout.addRow("prefix:", prefixEdit)
    configLayout.addRow("suffix (real):", suffixEdit)
    configLayout.addRow("opening delimiter:", openingEdit)
    configLayout.addRow("separator:", separatorEdit)
    configLayout.addRow("closing delimiter:", closingEdit)
    configLayout.addRow("decimals (real and slider):", decimalsSpin)
    configLayout.addRow("singleStep:", singleStepSpin)
    configLayout.addRow("collisionMode:", collisionCombo)
    for box in (overlapCheck, trackCheck, trackingCheck, freeEntryCheck, readOnlyCheck, enabledCheck):
        configLayout.addRow(box)
    configLayout.addRow(errorLabel)

    scenariosBox = QGroupBox("Scenarios")
    scenariosLayout = QVBoxLayout(scenariosBox)
    for button in scenarios:
        scenariosLayout.addWidget(button)
    scenariosLayout.addStretch(1)

    leftColumn = QVBoxLayout()
    leftColumn.addWidget(stageBox)
    leftColumn.addWidget(textBox)
    leftColumn.addWidget(hint)
    leftColumn.addWidget(stateLabel)
    leftColumn.addWidget(QLabel("Log:"))
    leftColumn.addWidget(log, 1)

    rightColumn = QVBoxLayout()
    rightColumn.addWidget(configBox)
    rightColumn.addWidget(scenariosBox, 1)

    mainWindow = QWidget()
    mainLayout = QHBoxLayout(mainWindow)
    mainLayout.addLayout(leftColumn, 3)
    mainLayout.addLayout(rightColumn, 2)

    refreshState()
    mainWindow.setWindowTitle("QRangeSpinBox / QRealRangeSpinBox Demo")
    mainWindow.resize(1200, 700)
    mainWindow.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
