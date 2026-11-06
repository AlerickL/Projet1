from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.gui.QParametres import QParametres
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique
from projects.p1.model.modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant
from projects.p1.gui.QMenuFormule import QMenuFormule
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QBoutonMultipleRealSliderSpinBox import QBoutonMultipleRealSliderSpinBox
from projects.p1.gui.QSansMethode import QSansMethode
from projects.p1.gui.QMethodeDerive import QMethodeDerive
from projects.p1.gui.QMethodeIntegrale import QMethodeIntegrale

class QMethode(QBoutonMultipleRealSliderSpinBox):
    modeleChanger = Signal()
    def __init__(self,modele:Modele):
        self.__modele:Modele = modele

        boutonSansMethode = QPushButton("Aucune méthode")
        boutonDerive = QPushButton("Dérivé")
        boutonIntegrale = QPushButton("Intégrale")

        super().__init__("Méthodes numériques",[],[boutonSansMethode,boutonDerive,boutonIntegrale])

        self.__sansMethode = QSansMethode()
        self.__methodeDerive = QMethodeDerive(self.__modele)
        self.__methodeIntegrale = QMethodeIntegrale(self.__modele)


        self.layout().addWidget(self.__sansMethode)
        self.layout().addWidget(self.__methodeDerive)
        self.layout().addWidget(self.__methodeIntegrale)

        self.__methodeDerive.setVisible(False)
        self.__methodeIntegrale.setVisible(False)

        boutonSansMethode.pressed.connect(self.__mettreSansMethode)
        boutonDerive.pressed.connect(self.__mettreMethodeDerive)
        boutonIntegrale.pressed.connect(self.__mettreMethodeIntegrale)

        self.__methodeDerive.modeleChanger.connect(self.modeleChanger)
        self.__methodeIntegrale.modeleChanger.connect(self.modeleChanger)

    @property
    def methodeDerive(self) -> QMethodeDerive:
        return self.__methodeDerive
    @property
    def methodeIntegrale(self) -> QMethodeIntegrale:
        return self.__methodeIntegrale

    @property
    def methode(self):
        return self.__methode.me

    def __mettreSansMethode(self):
        self.__modele.mettre_affichage_aucun()
        self.__methodeDerive.setVisible(False)
        self.__methodeIntegrale.setVisible(False)
        self.__sansMethode.setVisible(True)
        self.modeleChanger.emit()

    def __mettreMethodeDerive(self):
        self.__modele.mettre_affichage_derive()
        self.__methodeDerive.setVisible(True)
        self.__methodeIntegrale.setVisible(False)
        self.__sansMethode.setVisible(False)
        self.modeleChanger.emit()

    def __mettreMethodeIntegrale(self):
        self.__modele.mettre_affichage_integrale()
        self.__methodeDerive.setVisible(False)
        self.__methodeIntegrale.setVisible(True)
        self.__sansMethode.setVisible(False)
        self.modeleChanger.emit()