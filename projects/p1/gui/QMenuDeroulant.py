from __future__ import annotations
import sys
from typing import override
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.Modele import Modele

class QMenuDeroulant(QComboBox):

    def __init__(self,modele:Modele):
        self.__modele = modele
        super().__init__()
        self.addItem(self.__modele.avoir_info_fonction().nom)
        self.__modele.changer_fonction_second_degre()
        self.addItem(self.__modele.avoir_info_fonction().nom)
        self.__modele.changer_fonction_sin_amortie()
        self.addItem(self.__modele.avoir_info_fonction().nom)
        self.__modele.changer_fonction_double_bosse()
        self.addItem(self.__modele.avoir_info_fonction().nom)

