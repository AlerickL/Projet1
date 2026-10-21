"""Démo : `QScreenColorPicker` seule, lancée par un bouton, avec ses réglages et ses signaux."""

from __future__ import annotations

import sys

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSpinBox,
    QVBoxLayout, QWidget,
)

from ..q_screen_color_picker import QScreenColorPicker


def main() -> int:
    app = QApplication(sys.argv)
    window = QWidget()
    picker = QScreenColorPicker(window)

    pickButton = QPushButton("Pick a colour on screen")
    pickButton.clicked.connect(picker.start)
    chip = QLabel()
    chip.setFixedSize(64, 32)
    chosen = QColor("#2a9d8f")

    def showChosen(color: QColor) -> None:
        nonlocal chosen
        chosen = QColor(color)
        chip.setStyleSheet(f"background: {color.name()}; border: 1px solid gray;")
        chip.setToolTip(color.name().upper())
        if referenceCheck.isChecked():
            picker.setReferenceColor(color)
    referenceCheck = QCheckBox("Compare with the chosen colour (referenceColor)")
    referenceCheck.setChecked(True)

    def compare(on: bool) -> None:
        picker.setReferenceColor(chosen if on else QColor())
    referenceCheck.toggled.connect(compare)
    showChosen(chosen)

    zoomSpin = QSpinBox()
    zoomSpin.setRange(2, 24)
    zoomSpin.setValue(picker.zoom())
    zoomSpin.valueChanged.connect(picker.setZoom)
    sampleCombo = QComboBox()
    for side in range(1, 10):
        sampleCombo.addItem(f"{side} × {side}" if side % 2 else f"disc, radius {side}", side)
    def setSample(_: int) -> None:
        picker.setSampleSize(int(sampleCombo.currentData()))
    sampleCombo.currentIndexChanged.connect(setSample)
    loupeSpin = QSpinBox()
    loupeSpin.setRange(0, 1000)
    loupeSpin.setSpecialValueText("0 (default)")
    loupeSpin.setToolTip(f"Clamped to [{picker.minimumLoupeSize()}, {picker.maximumLoupeSize()}].")
    loupeSpin.valueChanged.connect(picker.setLoupeSize)

    log = QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumBlockCount(300)
    historyLabel = QLabel()

    def showHistory() -> None:
        historyLabel.setText("  ".join(color.name().upper() for color in QScreenColorPicker.history()) or "(empty)")

    def logCurrent(color: QColor) -> None:
        log.appendPlainText(f"currentColorChanged({color.name().upper()})")

    def logSelected(color: QColor) -> None:
        log.appendPlainText(f"colorSelected({color.name().upper()})")
        showChosen(color)
        showHistory()

    def logActive(on: bool) -> None:
        log.appendPlainText(f"activeChanged({on})")

    picker.currentColorChanged.connect(logCurrent)
    picker.colorSelected.connect(logSelected)
    picker.canceled.connect(lambda: log.appendPlainText("canceled()"))
    picker.activeChanged.connect(logActive)
    clearButton = QPushButton("Clear history")
    clearButton.clicked.connect(lambda: (QScreenColorPicker.clearHistory(), showHistory()))
    showHistory()

    form = QFormLayout()
    form.addRow(referenceCheck)
    form.addRow("zoom:", zoomSpin)
    form.addRow("sampleSize:", sampleCombo)
    form.addRow("loupeSize:", loupeSpin)
    form.addRow("history():", historyLabel)
    form.addRow(clearButton)
    top = QHBoxLayout()
    top.addWidget(pickButton)
    top.addWidget(chip)
    top.addStretch(1)
    hint = QLabel("While picking: click or Enter picks, Esc cancels, arrows move one screen pixel (Shift: ten), "
                  "Shift while moving locks an axis, Alt takes the hue only, Ctrl the lightness only, 1 to 9 average (odd: a square, even: a disc), "
                  "the wheel zooms, Tab walks the history, Ctrl+C copies.")
    hint.setWordWrap(True)
    layout = QVBoxLayout(window)
    layout.addLayout(top)
    layout.addWidget(hint)
    layout.addLayout(form)
    layout.addWidget(QLabel("Signals:"))
    layout.addWidget(log, 1)

    window.setWindowTitle("QScreenColorPicker Demo")
    window.resize(560, 520)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
