
import sys

from PySide6.QtWidgets import QApplication, QWidget
from edustem.pyside6.widgets.q_range_slider import QRealRangeSlider


def main() -> None:
    app = QApplication(sys.argv)

    window = QRealRangeSlider()
    window.setWindowTitle("420-SF3 Projet 1")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
