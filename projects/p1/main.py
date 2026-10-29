
import sys

from PySide6.QtWidgets import QApplication, QWidget
from edustem.pyside6.widgets.q_range_slider import QRealRangeSlider
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from edustem.pyside6.widgets.q_real_slider import QRealDial
from projects.p1.gui.QMultipleRealSliderSpinBox import QMultipleRealSliderSpinBox


def main() -> None:
    app = QApplication(sys.argv)

    reel = QRealSliderSpinBox()
    reel.setPrefix("allo")
    window = QMultipleRealSliderSpinBox("titre",[reel])
    window.setWindowTitle("420-SF3 Projet 1")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
