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
        self.setAspectLocked(True)

        #Courbe principale
        __xValeurs, __yValeurs = self.__modele.fonction_math.calculer_np(-10, 10, 500)
        self.__courbe : pg.PlotDataItem = pg.PlotDataItem(__xValeurs, __yValeurs, pen="white", width=4)
        self.__viewBox : pg.ViewBox = self.getViewBox()

        self.addItem(self.__courbe)

        # Tangente
        self.__tangente : pg.PlotDataItem = pg.PlotDataItem((), (), pen="red", width=5)
        self.__tangente.hide()

        # Secante
        self.__secante : pg.PlotDataItem = pg.PlotDataItem((), (), pen="yellow", width=5)
        self.__secante.hide()

        #Point d'intérêt
        self.__pointInteret : pg.ScatterPlotItem = pg.ScatterPlotItem((), (), pen="Red", size=10)
        self.__pointInteret.hide()

        self.addItem(self.__tangente)
        self.addItem(self.__secante)
        self.addItem(self.__pointInteret)

        self.__viewBox.sigRangeChangedManually.connect(self.actualiser)
        

    @Slot()
    def actualiser(self):
        self.setTitle(self.__modele.fonction_math.info.nom)
        __xMin, __xMax = self.__viewBox.viewRange()[0]
        __xValeurs, __yValeurs = self.__modele.fonction_math.calculer_np(__xMin, __xMax, 500)
        self.__courbe.setData(__xValeurs, __yValeurs)

        if self.__modele.methode_derive_a_afficher:
            if self.__modele.tangente_a_afficher:
                self.__afficherTangente()
                print("afficher tangente")
            if self.__modele.secante_a_afficher:
                self.__afficherSecante()
                print("afficher secante")
            if self.__modele.tangente_et_secante_a_afficher:
                self.__afficherTangenteEtSecante()
        elif self.__modele.methode_integrale_a_afficher:
            self.__pointInteret.hide()
            self.__tangente.hide()
            self.__secante.hide()
            pass
        else: # aucune méthode
            self.__pointInteret.hide()
            pass


    def __afficherPointInteret(self):
         self.__pointInteret.show()
         _x, _y = self.__modele.methode_derive.point_interet, self.__modele.fonction_math.calculer(self.__modele.methode_derive.point_interet)
         self.__pointInteret.setData([_x], [_y])
    
        
    def __afficherTangente(self, cacherSecante:bool = True):
        self.__afficherPointInteret()
        __xValeurs, __yValeurs = self.__modele.avoir_deux_points_tangente()
        self.__tangente.setData(__xValeurs, __yValeurs)

        if cacherSecante:
            self.__secante.hide()
        self.__tangente.show()
    
    def __afficherSecante(self, cacherTangente:bool = True):
        self.__afficherPointInteret()
        __xValeurs, __yValeurs = self.__modele.avoir_deux_points_derive_approxime()
        self.__secante.setData(__xValeurs, __yValeurs)

        if cacherTangente:
            self.__tangente.hide()
        self.__secante.show()
    
    def __afficherTangenteEtSecante(self):
        self.__afficherTangente(False)
        self.__afficherSecante(False)




