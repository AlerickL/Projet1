from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox, QSliderSpinBox, QAbstractSliderSpinBox
from edustem.pyside6.widgets.q_range_slider_spin_box import QRealRangeSliderSpinBox
from projects.p1.gui.QBoutonMultipleRealSliderSpinBox import QBoutonMultipleRealSliderSpinBox
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique
from projects.p1.model.modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant
from projects.p1.gui.QMenuFormule import QMenuFormule
from projects.p1.gui.QSelectionFonction import QSelectionFonction

class QMethodeIntegrale(QBoutonMultipleRealSliderSpinBox):
    modeleChanger = Signal()
    def __init__(self,modele:Modele):
        self.__modele = modele

        pas:QSliderSpinBox = QSliderSpinBox()
        pas.setRange(1,100)
        pas.setValue(self.__modele.methode_integrale.precision)
        pas.setPrefix("Nombre de formes ")

        positionForme:QRealSliderSpinBox = QRealSliderSpinBox()
        positionForme.setValue(self.__modele.methode_integrale.alpha)
        positionForme.setPrefix("Position forme (alpha) ")

        self.__sliders:list[QAbstractSliderSpinBox] = [pas,positionForme]

        self.__boutonGauche = QPushButton("Gauche")
        self.__boutonCentre = QPushButton("Centre")
        self.__boutonDroite = QPushButton("Droite")

        self.__boutonGauche.pressed.connect(self.__mettre_forme_a_gauche)
        self.__boutonCentre.pressed.connect(self.__mettre_forme_au_milieu)
        self.__boutonDroite.pressed.connect(self.__mettre_forme_a_droite)

        self.__boutons = [self.__boutonGauche,self.__boutonCentre,self.__boutonDroite]

        super().__init__("Méthode intégrale",self.__sliders,self.__boutons)

        self.valeurChanger.connect(self.__modifierModele)

        self.__rangeSliderSpinBox:QRealRangeSliderSpinBox = QRealRangeSliderSpinBox()
        self.__rangeSliderSpinBox.setLimits(-10,10)
        self.__rangeSliderSpinBox.setPrefix("Bornes ")

        self.__integraleApprox = QLabel("Intégrale approximée : ")
        self.__integraleExacte = QLabel("Intégrale exacte : ")
        self.recalculer()

        self.__boutonRectangle = QPushButton("Rectangle")
        self.__boutonTrapeze = QPushButton("Trapèze")

        secondBoutonsLayout = QHBoxLayout()
        secondBoutonsLayout.addWidget(self.__boutonRectangle)
        secondBoutonsLayout.addWidget(self.__boutonTrapeze)

        self.__boutonRectangle.pressed.connect(self.mettreRectangle)
        self.__boutonTrapeze.pressed.connect(self.mettreTrapeze)

        self.layout().addWidget(self.__rangeSliderSpinBox)
        self.layout().addWidget(self.__integraleApprox)
        self.layout().addWidget(self.__integraleExacte)
        self.layout().addWidget(self.__boutonRectangle)
        self.layout().addWidget(self.__boutonTrapeze)

        self.__rangeSliderSpinBox.rangeChanged.connect(self.__modifierModele)

        self.modeleChanger.connect(self.recalculer)

    @Slot()
    def __mettre_forme_a_gauche(self):
        self.__modele.mettre_integrale_a_gauche()
        self.__sliders[1].setValue(0)
        self.modeleChanger.emit()
    @Slot()
    def __mettre_forme_au_milieu(self):
        self.__modele.mettre_integrale_au_milieu()
        self.__sliders[1].setValue(0.5)
        self.modeleChanger.emit()
    @Slot()
    def __mettre_forme_a_droite(self):
        self.__modele.mettre_integrale_a_droite()
        self.__sliders[1].setValue(1)
        self.modeleChanger.emit()

    @Slot()
    def __modifierModele(self):
        self.__modele.methode_integrale.precision = self.__sliders[0].value()
        self.__modele.methode_integrale.alpha = self.__sliders[1].value()
        self.__modele.methode_integrale.intervalle = (self.__rangeSliderSpinBox.lowerValue(),self.__rangeSliderSpinBox.upperValue())
        self.modeleChanger.emit()

    @Slot()
    def recalculer(self):
        print("recalculer")
        self.__integraleApprox.setText(f"Intégrale approximée : {self.__modele.methode_integrale.approximation} ")
        self.__integraleExacte.setText(f"Intégrale exacte : {self.__modele.methode_integrale.fonction_math.calculer_exacte_integrale(*self.__modele.methode_integrale.intervalle)}")

    @Slot()
    def mettreRectangle(self):
        self.__modele.mettre_mode_rectangle()
        self.modeleChanger.emit()

    @Slot()
    def mettreTrapeze(self):
        self.__modele.mettre_mode_trapeze()
        self.modeleChanger.emit()


        