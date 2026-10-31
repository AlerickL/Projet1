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

class QParametresTransformationCanonique(QBoutonMultipleRealSliderSpinBox):
    def __init__(self,modele:Modele,parent:QWidget|None=None)-> None:
        self.__modele = modele

        self.__reelTransX = QRealSliderSpinBox()
        self.__reelTransX.setPrefix(modele.transformation_canonique.trans_x.info.nom+ " ")
        self.__reelTransX.setRange(modele.transformation_canonique.trans_x.min_valeur,modele.transformation_canonique.trans_x.max_valeur)
        self.__reelTransX.setValue(modele.transformation_canonique.trans_x.defaut_valeur)

        self.__reelTransY = QRealSliderSpinBox()
        self.__reelTransY.setPrefix(modele.transformation_canonique.trans_y.info.nom+ " ")
        self.__reelTransY.setRange(modele.transformation_canonique.trans_y.min_valeur,modele.transformation_canonique.trans_y.max_valeur)
        self.__reelTransY.setValue(modele.transformation_canonique.trans_y.defaut_valeur)

        self.__reelZoomX = QRealSliderSpinBox()
        self.__reelZoomX.setPrefix(modele.transformation_canonique.zoom_x.info.nom+ " ")
        self.__reelZoomX.setRange(modele.transformation_canonique.zoom_x.min_valeur,modele.transformation_canonique.zoom_x.max_valeur)
        self.__reelZoomX.setValue(modele.transformation_canonique.zoom_x.defaut_valeur)

        self.__reelZoomY = QRealSliderSpinBox()
        self.__reelZoomY.setPrefix(modele.transformation_canonique.zoom_y.info.nom+ " ")
        self.__reelZoomY.setRange(modele.transformation_canonique.zoom_y.min_valeur,modele.transformation_canonique.zoom_y.max_valeur)
        self.__reelZoomY.setValue(modele.transformation_canonique.zoom_y.defaut_valeur)

        boutonInformation = QPushButton("Information")
        boutonIdentite = QPushButton("Identité")
        boutonSymetrieX = QPushButton("Symétrie en X")
        boutonSymetrieY = QPushButton("Symétrie en Y")

        boutonInformation.pressed.connect(self.__donnerInformation)
        boutonIdentite.pressed.connect(self.__mettreIdentite)
        boutonSymetrieX.pressed.connect(self.__mettreSymetrieX)
        boutonSymetrieY.pressed.connect(self.__mettreSymetrieY)

        # cast(QHBoxLayout, self.layout()).addWidget(self.__boutonLayout)

        super().__init__("Transformations canoniques",[self.__reelTransX,self.__reelTransY,self.__reelZoomX,self.__reelZoomY],[boutonInformation,boutonIdentite,boutonSymetrieX,boutonSymetrieY],parent)

    def __donnerInformation(self):
        QMessageBox.information(self,"Transformations canoniqes","Les transformations canoniques sont les déplacements de la fonction dans le plan.\nLe bouton identité réinitialise les paramètres. Les deux autres applique une symétrie à la fonction selon l'axe mentionné.\nElles appliquent la symétrie sur la fonction actuelle et non celle de l'identité.")
    
    def __mettreIdentite(self) -> None:
        self.__modele.mettre_identite()
        self.__appliquerModele()

    def __mettreSymetrieX(self) -> None:
        self.__modele.mettre_symetrie_x()
        self.__appliquerModele()

    def __mettreSymetrieY(self) -> None:
            self.__modele.mettre_symetrie_y()
            self.__appliquerModele()

    def __appliquerModele(self):
        self.__reelTransX.setValue(self.__modele.transformation_canonique.trans_x.valeur)
        self.__reelTransY.setValue(self.__modele.transformation_canonique.trans_y.valeur)
        self.__reelZoomX.setValue(self.__modele.transformation_canonique.zoom_x.valeur)
        self.__reelZoomY.setValue(self.__modele.transformation_canonique.zoom_y.valeur)