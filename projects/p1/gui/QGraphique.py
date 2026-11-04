from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant
from projects.p1.gui.QMenuFormule import QMenuFormule
from projects.p1.gui.QParametres import QParametres
import pyqtgraph as pg

class QGraphique(pg.PlotWidget):
    def __init__(self,modele:Modele):
        super().__init__()
        self.__modele = modele
        self.plotItem.setTitle(self.__modele.fonction_math.info.nom)
        xValeurs, yValeurs = self.__modele.fonction_math.calculer_np(0.0,1.0,100)
        self.plotItem.plot(xValeurs, yValeurs)
# fix renitialiser puisque le graphique ne se met pas à jour quand on change de fonction

    def actualiser(self):
        self.plotItem.clear()
        self.plotItem.setTitle(self.__modele.fonction_math.info.nom)
        xValeurs, yValeurs = self.__modele.fonction_math.calculer_np(0.0,1.0,100)
        self.plotItem.plot(xValeurs, yValeurs)
    