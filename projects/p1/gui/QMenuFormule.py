from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.Modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant

class QMenuFormule(QWidget):

    def __init__(self,modele:Modele):
        super().__init__()
        self.__modele = modele
        self.__menu = QMenuDeroulant(modele)
        self.__vrai_formule = QLabel(self.__modele.avoir_vraie_formule())
        
      
        principalLayout = QVBoxLayout()

        principalLayout.addWidget(self.__menu)
        principalLayout.addWidget(self.__vrai_formule)

        self.setLayout(principalLayout)

