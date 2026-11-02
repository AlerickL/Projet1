from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.Modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant
from projects.p1.gui.QMenuFormule import QMenuFormule
from projects.p1.gui.QParametres import QParametres
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique

class QFonctionTransformationCanonique(QWidget):
    """Widget combinant QSelectionFormule et QTransformationCanonique.
    """
    def __init__(self,modele:Modele):
        super().__init__()
        self.__selectionFonction = QSelectionFonction(modele)
        self.__TransformationCanonique = QTransformationCanonique(modele)
        self.__selectionFonction.modeleChanger.connect(self.__test)
        self.__TransformationCanonique.modeleChanger.connect(self.__test)

        principalLayout = QVBoxLayout()

        principalLayout.addWidget(self.__selectionFonction)
        principalLayout.addWidget(self.__TransformationCanonique)

        self.setLayout(principalLayout)

    def __test(self):
        print("TTTesTTT")