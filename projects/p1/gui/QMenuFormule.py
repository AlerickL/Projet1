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
    formuleChange = Signal()
    modeleChanger = Signal()
    def __init__(self,modele:Modele):
        super().__init__()
        self.__modele = modele
        self._menu = QMenuDeroulant(modele)
        self.__vrai_formule = QLabel(self.__modele.avoir_vraie_formule())
        
      
        principalLayout = QHBoxLayout()
        secondLayout = QVBoxLayout()

        secondLayout.addWidget(QLabel("Sélection de la fonction"))
        secondLayout.addWidget(self._menu)
        secondLayout.addWidget(self.__vrai_formule)

        principalLayout.addLayout(secondLayout)
        self.setLayout(principalLayout)

        self._menu.currentTextChanged.connect(self.__changementFonctionModele)
        self._menu.currentTextChanged.connect(self.formuleChange)

    def menu(self):
        return self._menu

    @Slot()
    def __changementFonctionModele(self):
        if self._menu.currentText() == "Fonction sinus":
            self.__modele.changer_fonction_sin()
        elif self._menu.currentText() == "Fonction polynomial du second degré":
            self.__modele.changer_fonction_second_degre()
        elif self._menu.currentText() == "Fonction sinus amortie":
            self.__modele.changer_fonction_sin_amortie()
        elif self._menu.currentText() == "Fonction double bosse":
            self.__modele.changer_fonction_double_bosse()
        self.changerVraiFormule()


    @Slot()
    def changerVraiFormule(self):
        self.__vrai_formule.setText(self.__modele.avoir_vraie_formule())
        self.modeleChanger.emit()

