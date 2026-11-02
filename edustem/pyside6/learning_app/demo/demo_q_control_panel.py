"""Démo de `QControlPanel` et de `QReadoutLabel` : une étape « À vous », rejouée à la demande.

Lancement (depuis new/sf3, avec le venv du projet) :
    python -m edustem.pyside6.learning_app.demo.demo_q_control_panel
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from ..common.q_control_panel import QControlPanel
from ..common.q_readout_label import QReadoutLabel


class QDemoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QControlPanel demo")
        self.readout = QReadoutLabel()
        self.controls = QControlPanel()
        self.widthSlider = self.controls.addSlider("Width", 1, 100, 25, divisor=10, suffix="px")
        self.styleCombo = self.controls.addComboBox("Style", [("Solid", "solid"), ("Dashed", "dashed")])
        self.gridCheck = self.controls.addCheckBox("Show the grid", checked=True)
        self.planeGroup = self.controls.addRadioGroup("Plane", ["XY", "XZ", "YZ"])
        self.runButton = self.controls.addButton("Run")

        replayButton = QPushButton("Replay the step")
        replayButton.clicked.connect(self.replay)
        revealSliderButton = QPushButton("Reveal the slider only")
        revealSliderButton.clicked.connect(lambda: self.controls.reveal(self.widthSlider))
        buttons = QHBoxLayout()
        buttons.addWidget(replayButton)
        buttons.addWidget(revealSliderButton)

        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(self.controls)
        layout.addWidget(self.readout)
        layout.addStretch(1)
        self.replay()

    @Slot()
    def replay(self) -> None:
        """Reset, then run the "À vous" step again: connections never pile up."""
        self.controls.resetControls()
        self.readout.clear()
        self.widthSlider.valueChanged.connect(self.showValues)
        self.styleCombo.currentIndexChanged.connect(self.showValues)
        self.gridCheck.toggled.connect(self.showValues)
        self.planeGroup.idToggled.connect(self.showValues)
        self.runButton.clicked.connect(self.showValues)
        self.controls.reveal()
        self.showValues()

    @Slot()
    def showValues(self) -> None:
        self.readout.setText(
            f"width = {self.widthSlider.value() / 10}\n"
            f"style = {self.styleCombo.currentData()}\n"
            f"grid = {self.gridCheck.isChecked()}\n"
            f"plane = {self.planeGroup.checkedId()}"
        )


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = QDemoWindow()
    window.resize(420, 300)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
