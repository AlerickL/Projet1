
import sys

from PySide6.QtWidgets import QApplication, QWidget


def main() -> None:
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("420-SF3 Projet 0")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
