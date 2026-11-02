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
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QGraphTest import QGraphTest

class QApp(QWidget):

    def __init__(self,modele):
        super().__init__()
        self.__modele = modele
        self.__graphe = QGraphTest(self.__modele)
        self.__selection = QSelectionFonction(self.__modele)
        self.__

        principalLayout = QHBoxLayout()

        principalLayout.addWidget(self.__graphe)
        principalLayout.addWidget(self.__selection)

        self.setLayout(principalLayout)

        self.__selection.modeleChanger.connect(self.__graphe.actualiser)

    
