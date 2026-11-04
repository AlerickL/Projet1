from __future__ import annotations
import sys
from typing import override, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.gui.QParametres import QParametres
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique
from projects.p1.model.modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant
from projects.p1.gui.QMenuFormule import QMenuFormule
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QFonctionTransformartionCanonique import QFonctionTransformationCanonique


class QSansMethode(QWidget):
    def __init__(self):
        super().__init__()
        self.__label = QLabel("Joke de math : plante racine")

        principalLayout = QHBoxLayout()

        principalLayout.addLayout(self.__label)

        self.setLayout(principalLayout)