from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.gui.QMultipleRealSliderSpinBox import QMultipleRealSliderSpinBox 

class QBoutonMultipleRealSliderSpinBox(QMultipleRealSliderSpinBox):
    """Widget héritant de QMultipleRealSliderSpinBox. C'est une liste de QRealSliderSpinBox avec une série de bouton à la fin.
    """
    def __init__(self,label:str,reels:list[QRealSliderSpinBox],boutons:list[QPushButton],parent:QWidget|None = None):
        super().__init__(label,reels,parent)
        self.__bouton = boutons

        boutonLayout = QHBoxLayout()

        for bouton in boutons:
            bouton.setSizePolicy(QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Maximum)
            boutonLayout.addWidget(bouton)

        self.layout().addLayout(boutonLayout)

    def avoirBoutons(self) -> list[QPushButton]:
        return self.__bouton

