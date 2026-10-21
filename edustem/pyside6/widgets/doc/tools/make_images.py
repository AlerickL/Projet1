"""Produit les images du catalogue des widgets.

Chaque widget visuel de `edustem.pyside6.widgets` est construit dans un usage
typique, puis rendu seul dans une image PNG du dossier `doc/images/`. Toutes
les images partagent la même échelle (`_PIXEL_RATIO`), la même marge et le
même fond : leurs tailles relatives restent fidèles d'un widget à l'autre.
Les contrôles horizontaux reçoivent une largeur commune (`_CONTROL_WIDTH`).

Le catalogue affiche chaque image à sa largeur logique, soit sa largeur en
pixels divisée par `_PIXEL_RATIO`. Sans cette largeur explicite, l'aperçu
réduirait les images larges et laisserait les petites à pleine taille : les
widgets ne paraîtraient plus à l'échelle d'une même application. Le script
met donc à jour l'attribut `width` de chaque `<img>` du catalogue.

Les widgets de `_HOVERED` sont rendus comme survolés par la souris, sans que
le pointeur paraisse. Au repos, le style Windows 11 réduit `QRealScrollBar` à
un mince trait ; survolée, elle montre sa gouttière et ses flèches.

Lancer depuis `new/sf3`, sur la plateforme graphique réelle (pas
`offscreen`), pour obtenir le style natif et le rendu de `QLatexLabel` :

    python -m edustem.pyside6.widgets.doc.tools.make_images
    python -m edustem.pyside6.widgets.doc.tools.make_images QRealDial QLatexLabel
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QEventLoop, QMargins, QPoint, QPointF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QEnterEvent, QPixmap
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from ...q_color_box import QColorBox
from ...q_color_edit import QColorEdit
from ...q_domain_explorer_box import QDomainExplorerBox
from ...q_latex_label import QLatexLabel
from ...q_python_code_view import QPythonCodeView
from ...q_range_slider import QRangeSlider, QRealRangeSlider
from ...q_range_slider_spin_box import QRangeSliderSpinBox, QRealRangeSliderSpinBox
from ...q_range_spin_box import QRangeSpinBox, QRealRangeSpinBox
from ...q_real_slider import QRealDial, QRealScrollBar, QRealSlider
from ...q_slider_spin_box import QRealSliderSpinBox, QSliderSpinBox
from ...q_state_indicator_bar import QStateIndicatorBar, QStateSet

_DOC_DIR = Path(__file__).resolve().parents[1]
_IMAGES_DIR = _DOC_DIR / "images"
_CATALOGUE = _DOC_DIR / "catalogue_widgets.md"
_PIXEL_RATIO = 2.0      # same scale for every image, whatever the screen
_MARGIN = 12            # logical pixels around the widget
_CONTROL_WIDTH = 360    # common width of the horizontal controls
_LATEX_TIMEOUT_MS = 20000
_DIAL_SIZE = 50         # a dial as found in a settings panel
_HOVERED = {"QRealScrollBar"}
_HOVER_DELAY_MS = 600

_CODE_SAMPLE = '''import numpy as np

def derivative(f, x: float, h: float, alpha: float = 0.5) -> float:
    """Approximate f'(x) with a finite difference."""
    x_minus = x - alpha * h
    x_plus = x + (1.0 - alpha) * h
    return (f(x_plus) - f(x_minus)) / h

print(derivative(np.sin, 0.0, 0.1))'''


def _width(widget: QWidget, width: int = _CONTROL_WIDTH) -> QWidget:
    """Fixe la largeur commune d'un contrôle horizontal et rend le widget."""
    widget.setFixedWidth(width)
    return widget


def _color_box() -> QWidget:
    return QColorBox(QColor("#1e88e5"))


def _color_edit() -> QWidget:
    return _width(QColorEdit(QColor("#1e88e5")))


def _latex_label() -> QWidget:
    label = QLatexLabel(r"f_c(x) = s_y\, f\!\left(\frac{x - \delta_x}{s_x}\right) + \delta_y")
    label.setZoomFactor(1.3)  # a formula shown as a heading, slightly above the text size
    return label


def _python_code_view() -> QWidget:
    view = QPythonCodeView()
    view.setPlainText(_CODE_SAMPLE)
    view.setFixedSize(QSize(520, 165))
    return view


def _real_slider() -> QWidget:
    slider = QRealSlider(Qt.Orientation.Horizontal)
    slider.setRange(-5.0, 5.0)
    slider.setValue(1.25)
    return _width(slider)


def _real_scroll_bar() -> QWidget:
    bar = QRealScrollBar(Qt.Orientation.Horizontal)
    bar.setRange(0.0, 100.0)
    bar.setPageStep(20.0)
    bar.setValue(30.0)
    return _width(bar)


def _real_dial() -> QWidget:
    dial = QRealDial()
    dial.setRange(0.0, 360.0)
    dial.setValue(135.0)
    dial.setNotchesVisible(True)
    dial.setFixedSize(_DIAL_SIZE, _DIAL_SIZE)
    return dial


def _slider_spin_box() -> QWidget:
    widget = QSliderSpinBox()
    widget.setRange(1, 100)
    widget.setValue(8)
    widget.setPrefix("N = ")
    return _width(widget)


def _real_slider_spin_box() -> QWidget:
    widget = QRealSliderSpinBox()
    widget.setRange(-5.0, 5.0)
    widget.setValue(1.25)
    widget.setPrefix("x = ")
    return _width(widget)


def _range_slider() -> QWidget:
    slider = QRangeSlider()
    slider.setLimits(0, 100)
    slider.setRange(20, 65)
    return _width(slider)


def _real_range_slider() -> QWidget:
    slider = QRealRangeSlider()
    slider.setLimits(-5.0, 5.0)
    slider.setRange(-2.0, 3.0)
    return _width(slider)


def _range_spin_box() -> QWidget:
    spin_box = QRangeSpinBox()
    spin_box.setLimits(0, 100)
    spin_box.setRange(20, 65)
    return spin_box


def _real_range_spin_box() -> QWidget:
    spin_box = QRealRangeSpinBox()
    spin_box.setLimits(-5.0, 5.0)
    spin_box.setRange(-2.0, 3.0)
    return spin_box


def _range_slider_spin_box() -> QWidget:
    widget = QRangeSliderSpinBox()
    widget.setLimits(0, 100)
    widget.setRange(20, 65)
    return _width(widget)


def _real_range_slider_spin_box() -> QWidget:
    widget = QRealRangeSliderSpinBox()
    widget.setLimits(-5.0, 5.0)
    widget.setRange(-2.0, 3.0)
    return _width(widget)


def _state_indicator_bar() -> QWidget:
    bar = QStateIndicatorBar()
    bar.addIndicators(["Pump", "Heater", "Fan"], QStateSet.activity())
    bar.addIndicator("Network", QStateSet.connection(), shape=QStateIndicatorBar.Shape.Rectangular)
    bar.addIndicator("Alarm", QStateSet.severity(), shape=QStateIndicatorBar.Shape.TriangleUp)
    bar.setStates([2, 0, 1, 1, 1])
    return bar


def _domain_explorer_box() -> QWidget:
    box = QDomainExplorerBox()
    box.setMarkerCount(5)
    return _width(box)


# Class name -> builder, in the order of the catalogue.
_BUILDERS: dict[str, Callable[[], QWidget]] = {
    "QColorBox": _color_box,
    "QColorEdit": _color_edit,
    "QLatexLabel": _latex_label,
    "QPythonCodeView": _python_code_view,
    "QRealSlider": _real_slider,
    "QRealScrollBar": _real_scroll_bar,
    "QRealDial": _real_dial,
    "QSliderSpinBox": _slider_spin_box,
    "QRealSliderSpinBox": _real_slider_spin_box,
    "QRangeSlider": _range_slider,
    "QRealRangeSlider": _real_range_slider,
    "QRangeSpinBox": _range_spin_box,
    "QRealRangeSpinBox": _real_range_spin_box,
    "QRangeSliderSpinBox": _range_slider_spin_box,
    "QRealRangeSliderSpinBox": _real_range_slider_spin_box,
    "QStateIndicatorBar": _state_indicator_bar,
    "QDomainExplorerBox": _domain_explorer_box,
}


def image_name(class_name: str) -> str:
    """Rend le nom de fichier d'une classe : `QRealDial` donne `q_real_dial.png`."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower() + ".png"


def _pause(milliseconds: int) -> None:
    """Laisse tourner la boucle d'événements pendant la durée donnée."""
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for_latex(label: QLatexLabel) -> None:
    """Attend la fin du rendu d'un `QLatexLabel`, avec un délai maximal."""
    if label.renderState() != QLatexLabel.RenderState.Pending:
        return
    loop = QEventLoop()
    label.renderStateChanged.connect(loop.quit)
    QTimer.singleShot(_LATEX_TIMEOUT_MS, loop.quit)
    loop.exec()


def _capture(widget: QWidget, hovered: bool = False) -> QPixmap:
    """Rend le widget seul, à sa taille naturelle, avec sa marge.

    Args:
        widget: Le widget à rendre.
        hovered: Rendre le widget comme survolé, sans pointeur visible.
    """
    # The widget is shown in a window, but only the widget is rendered: the
    # minimum width of a window must not stretch it.
    frame = QWidget()
    layout = QVBoxLayout(frame)
    layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    frame.show()
    QApplication.processEvents()
    if isinstance(widget, QLatexLabel):
        _wait_for_latex(widget)
        # The rendered formula changes the size hint: the window must follow.
        frame.adjustSize()
        QApplication.processEvents()
    # No focus: no text cursor nor focus frame in the image.
    focused = QApplication.focusWidget()
    if focused is not None:
        focused.clearFocus()
    if hovered:
        # The style reads State_MouseOver from this attribute: no real pointer is needed.
        widget.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, True)
        QApplication.sendEvent(widget, QEnterEvent(QPointF(5, 5), QPointF(5, 5), QPointF(5, 5)))
        widget.update()
        _pause(_HOVER_DELAY_MS)  # the style animates the change of state
    QApplication.processEvents()

    size = widget.size().grownBy(QMargins(_MARGIN, _MARGIN, _MARGIN, _MARGIN))
    ratio = widget.devicePixelRatioF()
    pixmap = QPixmap(round(size.width() * ratio), round(size.height() * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(widget.palette().window().color())
    widget.render(pixmap, QPoint(_MARGIN, _MARGIN))
    frame.close()
    frame.deleteLater()
    return pixmap


def _update_catalogue(widths: dict[str, int]) -> None:
    """Règle la largeur d'affichage des images produites dans le catalogue."""
    text = _CATALOGUE.read_text(encoding="utf-8")
    for file_name, width in widths.items():
        pattern = rf'(<img src="images/{re.escape(file_name)}" width=")\d+(")'
        text = re.sub(pattern, rf"\g<1>{width}\g<2>", text)
    _CATALOGUE.write_text(text, encoding="utf-8")


def main(names: list[str]) -> int:
    """Produit les images demandées, ou toutes si aucun nom n'est donné."""
    unknown = [name for name in names if name not in _BUILDERS]
    if unknown:
        print(f"Unknown widgets: {', '.join(unknown)}", file=sys.stderr)
        return 1
    # Same scale and same light theme on every machine: the images must not
    # depend on the screen nor on the system theme.
    # A 100 % screen (96 DPI) magnified by `_PIXEL_RATIO`.
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_FONT_DPI"] = "96"
    os.environ["QT_SCALE_FACTOR"] = str(_PIXEL_RATIO)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    _IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    widths: dict[str, int] = {}
    for name in names or list(_BUILDERS):
        pixmap = _capture(_BUILDERS[name](), name in _HOVERED)
        path = _IMAGES_DIR / image_name(name)
        if not pixmap.save(str(path)):
            print(f"Cannot write {path}", file=sys.stderr)
            return 1
        widths[path.name] = round(pixmap.width() / _PIXEL_RATIO)
        print(f"{path.name}: {pixmap.width()} x {pixmap.height()}, shown {widths[path.name]} wide")
    _update_catalogue(widths)
    del app
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
