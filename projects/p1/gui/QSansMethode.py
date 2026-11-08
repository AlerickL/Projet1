from __future__ import annotations
import sys
from typing import override, cast
import random
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QColor, QShowEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton, QSizePolicy
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.gui.QParametres import QParametres
from projects.p1.gui.QTransformationCanonique import QTransformationCanonique
from projects.p1.model.modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant
from projects.p1.gui.QMenuFormule import QMenuFormule
from projects.p1.gui.QSelectionFonction import QSelectionFonction
from projects.p1.gui.QGraphique import QGraphique
from projects.p1.gui.QBoutonMultipleRealSliderSpinBox import QBoutonMultipleRealSliderSpinBox



class QSansMethode(QWidget):
    def __init__(self, parent:QWidget|None = None):
        super().__init__(parent)
        self.__blagues  = (
            "C'est le Logarithme qui tente de motiver l'Exponentielle. Elle répond : « Que je m'intègre ou non, c'est pareil ».",
            "Quelle est la fonction la plus heureuse ? |x|, parce qu'elle est toujours positive.",
            "y = mx + b est définitivement mon one-liner favori.",
            "Tu sais qui a inventé l'algèbre ? Un X-pert.",
            "Pourquoi les arbres de maths tombent-ils en hiver ? Parce qu'ils n'ont pas de racines réelles.",
            "Le cercle a décidé de ne pas aller à l'université parce qu'il avait déjà 360 degrés.",
            "Il y a 10 types de personnes dans le monde : celles qui comprennent le binaire, et les autres.",
            "Les statistiques, c'est comme le bikini : ça donne des idées mais ça cache l'essentiel.",
            "Pourquoi le livre de maths est-il toujours déprimé ? Parce qu'il a trop de problèmes.",
            "Ma blonde est comme la racine carrée de -100 : un solide 10, mais purement imaginaire.",
            "Il y a trois types de mathématiciens dans le monde : ceux qui savent compter, et ceux qui ne savent pas.",
            "Mon psychiatre dit que je souffre d'un trouble de l'attention aigu, mais je pense qu'il est juste un peu obtus.",
            "Mon colocataire passe son temps à calculer des intégrales impropres, je trouve que son comportement manque vraiment de limites.",
            )
        self.__titre = QLabel("Joke de math : ")
        self.__titre.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.__blague = QLabel("L'amour, c'est comme les maths : ça commence par un Bézout et ça finit par un Gauss.")
        self.__blague.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__blague.setWordWrap(True)

        layoutPrincipal : QVBoxLayout = QVBoxLayout()
        layoutBlague : QHBoxLayout = QHBoxLayout()

        self.__random : QPushButton = QPushButton("Trop drôle! Une autre SVP!")
        self.__random.pressed.connect(self.__generer_blague)


        layoutBlague.addWidget(self.__titre)
        layoutBlague.addWidget(self.__blague)
        layoutPrincipal.addLayout(layoutBlague)
        layoutPrincipal.addWidget(self.__random)

        self.setLayout(layoutPrincipal)

    @Slot()
    def __generer_blague(self):
        rnd = random.randint(0, len(self.__blagues))
        self.__blague.setText(self.__blagues[rnd])
        