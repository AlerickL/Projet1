"""Démo de `QDrawingCodeEditor` avec `runDrawingProgram` : un petit atelier de dessin.

Taper un programme : il s'exécute une demi-seconde après la dernière touche ;
une erreur surligne sa ligne.

Lancement (depuis new/sf3, avec le venv du projet) :
    python -m edustem.pyside6.learning_app.demo.demo_q_drawing_code_editor
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer, Slot
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..qpainter.drawing_sandbox import runDrawingProgram
from ..qpainter.q_drawing_canvas import QDrawingCanvas
from ..qpainter.q_drawing_code_editor import QDrawingCodeEditor

_Program = """painter.setPen(QPen(QColor("#2b2d42"), 3))
for i in range(5):
    painter.drawRect(40 + 30 * i, 40 + 20 * i, 120, 80)
print("five rectangles")
"""


class QDemoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QDrawingCodeEditor demo")
        self.editor = QDrawingCodeEditor()
        self.canvas = QDrawingCanvas(480, 360)
        self.report = QLabel()
        self.report.setWordWrap(True)
        snippetButton = QPushButton("Insert a snippet")
        snippetButton.clicked.connect(lambda: self.editor.insertSnippet('painter.setBrush(QColor("#8ecae6"))'))
        self.pause = QTimer(self, singleShot=True, interval=500)
        self.pause.timeout.connect(self.run)
        self.editor.textChanged.connect(self.pause.start)

        left = QVBoxLayout()
        left.addWidget(self.editor)
        left.addWidget(snippetButton)
        right = QVBoxLayout()
        right.addWidget(self.canvas)
        right.addWidget(self.report)
        right.addStretch(1)
        layout = QHBoxLayout(self)
        layout.addLayout(left, 1)
        layout.addLayout(right)
        self.editor.setPlainText(_Program)

    @Slot()
    def run(self) -> None:
        image = QImage(480, 360, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor("white"))
        with QPainter(image) as painter:
            report = runDrawingProgram(self.editor.toPlainText(), painter)
        self.canvas.setImage(image)
        self.editor.setErrorLine(report.errorLine)
        self.report.setText(report.errorMessage or f"OK. Output: {report.output.strip() or '(none)'}")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = QDemoWindow()
    window.resize(1000, 460)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
