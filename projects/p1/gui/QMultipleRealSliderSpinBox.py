from __future__ import annotations
import sys
from typing import override
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent, QFont
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QSizePolicy
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox

class QMultipleRealSliderSpinBox(QWidget):
    """QMultipleRealSliderSpinBox est une collection de RealSliderSpinBox (fournit dans le cours)
    ValeurChanger est un signal envoyé quand un RealSliderSpinBox est modifié.
    """
    valeurChanger = Signal(int|float)
    def __init__(self,label:str,reels:list[QRealSliderSpinBox],parent:QWidget|None = None) -> None:
        super().__init__(parent)

        self.__reels = reels

        mainLayout = QVBoxLayout()
        reelLayout = QVBoxLayout()

        titre:QLabel = QLabel(label)
        font : QFont = titre.font()
        font.setBold(True)
        titre.setFont(font)
        
        titre.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Maximum)

        for reel in reels:
            reelLayout.addWidget(reel)

        mainLayout.addWidget(titre)
        mainLayout.addLayout(reelLayout)

        self.setLayout(mainLayout)

        self.valeurChanger.connect(self.__print)

        for reel in self.__reels:
            reel.valueChanged.connect(self.valeurChanger)


    def valeurs(self) -> list[float]:
        return [reel.value() for reel in self.__reels]

    def __print(self): # À enlever un jour !
        print(self.valeurs())
        
    



