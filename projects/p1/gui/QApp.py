from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from projects.p1.gui.QMenuDroite import QMenuDroite
from projects.p1.gui.QGraphique import QGraphique

class QApp(QWidget):

    def __init__(self,modele):
        super().__init__()
        self.__modele = modele
        self.__graphe = QGraphique(modele)
        self.__menuDroite = QMenuDroite(self.__modele)


        principalLayout = QHBoxLayout()
        droiteLayout = QVBoxLayout()

        principalLayout.addWidget(self.__graphe)
        droiteLayout.addWidget(self.__menuDroite)
        
        principalLayout.addLayout(droiteLayout)

        self.setLayout(principalLayout)

        self.__menuDroite.modeleChanger.connect(self.__graphe.actualiser)
