
import sys

from PySide6.QtWidgets import QApplication, QWidget, QComboBox
from edustem.pyside6.widgets.q_range_slider import QRealRangeSlider
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from edustem.pyside6.widgets.q_real_slider import QRealDial
from projects.p1.gui.QMultipleRealSliderSpinBox import QMultipleRealSliderSpinBox
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QParametres import QParametres
from projects.p1.model.Modele import Modele

def main() -> None:
    app = QApplication(sys.argv)

    modele = Modele()

    reel = QRealSliderSpinBox()
    reel2 = QRealSliderSpinBox()
    reel.setPrefix("allo")
    #window = QMultipleRealSliderSpinBox("titre",[reel,reel2])
    #window = QTransformationCanonique(modele)
    window = QSelectionFonction(modele)
    window.setWindowTitle("420-SF3 Projet 1")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
