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
        self.__line : pg.PlotDataItem = pg.PlotDataItem(__xValeurs, __yValeurs, pen="purple", width=2)
        self.__viewBox : pg.ViewBox = self.getViewBox()
    

        self.addItem(self.__line)
        self.__viewBox.sigRangeChangedManually.connect(self.actualiser)
        

    @Slot()
    def actualiser(self):
        self.setTitle(self.__modele.fonction_math.info.nom)
        __x_min, __x_max = self.__viewBox.viewRange()[0]
        __xValeurs, __yValeurs = self.__modele.fonction_math.calculer_np(__x_min, __x_max, 500)
        self.__line.setData(__xValeurs, __yValeurs)
