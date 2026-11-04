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
from projects.p1.gui.QBoutonMultipleRealSliderSpinBox import QBoutonMultipleRealSliderSpinBox
from projects.p1.gui.QFonctionTransformartionCanonique import QFonctionTransformationCanonique

class QMethodeDerive(QBoutonMultipleRealSliderSpinBox):
    modeleChanger = Signal()
    def __init__(self,modele:Modele):
        self.__modele = modele

        pointInteret:QRealSliderSpinBox = QRealSliderSpinBox()
        pointInteret.setRange(-10,10)
        pointInteret.setValue(self.__modele.methode_derive.point_interet)
        pointInteret.setPrefix("Point d'intérêt ")

        pas:QRealSliderSpinBox = QRealSliderSpinBox()
        pas.setRange(0,5)
        pas.setValue(self.__modele.methode_derive.precision)
        pas.setPrefix("Pas (h) ")

        positionPas:QRealSliderSpinBox = QRealSliderSpinBox()
        positionPas.setValue(self.__modele.methode_derive.alpha)
        positionPas.setPrefix("Position pas (alpha) ")

        etendueVisible:QRealSliderSpinBox = QRealSliderSpinBox()
        etendueVisible.setRange(0,5)
        etendueVisible.setValue(self.__modele.methode_derive.etendue_visible)
        etendueVisible.setPrefix("étendue visible ")
        

        self.__reels = [pointInteret,pas,etendueVisible,positionPas]

        self.__boutonGauche = QPushButton("Gauche")
        self.__boutonCentre = QPushButton("Centre")
        self.__boutonDroite = QPushButton("Droite")

        self.__boutonGauche.pressed.connect(self.__mettreDeriveAGauche)
        self.__boutonCentre.pressed.connect(self.__mettreDeriveAuMilieu)
        self.__boutonDroite.pressed.connect(self.__mettreDeriveADroite)

        self.__boutons = [self.__boutonGauche,self.__boutonCentre,self.__boutonDroite]
        
        super().__init__("Méthode dérivé",self.__reels,self.__boutons)

        self.valeurChanger.connect(self.__modifierModele)

        self.__penteApprox = QLabel("Pente approximée : ")
        self.__penteExacte = QLabel("Pente exacte : ")
        self.recalculer()

        self.layout().addWidget(self.__penteApprox)
        self.layout().addWidget(self.__penteExacte)

        boutonTangente = QPushButton("Tangente")
        boutonSecante = QPushButton("Sécante")
        boutonTotal = QPushButton("Les deux")

        boutonTangente.pressed.connect(self.__mettreTangente)
        boutonSecante.pressed.connect(self.__mettreSecante)
        boutonTotal.pressed.connect(self.__mettreTangenteEtSecante)

        self.modeleChanger.connect(self.recalculer)

    @Slot()
    def __mettreDeriveAGauche(self):
        self.__modele.mettre_derive_a_gauche()
        self.__reels[3].setValue(0)
        self.modeleChanger.emit()
    @Slot()
    def __mettreDeriveAuMilieu(self):
        self.__modele.mettre_derive_au_milieu()
        self.__reels[3].setValue(0.5)
        self.modeleChanger.emit()
    @Slot()
    def __mettreDeriveADroite(self):
        self.__modele.mettre_derive_a_droite()
        self.__reels[3].setValue(1)
        self.modeleChanger.emit()

    @Slot()
    def __modifierModele(self):
        self.__modele.methode_derive.point_interet = self.__reels[0].value()
        self.__modele.methode_derive.precision = self.__reels[1].value()
        self.__modele.methode_derive.alpha = self.__reels[3].value()
        self.__modele.methode_derive.etendue_visible = self.__reels[2].value()
        self.modeleChanger.emit()

    @Slot()
    def recalculer(self):
        self.__penteApprox.setText(f"Pente approximée : {self.__modele.methode_derive.approximation}")
        self.__penteExacte.setText(f"Pente exacte : {self.__modele.methode_derive.fonction_math.calculer_exacte_derive(self.__reels[0].value())}")

    @Slot()
    def __mettreTangente(self):
        self.__modele.mettre_mode_tangente()
        self.modeleChanger.emit()

    @Slot()
    def __mettreSecante(self):
        self.__modele.mettre_mode_secante()
        self.modeleChanger.emit()

    @Slot()
    def __mettreTangenteEtSecante(self):
        self.__modele.mettre_mode_tangente_et_secante()
        self.modeleChanger.emit()