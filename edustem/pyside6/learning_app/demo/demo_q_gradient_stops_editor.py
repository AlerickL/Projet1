"""Démo du constructeur de dégradés de qpainter 2.4 : `QGradientStopsEditor` et `QGradientCodeView`.

Démo commune aux deux outils. Modifier les points d'arrêt : l'aperçu
repeint un dégradé linéaire avec eux, et la vue de code écrit le code
Python qui le recrée.

Lancement (depuis new/sf3, avec le venv du projet) :
    python -m edustem.pyside6.learning_app.demo.demo_q_gradient_stops_editor
"""

from __future__ import annotations

import sys
from typing import override

from PySide6.QtCore import QPointF, Slot
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from ..qpainter.q_gradient_code_view import QGradientCodeView
from ..qpainter.q_gradient_stops_editor import QGradientStopsEditor


class _QGradientPreview(QLabel):
    """Une bande peinte avec le dégradé courant."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(60)
        self.gradient = QLinearGradient()

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        with QPainter(self) as painter:
            painter.fillRect(self.rect(), self.gradient)


class QDemoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gradient builder demo")
        self.editor = QGradientStopsEditor()
        self.editor.setStops([(0.0, QColor("royalblue")), (0.5, QColor("gold")), (1.0, QColor("crimson"))])
        self.preview = _QGradientPreview()
        self.codeView = QGradientCodeView()
        layout = QVBoxLayout(self)
        layout.addWidget(self.editor)
        layout.addWidget(self.preview)
        layout.addWidget(self.codeView)
        self.editor.stopsChanged.connect(self.refresh)
        self.refresh()

    @Slot()
    def refresh(self) -> None:
        gradient = QLinearGradient(QPointF(0, 0), QPointF(self.preview.width(), 0))
        gradient.setStops(self.editor.stops())
        self.preview.gradient = gradient
        self.preview.update()
        self.codeView.setGradient(gradient)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = QDemoWindow()
    window.resize(560, 480)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
