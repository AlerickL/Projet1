from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox

class QMultipleRealSliderSpinBox(QWidget):
    """QMultipleRealSliderSpinBox est une collection de RealSliderSpinBox (fournit dans le cours)
    ValeurChanger est un signal envoyé quand un RealSliderSpinBox est modifié.
    """ 
    valeurChanger = Signal()
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

        for reel in self.__reels:
            reel.valueChanged.connect(self.valeurChanger)


    def valeurs(self) -> list[float]:
        return [reel.value() for reel in self.__reels]

        
    



