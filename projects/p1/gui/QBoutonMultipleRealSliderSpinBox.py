from __future__ import annotations
import sys
from typing import override
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QPushButton
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.gui.QMultipleRealSliderSpinBox import QMultipleRealSliderSpinBox 

class QBoutonMultipleRealSliderSpinBox(QMultipleRealSliderSpinBox):

    def __init__(self,label:str,reels:list[QRealSliderSpinBox],boutons:list[QPushButton],parent:QWidget|None = None):
        super().__init__(label,reels,parent)
        self.__bouton = boutons

        boutonLayout = QHBoxLayout()

        for bouton in boutons:
            boutonLayout.addWidget(bouton)

        self.layout().addLayout(boutonLayout)

    def avoirBoutons(self) -> list[QPushButton]:
        return self.__bouton
