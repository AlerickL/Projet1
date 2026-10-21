"""Démo : `QRangeDomainBinding`, un `QDomainExplorerBox` qui pilote un widget à intervalle.

Le domaine balaie la propriété choisie (centre, borne inférieure ou borne supérieure) ; les
réglages du widget (mode de collision, égalité des bornes) changent le domaine.
"""

from __future__ import annotations

import sys
from typing import Any

from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPlainTextEdit, QStackedWidget,
    QVBoxLayout, QWidget,
)

from ..q_domain_explorer_box import QDomainExplorerBox
from ..q_range_domain_binding import QRangeDomainBinding
from ..q_range_slider import QAbstractRangeSlider, QRangeSlider, QRealRangeSlider
from ..q_range_slider_spin_box import QRangeSliderSpinBox, QRealRangeSliderSpinBox
from ..q_range_spin_box import QRangeSpinBox, QRealRangeSpinBox


def main() -> int:
    app = QApplication(sys.argv)
    Target = QRangeDomainBinding.Target
    Mode = QAbstractRangeSlider.CollisionMode

    widgets: list[Any] = [QRealRangeSliderSpinBox(), QRangeSliderSpinBox(), QRealRangeSlider(), QRangeSlider(),
                          QRealRangeSpinBox(), QRangeSpinBox()]
    stack = QStackedWidget()
    for widget in widgets:
        if hasattr(widget, "setDecimals"):
            widget.setDecimals(1)
        widget.setLimits(-10, 10)
        widget.setRange(-2, 2)
        stack.addWidget(widget)

    explorer = QDomainExplorerBox()
    stateLabel = QLabel()
    stateLabel.setWordWrap(True)
    log = QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumBlockCount(300)

    widgetCombo = QComboBox()
    for widget in widgets:
        widgetCombo.addItem(type(widget).__name__, widget)
    targetCombo = QComboBox()
    for target in Target:
        targetCombo.addItem(target.name, target)
    targetCombo.setCurrentIndex(targetCombo.findData(Target.Center))
    collisionCombo = QComboBox()
    for mode in Mode:
        collisionCombo.addItem(mode.name, mode)
    overlapCheck = QCheckBox("Overlap allowed (the bounds may be equal)")
    overlapCheck.setChecked(True)

    def current() -> Any:
        return widgetCombo.currentData()

    def binding() -> QRangeDomainBinding:
        bound = explorer.binding()
        assert isinstance(bound, QRangeDomainBinding)
        return bound

    def refreshState() -> None:
        w, b = current(), binding()
        stateLabel.setText(
            f"range() = {w.range()},  length() = {w.length():.15g},  center() = {w.center():.15g}\n"
            f"binding: target {b.target().name},  size() = {b.size()},  index() = {b.index()},  "
            f"valueFromIndex(index()) = {b.valueFromIndex(b.index()):.15g}")

    def attach(_: int) -> None:
        """Binds the explorer to the chosen widget, with the chosen target."""
        w = current()
        stack.setCurrentWidget(w)
        w.setCollisionMode(collisionCombo.currentData())
        w.setOverlapAllowed(overlapCheck.isChecked())
        explorer.setBinding(QRangeDomainBinding(w, target=targetCombo.currentData()))
        refreshState()

    def changeTarget(_: int) -> None:
        binding().setTarget(targetCombo.currentData())
        refreshState()

    def changeCollision(_: int) -> None:
        current().setCollisionMode(collisionCombo.currentData())
        refreshState()

    def changeOverlap(allowed: bool) -> None:
        current().setOverlapAllowed(allowed)
        refreshState()

    for widget in widgets:
        def logRange(lower: float, upper: float, name: str = type(widget).__name__) -> None:
            log.appendPlainText(f"{name}.rangeChanged({lower:.15g}, {upper:.15g})")
            refreshState()
        widget.rangeChanged.connect(logRange)

    widgetCombo.currentIndexChanged.connect(attach)
    targetCombo.currentIndexChanged.connect(changeTarget)
    collisionCombo.currentIndexChanged.connect(changeCollision)
    overlapCheck.toggled.connect(changeOverlap)

    stageBox = QGroupBox("Explorer and bound widget")
    stage = QVBoxLayout(stageBox)
    stage.addWidget(explorer)
    stage.addWidget(stack)

    configBox = QGroupBox("Configuration")
    config = QFormLayout(configBox)
    config.addRow("widget:", widgetCombo)
    config.addRow("target:", targetCombo)
    config.addRow("collisionMode:", collisionCombo)
    config.addRow(overlapCheck)

    hint = QLabel("Center sweeps the whole interval at constant length. LowerValue and UpperValue move one bound: "
                  "in Blocking it stops against the other one, in Pushing it pushes the other one to the limit "
                  "(and the pushed bound does not come back). The markers' tooltips are computed when the binding "
                  "is attached.")
    hint.setWordWrap(True)

    column = QVBoxLayout()
    column.addWidget(stageBox)
    column.addWidget(stateLabel)
    column.addWidget(hint)
    column.addWidget(QLabel("Log:"))
    column.addWidget(log, 1)

    mainWindow = QWidget()
    mainLayout = QHBoxLayout(mainWindow)
    mainLayout.addLayout(column, 3)
    side = QVBoxLayout()
    side.addWidget(configBox)
    side.addStretch(1)
    mainLayout.addLayout(side, 2)

    attach(0)
    mainWindow.setWindowTitle("QRangeDomainBinding Demo")
    mainWindow.resize(1000, 600)
    mainWindow.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
