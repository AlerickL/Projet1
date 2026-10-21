"""Démo : un QStateIndicatorBar alimenté par une source simulée, avec ses réglages."""

from __future__ import annotations

import random
import sys

from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QSpinBox, QSplitter,
    QVBoxLayout, QWidget,
)

from ..q_state_indicator_bar import QStateIndicatorBar, QStateSet

_Shape = QStateIndicatorBar.Shape
_State = QStateSet.State
_IconSize = 64


def _strokeIcon(color: str, strokes: list[list[tuple[float, float]]]) -> QIcon:
    """Renvoie un pictogramme détouré : des traits épais sur fond
    transparent, donnés en fractions du carré de l'image."""
    pixmap = QPixmap(_IconSize, _IconSize)
    pixmap.fill(Qt.GlobalColor.transparent)
    with QPainter(pixmap) as painter:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(color), _IconSize * 0.22, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
        for stroke in strokes:
            painter.drawPolyline([QPointF(x * _IconSize, y * _IconSize) for x, y in stroke])
    return QIcon(pixmap)


def _stripesIcon(first: str, second: str) -> QIcon:
    """Renvoie une texture pleine : des bandes obliques de deux couleurs."""
    pixmap = QPixmap(_IconSize, _IconSize)
    pixmap.fill(QColor(first))
    with QPainter(pixmap) as painter:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(second), _IconSize * 0.16))
        for offset in range(-_IconSize, _IconSize, _IconSize // 3):
            painter.drawLine(offset, _IconSize, offset + _IconSize, 0)
    return QIcon(pixmap)


def _checkStates() -> QStateSet:
    """Renvoie un jeu dont chaque état est un pictogramme détouré."""
    cross = _strokeIcon("#c62828", [[(0.2, 0.2), (0.8, 0.8)], [(0.8, 0.2), (0.2, 0.8)]])
    tick = _strokeIcon("#2e7d32", [[(0.15, 0.55), (0.4, 0.8), (0.85, 0.2)]])
    return QStateSet([_State("Fail", "#c62828", icon=cross), _State("Pass", "#2e7d32", icon=tick)])


def _hazardStates() -> QStateSet:
    """Renvoie un jeu dont un état est une texture qui remplit la forme, et
    qui clignote avec une seconde texture."""
    return QStateSet([
        _State("Clear", "#9e9e9e"),
        _State(
            "Hazard", "#f9a825", blinking=True, icon=_stripesIcon("#f9a825", "#212121"),
            blinkIcon=_stripesIcon("#212121", "#f9a825"), imageMode=_State.ImageMode.Framed,
        ),
    ])


def main() -> int:
    app = QApplication(sys.argv)

    # One state set and one shape per family of indicators.
    bar = QStateIndicatorBar()
    bar.addIndicators(["Pump", "Heater", "Fan"], QStateSet.activity())
    bar.addIndicator("Network", QStateSet.connection(), shape=_Shape.Rectangular)
    bar.addIndicator("Alarm", QStateSet.severity(), shape=_Shape.TriangleUp)
    bar.addIndicator(
        "Level", QStateSet.gradient("#90caf9", "#0d47a1", ["Empty", "Low", "Half", "High", "Full"]),
        shape=_Shape.Rectangular,
    )
    bar.addIndicator("Check", _checkStates())
    bar.addIndicator("Zone", _hazardStates(), shape=_Shape.Diamond)
    # "Alarm" starts on its blinking state, "Zone" on its blinking texture.
    bar.setStates([2, 0, QStateIndicatorBar.NoState, 1, bar.stateIndexOf(4, "Critical"), 2, 1, 1])
    initialStates = bar.states()
    initialShapes = bar.indicatorShapes()

    # The bar never polls: this timer plays the external source and pushes its states.
    def pushRandomState() -> None:
        index = random.randrange(bar.count())
        bar.setState(index, random.randrange(bar.indicatorStateSet(index).count()))

    source = QTimer()
    source.setInterval(700)
    source.timeout.connect(pushRandomState)

    signalLabel = QLabel("none yet")
    signalCount = 0

    def showSignal(index: int, state: int) -> None:
        nonlocal signalCount
        signalCount += 1
        signalLabel.setText(
            f"#{signalCount}: {bar.indicatorName(index)} is now {bar.stateName(index) or 'without state'}"
            f" (index {index}, state {state})"
        )

    bar.stateChanged.connect(showSignal)

    batchLabel = QLabel("none yet")
    batchLabel.setWordWrap(True)
    batchCount = 0

    def showBatch() -> None:
        nonlocal batchCount
        batchCount += 1
        batchLabel.setText(f"#{batchCount}: now {bar.summaryText()}")

    bar.statesChanged.connect(showBatch)

    clickLabel = QLabel("none yet (click an indicator)")

    def showClick(index: int) -> None:
        marker = bar.markerRect(index)
        text = bar.textRect(index)
        textZone = "no text shown" if text.isEmpty() else f"text {text.width()}x{text.height()}"
        clickLabel.setText(
            f"{bar.indicatorName(index)} (index {index}): marker {marker.width()}x{marker.height()}"
            f" at ({marker.x()}, {marker.y()}), {textZone}"
        )

    bar.indicatorClicked.connect(showClick)

    sourceCheck = QCheckBox("Simulated source running")
    sourceCheck.toggled.connect(lambda checked: source.start() if checked else source.stop())

    initialButton = QPushButton("Reset to initial state")
    initialButton.clicked.connect(lambda: bar.setStates(initialStates))
    noStateButton = QPushButton("Reset to no state")
    noStateButton.clicked.connect(bar.clearStates)
    resetLayout = QHBoxLayout()
    resetLayout.addWidget(initialButton)
    resetLayout.addWidget(noStateButton)
    resetLayout.addStretch()

    enabledCheck = QCheckBox("Bar enabled")
    enabledCheck.setChecked(True)
    enabledCheck.toggled.connect(bar.setEnabled)

    indicatorChecks = QHBoxLayout()
    checks: list[QCheckBox] = []
    for index in range(bar.count()):
        check = QCheckBox(bar.indicatorName(index))
        check.setChecked(True)
        check.toggled.connect(lambda checked, i=index: bar.setIndicatorEnabled(i, checked))
        indicatorChecks.addWidget(check)
        checks.append(check)
    indicatorChecks.addStretch()

    def setEveryIndicatorEnabled(enabled: bool) -> None:
        bar.setAllIndicatorsEnabled(enabled)
        for check in checks:
            check.blockSignals(True)
            check.setChecked(enabled)
            check.blockSignals(False)

    enableAllButton = QPushButton("Enable all")
    enableAllButton.clicked.connect(lambda: setEveryIndicatorEnabled(True))
    disableAllButton = QPushButton("Disable all")
    disableAllButton.clicked.connect(lambda: setEveryIndicatorEnabled(False))
    enableLayout = QHBoxLayout()
    enableLayout.addWidget(enableAllButton)
    enableLayout.addWidget(disableAllButton)
    enableLayout.addStretch()

    shapeCombo = QComboBox()
    shapeCombo.addItem("One per family (initial)", None)
    for shape in _Shape:
        shapeCombo.addItem(f"All {shape.name}", shape)

    def applyShape() -> None:
        shape = shapeCombo.currentData()
        if shape is not None:
            bar.setAllIndicatorShapes(shape)
            return
        for index, initialShape in enumerate(initialShapes):
            bar.setIndicatorShape(index, initialShape)

    shapeCombo.currentIndexChanged.connect(applyShape)

    bevelCombo = QComboBox()
    for bevel in QStateIndicatorBar.Bevel:
        bevelCombo.addItem(bevel.name, bevel)
    bevelCombo.currentIndexChanged.connect(lambda: bar.setBevel(bevelCombo.currentData()))

    finishCombo = QComboBox()
    for finish in QStateIndicatorBar.Finish:
        finishCombo.addItem(finish.name, finish)
    finishCombo.currentIndexChanged.connect(lambda: bar.setFinish(finishCombo.currentData()))

    blinkCheck = QCheckBox("Enabled")
    blinkCheck.setChecked(bar.isBlinkEnabled())
    blinkCheck.toggled.connect(bar.setBlinkEnabled)
    blinkCheck.setToolTip(
        "The bar does not read the system's 'reduce animations' setting.\n"
        "An application that honors it turns the blink off here."
    )
    transitionCombo = QComboBox()
    for transition in QStateIndicatorBar.BlinkTransition:
        transitionCombo.addItem(transition.name, transition)
    transitionCombo.currentIndexChanged.connect(lambda: bar.setBlinkTransition(transitionCombo.currentData()))
    periodSpin = QSpinBox()
    periodSpin.setRange(QStateIndicatorBar.MinimumBlinkPeriod, 5000)
    periodSpin.setSingleStep(100)
    periodSpin.setSuffix(" ms")
    periodSpin.setValue(bar.blinkPeriod())
    periodSpin.valueChanged.connect(bar.setBlinkPeriod)
    darkeningSpin = QSpinBox()
    darkeningSpin.setRange(100, 1000)
    darkeningSpin.setSingleStep(25)
    darkeningSpin.setPrefix("darker ")
    darkeningSpin.setValue(bar.blinkDarkening())
    darkeningSpin.valueChanged.connect(bar.setBlinkDarkening)
    blinkLayout = QHBoxLayout()
    for widget in (blinkCheck, transitionCombo, periodSpin, darkeningSpin):
        blinkLayout.addWidget(widget)
    blinkLayout.addStretch()

    textModeCombo = QComboBox()
    for mode in QStateIndicatorBar.TextMode:
        textModeCombo.addItem(mode.name, mode)
    textModeCombo.setCurrentIndex(textModeCombo.findData(bar.textMode()))
    textModeCombo.currentIndexChanged.connect(lambda: bar.setTextMode(textModeCombo.currentData()))

    positionCombo = QComboBox()
    for position in QStateIndicatorBar.MarkerPosition:
        positionCombo.addItem(position.name, position)
    positionCombo.currentIndexChanged.connect(lambda: bar.setMarkerPosition(positionCombo.currentData()))

    verticalCheck = QCheckBox("Vertical")
    verticalCheck.toggled.connect(
        lambda checked: bar.setOrientation(Qt.Orientation.Vertical if checked else Qt.Orientation.Horizontal)
    )

    horizontalCombo = QComboBox()
    for name, flag in (("Left", Qt.AlignmentFlag.AlignLeft), ("Center", Qt.AlignmentFlag.AlignHCenter),
                       ("Right", Qt.AlignmentFlag.AlignRight)):
        horizontalCombo.addItem(name, flag)
    verticalCombo = QComboBox()
    for name, flag in (("Top", Qt.AlignmentFlag.AlignTop), ("Center", Qt.AlignmentFlag.AlignVCenter),
                       ("Bottom", Qt.AlignmentFlag.AlignBottom)):
        verticalCombo.addItem(name, flag)
    verticalCombo.setCurrentIndex(1)

    def applyAlignment() -> None:
        bar.setAlignment(horizontalCombo.currentData() | verticalCombo.currentData())

    horizontalCombo.currentIndexChanged.connect(applyAlignment)
    verticalCombo.currentIndexChanged.connect(applyAlignment)
    alignmentLayout = QHBoxLayout()
    alignmentLayout.addWidget(horizontalCombo)
    alignmentLayout.addWidget(verticalCombo)

    spacingSpin = QSpinBox()
    spacingSpin.setRange(-1, 60)
    spacingSpin.setSpecialValueText("Style default")
    spacingSpin.setValue(bar.spacing())
    spacingSpin.valueChanged.connect(bar.setSpacing)

    textSpacingSpin = QSpinBox()
    textSpacingSpin.setRange(-1, 60)
    textSpacingSpin.setSpecialValueText("Style default")
    textSpacingSpin.setValue(bar.textSpacing())
    textSpacingSpin.valueChanged.connect(bar.setTextSpacing)

    form = QFormLayout()
    form.addRow("Source:", sourceCheck)
    form.addRow("", resetLayout)
    form.addRow("Last stateChanged signal:", signalLabel)
    form.addRow("Last statesChanged signal:", batchLabel)
    form.addRow("Last indicatorClicked signal:", clickLabel)
    form.addRow("Enabled:", enabledCheck)
    form.addRow("", indicatorChecks)
    form.addRow("", enableLayout)
    form.addRow("Shape:", shapeCombo)
    form.addRow("Bevel:", bevelCombo)
    form.addRow("Finish:", finishCombo)
    form.addRow("Blink:", blinkLayout)
    form.addRow("Text mode:", textModeCombo)
    form.addRow("Marker position:", positionCombo)
    form.addRow("Orientation:", verticalCheck)
    form.addRow("Alignment:", alignmentLayout)
    form.addRow("Spacing between indicators:", spacingSpin)
    form.addRow("Spacing marker to text:", textSpacingSpin)

    # The splitter gives the bar a pane larger or smaller than its size hint: larger, the alignment
    # shows; smaller, the names fold in Collapsible text mode.
    barFrame = QFrame()
    barFrame.setFrameShape(QFrame.Shape.StyledPanel)
    barLayout = QVBoxLayout(barFrame)
    barLayout.addWidget(bar, 1)
    handleHint = QLabel("Drag the handle on my left\nto give the bar more or less room.")
    handleHint.setAlignment(Qt.AlignmentFlag.AlignCenter)
    handleHint.setFrameShape(QFrame.Shape.StyledPanel)
    handleHint.setMinimumWidth(40)
    stage = QSplitter(Qt.Orientation.Horizontal)
    stage.addWidget(barFrame)
    stage.addWidget(handleHint)
    stage.setChildrenCollapsible(False)
    stage.setStretchFactor(0, 1)
    stage.setMinimumHeight(170)

    window = QWidget()
    mainLayout = QVBoxLayout(window)
    mainLayout.addWidget(stage, 1)
    mainLayout.addWidget(QLabel(
        "Hover an indicator: its tooltip shows its name, its state and its possible states.\n"
        "With the Collapsible text mode, squeeze the bar: the names fold all at once."
    ))
    mainLayout.addLayout(form)

    window.setWindowTitle("QStateIndicatorBar Demo")
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
