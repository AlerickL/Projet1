from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QMessageBox
from projects.p1.model.modele import Modele
from projects.p1.gui.QBoutonMultipleRealSliderSpinBox import QBoutonMultipleRealSliderSpinBox
from projects.p1.gui.QSansMethode import QSansMethode
from projects.p1.gui.QMethodeDerive import QMethodeDerive
from projects.p1.gui.QMethodeIntegrale import QMethodeIntegrale

class QMethode(QBoutonMultipleRealSliderSpinBox):
    modeleChanger = Signal()
    def __init__(self,modele:Modele):
        self.__modele:Modele = modele

        __boutonSansMethode = QPushButton("Aucune méthode")
        __boutonDerive = QPushButton("Dérivé")
        __boutonIntegrale = QPushButton("Intégrale")


        super().__init__("Méthodes numériques",[],[__boutonSansMethode,__boutonDerive,__boutonIntegrale])

        self.__boutonInfo = QPushButton("Information")
        self.__boutonReinitialiser = QPushButton("Réinitialiser")

        self.__boutonInfo.pressed.connect(self.__mettreInfo)
        self.__boutonReinitialiser.pressed.connect(self.__reinitialiser)

        self.__sansMethode = QSansMethode()
        self.__methodeDerive = QMethodeDerive(self.__modele)
        self.__methodeIntegrale = QMethodeIntegrale(self.__modele)

        self.layout().addWidget(self.__boutonInfo)
        self.layout().addWidget(self.__boutonReinitialiser)
        self.layout().addWidget(self.__sansMethode)
        self.layout().addWidget(self.__methodeDerive)
        self.layout().addWidget(self.__methodeIntegrale)

        self.__methodeDerive.setVisible(False)
        self.__methodeIntegrale.setVisible(False)

        
        __boutonSansMethode.pressed.connect(self.__mettreSansMethode)
        __boutonDerive.pressed.connect(self.__mettreMethodeDerive)
        __boutonIntegrale.pressed.connect(self.__mettreMethodeIntegrale)

        self.__methodeDerive.modeleChanger.connect(self.modeleChanger)
        self.__methodeIntegrale.modeleChanger.connect(self.modeleChanger)

    @property
    def methodeDerive(self) -> QMethodeDerive:
        return self.__methodeDerive
    @property
    def methodeIntegrale(self) -> QMethodeIntegrale:
        return self.__methodeIntegrale

    def __mettreSansMethode(self):
        self.__modele.mettre_affichage_aucun()
        self.__methodeDerive.setVisible(False)
        self.__methodeIntegrale.setVisible(False)
        self.__sansMethode.setVisible(True)
        self.modeleChanger.emit()

    def __mettreMethodeDerive(self):
        self.__modele.mettre_affichage_derive()
        self.__methodeIntegrale.setVisible(False)
        self.__sansMethode.setVisible(False)
        self.__methodeDerive.setVisible(True)
        self.modeleChanger.emit()

    def __mettreMethodeIntegrale(self):
        self.__modele.mettre_affichage_integrale()
        self.__methodeDerive.setVisible(False)
        self.__methodeIntegrale.setVisible(True)
        self.__sansMethode.setVisible(False)
        self.modeleChanger.emit()

    def __mettreInfo(self):
        if self.__modele.methode_derive_a_afficher or self.__modele.methode_integrale_a_afficher:
            if self.__modele.methode_derive_a_afficher:
                methodeInfo = self.__modele.methode_derive.info
            else:
                methodeInfo = self.__modele.methode_integrale.info
            texte = "Résumé :\n" + methodeInfo.resume+"\n\nDétails :\n"+methodeInfo.details
        else:
            texte = "C'est des blagues vraiment super cool"

        QMessageBox.information(self,"La méthode numérique actuellement appliquée",texte)

    def __reinitialiser(self):
        if self.__modele.methode_derive_a_afficher:
            self.methodeDerive.reinitialiser()
        elif self.__modele.methode_integrale_a_afficher:
            self.methodeIntegrale.reinitialiser()
