from __future__ import annotations
import sys
#from QMultipleRealSliderSpinBox import QMultipleRealSliderSpinBox
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.Modele import Modele
from projects.p1.gui.QBoutonMultipleRealSliderSpinBox import QBoutonMultipleRealSliderSpinBox

class QParametres(QBoutonMultipleRealSliderSpinBox):

    def __init__(self,modele:Modele,parent:QWidget|None=None):
        self.__modele:Modele = modele
        self.__modele.changer_fonction_sin_amortie()
        self.__reels:list[QRealSliderSpinBox] = []

        self.__actualiserParametres()

        boutonInformation = QPushButton("Information")
        boutonReinitialiser = QPushButton("Réinitialiser")

        boutonInformation.pressed.connect(self.__donnerInformation)
        boutonReinitialiser.pressed.connect(self.__reinitialiser)
    
        super().__init__("Paramètres de la fonction",self.__reels,[boutonInformation,boutonReinitialiser],parent)

    def __actualiserParametres(self):

        for parametre in self.__modele.fonction_math.parametres:
            reel:QRealSliderSpinBox = QRealSliderSpinBox()
            reel.setPrefix(parametre.info.nom)
            reel.setRange(parametre.min_valeur,parametre.max_valeur)
            reel.setValue(parametre.valeur)
            self.__reels.append(reel)

    @Slot()
    def __donnerInformation(self) -> None:
        texte = f"Résumé de la fonction : {self.__modele.fonction_math.info.resume}\nDétails de la fonction : {self.__modele.fonction_math.info.details}\n"
        for parametre in self.__modele.fonction_math.parametres:
            texte += f"{parametre.info.nom} :\n    résumé : {parametre.info.resume}\n\n" 
        QMessageBox.information(self,f"{self.__modele.fonction_math.info.nom} : les paramètres",texte)

    @Slot()
    def __reinitialiser(self) -> None:
        self.__modele.fonction_math.redemarrer_parametres()
        self.__appliquerModele()

    def __appliquerModele(self):
        for i in range(len(self.__reels)):
            self.__reels[i].setValue(self.__modele.fonction_math.parametres[i].valeur)







