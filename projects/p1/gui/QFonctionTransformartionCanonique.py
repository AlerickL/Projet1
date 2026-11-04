from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant
from projects.p1.gui.QMenuFormule import QMenuFormule
from projects.p1.gui.QParametres import QParametres
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique

class QFonctionTransformationCanonique(QWidget):
    """Widget combinant QSelectionFormule et QTransformationCanonique.
    """
    modeleChanger = Signal()
    def __init__(self,modele:Modele):
        super().__init__()
        self.__selectionFonction = QSelectionFonction(modele)
        self.__transformationCanonique = QTransformationCanonique(modele)
        self.__selectionFonction.modeleChanger.connect(self.__test)
        self.__transformationCanonique.modeleChanger.connect(self.__test)

        principalLayout = QVBoxLayout()

        principalLayout.addWidget(self.__selectionFonction)
        principalLayout.addWidget(self.__transformationCanonique)

        self.setLayout(principalLayout)
        
        self.__selectionFonction.modeleChanger.connect(self.modeleChanger)
        self.__transformationCanonique.modeleChanger.connect(self.modeleChanger) 


    def __test(self):
        print("TTTesTTT")