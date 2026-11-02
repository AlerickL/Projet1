"""Démo de `QRunTimeBar`, la barre du temps de calcul de l'atelier de dessin (notion 5.2).

Le curseur règle le temps de calcul, en pourcentage de la limite d'une
seconde : la barre est verte, orange dès 60 %, rouge dès 85 %, et pleine
au-delà de 100 %.

Lancement (depuis new/sf3, avec le venv du projet) :
    python -m edustem.pyside6.learning_app.demo.demo_q_run_time_bar
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

from ..qpainter.q_run_time_bar import QRunTimeBar


class QDemoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QRunTimeBar demo")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 150)
        self.slider.setValue(42)
        self.runTimeBar = QRunTimeBar(1.0)
        self.slider.valueChanged.connect(lambda percent: self.runTimeBar.setRunTime(percent / 100))
        self.runTimeBar.setRunTime(self.slider.value() / 100)

        options = QHBoxLayout()
        options.addWidget(QLabel("Run time (% of the limit)"))
        options.addWidget(self.slider, 1)
        layout = QVBoxLayout(self)
        layout.addLayout(options)
        layout.addWidget(self.runTimeBar)
        layout.addStretch(1)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = QDemoWindow()
    window.resize(480, 120)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
