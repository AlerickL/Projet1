"""Démo : QLatexLabel, toute son API réglable en direct, et une formule alignée sur une ligne de texte.

Exécution (depuis new/sf3, avec le venv du projet) :
    python -m edustem.pyside6.widgets.demo.demo_q_latex_label [--cdn]
"""

from __future__ import annotations

import math
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ..q_latex_label import QLatexLabel, QMathJaxRenderer

_Examples: tuple[tuple[str, str], ...] = (
    ("Integral", r"\int_{-\infty}^{+\infty} e^{-x^2}\,dx = \sqrt{\pi}"),
    ("System", r"\begin{aligned} x+y &= 3 \\ 2x-y &= 0 \end{aligned}"),
    ("Matrix", r"A=\begin{pmatrix}1&2\\3&4\end{pmatrix},\quad \det(A)=-2"),
    ("Physics", r"\vec{F}=m\vec{a},\qquad E=\frac{1}{2}mv^2"),
    ("Chemistry", r"\ce{2H2 + O2 -> 2H2O}"),
    ("Error: missing brace", r"\frac{1}{"),
    ("Error: unknown command", r"\notARealCommand + x"),
)

_Alignments: tuple[tuple[str, Qt.AlignmentFlag], ...] = (
    ("Center", Qt.AlignmentFlag.AlignCenter),
    ("Left", Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
    ("Right", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
    ("Top left", Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop),
    ("Left, on the baseline", Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBaseline),
)


class QLatexLabelDemo(QWidget):
    """Fenêtre de démonstration : une source, un label principal réglable, un label en mode Raw, et une phrase."""

    def __init__(self, engine: QMathJaxRenderer) -> None:
        super().__init__()
        self.engine = engine
        self.setWindowTitle("QLatexLabel demo")
        self.resize(980, 780)

        self.editor = QPlainTextEdit()
        self.editor.setMaximumHeight(110)
        self.examples = QComboBox()
        for title, latex in _Examples:
            self.examples.addItem(title, latex)

        self.label = QLatexLabel(renderer=engine)
        self.label.setFont(QFont("Times New Roman", 24))
        self.label.setMinimumHeight(140)
        self.rawLabel = QLatexLabel(renderer=engine, errorMode=QLatexLabel.ErrorMode.Raw)
        self.rawLabel.setFont(QFont("Times New Roman", 16))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("LaTeX source (no $ delimiters, no document):"))
        layout.addWidget(self.editor)
        layout.addWidget(self.examples)
        layout.addWidget(self.label, 1)
        layout.addWidget(QLabel("Same source, same presentation, in Raw error mode:"))
        layout.addWidget(self.rawLabel)
        layout.addWidget(self._createSentence())
        controls = QHBoxLayout()
        controls.addWidget(self._createPresentationBox())
        controls.addWidget(self._createBehaviourBox())
        layout.addLayout(controls)
        layout.addLayout(self._createActions())
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.editor.textChanged.connect(self._onSourceChanged)
        self.examples.currentIndexChanged.connect(self._onExampleChosen)
        for signal in (self.label.renderStateChanged, self.label.errorChanged, self.rawLabel.renderStateChanged,
                       engine.readyChanged, engine.engineFailed):
            signal.connect(self._updateStatus)
        self.editor.setPlainText(self.examples.currentData())
        self._updateStatus()

    # -- Sections ----------------------------------------------------------------------------------

    def _createSentence(self) -> QGroupBox:
        """A line of text with an inline formula, both on the same baseline."""
        font = QFont("Times New Roman", 16)
        before = QLabel("The area under the curve is")
        after = QLabel("square units.")
        self.inlineLabel = QLatexLabel(r"\int_0^1 x^2\,dx = \tfrac{1}{3}", renderer=self.engine)
        self.inlineLabel.setDisplayMode(False)
        self.inlineLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBaseline)
        self.inlineLabel.setScaleMode(QLatexLabel.ScaleMode.Natural)
        for widget in (before, self.inlineLabel, after):
            widget.setFont(font)
            widget.setContentsMargins(0, 0, 0, 0)
        for text in (before, after):
            text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.sentenceTexts = (before, after)
        self.inlineLabel.renderFinished.connect(self._alignSentence)

        box = QGroupBox("Inline formula, aligned on the text baseline")
        row = QHBoxLayout(box)
        for widget in (before, self.inlineLabel, after):
            row.addWidget(widget, 0, Qt.AlignmentFlag.AlignTop)
        row.addStretch()
        return box

    def _createPresentationBox(self) -> QGroupBox:
        self.zoomSpin = QDoubleSpinBox()
        self.zoomSpin.setRange(0.1, 8)
        self.zoomSpin.setSingleStep(0.1)
        self.zoomSpin.setValue(self.label.zoomFactor())
        self.zoomSpin.valueChanged.connect(self.label.setZoomFactor)
        self.zoomSpin.valueChanged.connect(self.rawLabel.setZoomFactor)

        self.fontSpin = QSpinBox()
        self.fontSpin.setRange(6, 72)
        self.fontSpin.setSuffix(" pt")
        self.fontSpin.setValue(self.label.font().pointSize())
        self.fontSpin.valueChanged.connect(self._onFontSizeChanged)

        self.alignmentCombo = QComboBox()
        for title, alignment in _Alignments:
            self.alignmentCombo.addItem(title, alignment)
        self.alignmentCombo.setCurrentIndex(self.alignmentCombo.findData(self.label.alignment()))
        self.alignmentCombo.currentIndexChanged.connect(
            lambda: self.label.setAlignment(self.alignmentCombo.currentData()))

        self.scaleCombo = QComboBox()
        for mode in QLatexLabel.ScaleMode:
            self.scaleCombo.addItem(mode.name, mode)
        self.scaleCombo.setCurrentIndex(self.scaleCombo.findData(self.label.scaleMode()))
        self.scaleCombo.currentIndexChanged.connect(lambda: self.label.setScaleMode(self.scaleCombo.currentData()))

        self.displayCheck = QCheckBox("Display (block) mode")
        self.displayCheck.setChecked(self.label.displayMode())
        self.displayCheck.toggled.connect(self.label.setDisplayMode)
        self.displayCheck.toggled.connect(self.rawLabel.setDisplayMode)

        colorButton = QPushButton("Choose...")
        colorButton.clicked.connect(self._onChooseColor)
        paletteButton = QPushButton("Palette")
        paletteButton.clicked.connect(lambda: self.label.setForegroundColor(QColor()))
        colorRow = QHBoxLayout()
        colorRow.addWidget(colorButton)
        colorRow.addWidget(paletteButton)

        box = QGroupBox("Presentation")
        form = QFormLayout(box)
        form.addRow("Zoom:", self.zoomSpin)
        form.addRow("Font size:", self.fontSpin)
        form.addRow("Alignment:", self.alignmentCombo)
        form.addRow("Scale mode:", self.scaleCombo)
        form.addRow("", self.displayCheck)
        form.addRow("Color:", colorRow)
        return box

    def _createBehaviourBox(self) -> QGroupBox:
        self.errorCombo = QComboBox()
        for mode in QLatexLabel.ErrorMode:
            self.errorCombo.addItem(mode.name, mode)
        self.errorCombo.setCurrentIndex(self.errorCombo.findData(self.label.errorMode()))
        self.errorCombo.currentIndexChanged.connect(lambda: self.label.setErrorMode(self.errorCombo.currentData()))
        self.errorCombo.currentIndexChanged.connect(self._updateStatus)

        self.intervalSpin = QSpinBox()
        self.intervalSpin.setRange(0, 1000)
        self.intervalSpin.setSuffix(" ms")
        self.intervalSpin.setValue(self.label.updateInterval())
        self.intervalSpin.valueChanged.connect(self.label.setUpdateInterval)

        self.animationCheck = QCheckBox("Update the source at 30 Hz")
        self.animationTimer = QTimer(self)
        self.animationTimer.setInterval(33)
        self.animationStep = 0
        self.animationTimer.timeout.connect(self._onAnimationTick)
        self.animationCheck.toggled.connect(
            lambda active: self.animationTimer.start() if active else self.animationTimer.stop())

        box = QGroupBox("Behaviour")
        form = QFormLayout(box)
        form.addRow("On render failure:", self.errorCombo)
        form.addRow("Coalescing interval:", self.intervalSpin)
        form.addRow("", self.animationCheck)
        return box

    def _createActions(self) -> QHBoxLayout:
        buttons = [
            ("Copy LaTeX", self.label.copyLatex),
            ("Copy SVG", self.label.copySvg),
            ("Copy MathML", self.label.copyMathML),
            ("Export SVG...", self._onExport),
            ("Reload engine", self.engine.reload),
            ("Clear cache", self._onClearCache),
        ]
        row = QHBoxLayout()
        self.exportButtons: list[QPushButton] = []
        for text, handler in buttons:
            button = QPushButton(text)
            button.clicked.connect(handler)
            row.addWidget(button)
            if text in ("Copy SVG", "Copy MathML", "Export SVG..."):
                self.exportButtons.append(button)
        row.addStretch()
        return row

    # -- Handlers ----------------------------------------------------------------------------------

    def _onSourceChanged(self) -> None:
        source = self.editor.toPlainText()
        self.label.setLatex(source)
        self.rawLabel.setLatex(source)

    def _onExampleChosen(self) -> None:
        self.editor.setPlainText(self.examples.currentData())

    def _onFontSizeChanged(self, size: int) -> None:
        font = QFont(self.label.font())
        font.setPointSize(size)
        self.label.setFont(font)

    def _onChooseColor(self) -> None:
        current = self.label.foregroundColor()
        if not current.isValid():
            current = self.label.palette().color(self.label.foregroundRole())
        color = QColorDialog.getColor(current, self, "Formula color",
                                      QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self.label.setForegroundColor(color)

    def _onExport(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Export formula", "formula.svg", "SVG images (*.svg)")
        if not filename:
            return
        try:
            if not self.label.saveSvg(filename):
                QMessageBox.information(self, "Export", "No formula is ready to export.")
        except OSError as error:
            QMessageBox.warning(self, "Export failed", str(error))

    def _onClearCache(self) -> None:
        self.engine.clearCache()
        self._updateStatus()

    def _onAnimationTick(self) -> None:
        self.animationStep += 1
        t = self.animationStep / 30
        self.editor.setPlainText(rf"x(t)=\sin(t),\qquad t={t:.2f},\quad x(t)={math.sin(t):.3f}")

    def _alignSentence(self) -> None:
        """Pushes the plain text down so that its baseline meets the formula's."""
        offset = self.inlineLabel.baselineOffset() - self.sentenceTexts[0].fontMetrics().ascent()
        for text in self.sentenceTexts:
            text.setContentsMargins(0, max(0, offset), 0, 0)

    def _updateStatus(self, *_arguments: object) -> None:
        if self.engine.errorString():
            engineState = f"failed ({self.engine.errorString()})"
        else:
            engineState = "ready" if self.engine.isReady() else "loading..."
        visibility = "hidden by the error" if self.label.isHidden() else "visible"
        text = (f"Engine: {self.engine.source().value}, {engineState}, {self.engine.cacheEntryCount()} cached, "
                f"{self.engine.conversionCount()} conversions | Label: {self.label.renderState().name}, "
                f"{visibility} | Raw label: {self.rawLabel.renderState().name}")
        if self.label.errorString():
            text += f" | {self.label.errorString()}"
        self.status.setText(text)
        for button in self.exportButtons:
            button.setEnabled(bool(self.label.svgData()))


def main() -> int:
    app = QApplication(sys.argv)
    source = QMathJaxRenderer.Source.Cdn if "--cdn" in sys.argv else QMathJaxRenderer.Source.Local
    engine = QMathJaxRenderer(app, source=source)
    app.aboutToQuit.connect(engine.close)
    demo = QLatexLabelDemo(engine)
    demo.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
