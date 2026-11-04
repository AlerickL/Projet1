from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.modele import Modele

class QMenuDeroulant(QComboBox):
    """Menu déroulant avec le nom des fonctions.
    """
    def __init__(self,modele:Modele):
        super().__init__()
        self.__modele = modele
        self.addItem(self.__modele.fonction_sin.info.nom)
        self.addItem(self.__modele.fonction_second_degre.info.nom)
        self.addItem(self.__modele.fonction_sin_amortie.info.nom)
        self.addItem(self.__modele.fonction_double_bosse.info.nom)
        self.setToolTip("Permet de sélectionner une fonction\n\nNos fonctions de bases :\n    fonction sinus\n    fonction polynomiale du second degré\n\nNos fonctions avancées :\n    fonction sinus amortie\n   fonction double bosse")

