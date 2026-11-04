from __future__ import annotations
import sys
#from QMultipleRealSliderSpinBox import QMultipleRealSliderSpinBox
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.modele import Modele
from projects.p1.gui.QBoutonMultipleRealSliderSpinBox import QBoutonMultipleRealSliderSpinBox

class QTransformationCanonique(QBoutonMultipleRealSliderSpinBox):
    """Widget affichant les transformations canoniques de la fonction.
    modeleChanger est un signal envoyé quand le modèle est modifié par la classe
    """
    modeleChanger = Signal()
    def __init__(self,modele:Modele,parent:QWidget|None=None)-> None:
        self.__modele = modele

        self.__reelTransX:QRealSliderSpinBox = QRealSliderSpinBox()
        self.__reelTransX.setPrefix(modele.transformation_canonique.trans_x.info.nom+ " ")
        self.__reelTransX.setRange(modele.transformation_canonique.trans_x.min_valeur,modele.transformation_canonique.trans_x.max_valeur)
        self.__reelTransX.setValue(modele.transformation_canonique.trans_x.defaut_valeur)
        self.__reelTransX.setToolTip(self.__modele.transformation_canonique.trans_x.info.resume)

        self.__reelTransY:QRealSliderSpinBox = QRealSliderSpinBox()
        self.__reelTransY.setPrefix(modele.transformation_canonique.trans_y.info.nom+ " ")
        self.__reelTransY.setRange(modele.transformation_canonique.trans_y.min_valeur,modele.transformation_canonique.trans_y.max_valeur)
        self.__reelTransY.setValue(modele.transformation_canonique.trans_y.defaut_valeur)
        self.__reelTransY.setToolTip(self.__modele.transformation_canonique.trans_y.info.resume)

        self.__reelZoomX:QRealSliderSpinBox = QRealSliderSpinBox()
        self.__reelZoomX.setPrefix(modele.transformation_canonique.zoom_x.info.nom+ " ")
        self.__reelZoomX.setRange(modele.transformation_canonique.zoom_x.min_valeur,modele.transformation_canonique.zoom_x.max_valeur)
        self.__reelZoomX.setValue(modele.transformation_canonique.zoom_x.defaut_valeur)
        self.__reelZoomX.setToolTip(self.__modele.transformation_canonique.zoom_x.info.resume)

        self.__reelZoomY:QRealSliderSpinBox = QRealSliderSpinBox()
        self.__reelZoomY.setPrefix(modele.transformation_canonique.zoom_y.info.nom+ " ")
        self.__reelZoomY.setRange(modele.transformation_canonique.zoom_y.min_valeur,modele.transformation_canonique.zoom_y.max_valeur)
        self.__reelZoomY.setValue(modele.transformation_canonique.zoom_y.defaut_valeur)
        self.__reelZoomY.setToolTip(self.__modele.transformation_canonique.zoom_y.info.resume)

        boutonInformation = QPushButton("Information")
        boutonIdentite = QPushButton("Identité")
        boutonSymetrieX = QPushButton("Symétrie en X")
        boutonSymetrieY = QPushButton("Symétrie en Y")

        boutonInformation.pressed.connect(self.__donnerInformation)
        boutonIdentite.pressed.connect(self.__mettreIdentite)
        boutonSymetrieX.pressed.connect(self.__mettreSymetrieX)
        boutonSymetrieY.pressed.connect(self.__mettreSymetrieY)

        super().__init__("Transformations canoniques",[self.__reelTransX,self.__reelTransY,self.__reelZoomX,self.__reelZoomY],[boutonInformation,boutonIdentite,boutonSymetrieX,boutonSymetrieY],parent)

        self.valeurChanger.connect(self.__modifierModele)

    @Slot()
    def __donnerInformation(self):
        QMessageBox.information(self,"Transformations canoniqes","Les transformations canoniques sont les déplacements de la fonction dans le plan.\nLe bouton identité réinitialise les paramètres. Les deux autres applique une symétrie à la fonction selon l'axe mentionné.\nElles appliquent la symétrie sur la fonction actuelle et non celle de l'identité.")

    @Slot()
    def __mettreIdentite(self) -> None:
        self.blockSignals(True)
        self.__modele.mettre_identite()
        self.__appliquerModele()
        self.blockSignals(False)
        self.modeleChanger.emit()

    @Slot()
    def __mettreSymetrieX(self) -> None:
        self.__modele.mettre_symetrie_x()
        self.__appliquerModele()
        

    @Slot()
    def __mettreSymetrieY(self) -> None:
            self.__modele.mettre_symetrie_y()
            self.__appliquerModele()

    def __appliquerModele(self) -> None:
        self.__reelTransX.setValue(self.__modele.transformation_canonique.trans_x.valeur)
        self.__reelTransY.setValue(self.__modele.transformation_canonique.trans_y.valeur)
        self.__reelZoomX.setValue(self.__modele.transformation_canonique.zoom_x.valeur)
        self.__reelZoomY.setValue(self.__modele.transformation_canonique.zoom_y.valeur)
        self.modeleChanger.emit()

    def __modifierModele(self) -> None:
        print("HHHHHHHHHHHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        self.__modele.transformation_canonique.trans_x.valeur = self.valeurs()[0]
        self.__modele.transformation_canonique.trans_y.valeur = self.valeurs()[1]
        self.__modele.transformation_canonique.zoom_x.valeur = self.valeurs()[2]
        self.__modele.transformation_canonique.zoom_y.valeur = self.valeurs()[3]
        self.modeleChanger.emit()