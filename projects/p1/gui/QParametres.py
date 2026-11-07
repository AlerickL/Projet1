from __future__ import annotations
import sys
#from QMultipleRealSliderSpinBox import QMultipleRealSliderSpinBox
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.modele import Modele
from projects.p1.model.fonction_math import FonctionMath
from projects.p1.gui.QBoutonMultipleRealSliderSpinBox import QBoutonMultipleRealSliderSpinBox

class QParametres(QBoutonMultipleRealSliderSpinBox):
    """La liste des paramètres de la fonction du modèle. 
    modifierModele est envoyé quand cette classe modifi le modele qu'il contient.
    """
    modifierModele = Signal()
    def __init__(self,modele:Modele,fonction_math:FonctionMath,parent:QWidget|None=None):
        self.__modele:Modele = modele
        self.__fonction_math:FonctionMath = fonction_math
        self.__reels:list[QRealSliderSpinBox] = []

        self.actualiserParametres()

        self.__boutonInformation = QPushButton("Information")
        self.__boutonReinitialiser = QPushButton("Réinitialiser")
        self.__boutonInformation.pressed.connect(self.__donnerInformation)
        self.__boutonReinitialiser.pressed.connect(self.__reinitialiser)

        super().__init__("Paramètres de la fonction",self.__reels,[self.__boutonInformation,self.__boutonReinitialiser],parent)
        self.valeurChanger.connect(self.__modifierModele)

        for i in range(len(self.__reels)):
            self.__reels[i].setToolTip(self.__fonction_math.parametres[i].info.resume)

    def actualiserParametres(self):
        self.__reels = []
        for parametre in self.__fonction_math.parametres:
            reel:QRealSliderSpinBox = QRealSliderSpinBox()
            reel.setPrefix(parametre.info.nom + " ")
            reel.setRange(parametre.min_valeur,parametre.max_valeur)
            reel.setValue(parametre.valeur)
            self.__reels.append(reel)
        

    @Slot()
    def __donnerInformation(self) -> None:
        texte = f"Résumé de la fonction : {self.__fonction_math.info.resume}\nDétails de la fonction : {self.__fonction_math.info.details}\n"
        for parametre in self.__fonction_math.parametres:
            texte += f"{parametre.info.nom} :\n    résumé : {parametre.info.resume}\n\n" 
        QMessageBox.information(self,f"{self.__fonction_math.info.nom} : les paramètres",texte)

    @Slot()
    def __reinitialiser(self) -> None:
        self.__fonction_math.redemarrer_parametres()
        self.blockSignals(True)
        self.__appliquerModele()
        self.blockSignals(False)
        self.modifierModele.emit()

    def __appliquerModele(self):
        for i in range(len(self.__reels)):
            print(self.__reels[i].value())
            self.__reels[i].setValue(self.__fonction_math.parametres[i].valeur)

    @Slot()
    def __modifierModele(self):
        for i in range(len(self.__reels)):
            self.__modele.changer_valeur_parametre(i,self.__reels[i].value())
        self.modifierModele.emit()








