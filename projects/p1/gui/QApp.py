from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.gui.QFonctionTransformartionCanonique import QFonctionTransformationCanonique
from projects.p1.gui.QParametres import QParametres
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique
from projects.p1.model.modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant
from projects.p1.gui.QMenuFormule import QMenuFormule
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QFonctionTransformartionCanonique import QFonctionTransformationCanonique
from projects.p1.gui.QGraphTest import QGraphTest

class QApp(QWidget):

    def __init__(self,modele):
        super().__init__()
        self.__modele = modele
        self.__graphe = QGraphTest(self.__modele)
        self.__fonctionSelectionTransformationCanonique = QFonctionTransformationCanonique(modele)


        principalLayout = QHBoxLayout()
        droiteLayout = QVBoxLayout()

        principalLayout.addWidget(self.__graphe)
        droiteLayout.addWidget(self.__fonctionSelectionTransformationCanonique)
        
        principalLayout.addLayout(droiteLayout)

        self.setLayout(principalLayout)

        self.__fonctionSelectionTransformationCanonique.modeleChanger.connect(self.__graphe.actualiser)
