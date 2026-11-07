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
from projects.p1.gui.QMethode import QMethode
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique

class QMenuDroite(QWidget):
    """Widget combinant QSelectionFormule et QTransformationCanonique.
    """
    modeleChanger = Signal()
    def __init__(self,modele:Modele):
        self.__modele:Modele = modele
        super().__init__()
        self.__selectionFonction = QSelectionFonction(self.__modele)
        self.__transformationCanonique = QTransformationCanonique(self.__modele)
        self.__methode = QMethode(self.__modele)


        principalLayout = QVBoxLayout()

        principalLayout.addWidget(self.__selectionFonction)
        principalLayout.addWidget(self.__transformationCanonique)
        principalLayout.addWidget(self.__methode)

        self.setLayout(principalLayout)
        
        self.__selectionFonction.modeleChanger.connect(self.modeleChanger)
        self.__transformationCanonique.modeleChanger.connect(self.modeleChanger) 
        self.__methode.modeleChanger.connect(self.modeleChanger)
        self.__transformationCanonique.modeleChanger.connect(self.__methode.actualiser)
        self.__selectionFonction.modeleChanger.connect(self.__methode.actualiser)

        self.modeleChanger.connect(self.__methode.methodeDerive.recalculer)
        self.modeleChanger.connect(self.__methode.methodeIntegrale.recalculer)


