"""Démo de `QReadoutLabel`, la lecture commune aux trois applications d'apprentissage.

Taper un texte, puis « Show » : la lecture paraît avec lui, en police à
chasse fixe. « Clear » la vide, ce qui la cache.

Lancement (depuis new/sf3, avec le venv du projet) :
    python -m edustem.pyside6.learning_app.demo.demo_q_readout_label
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ..common.q_readout_label import QReadoutLabel


class QDemoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QReadoutLabel demo")
        self.textEdit = QLineEdit("pen.width() -> 4")
        showButton = QPushButton("Show")
        clearButton = QPushButton("Clear")
        self.readout = QReadoutLabel()
        showButton.clicked.connect(lambda: self.readout.setText(self.textEdit.text()))
        clearButton.clicked.connect(self.readout.clear)

        options = QHBoxLayout()
        options.addWidget(self.textEdit, 1)
        options.addWidget(showButton)
        options.addWidget(clearButton)
        layout = QVBoxLayout(self)
        layout.addLayout(options)
        layout.addWidget(QLabel("The content area would be here."), 1)
        layout.addWidget(self.readout)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = QDemoWindow()
    window.resize(480, 240)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
