"""Démo de `QDrawingWorkshop`, l'atelier de dessin de la notion 5.2, seul dans sa fenêtre.

Écrire dans l'éditeur : le canevas suit, une demi-seconde après la dernière
frappe. La barre de l'éditeur insère un fragment ou charge une œuvre.

Lancement (depuis new/sf3, avec le venv du projet) :
    python -m edustem.pyside6.learning_app.demo.demo_q_drawing_workshop
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ..qpainter.q_drawing_workshop import QDrawingWorkshop


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = QDrawingWorkshop()
    window.setWindowTitle("QDrawingWorkshop demo")
    window.resize(640, 900)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
