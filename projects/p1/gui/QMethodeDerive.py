from __future__ import annotations
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from edustem.pyside6.widgets.q_slider_spin_box import QRealSliderSpinBox
from projects.p1.model.modele import Modele
from projects.p1.gui.QBoutonMultipleRealSliderSpinBox import QBoutonMultipleRealSliderSpinBox

class QMethodeDerive(QBoutonMultipleRealSliderSpinBox):
    modeleChanger = Signal()
    def __init__(self,modele:Modele):
        self.__modele = modele

        pointInteret:QRealSliderSpinBox = QRealSliderSpinBox()
        pointInteret.setRange(-10,10)
        pointInteret.setValue(self.__modele.methode_derive.point_interet)
        pointInteret.setPrefix("Point d'intérêt ")

        pas:QRealSliderSpinBox = QRealSliderSpinBox()
        pas.setRange(0,5)
        pas.setValue(self.__modele.methode_derive.precision)
        pas.setPrefix("Pas (h) ")

        positionPas:QRealSliderSpinBox = QRealSliderSpinBox()
        positionPas.setValue(self.__modele.methode_derive.alpha)
        positionPas.setPrefix("Position pas (alpha) ")

        etendueVisible:QRealSliderSpinBox = QRealSliderSpinBox()
        etendueVisible.setRange(0,5)
        etendueVisible.setValue(self.__modele.methode_derive.etendue_visible)
        etendueVisible.setPrefix("étendue visible ")
        

        self.__reels = [pointInteret,pas,etendueVisible,positionPas]

        self.__boutonGauche = QPushButton("Gauche")
        self.__boutonCentre = QPushButton("Centre")
        self.__boutonDroite = QPushButton("Droite")

        self.__boutonGauche.pressed.connect(self.__mettreDeriveAGauche)
        self.__boutonCentre.pressed.connect(self.__mettreDeriveAuMilieu)
        self.__boutonDroite.pressed.connect(self.__mettreDeriveADroite)

        self.__boutons = [self.__boutonGauche,self.__boutonCentre,self.__boutonDroite]
        
        super().__init__("Méthode dérivé",self.__reels,self.__boutons)

        self.valeurChanger.connect(self.__modifierModele)

        __layoutPente = QVBoxLayout()
        self.__penteApprox = QLabel("Pente approximée : ")
        self.__penteExacte = QLabel("Pente exacte : ")
        __layoutPente.addWidget(self.__penteApprox)
        __layoutPente.addWidget(self.__penteExacte)

        __layoutEcart = QVBoxLayout()
        self.__ecartRelatif = QLabel("Écart Relatif : ")
        self.__ecartAbsolu = QLabel("Écart Absolu : ")
        __layoutEcart.addWidget(self.__ecartAbsolu)
        __layoutEcart.addWidget(self.__ecartRelatif)

        __layoutPenteEcart = QHBoxLayout()
        __layoutPenteEcart.addLayout(__layoutPente)
        __layoutPenteEcart.addLayout(__layoutEcart)

        __widgetPenteEcart = QWidget()
        __widgetPenteEcart.setLayout(__layoutPenteEcart)

        self.recalculer()

        self.layout().addWidget(__widgetPenteEcart)
     
        boutonTangente = QPushButton("Tangente")
        boutonTangente.clicked.connect(self.__mettreTangente)
        boutonSecante = QPushButton("Sécante")
        boutonSecante.clicked.connect(self.__mettreSecante)
        boutonTotal = QPushButton("Les deux")
        boutonTotal.clicked.connect(self.__mettreTangenteEtSecante)

        __layout_boutons = QHBoxLayout()
        __layout_boutons.addWidget(boutonTangente)
        __layout_boutons.addWidget(boutonSecante)
        __layout_boutons.addWidget(boutonTotal)

        self.layout().addLayout(__layout_boutons)

        boutonTangente.pressed.connect(self.__mettreTangente)
        boutonSecante.pressed.connect(self.__mettreSecante)
        boutonTotal.pressed.connect(self.__mettreTangenteEtSecante)

    @Slot()
    def __mettreDeriveAGauche(self):
        self.__modele.mettre_derive_a_gauche()
        self.__reels[3].setValue(0)
        self.modeleChanger.emit()
    @Slot()
    def __mettreDeriveAuMilieu(self):
        self.__modele.mettre_derive_au_milieu()
        self.__reels[3].setValue(0.5)
        self.modeleChanger.emit()
    @Slot()
    def __mettreDeriveADroite(self):
        self.__modele.mettre_derive_a_droite()
        self.__reels[3].setValue(1)
        self.modeleChanger.emit()

    @Slot()
    def __modifierModele(self):
        self.__modele.methode_derive.point_interet = self.__reels[0].value()
        self.__modele.methode_derive.precision = self.__reels[1].value()
        self.__modele.methode_derive.alpha = self.__reels[3].value()
        self.__modele.methode_derive.etendue_visible = self.__reels[2].value()
        self.modeleChanger.emit()

    @Slot()
    def recalculer(self):
        self.__penteApprox.setText(f"Pente approximée : {self.__modele.methode_derive.approximation}")
        self.__penteExacte.setText(f"Pente exacte : {self.__modele.methode_derive.valeur_exacte}")
        self.__ecartAbsolu.setText(f"Écart Absolu : {self.__modele.methode_derive.ecart_absolu()}")
        self.__ecartRelatif.setText(f"Écart Relatif :  {self.__modele.methode_derive.ecart_relatif():.2f}%")

    @Slot()
    def __mettreTangente(self):
        self.__modele.mettre_mode_tangente()
        self.modeleChanger.emit()

    @Slot()
    def __mettreSecante(self):
        self.__modele.mettre_mode_secante()
        self.modeleChanger.emit()

    @Slot()
    def __mettreTangenteEtSecante(self):
        self.__modele.mettre_mode_tangente_et_secante()
        self.modeleChanger.emit()

    def __appliquerModele(self):
        self.__reels[0].setValue(self.__modele.methode_derive.point_interet)
        self.__reels[1].setValue(self.__modele.methode_derive.precision)
        self.__reels[2].setValue(self.__modele.methode_derive.etendue_visible)
        self.__reels[3].setValue(self.__modele.methode_derive.alpha)

    def reinitialiser(self):
        self.blockSignals(True)
        self.__modele.methode_derive.reinitialiser()
        self.__appliquerModele()
        self.blockSignals(False)
        self.modeleChanger.emit()