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
        reel_trans_x = QRealSliderSpinBox()
        reel_trans_x.setPrefix(modele.transformation_canonique.trans_x.info.nom+ " ")
        reel_trans_x.setRange(modele.transformation_canonique.trans_x.min_valeur,modele.transformation_canonique.trans_x.max_valeur)
        self.__init__("Transformations canoniques",[reel_trans_x],parent)