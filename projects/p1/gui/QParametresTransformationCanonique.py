from __future__ import annotations
import sys
#from QMultipleRealSliderSpinBox import QMultipleRealSliderSpinBox
from typing import override
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.Modele import Modele
from projects.p1.gui.QMultipleRealSliderSpinBox import QMultipleRealSliderSpinBox

class QParametresTransformationCanonique(QMultipleRealSliderSpinBox):
    def __init__(self,modele:Modele,parent:QWidget|None=None)-> None:

        reelTransX = QRealSliderSpinBox()
        reelTransX.setPrefix(modele.transformation_canonique.trans_x.info.nom+ " ")
        reelTransX.setRange(modele.transformation_canonique.trans_x.min_valeur,modele.transformation_canonique.trans_x.max_valeur)
        reelTransX.setValue(modele.transformation_canonique.trans_x.defaut_valeur)

        reelTransY = QRealSliderSpinBox()
        reelTransY.setPrefix(modele.transformation_canonique.trans_y.info.nom+ " ")
        reelTransY.setRange(modele.transformation_canonique.trans_y.min_valeur,modele.transformation_canonique.trans_y.max_valeur)
        reelTransY.setValue(modele.transformation_canonique.trans_y.defaut_valeur)

        reelZoomX = QRealSliderSpinBox()
        reelZoomX.setPrefix(modele.transformation_canonique.zoom_x.info.nom+ " ")
        reelZoomX.setRange(modele.transformation_canonique.zoom_x.min_valeur,modele.transformation_canonique.zoom_x.max_valeur)
        reelZoomX.setValue(modele.transformation_canonique.zoom_x.defaut_valeur)

        reelZoomY = QRealSliderSpinBox()
        reelZoomY.setPrefix(modele.transformation_canonique.zoom_y.info.nom+ " ")
        reelZoomY.setRange(modele.transformation_canonique.zoom_y.min_valeur,modele.transformation_canonique.zoom_y.max_valeur)
        reelZoomY.setValue(modele.transformation_canonique.zoom_y.defaut_valeur)

        
        #self.layout().addWidget(self.)

        super().__init__("Transformations canoniques",[reelTransX,reelTransY,reelZoomX,reelZoomY],parent)