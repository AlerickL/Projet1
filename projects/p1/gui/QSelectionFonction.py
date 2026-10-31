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

class QSelectionFonction(QMenuFormule):

    def __init__(self,modele):
        self.__modele = modele

        super().__init__(self.__modele)

        parametres = QParametres(self.__modele)

        self.layout().addWidget(parametres)

        #self.setLayout(principalLayout)