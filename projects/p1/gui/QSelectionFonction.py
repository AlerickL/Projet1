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
    """Collection de QMenuFormule (dont il hérite) et d'un ensemble de QParametres
    Il n'affiche qu'un QParametre à la fois, celui de la fonction qu'utilise actuellement le modèle. les autres sont storé en mémoire et caché.
    """
    def __init__(self,modele:Modele):
        modele.changer_fonction_sin()
        self.__modele = modele

        super().__init__(self.__modele)

        self.__parametres_sin = QParametres(self.__modele,self.__modele.fonction_sin)
        self.__parametres_second_degre = QParametres(self.__modele,self.__modele.fonction_second_degre)
        self.__parametres_sin_amortie = QParametres(self.__modele,self.__modele.fonction_sin_amortie)
        self.__parametres_double_bosse = QParametres(self.__modele,self.__modele.fonction_double_bosse)

        self.__parametres_sin.modifierModele.connect(self.changerVraiFormule)
        self.__parametres_second_degre.modifierModele.connect(self.changerVraiFormule)
        self.__parametres_sin_amortie.modifierModele.connect(self.changerVraiFormule)
        self.__parametres_double_bosse.modifierModele.connect(self.changerVraiFormule)
        
        self.layout().addWidget(self.__parametres_second_degre)
        self.layout().addWidget(self.__parametres_sin_amortie)
        self.layout().addWidget(self.__parametres_double_bosse)
        self.layout().addWidget(self.__parametres_sin)

        self.__changerParametres()
        
        self.formuleChange.connect(self.__changerParametres)
        
        
    def __changerParametres(self):
        if self.menu().currentText() == "Fonction double bosse":
            self.__parametres_sin_amortie.setVisible(False)
            self.__parametres_second_degre.setVisible(False)
            self.__parametres_double_bosse.setVisible(True)
            self.__parametres_sin.setVisible(False)
            
            self.__modele.changer_fonction_double_bosse()
        elif self.menu().currentText() == "Fonction polynomial du second degré":
            self.__parametres_sin_amortie.setVisible(False)
            self.__parametres_double_bosse.setVisible(False)
            self.__parametres_second_degre.setVisible(True)
            self.__parametres_sin.setVisible(False)
            self.__modele.changer_fonction_second_degre()
        elif self.menu().currentText() == "Fonction sinus amortie":
            self.__parametres_double_bosse.setVisible(False)
            self.__parametres_second_degre.setVisible(False)
            self.__parametres_sin.setVisible(False)
            self.__parametres_sin_amortie.setVisible(True)
            self.__modele.changer_fonction_sin_amortie()
        elif self.menu().currentText() == "Fonction sinus":
            self.__parametres_sin_amortie.setVisible(False)
            self.__parametres_double_bosse.setVisible(False)
            self.__parametres_second_degre.setVisible(False)
            self.__parametres_sin.setVisible(True)
            self.__modele.changer_fonction_sin()
