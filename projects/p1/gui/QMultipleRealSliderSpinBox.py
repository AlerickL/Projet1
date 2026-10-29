from __future__ import annotations
import sys
from typing import override
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox

class QMultipleRealSliderSpinBox(QWidget):
    def __init__(self,label:str,reels:list[QRealSliderSpinBox],parent:QWidget|None = None) -> None:
        super().__init__(parent)

        mainLayout = QVBoxLayout()
        reelLayout = QVBoxLayout()

        titre = QLabel(label)

        for reel in reels:
            reelLayout.addWidget(reel)

        mainLayout.addWidget(titre)
        mainLayout.addLayout(reelLayout)

        self.setLayout(mainLayout)
    



