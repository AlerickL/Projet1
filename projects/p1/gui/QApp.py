from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.gui.QMenuDroite import QMenuDroite
from projects.p1.gui.QParametres import QParametres
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique
from projects.p1.model.modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant
from projects.p1.gui.QMenuFormule import QMenuFormule
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QMenuDroite import QMenuDroite
from projects.p1.gui.QGraphique import QGraphique

class QApp(QWidget):

    def __init__(self,modele):
        super().__init__()
        self.__modele = modele
        self.__graphe = QGraphique(modele)
        self.__menuDroite = QMenuDroite(self.__modele)


        principalLayout = QHBoxLayout()
        droiteLayout = QVBoxLayout()

        principalLayout.addWidget(self.__graphe)
        droiteLayout.addWidget(self.__menuDroite)
        
        principalLayout.addLayout(droiteLayout)

        self.setLayout(principalLayout)

        self.__menuDroite.modeleChanger.connect(self.__graphe.actualiser)

        self.__menuDroite.tangente.connect(self.__graphe.afficher_tangente)
        self.__menuDroite.secante.connect(self.__graphe.afficher_secante)
        self.__menuDroite.tangenteEtSecante.connect(self.__graphe.afficher_tangente_et_secante)