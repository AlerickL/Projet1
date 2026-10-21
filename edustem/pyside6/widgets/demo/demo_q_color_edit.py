"""Démo : `QColorEdit` à l'horizontale et à la verticale, avec chaque réglage exposé à côté.

Les deux éditeurs partagent la même couleur et les mêmes réglages. Un `QLineEdit` placé
au-dessus sert de référence pour la hauteur. Trois barres de séparation donnent aux éditeurs
plus ou moins de place, dans les deux sens ; une case choisit s'ils la prennent.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpinBox, QSplitter, QStyleFactory, QVBoxLayout, QWidget,
)

from ..q_color_edit import QColorEdit


def main() -> int:
    app = QApplication(sys.argv)
    Space, Notation, Text = QColorEdit.ColorSpace, QColorEdit.ValueNotation, QColorEdit.TextDirection

    horizontal = QColorEdit(QColor(230, 120, 40, 200))
    vertical = QColorEdit(horizontal.color(), Qt.Orientation.Vertical)
    edits: tuple[QColorEdit, QColorEdit] = (horizontal, vertical)
    reference = QLineEdit("QLineEdit, for the height")

    # -- Displays ------------------------------------------------------------
    stateLabels: dict[str, QLabel] = {key: QLabel(wordWrap=True) for key in ("color", "channels", "size", "actual")}
    log = QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumBlockCount(300)
    errorLabel = QLabel()
    errorLabel.setStyleSheet("color: firebrick;")
    errorLabel.setWordWrap(True)

    def refreshState() -> None:
        color = horizontal.color()
        first, second = horizontal.plane()
        stateLabels["color"].setText(f"{color.name(QColor.NameFormat.HexArgb)}   rgba {color.getRgb()}")
        stateLabels["channels"].setText(
            f"{horizontal.colorSpace().name}: " + ", ".join(f"{v:.3f}" for v in horizontal.channelValues())
            + f"   currentChannel() = {horizontal.currentChannel()}   plane() = ({first}, {second})")
        stateLabels["size"].setText(
            f"sizeHint() = {horizontal.sizeHint().toTuple()}   minimumSizeHint() = {horizontal.minimumSizeHint().toTuple()}"
            f"   QLineEdit sizeHint() height = {reference.sizeHint().height()}")
        stateLabels["actual"].setText(
            f"horizontal {horizontal.size().toTuple()}   vertical {vertical.size().toTuple()}"
            f"   QLineEdit {reference.size().toTuple()}   devicePixelRatio = {horizontal.devicePixelRatioF():g}")

    def forBoth(method: Callable[[QColorEdit], object]) -> None:
        errorLabel.clear()
        try:
            for edit in edits:
                method(edit)
        except (ValueError, IndexError) as error:
            errorLabel.setText(f"Rejected: {error}")
        refreshState()

    # -- Signals of the editors: log, and the other one kept in step ------------
    def connectEdit(name: str, edit: QColorEdit, other: QColorEdit) -> None:
        def logLine(text: str) -> None:
            log.appendPlainText(f"{name:11} {text}")
            refreshState()

        edit.colorChanged.connect(lambda c: (other.setColor(c), logLine(f"colorChanged({c.name(QColor.NameFormat.HexArgb)})")))
        edit.colorSpaceChanged.connect(lambda s: (other.setColorSpace(s), spaceCombo.setCurrentIndex(spaceCombo.findData(s)),
                                                  logLine(f"colorSpaceChanged({s.name})")))
        edit.expandedChanged.connect(lambda on: (other.setExpanded(on), expandedCheck.setChecked(on),
                                                 logLine(f"expandedChanged({on})")))
        edit.alphaVisibleChanged.connect(lambda on: (other.setAlphaVisible(on), alphaVisibleCheck.setChecked(on),
                                                     logLine(f"alphaVisibleChanged({on})")))
        edit.planeVisibleChanged.connect(lambda on: (other.setPlaneVisible(on), planeVisibleCheck.setChecked(on),
                                                     logLine(f"planeVisibleChanged({on})")))
        edit.planeChanged.connect(lambda a, b: (other.setPlane(a, b), logLine(f"planeChanged({a}, {b})")))
        edit.valueNotationChanged.connect(lambda n: (other.setValueNotation(n), notationCombo.setCurrentIndex(notationCombo.findData(n)),
                                                     logLine(f"valueNotationChanged({n.name})")))

    # -- Configuration widgets ------------------------------------------------
    def combo(items: list[tuple[str, object]], apply: Callable[[object], object]) -> QComboBox:
        box = QComboBox()
        for text, data in items:
            box.addItem(text, data)
        box.currentIndexChanged.connect(lambda _: apply(box.currentData()))
        return box

    def check(text: str, checked: bool, apply: Callable[[QColorEdit, bool], object]) -> QCheckBox:
        box = QCheckBox(text)
        box.setChecked(checked)
        box.toggled.connect(lambda on: forBoth(lambda edit: apply(edit, on)))
        return box

    def spin(low: int, high: int, value: int, special: str, apply: Callable[[QColorEdit, int], object]) -> QSpinBox:
        box = QSpinBox()
        box.setRange(low, high)
        box.setValue(value)
        box.setSpecialValueText(special)
        box.valueChanged.connect(lambda v: forBoth(lambda edit: apply(edit, v)))
        return box

    spaceCombo = combo([(s.name, s) for s in Space], lambda s: forBoth(lambda edit: edit.setColorSpace(s)))
    notationCombo = combo([(n.name, n) for n in Notation], lambda n: forBoth(lambda edit: edit.setValueNotation(n)))
    textCombo = combo([(t.name, t) for t in Text], lambda t: forBoth(lambda edit: edit.setTextDirection(t)))
    textCombo.blockSignals(True)
    textCombo.setCurrentIndex(textCombo.findData(horizontal.textDirection()))
    textCombo.blockSignals(False)

    def setStyle(name: object) -> None:
        for widget in (*edits, reference):
            widget.setStyle(QStyleFactory.create(str(name)))    # one instance each: a widget does not own its style
        refreshState()
    styleCombo = combo([(name, name) for name in QStyleFactory.keys()], setStyle)
    styleCombo.blockSignals(True)
    styleCombo.setCurrentIndex(styleCombo.findText(app.style().objectName(), Qt.MatchFlag.MatchFixedString))
    styleCombo.blockSignals(False)

    fontSpin = QSpinBox()
    fontSpin.setRange(6, 24)
    fontSpin.setValue(app.font().pointSize())

    def setFontSize(points: int) -> None:
        for widget in (*edits, reference):
            font = widget.font()
            font.setPointSize(points)
            widget.setFont(font)
        refreshState()
    fontSpin.valueChanged.connect(setFontSize)

    swatchSpin = spin(0, 400, 0, "0 (automatic)", lambda edit, v: edit.setSwatchLength(v))
    textSpin = spin(0, 800, 0, "0 (natural)", lambda edit, v: edit.setTextWidth(v))
    textSpin.setToolTip("The width of the open text zone, left of the bands; never shown wider than its natural "
                        f"width ({horizontal.naturalTextWidth()} at the start).")
    horizontal.textWidthChanged.connect(lambda width: (textSpin.blockSignals(True), textSpin.setValue(width),
                                                       textSpin.blockSignals(False)))
    popupSpin = spin(0, 1000, 0, "0 (default)", lambda edit, v: edit.setPlanePopupSize(v))
    popupSpin.setToolTip(f"Clamped to [{horizontal.minimumPlanePopupSize()}, {horizontal.maximumPlanePopupSize()}].")
    pickers = [edit.screenColorPicker() for edit in edits]
    loupeSpin = spin(0, 1000, 0, "0 (default)", lambda edit, v: edit.screenColorPicker().setLoupeSize(v))
    loupeSpin.setToolTip(f"Clamped to [{pickers[0].minimumLoupeSize()}, {pickers[0].maximumLoupeSize()}].")
    zoomSpin = spin(2, 24, pickers[0].zoom(), "", lambda edit, v: edit.screenColorPicker().setZoom(v))
    sampleCombo = combo([(f"{side} × {side}" if side % 2 else f"disc, radius {side}", side) for side in range(1, 10)],
                        lambda side: forBoth(lambda edit: edit.screenColorPicker().setSampleSize(int(str(side)))))

    def setGrowing(grow: bool) -> None:
        """Lets the three widgets take the room across them, or keeps them at their recommended thickness."""
        across = QSizePolicy.Policy.Expanding if grow else QSizePolicy.Policy.Fixed
        for widget in (horizontal, reference):
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, across)
        vertical.setSizePolicy(across, QSizePolicy.Policy.Expanding)
    growCheck = QCheckBox("Expanding across (take the room the splitters give)")
    growCheck.toggled.connect(setGrowing)
    rightToLeftCheck = QCheckBox("Right-to-left layout")
    rightToLeftCheck.toggled.connect(lambda on: forBoth(lambda edit: edit.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft if on else Qt.LayoutDirection.LeftToRight)))

    availableChecks: dict[QColorEdit.ColorSpace, QCheckBox] = {}

    def applyAvailable() -> None:
        forBoth(lambda edit: edit.setAvailableColorSpaces([s for s, box in availableChecks.items() if box.isChecked()]))
    for space in Space:
        box = QCheckBox(space.name)
        box.setChecked(True)
        box.toggled.connect(lambda _: applyAvailable())
        availableChecks[space] = box

    expandedCheck = check("expanded", True, lambda edit, on: edit.setExpanded(on))
    alphaVisibleCheck = check("alphaVisible", False, lambda edit, on: edit.setAlphaVisible(on))
    planeVisibleCheck = check("planeVisible", False, lambda edit, on: edit.setPlaneVisible(on))
    textVisibleCheck = check("textVisible (the text zone, left of the bands)", False,
                             lambda edit, on: edit.setTextVisible(on))
    horizontal.textVisibleChanged.connect(lambda on: (textVisibleCheck.blockSignals(True), textVisibleCheck.setChecked(on),
                                                      textVisibleCheck.blockSignals(False), vertical.setTextVisible(on)))
    stateChecks: list[QCheckBox] = [
        expandedCheck,
        alphaVisibleCheck,
        planeVisibleCheck,
        textVisibleCheck,
        check("invertedAppearance", False, lambda edit, on: edit.setInvertedAppearance(on)),
        check("frame (drawn by the style)", True, lambda edit, on: edit.setFrame(on)),
        check("useAlpha", True, lambda edit, on: edit.setUseAlpha(on)),
        check("tracking (the colour follows the drag)", True, lambda edit, on: edit.setTracking(on)),
        check("dialogEnabled (the swatch opens the dialog)", True, lambda edit, on: edit.setDialogEnabled(on)),
        check("enabled", True, lambda edit, on: edit.setEnabled(on)),
    ]
    offerChecks: list[QCheckBox] = [
        check("expandToggleVisible", True, lambda edit, on: edit.setExpandToggleVisible(on)),
        check("alphaToggleVisible", True, lambda edit, on: edit.setAlphaToggleVisible(on)),
        check("colorSpaceLabelVisible", True, lambda edit, on: edit.setColorSpaceLabelVisible(on)),
        check("notationToggleVisible", False, lambda edit, on: edit.setNotationToggleVisible(on)),
        check("planeToggleVisible", True, lambda edit, on: edit.setPlaneToggleVisible(on)),
        check("swatchHandleVisible", True, lambda edit, on: edit.setSwatchHandleVisible(on)),
        check("textHandleVisible", True, lambda edit, on: edit.setTextHandleVisible(on)),
    ]
    eyedropperCombo = combo([(button.name, button) for button in QColorEdit.EyedropperButton],
                            lambda button: forBoth(lambda edit: edit.setEyedropperButton(button)))
    eyedropperCombo.blockSignals(True)
    eyedropperCombo.setCurrentIndex(eyedropperCombo.findData(horizontal.eyedropperButton()))
    eyedropperCombo.blockSignals(False)

    def presetButton(text: str, action: Callable[[QColorEdit], object]) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(lambda: forBoth(action))
        return button

    scenarios: list[QPushButton] = [
        presetButton("Tomato, opaque", lambda edit: edit.setColor(QColor("tomato"))),
        presetButton("Steel blue, half transparent", lambda edit: edit.setColor(QColor(70, 130, 180, 128))),
        presetButton("Grey (the hue on display is kept)", lambda edit: edit.setColor(QColor(128, 128, 128))),
        presetButton("Black (hue and saturation are kept)", lambda edit: edit.setColor(QColor(0, 0, 0))),
        presetButton("A CMYK colour (the space on display is kept)",
                     lambda edit: edit.setColor(QColor.fromCmykF(0.1, 0.6, 0.9, 0.2))),
        presetButton("Invalid colour (ignored)", lambda edit: edit.setColor(QColor())),
        presetButton("First channel to 0.5", lambda edit: edit.setChannelValue(0, 0.5)),
        presetButton("Channel 7 to 0.5 (rejected)", lambda edit: edit.setChannelValue(7, 0.5)),
        presetButton("Next plane", lambda edit: edit.setPlane(*edit.planes()[(edit.planes().index(edit.plane()) + 1)
                                                                          % len(edit.planes())])),
        presetButton("Plane (0, 0) (rejected)", lambda edit: edit.setPlane(0, 0)),
        presetButton("No colour space at all (rejected)", lambda edit: edit.setAvailableColorSpaces([])),
    ]
    popupButton = QPushButton("Open the plane popup (horizontal)")
    popupButton.clicked.connect(horizontal.showPlanePopup)
    pickButton = QPushButton("Pick a screen colour (horizontal)")
    pickButton.clicked.connect(horizontal.pickScreenColor)
    typeButton = QPushButton("Type the values (horizontal, editAsText, F2)")
    typeButton.clicked.connect(horizontal.editAsText)
    clearButton = QPushButton("Clear log")
    clearButton.clicked.connect(log.clear)

    # -- Layout --------------------------------------------------------------
    # The stage: three splitters give the editors more or less room, along them and across them.
    horizontalPane = QWidget()
    horizontalLayout = QVBoxLayout(horizontalPane)
    horizontalLayout.addWidget(reference)
    horizontalLayout.addWidget(horizontal)
    verticalPane = QWidget()
    QHBoxLayout(verticalPane).addWidget(vertical)

    hint = QLabel("Hover any part for its tooltip. Drag a grip; a click elsewhere in a band pages toward the pointer "
                  "(Shift+click jumps); the wheel sets the band under the pointer. Keyboard: the arrows across the bands "
                  "pick a channel, the arrows along them set it. Show the plane with the last arrow, then click it to "
                  "open it. The folded corner of the swatch is the eyedropper: click it, or press it, drag to a colour "
                  "and release. The narrow dotted handles: after the swatch, its length (double-click: automatic); "
                  "left of the bands, the values as text (click to open or close, drag for the width, F2). I starts "
                  "the eyedropper, P opens the plane; Ctrl+C and Ctrl+V copy and paste the colour. Drag the splitter "
                  "handles to resize the editors.")
    hint.setWordWrap(True)
    stateBox = QGroupBox("State (read from the horizontal editor)")
    stateLayout = QFormLayout(stateBox)
    for label, key in (("color():", "color"), ("channelValues():", "channels"), ("Recommended:", "size"),
                       ("Actual sizes:", "actual")):
        stateLayout.addRow(label, stateLabels[key])
    reportPane = QWidget()
    reportLayout = QVBoxLayout(reportPane)
    reportLayout.addWidget(hint)
    reportLayout.addWidget(stateBox)
    reportLayout.addWidget(QLabel("Log:"))
    reportLayout.addWidget(log, 1)

    leftSplitter = QSplitter(Qt.Orientation.Vertical)      # across the horizontal editor
    leftSplitter.addWidget(horizontalPane)
    leftSplitter.addWidget(reportPane)
    leftSplitter.setStretchFactor(1, 1)
    stageSplitter = QSplitter(Qt.Orientation.Horizontal)   # along the horizontal editor, across the vertical one
    stageSplitter.addWidget(leftSplitter)
    stageSplitter.addWidget(verticalPane)
    stageSplitter.setStretchFactor(0, 1)
    for splitter in (leftSplitter, stageSplitter):
        splitter.setChildrenCollapsible(False)
        splitter.splitterMoved.connect(lambda *_: refreshState())

    configBox = QGroupBox("Configuration (applied to both)")
    configLayout = QFormLayout(configBox)
    configLayout.addRow("colorSpace:", spaceCombo)
    availableRow = QHBoxLayout()
    for box in availableChecks.values():
        availableRow.addWidget(box)
    configLayout.addRow("available:", availableRow)
    configLayout.addRow("valueNotation:", notationCombo)
    configLayout.addRow("textDirection:", textCombo)
    configLayout.addRow("swatchLength:", swatchSpin)
    configLayout.addRow("textWidth:", textSpin)
    configLayout.addRow("planePopupSize:", popupSpin)
    configLayout.addRow("eyedropperButton:", eyedropperCombo)
    configLayout.addRow("eyedropper loupeSize:", loupeSpin)
    configLayout.addRow("eyedropper zoom:", zoomSpin)
    configLayout.addRow("eyedropper sampleSize:", sampleCombo)
    configLayout.addRow("style:", styleCombo)
    configLayout.addRow("font size:", fontSpin)
    configLayout.addRow(growCheck)
    configLayout.addRow(rightToLeftCheck)
    for box in stateChecks:
        configLayout.addRow(box)
    configLayout.addRow(errorLabel)

    offerBox = QGroupBox("Toggles on offer")
    offerLayout = QVBoxLayout(offerBox)
    for box in offerChecks:
        offerLayout.addWidget(box)
    scenariosBox = QGroupBox("Scenarios")
    scenariosLayout = QVBoxLayout(scenariosBox)
    for button in (*scenarios, popupButton, pickButton, typeButton, clearButton):
        scenariosLayout.addWidget(button)

    sidePane = QWidget()
    sideLayout = QHBoxLayout(sidePane)
    for boxes in ((configBox,), (offerBox, scenariosBox)):
        column = QVBoxLayout()
        for box in boxes:
            column.addWidget(box)
        column.addStretch(1)
        sideLayout.addLayout(column)

    mainWindow = QSplitter(Qt.Orientation.Horizontal)      # the stage against the settings
    mainWindow.addWidget(stageSplitter)
    mainWindow.addWidget(sidePane)
    mainWindow.setStretchFactor(0, 1)
    mainWindow.setChildrenCollapsible(False)
    mainWindow.splitterMoved.connect(lambda *_: refreshState())

    connectEdit("horizontal", horizontal, vertical)
    connectEdit("vertical", vertical, horizontal)
    mainWindow.setWindowTitle("QColorEdit Demo")
    mainWindow.resize(1400, 760)
    mainWindow.show()
    refreshState()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
