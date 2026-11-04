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
    def __init__(self : pg.PlotWidget, modele:Modele):
        super().__init__()
        self.__modele : Modele = modele
        self.showGrid(x=True, y=True)
        self.setTitle(self.__modele.fonction_math.info.nom)
        
        self.plotItem.enableAutoRange()
        __xValeurs, __yValeurs = self.__modele.fonction_math.calculer_np(-10, 10, 500)
        self.__courbe : pg.PlotDataItem = pg.PlotDataItem(__xValeurs, __yValeurs, pen="yellow", width=4)
        self.__viewBox : pg.ViewBox = self.getViewBox()

        self.addItem(self.__courbe)
        

        self.__tangente : pg.PlotDataItem = pg.PlotDataItem(pen="red",width=5)
        self.__tangente.hide()
        self.__secante : pg.PlotDataItem = pg.PlotDataItem(pen="blue",width=5)
        self.__secante.hide()

        self.addItem(self.__tangente)
        self.addItem(self.__secante)   

        self.__viewBox.sigRangeChangedManually.connect(self.actualiser)
        

    @Slot()
    def actualiser(self):
        self.setTitle(self.__modele.fonction_math.info.nom)
        __x_min, __x_max = self.__viewBox.viewRange()[0]
        __xValeurs, __yValeurs = self.__modele.fonction_math.calculer_np(__x_min, __x_max, 500)
        self.__courbe.setData(__xValeurs, __yValeurs)

    @Slot()
    def afficher_tangente(self, hide_secante:bool = True):
        __xValeurs, __yValeurs = self.__modele.avoir_deux_points_tangente()
        self.__tangente.setData(__xValeurs, __yValeurs)

        if hide_secante:
            self.__secante.hide()
        self.__tangente.show()

    @Slot()
    def afficher_secante(self, hide_tangente:bool = True):
        __xValeurs, __yValeurs = self.__modele.avoir_deux_points_derive_approxime()
        self.__secante.setData(__xValeurs, __yValeurs)

        if hide_tangente:
            self.__tangente.hide()
        self.__secante.show()

    @Slot()
    def afficher_tangente_et_secante(self):
        self.afficher_tangente(False)
        self.afficher_secante(False)




