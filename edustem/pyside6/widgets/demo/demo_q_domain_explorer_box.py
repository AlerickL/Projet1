"""Démo : navigation dans une liste et dans des widgets Qt standards avec
QDomainExplorerBox.

Le thème (clair/sombre) suit celui du système au démarrage et en direct s'il
change pendant l'exécution. La palette est celle du style courant, avec repli
sur une palette sombre codée en dur pour les styles qui n'en ont pas (voir
`applyColorScheme()`).
"""

from __future__ import annotations

import html
import sys
from typing import override

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette, QResizeEvent
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QRadioButton, QScrollBar, QSizePolicy, QSlider,
    QSpinBox, QStyleFactory, QTabBar, QTabWidget, QToolBox, QVBoxLayout, QWidget,
)

from ..q_domain_explorer_box import (
    QButtonDomainBinding, QSliderDomainBinding, QButtonGroupDomainBinding,
    QCallbackDomainBinding, QComboBoxDomainBinding, QCurrentIndexDomainBinding, QDomainBinding,
    QDomainExplorerBox, QDoubleSpinBoxDomainBinding, QListViewDomainBinding, QSpinBoxDomainBinding,
)

MAB: type[QDomainExplorerBox] = QDomainExplorerBox


def darkPalette() -> QPalette:
    """Palette sombre de secours, pour les plateformes sans thème système."""
    p = QPalette()
    roles: dict[QPalette.ColorRole, str] = {
        QPalette.ColorRole.Window: "#2b2b2b", QPalette.ColorRole.WindowText: "#e6e6e6",
        QPalette.ColorRole.Base: "#1f1f1f", QPalette.ColorRole.AlternateBase: "#2b2b2b",
        QPalette.ColorRole.Button: "#353535", QPalette.ColorRole.ButtonText: "#e6e6e6",
        QPalette.ColorRole.Text: "#e6e6e6", QPalette.ColorRole.Highlight: "#3d8fd6",
        QPalette.ColorRole.HighlightedText: "#ffffff", QPalette.ColorRole.ToolTipBase: "#353535",
        QPalette.ColorRole.ToolTipText: "#e6e6e6", QPalette.ColorRole.Mid: "#4a4a4a",
    }
    for role, color in roles.items():
        p.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText, QPalette.ColorRole.Text):
        p.setColor(QPalette.ColorGroup.Disabled, role, QColor("#7a7a7a"))
    return p


def applyColorScheme(dark: bool) -> None:
    """Demande le schéma clair ou sombre (Qt ≥ 6.8) et laisse le style fournir sa palette.

    `setPalette(QPalette())` rend la main à la palette du style pour ce schéma :
    windows11 et Fusion ont chacun leur version claire et sombre. Imposer
    `style().standardPalette()` figerait au contraire la palette Windows
    classique, claire, quel que soit le schéma. La palette sombre de secours ne
    sert qu'aux styles sans version sombre (ex. windowsvista).
    """
    hints = QGuiApplication.styleHints()
    hints.setColorScheme(Qt.ColorScheme.Dark if dark else Qt.ColorScheme.Light)
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    app.setPalette(QPalette())
    if dark and app.palette().color(QPalette.ColorRole.Window).lightnessF() > 0.5:
        app.setPalette(darkPalette())


def richToolTip(text: str) -> str:
    """Met une infobulle en texte riche, pour que Qt en replie les lignes.

    Qt n'applique le retour à la ligne qu'au texte riche : en texte brut, une
    longue infobulle tient sur une seule ligne, parfois large comme l'écran.
    Un préfixe d'appel (« setPreferredWidth(): … ») devient un titre en gras,
    le reste un paragraphe.

    Args:
        text: Texte brut de l'infobulle.

    Retourne:
        Le même texte, en HTML.
    """
    head, separator, body = text.partition(": ")
    if separator and head.endswith(")"):
        body = body[:1].upper() + body[1:]
        return f"<p><b>{html.escape(head)}</b></p><p>{html.escape(body)}</p>"
    return f"<p>{html.escape(text)}</p>"


class QListBindingPage(QWidget):
    """Terrain de jeu : un QDomainExplorerBox relié à une liste, et ses réglages par thème.

    À gauche, on observe et on joue : le widget, la liste qu'il pilote (via
    QCallbackDomainBinding) et le journal des signaux émis. À droite, on règle
    le widget lui-même : une section repliable par aspect.
    """

    _DefaultRow: int = 3
    _LogSize: int = 100
    _ActionPurposes: dict[MAB.Action, str] = {
        MAB.Action.ResetToDefault: "Moves the domain to its default value (binding.resetToDefault()).",
        MAB.Action.Randomize: "Moves the domain to a random position (binding.randomIndex()).",
        MAB.Action.AnimWrap: "Steps right one position at a time, back to the start after the last.",
        MAB.Action.AnimBounce: "Steps back and forth, turning around at each end.",
    }
    _SectionPurposes: tuple[str, ...] = (
        "How many positions the axis offers, and which ones are shown or clickable.",
        "Which action buttons are shown or clickable.",
        "Pace of the wrap and bounce animations.",
        "The calls that reproduce each gesture exactly, as code would use them.",
        "The widths involved in laying out the widget, and live measurements.",
        "The optional button that collapses the widget down to itself.",
        "Change the list the explorer drives, and its default row, while it runs.",
        "Theme, style and enabled state: the widget follows them all.",
    )

    def __init__(self) -> None:
        super().__init__()

        self.__list = QListWidget()
        self.__list.addItems([f"Value {i:02d}" for i in range(1, 13)])
        self.__list.setCurrentRow(self._DefaultRow)
        self.__list.setToolTip(richToolTip('The domain driven by the explorer, through a QCallbackDomainBinding: each row is a position.'))

        self.__button = QDomainExplorerBox()
        # All the "widget signal -> move within the list" mechanics are delegated
        # to a QDomainBinding, built independently of the widget then attached via
        # setBinding() (like a QLayout built then installed via setLayout()).
        self.__binding = QCallbackDomainBinding(
            self.__list,
            index=self.__list.currentRow, setIndex=self.__list.setCurrentRow, size=self.__list.count,
            defaultValue=self._DefaultRow,
        )
        self.__button.setBinding(self.__binding)

        self.__log = QListWidget()
        self.__log.setToolTip(richToolTip('Every signal emitted by the explorer, newest at the bottom. One gesture may emit several signals.'))
        self.__sizeInfo = QLabel()
        self.__connectLog()

        intro = QLabel("The explorer widget just below drives the list underneath it. Click a "
                       "position on its axis, reset, randomize or start an animation, and watch "
                       "the list follow; every signal the explorer emits is logged at the bottom. "
                       "The settings on the right control the explorer itself.")
        intro.setWordWrap(True)

        top = QHBoxLayout()
        top.addWidget(self.__button)
        # No addStretch() here: without it, it is solely the button's horizontal size
        # policy (Sizes section) that decides whether it claims the space freed by
        # resizing the window, or leaves it empty next to itself.

        self.__markersBox = QWidget()
        self.__markersGrid = QGridLayout()
        sections = QToolBox()
        sections.addItem(self.__buildMarkers(), "Markers")
        sections.addItem(self.__buildActions(), "Action buttons")
        sections.addItem(self.__buildAnimation(), "Animation")
        sections.addItem(self.__buildProgrammatic(), "Programmatic API")
        sections.addItem(self.__buildSizes(), "Sizes")
        sections.addItem(self.__buildCollapse(), "Collapse")
        sections.addItem(self.__buildDomain(), "Domain")
        sections.addItem(self.__buildAppearance(), "Appearance")
        for index, purpose in enumerate(self._SectionPurposes):
            sections.setItemToolTip(index, richToolTip(purpose))

        # Left: observe and play with the widget. Right: control the widget itself.
        observe = QVBoxLayout()
        observe.addWidget(intro)
        observe.addLayout(top)
        observe.addWidget(self.__list, 1)
        observe.addWidget(QLabel("Signals:"))
        observe.addWidget(self.__log, 1)
        control = QVBoxLayout()
        control.addWidget(QLabel("Widget settings:"))
        control.addWidget(sections, 1)
        layout = QHBoxLayout(self)
        layout.addLayout(observe, 3)
        layout.addLayout(control, 2)
        self.__rebuildMarkerControls()
        self.__refreshSizeInfo()

        # Initial state determined by the system rather than left to the style's
        # default palette, and tracked live if the system theme changes afterwards.
        hints = QGuiApplication.styleHints()
        self.__syncColorScheme(hints.colorScheme())
        hints.colorSchemeChanged.connect(self.__syncColorScheme)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        # It really is the resizing of THE WINDOW (not a control) that makes
        # width() vary here: that is exactly the behavior we want to observe.
        self.__refreshSizeInfo()

    # ------------------------------------------------------------------ sections

    def __buildMarkers(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()
        count = QSpinBox()
        count.setRange(2, 9)
        count.setValue(self.__button.markerCount())
        count.valueChanged.connect(self.__onMarkerCount)
        count.setToolTip(richToolTip('setMarkerCount(): number of markers on the axis (at least 2). Marker i sits at i / (count − 1); the binding maps it to the nearest list row.'))
        form.addRow("Marker count", count)
        layout.addLayout(form)
        self.__markersBox.setLayout(self.__markersGrid)
        layout.addWidget(self.__markersBox)
        layout.addStretch()
        return page

    def __buildActions(self) -> QWidget:
        page = QWidget()
        grid = QGridLayout(page)
        grid.addWidget(QLabel("Name"), 0, 0)
        grid.addWidget(QLabel("Enabled"), 0, 1)
        grid.addWidget(QLabel("Visible"), 0, 2)
        for row, action in enumerate(MAB.Action, start=1):
            name = QLabel(action.name)
            name.setToolTip(richToolTip(self._ActionPurposes[action]))
            grid.addWidget(name, row, 0)
            enabled = QCheckBox()
            enabled.setChecked(True)
            enabled.toggled.connect(lambda on, a=action: self.__button.setActionEnabled(a, on))
            enabled.setToolTip(richToolTip('setActionEnabled(): a disabled button is dimmed and ignores clicks and directives.'))
            grid.addWidget(enabled, row, 1)
            visible = QCheckBox()
            visible.setChecked(True)
            visible.toggled.connect(lambda on, a=action: self.__button.setActionVisible(a, on))
            visible.setToolTip(richToolTip('setActionVisible(): a hidden button takes no width; minimumSizeHint() shrinks accordingly.'))
            visible.toggled.connect(lambda _: self.__refreshSizeInfo())
            grid.addWidget(visible, row, 2)
        grid.setRowStretch(len(MAB.Action) + 1, 1)
        return page

    def __buildAnimation(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow(self.__note("Each step moves the list by one row. Two settings set the pace, "
                                "with or without a binding: the base interval, chosen by the "
                                "programmer, and the speed factor, adjusted by the user."))
        interval = QSpinBox()
        interval.setRange(10, 5000)
        interval.setSingleStep(50)
        interval.setSuffix(" ms")
        interval.setValue(round(self.__button.stepInterval()))
        interval.valueChanged.connect(self.__button.setStepInterval)
        interval.setToolTip(richToolTip("setStepInterval(): the base pace, a programmer's setting: time "
                                        "between two steps at speed ×1 (500 ms by default). Takes effect "
                                        "from the next step, even while running. A leader does not relay it."))
        form.addRow("Base interval", interval)
        speed = QDoubleSpinBox()
        low, high = self.__button.speedFactorRange()
        speed.setRange(low, high)
        speed.setSingleStep(0.25)
        speed.setPrefix("×")
        speed.setValue(self.__button.speedFactor())
        speed.valueChanged.connect(self.__button.setSpeedFactor)
        speed.setToolTip(richToolTip("setSpeedFactor(): the user's adjustment, relative to the base "
                                     "interval and bounded by speedFactorRange(). The +/− keys multiply "
                                     "or divide it by speedFactorStep() (×1.25). A leader relays it."))

        def showSpeed(factor: float) -> None:
            # Display only: echoing the rounded value back would overwrite the exact
            # factor set by the +/− keys (1.5625 shown as 1.56).
            speed.blockSignals(True)
            speed.setValue(factor)
            speed.blockSignals(False)

        self.__button.speedFactorChanged.connect(showSpeed)
        form.addRow("Speed factor", speed)
        effective = QLabel()
        effective.setToolTip(richToolTip("The resulting pace: stepInterval() / speedFactor()."))

        def refreshEffective() -> None:
            ms = self.__button.stepInterval() / self.__button.speedFactor()
            effective.setText(f"one step every {ms:.0f} ms")

        interval.valueChanged.connect(refreshEffective)
        self.__button.speedFactorChanged.connect(refreshEffective)
        refreshEffective()
        form.addRow("Actual pace", effective)
        form.addRow(self.__note("Keyboard, while the explorer has focus: +/− change the speed, "
                                "Esc stops the animation."))
        return page

    def __buildProgrammatic(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow(self.__note("Same path as a click: same rules, signals and rendering."))

        marker = QSpinBox()
        marker.setRange(0, self.__button.markerCount() - 1)
        self.__button.markerActivated.connect(marker.setValue)
        self.__programmaticMarker = marker
        marker.setToolTip(richToolTip('Index of the marker to activate.'))
        activateMarker = QPushButton("activateMarker")
        activateMarker.clicked.connect(lambda: self.__button.activateMarker(marker.value()))
        activateMarker.setToolTip(richToolTip('activateMarker(i): exactly like clicking marker i. A running animation stops first.'))
        form.addRow(self.__row(marker, activateMarker))

        action = QComboBox()
        for a in MAB.Action:
            action.addItem(a.name, a)
        activateAction = QPushButton("activateAction")
        activateAction.clicked.connect(lambda: self.__button.activateAction(action.currentData()))
        activateAction.setToolTip(richToolTip('activateAction(action): exactly like clicking that button. Reset and randomize act at once; an animation button starts its animation, or stops it if it is the one running.'))
        form.addRow(self.__row(action, activateAction))

        mode = QComboBox()
        for m in MAB.AnimationMode:
            mode.addItem(m.name, m)
        start = QPushButton("startAnimation")
        start.clicked.connect(lambda: self.__button.startAnimation(mode.currentData()))
        start.setToolTip(richToolTip('startAnimation(mode): sets a state, like setChecked(). No effect if that mode already runs; switches if the other mode runs.'))
        stop = QPushButton("stopAnimation")
        stop.clicked.connect(self.__button.stopAnimation)
        stop.setToolTip(richToolTip('stopAnimation(): stops in place; the domain keeps its current position.'))
        form.addRow(self.__row(mode, start, stop))
        return page

    def __buildSizes(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        preferred = QSpinBox()
        preferred.setRange(0, 800)
        preferred.setSingleStep(10)
        preferred.setSpecialValueText("auto")
        preferred.setSuffix(" px")
        preferred.valueChanged.connect(lambda v: self.__button.setPreferredWidth(v or None))
        preferred.setToolTip(richToolTip('setPreferredWidth(): the width the widget suggests to its layout, through sizeHint(). A suggestion, not a constraint: the layout may still grow it or shrink it down to minimumSizeHint(). Extra width goes to the axis. auto = None, the most compact width.'))
        preferred.valueChanged.connect(lambda _: self.__refreshSizeInfo())
        form.addRow("Preferred width", preferred)

        buttonWidth = QSpinBox()
        buttonWidth.setRange(0, 40)
        buttonWidth.setSpecialValueText("auto")
        buttonWidth.setSuffix(" px")
        buttonWidth.valueChanged.connect(lambda v: self.__button.setButtonWidth(v or None))
        buttonWidth.setToolTip(richToolTip('setButtonWidth(): width of each action button. auto = 18 px; never below 16 px; 16 to 24 px recommended.'))
        buttonWidth.valueChanged.connect(lambda _: self.__refreshSizeInfo())
        form.addRow("Button width", buttonWidth)

        markerWidth = QSpinBox()
        markerWidth.setRange(0, 60)
        markerWidth.setSpecialValueText("auto")
        markerWidth.setSuffix(" px")
        markerWidth.valueChanged.connect(lambda v: self.__button.setMarkerWidth(v or None))
        markerWidth.setToolTip(richToolTip('setMarkerWidth(): minimum width per marker; the axis needs at least n times this width. auto = buttonWidth().'))
        markerWidth.valueChanged.connect(lambda _: self.__refreshSizeInfo())
        form.addRow("Min. marker width", markerWidth)

        sizePolicyCombo = QComboBox()
        # Without this, the combo sizes itself to its longest item
        # ("MinimumExpanding") and becomes, on its own, the width bottleneck for
        # the whole page; the full name stays readable in the dropdown list.
        sizePolicyCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        sizePolicyCombo.setMinimumContentsLength(10)
        for policy in QSizePolicy.Policy:
            sizePolicyCombo.addItem(policy.name, policy)
        sizePolicyCombo.setCurrentText(self.__button.sizePolicy().horizontalPolicy().name)

        def applySizePolicy(index: int) -> None:
            horizontal: QSizePolicy.Policy = sizePolicyCombo.itemData(index)
            self.__button.setSizePolicy(horizontal, self.__button.sizePolicy().verticalPolicy())
            self.__button.updateGeometry()
            self.__refreshSizeInfo()

        sizePolicyCombo.currentIndexChanged.connect(applySizePolicy)
        sizePolicyCombo.setToolTip(richToolTip('Horizontal QSizePolicy: how the layout uses sizeHint(). Preferred (default) keeps it unless space runs short; Expanding takes any free space; Fixed sticks to sizeHint().'))
        form.addRow("Size policy", sizePolicyCombo)
        self.__sizeInfo.setToolTip(richToolTip('Live measurements. width() is what the layout gave the widget; sizeHint() and minimumSizeHint() are what the widget asks for.'))
        form.addRow(self.__sizeInfo)
        return page

    def __buildCollapse(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        collapsible = QCheckBox("Collapsible")
        collapsible.setChecked(self.__button.isCollapsible())
        collapsible.toggled.connect(self.__button.setCollapsible)
        collapsible.setToolTip(richToolTip('setCollapsible(): shows the collapse button (the default). Unchecked, the widget cannot collapse.'))
        collapsible.toggled.connect(lambda _: self.__refreshSizeInfo())
        form.addRow(collapsible)
        collapsed = QCheckBox("Collapsed")
        collapsed.toggled.connect(self.__button.setCollapsed)
        collapsed.setToolTip(richToolTip('setCollapsed(): same as clicking the collapse button. Collapsed, only that button shows; a running animation goes on.'))
        self.__button.collapsedChanged.connect(collapsed.setChecked)  # the button changes it too
        form.addRow(collapsed)
        side = QComboBox()
        for position in MAB.CollapseButtonPosition:
            side.addItem(position.name, position)
        side.currentIndexChanged.connect(lambda i: self.__button.setCollapseButtonPosition(side.itemData(i)))
        side.setToolTip(richToolTip('setCollapseButtonPosition(): collapse button at the left (default) or right end.'))
        form.addRow("Button side", side)
        return page

    def __buildDomain(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        addItem = QPushButton("Add item")
        addItem.clicked.connect(self.__onAddItem)
        addItem.setToolTip(richToolTip('Appends a row to the list. The binding reads the size at each use, so the explorer adapts live.'))
        form.addRow(addItem)
        form.addRow(self.__note("The binding reads the list size at each use: "
                                "markers, randomize and animations follow it live."))

        defaultRow = QSpinBox()
        defaultRow.setRange(0, self.__list.count() - 1)
        defaultRow.setValue(self.__binding.defaultValue())
        defaultRow.valueChanged.connect(self.__binding.setDefaultValue)
        defaultRow.setToolTip(richToolTip('setDefaultValue(): where the reset button sends the domain. For a list, '
                                          'the value of a position is its row. The binding stores the value only; '
                                          'defaultIndex() is derived from it at each use.'))
        self.__defaultRow = defaultRow
        form.addRow("Default row", defaultRow)
        unset = QPushButton("unsetDefaultValue")
        unset.clicked.connect(self.__binding.unsetDefaultValue)
        unset.setToolTip(richToolTip('unsetDefaultValue(): no default value any more; reset goes to the first position.'))

        def showDefaultRow(row: int) -> None:
            # Display only: echoing the row back would define the default again,
            # right after unsetDefaultValue() left it undefined.
            defaultRow.blockSignals(True)
            defaultRow.setValue(row)
            defaultRow.blockSignals(False)

        self.__binding.defaultValueChanged.connect(showDefaultRow)
        form.addRow(unset)
        return page

    def __buildAppearance(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.__darkCheckBox = QCheckBox("Dark theme")
        self.__darkCheckBox.toggled.connect(applyColorScheme)
        self.__darkCheckBox.setToolTip(richToolTip('Light or dark palette. The explorer takes all its colors from the palette.'))
        form.addRow(self.__darkCheckBox)

        # The widget's look follows the style: windows11 draws its glyphs from
        # the style's icon font, any other style gets stroke-drawn glyphs.
        styleCombo = QComboBox()
        styleCombo.addItems(QStyleFactory.keys())
        styleCombo.setCurrentText(QApplication.style().name())

        def applyStyle(name: str) -> None:
            QApplication.setStyle(name)
            applyColorScheme(self.__darkCheckBox.isChecked())

        styleCombo.currentTextChanged.connect(applyStyle)
        styleCombo.setToolTip(richToolTip('Application style. windows11 draws the glyphs with its icon font; other styles get stroke-drawn equivalents.'))
        form.addRow("Style", styleCombo)

        enabled = QCheckBox("Widget enabled")
        enabled.setChecked(True)
        enabled.toggled.connect(self.__button.setEnabled)
        enabled.setToolTip(richToolTip('QWidget.setEnabled(): a disabled explorer ignores every gesture and directive; a running animation stops.'))
        form.addRow(enabled)
        return page

    # ------------------------------------------------------------------- helpers

    @staticmethod
    def __note(text: str) -> QLabel:
        """Texte explicatif d'une section, replié à la largeur de la colonne."""
        label = QLabel(text)
        label.setWordWrap(True)
        return label

    @staticmethod
    def __row(*widgets: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        for widget in widgets:
            row.addWidget(widget)
        return row

    def __connectLog(self) -> None:
        b = self.__button
        b.markerActivated.connect(lambda i: self.__logSignal(f"markerActivated({i})"))
        b.positionRequested.connect(lambda t: self.__logSignal(f"positionRequested({t:g})"))
        b.triggered.connect(lambda a: self.__logSignal(f"triggered({a.name})"))
        b.animationStateChanged.connect(
            lambda s: self.__logSignal(f"animationStateChanged({s.name})"
                                       + (f" · {b.animationMode().name}" if b.animationMode() else "")))
        b.speedFactorChanged.connect(lambda f: self.__logSignal(f"speedFactorChanged({f:.2f})"))
        b.collapsedChanged.connect(lambda c: self.__logSignal(f"collapsedChanged({c})"))
        b.collapsedChanged.connect(lambda _: self.__refreshSizeInfo())
        self.__binding.defaultValueChanged.connect(
            lambda v: self.__logSignal(f"binding.defaultValueChanged({v})"))

    def __logSignal(self, text: str) -> None:
        self.__log.addItem(text)
        while self.__log.count() > self._LogSize:
            self.__log.takeItem(0)
        self.__log.scrollToBottom()

    def __syncColorScheme(self, scheme: Qt.ColorScheme) -> None:
        """Reflète le thème système (appelée au démarrage et à chaque
        changement en direct via `colorSchemeChanged`) sur la case à cocher et
        la palette de l'application.
        """
        isDark = scheme == Qt.ColorScheme.Dark
        self.__darkCheckBox.blockSignals(True)
        self.__darkCheckBox.setChecked(isDark)
        self.__darkCheckBox.blockSignals(False)
        applyColorScheme(isDark)

    def __refreshSizeInfo(self) -> None:
        # One line per measurement rather than a single concatenated line: the
        # label's natural width then follows its longest line, not the sum
        # of all of them — otherwise it would stop the page from shrinking below that width.
        b = self.__button
        preferred = b.preferredWidth()
        self.__sizeInfo.setText(
            f"width(): {b.width()}px\n"
            f"sizeHint(): {b.sizeHint().width()}px\n"
            f"minimumSizeHint(): {b.minimumSizeHint().width()}px\n"
            f"preferredWidth(): {'None' if preferred is None else f'{preferred}px'}\n"
            f"buttonWidth(): {b.buttonWidth()}px · markerWidth(): {b.markerWidth()}px"
        )

    def __rebuildMarkerControls(self) -> None:
        while (item := self.__markersGrid.takeAt(0)) is not None:
            if (w := item.widget()) is not None:
                w.deleteLater()
        self.__markersGrid.addWidget(QLabel("Position"), 0, 0)
        self.__markersGrid.addWidget(QLabel("Enabled"), 0, 1)
        self.__markersGrid.addWidget(QLabel("Visible"), 0, 2)
        for i in range(self.__button.markerCount()):
            row = i + 1
            self.__markersGrid.addWidget(QLabel(f"{self.__button.markerPosition(i):.0%}"), row, 0)
            enabled = QCheckBox()
            enabled.setChecked(self.__button.isMarkerEnabled(i))
            enabled.toggled.connect(lambda on, k=i: self.__button.setMarkerEnabled(k, on))
            enabled.setToolTip(richToolTip('setMarkerEnabled(): a disabled marker ignores clicks and directives.'))
            self.__markersGrid.addWidget(enabled, row, 1)
            visible = QCheckBox()
            visible.setChecked(self.__button.isMarkerVisible(i))
            visible.toggled.connect(lambda on, k=i: self.__button.setMarkerVisible(k, on))
            visible.setToolTip(richToolTip('setMarkerVisible(): a hidden marker keeps its place on the axis but is neither drawn nor clickable.'))
            self.__markersGrid.addWidget(visible, row, 2)

    # ------------------------------------------------------------------ handlers

    def __onAddItem(self) -> None:
        self.__list.addItem(f"Value {self.__list.count() + 1:02d}")
        self.__defaultRow.setMaximum(self.__list.count() - 1)
        self.__logSignal(f"(list now has {self.__list.count()} items)")

    def __onMarkerCount(self, count: int) -> None:
        self.__button.setMarkerCount(count)
        self.__programmaticMarker.setRange(0, self.__button.markerCount() - 1)
        self.__rebuildMarkerControls()
        self.__refreshSizeInfo()


class QWidgetBindingsPage(QWidget):
    """Illustre chaque implémentation prête à l'emploi de QDomainBinding, reliée
    à une instance du widget Qt standard correspondant.
    """

    def __init__(self) -> None:
        super().__init__()
        intro = QLabel("Each row ties an explorer to a standard Qt widget through the "
                       "ready-made binding named in its title: markers, reset, randomize "
                       "and animations all act on that widget, with no extra code. Each binding "
                       "is given a default value in its widget's own terms (a slider value, a "
                       "checked state, a row): reset goes back to it.")
        intro.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addWidget(self.__sliderRow())
        layout.addWidget(self.__checkBoxRow())
        layout.addWidget(self.__comboBoxRow())
        layout.addWidget(self.__listRow())
        layout.addWidget(self.__spinBoxRow())
        layout.addWidget(self.__doubleSpinBoxRow())
        layout.addWidget(self.__tabBarRow())
        layout.addWidget(self.__buttonGroupRow())
        layout.addStretch()

    @staticmethod
    def __row[T, V](title: str, element: QWidget, binding: QDomainBinding[T, V]) -> QGroupBox:
        box = QGroupBox(title)
        button = QDomainExplorerBox()
        button.setBinding(binding)
        layout = QHBoxLayout(box)
        layout.addWidget(element)
        layout.addWidget(button)
        return box

    def __sliderRow(self) -> QGroupBox:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 10)
        return self.__row("QSlider (QSliderDomainBinding), default 5", slider,
                           QSliderDomainBinding(slider, defaultValue=5))

    def __checkBoxRow(self) -> QGroupBox:
        checkBox = QCheckBox("Enabled")
        return self.__row("QCheckBox (QButtonDomainBinding), default checked", checkBox,
                           QButtonDomainBinding(checkBox, defaultValue=True))

    def __comboBoxRow(self) -> QGroupBox:
        combo = QComboBox()
        combo.addItems(["Red", "Green", "Blue", "Yellow", "Purple"])
        return self.__row("QComboBox (QComboBoxDomainBinding), default Blue", combo,
                           QComboBoxDomainBinding(combo, defaultValue=2))

    def __listRow(self) -> QGroupBox:
        listWidget = QListWidget()
        listWidget.addItems([f"Row {i}" for i in range(6)])
        listWidget.setMaximumHeight(100)
        return self.__row("QListWidget (QListViewDomainBinding), default Row 3", listWidget,
                           QListViewDomainBinding(listWidget, defaultValue=3))

    def __spinBoxRow(self) -> QGroupBox:
        spin = QSpinBox()
        spin.setRange(0, 20)
        return self.__row("QSpinBox (QSpinBoxDomainBinding), default 10", spin,
                           QSpinBoxDomainBinding(spin, defaultValue=10))

    def __doubleSpinBoxRow(self) -> QGroupBox:
        dspin = QDoubleSpinBox()
        dspin.setRange(0.0, 1.0)
        dspin.setSingleStep(0.1)
        # 0.25 sits between two positions of the domain (step 0.1): reset restores it exactly.
        return self.__row("QDoubleSpinBox (QDoubleSpinBoxDomainBinding), default 0.25", dspin,
                           QDoubleSpinBoxDomainBinding(dspin, defaultValue=0.25))

    def __tabBarRow(self) -> QGroupBox:
        tabBar = QTabBar()
        for i in range(4):
            tabBar.addTab(f"Tab {i}")
        return self.__row("QTabBar (QCurrentIndexDomainBinding), default Tab 1", tabBar,
                           QCurrentIndexDomainBinding(tabBar, defaultValue=1))

    def __buttonGroupRow(self) -> QGroupBox:
        container = QWidget()
        radios = QHBoxLayout(container)
        radios.setContentsMargins(0, 0, 0, 0)
        group = QButtonGroup(container)
        for i in range(3):
            radio = QRadioButton(f"Option {i}")
            group.addButton(radio)
            radios.addWidget(radio)
        return self.__row("QButtonGroup (QButtonGroupDomainBinding), default Option 2", container,
                           QButtonGroupDomainBinding(group, defaultValue=2))


class QLeaderFollowersPage(QWidget):
    """Contrôle global : une pilote, non liée, rejoue ses gestes chez les
    suiveuses, chacune liée à un paramètre : quatre réels (curseur et boîte
    numérique), puis six de natures différentes (case à cocher, liste
    déroulante, compteur, onglets, boutons radio, barre de défilement), aux
    domaines de tailles diverses. Toutes les suiveuses partagent une colonne
    de la grille : même largeur, alignées verticalement.

    Chaque suiveuse reste libre : l'arrêter à la main fait repasser le
    bouton d'animation de la pilote à son glyphe une fois toutes arrêtées.
    """

    _Parameters: tuple[tuple[str, float], ...] = (("ΔX", 0.73), ("ΔY", 1.0), ("Scale X", 0.5), ("Scale Y", 0.78))

    def __init__(self) -> None:
        super().__init__()
        self.__leader = QDomainExplorerBox()
        self.__leader.setMarkerCount(5)
        self.__leader.animationStateChanged.connect(self.__onLeaderState)
        self.__followers: list[QDomainExplorerBox] = []

        grid = QGridLayout()
        leaderLabel = QLabel("All parameters:")
        leaderLabel.setToolTip(richToolTip("The leader: bound to no parameter, it replays each of its gestures "
                               "on its followers (addFollower()). Its animation buttons show ⏸ while "
                               "at least one follower runs that mode."))
        followsLabel = QLabel("Follows")
        followsLabel.setToolTip(richToolTip("Checked: the row follows the leader (addFollower()); "
                                "unchecked: removeFollower()."))
        grid.addWidget(leaderLabel, 0, 0, 1, 3)
        grid.addWidget(self.__leader, 0, 3)
        grid.addWidget(followsLabel, 0, 4)
        self.__grid = grid
        for name, value in self._Parameters:
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 1.0)
            spin.setSingleStep(0.01)
            slider.valueChanged.connect(lambda v, s=spin: s.setValue(v / 100.0))
            spin.valueChanged.connect(lambda v, s=slider: s.setValue(round(v * 100.0)))
            slider.setValue(round(value * 100.0))
            self.__addFollowerRow(name, [slider, spin], QSliderDomainBinding(slider, defaultValue=slider.value()))
        self.__addOtherKinds()
        grid.setColumnStretch(1, 1)

        collapsible = QCheckBox("Collapsible (leader and followers)")
        collapsible.setChecked(self.__leader.isCollapsible())
        collapsible.toggled.connect(self.__setCollapsible)
        collapsible.setToolTip(richToolTip("setCollapsible() on every explorer. Collapsing the leader collapses "
                               "its followers; each follower stays expandable by hand."))
        side = QComboBox()
        for position in MAB.CollapseButtonPosition:
            side.addItem(position.name, position)
        side.currentIndexChanged.connect(lambda i: self.__setCollapseSide(side.itemData(i)))
        side.setToolTip(richToolTip("setCollapseButtonPosition() on every explorer."))
        options = QHBoxLayout()
        options.addWidget(collapsible)
        options.addSpacing(16)
        options.addWidget(QLabel("Collapse button side:"))
        options.addWidget(side)
        options.addStretch()

        self.__status = QLabel()
        self.__onLeaderState(self.__leader.animationState())
        hint = QLabel("The leader replays every gesture on the checked followers; "
                      "each follower stays free to act on its own. Each binding takes its "
                      "parameter's initial value as default value: reset on the leader sends "
                      "every parameter back to it.")
        hint.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(grid)
        layout.addLayout(options)
        layout.addWidget(self.__status)
        layout.addStretch()

    def __addFollowerRow[T, V](self, name: str, elements: list[QWidget], binding: QDomainBinding[T, V]) -> None:
        """Ajoute une ligne : le paramètre (un ou deux widgets), sa suiveuse liée,
        et la case « suit ». Toutes les suiveuses partagent la colonne 3 de la
        grille : même largeur, alignées verticalement."""
        row = self.__grid.rowCount()
        follower = QDomainExplorerBox()
        follower.setBinding(binding)
        self.__leader.addFollower(follower)
        self.__followers.append(follower)
        follows = QCheckBox()
        follows.setChecked(True)
        follows.toggled.connect(lambda on, f=follower: self.__setFollows(f, on))
        follows.setToolTip(richToolTip(f"Whether {name} follows the leader."))
        self.__grid.addWidget(QLabel(f"{name}:"), row, 0)
        if len(elements) == 1:
            self.__grid.addWidget(elements[0], row, 1, 1, 2)
        else:
            self.__grid.addWidget(elements[0], row, 1)
            self.__grid.addWidget(elements[1], row, 2)
        self.__grid.addWidget(follower, row, 3)
        self.__grid.addWidget(follows, row, 4)

    def __addOtherKinds(self) -> None:
        """Paramètres d'autres natures, chacun relié par la liaison prête à
        l'emploi de son widget (comme dans l'onglet Widget Bindings)."""
        grid = QCheckBox("Show grid")
        self.__addFollowerRow("Grid", [grid], QButtonDomainBinding(grid))

        color = QComboBox()
        color.addItems(["Red", "Green", "Blue", "Yellow", "Purple"])
        self.__addFollowerRow("Color", [color], QComboBoxDomainBinding(color))

        iterations = QSpinBox()
        iterations.setRange(0, 20)
        iterations.setValue(5)
        self.__addFollowerRow("Iterations", [iterations],
                              QSpinBoxDomainBinding(iterations, defaultValue=iterations.value()))

        view = QTabBar()
        for title in ("Front", "Top", "Side", "Iso"):
            view.addTab(title)
        self.__addFollowerRow("View", [view], QCurrentIndexDomainBinding(view))

        quality = QWidget()
        radios = QHBoxLayout(quality)
        radios.setContentsMargins(0, 0, 0, 0)
        group = QButtonGroup(quality)
        for title in ("Low", "Medium", "High"):
            radio = QRadioButton(title)
            group.addButton(radio)
            radios.addWidget(radio)
        radios.addStretch()
        group.buttons()[1].setChecked(True)
        self.__addFollowerRow("Quality", [quality], QButtonGroupDomainBinding(group, defaultValue=1))

        offset = QScrollBar(Qt.Orientation.Horizontal)
        offset.setRange(0, 10)
        offset.setValue(3)
        self.__addFollowerRow("Offset", [offset], QSliderDomainBinding(offset, defaultValue=offset.value()))

    def __setFollows(self, follower: QDomainExplorerBox, follows: bool) -> None:
        if follows:
            self.__leader.addFollower(follower)
        else:
            self.__leader.removeFollower(follower)

    def __setCollapsible(self, collapsible: bool) -> None:
        for box in [self.__leader, *self.__followers]:
            box.setCollapsible(collapsible)

    def __setCollapseSide(self, position: MAB.CollapseButtonPosition) -> None:
        for box in [self.__leader, *self.__followers]:
            box.setCollapseButtonPosition(position)

    def __onLeaderState(self, state: MAB.AnimationState) -> None:
        mode = self.__leader.animationMode()
        self.__status.setText(f"Leader (aggregate): {state.name}"
                              + (f", {mode.name}" if mode is not None else ""))


class QDemoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QDomainExplorerBox Demo")
        tabs = QTabWidget()
        tabs.addTab(QListBindingPage(), "List Binding")
        tabs.addTab(QWidgetBindingsPage(), "Widget Bindings")
        tabs.addTab(QLeaderFollowersPage(), "Leader && Followers")  # && : a lone & is a mnemonic
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)


def main() -> int:
    app = QApplication(sys.argv)
    window = QDemoWindow()
    window.resize(860, 640)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
