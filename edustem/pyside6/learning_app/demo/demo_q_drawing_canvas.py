"""Démo de `QDrawingCanvas` : dessiner dans sa propre image, la confier au canevas, en agrandir une portion.

La case « Grid » affiche la grille, et le carré de couleur à côté choisit sa couleur.

Lancement (depuis new/sf3, avec le venv du projet) :
    python -m edustem.pyside6.learning_app.demo.demo_q_drawing_canvas
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QPointF, QRect, Qt, Slot
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from ...widgets.q_color_box import QColorBox
from ..qpainter.q_drawing_canvas import QDrawingCanvas


class QDemoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QDrawingCanvas demo")
        self.canvas = QDrawingCanvas(480, 360)
        self.gridCheck = QCheckBox("Grid")
        self.gridCheck.toggled.connect(self.canvas.setGridVisible)
        self.gridColorBox = QColorBox(self.canvas.gridColor(), useAlpha=False)
        self.gridColorBox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.gridColorBox.setToolTip("Grid color")
        self.gridColorBox.colorChanged.connect(self.canvas.setGridColor)
        self.antialiasCheck = QCheckBox("Antialiasing")
        self.antialiasCheck.toggled.connect(self.draw)
        self.viewCombo = QComboBox()
        self.viewCombo.addItem("Whole image", None)
        self.viewCombo.addItem("Magnify 60 × 45 at (0, 0)", QRect(0, 0, 60, 45))
        self.viewCombo.addItem("Magnify 24 × 18 at (100, 60)", QRect(100, 60, 24, 18))
        self.viewCombo.addItem("Magnify 40 × 30 at (460, 340), leaving the image", QRect(460, 340, 40, 30))
        self.viewCombo.currentIndexChanged.connect(lambda: self.canvas.setViewRect(self.viewCombo.currentData()))
        self.sizeCombo = QComboBox()
        self.sizeCombo.addItem("Image 480 × 360", (480, 360))
        self.sizeCombo.addItem("Image 240 × 180 (smaller)", (240, 180))
        self.sizeCombo.addItem("Image 640 × 480 (larger, cropped)", (640, 480))
        self.sizeCombo.currentIndexChanged.connect(self.draw)

        options = QHBoxLayout()
        for widget in (self.gridCheck, self.gridColorBox, self.antialiasCheck, self.viewCombo, self.sizeCombo):
            options.addWidget(widget)
        layout = QVBoxLayout(self)
        layout.addLayout(options)
        layout.addWidget(self.canvas)
        self.draw()

    @Slot()
    def draw(self) -> None:
        """Creates a new image, draws into it, then gives it to the canvas."""
        width, height = self.sizeCombo.currentData()
        image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        with QPainter(image) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, self.antialiasCheck.isChecked())
            painter.fillRect(0, 0, width // 2, height, QColor("white"))
            painter.setPen(QPen(QColor("#2b2d42"), 1))
            painter.drawLine(0, 0, width, height)
            painter.drawEllipse(QPointF(width / 2, height / 2), width / 4, height / 4)
        self.canvas.setImage(image)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = QDemoWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
