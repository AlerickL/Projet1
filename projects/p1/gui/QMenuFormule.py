from __future__ import annotations
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel,QHBoxLayout, QVBoxLayout, QSizePolicy
from projects.p1.model.modele import Modele
from projects.p1.gui.QMenuDeroulant import QMenuDeroulant

class QMenuFormule(QWidget):
    """menu déroulant et véritable formule de la fonction.
    formuleChange est émit quand la formule véritable est modifié.
    modeleChanger est émit quand la classe modifie le modèle.
    """
    formuleChange = Signal()
    modeleChanger = Signal()
    def __init__(self,modele:Modele):
        super().__init__()
        self.__modele = modele
        self._menu = QMenuDeroulant(modele)
        self.__vrai_formule = QLabel(self.__modele.avoir_vraie_formule())
        self.__vrai_formule.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Maximum)
        
      
        principalLayout = QHBoxLayout()
        secondLayout = QVBoxLayout()

        titre = QLabel("Sélection de la fonction")
        font : QFont = titre.font()

        font.setBold(True)
        titre.setFont(font)

        titre.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Maximum)

        secondLayout.addWidget(titre)
        secondLayout.addWidget(self._menu)
        secondLayout.addWidget(self.__vrai_formule)

        principalLayout.addLayout(secondLayout)
        self.setLayout(principalLayout)

        self._menu.currentTextChanged.connect(self.__changementFonctionModele)
        self._menu.currentTextChanged.connect(self.formuleChange)

    def menu(self):
        return self._menu

    @Slot()
    def __changementFonctionModele(self):
        if self._menu.currentText() == "Fonction sinus":
            self.__modele.changer_fonction_sin()
        elif self._menu.currentText() == "Fonction polynomial du second degré":
            self.__modele.changer_fonction_second_degre()
        elif self._menu.currentText() == "Fonction sinus amortie":
            self.__modele.changer_fonction_sin_amortie()
        elif self._menu.currentText() == "Fonction double bosse":
            self.__modele.changer_fonction_double_bosse()
        self.changerVraiFormule()


    @Slot()
    def changerVraiFormule(self):
        self.__vrai_formule.setText(self.__modele.avoir_vraie_formule())
        self.modeleChanger.emit()

