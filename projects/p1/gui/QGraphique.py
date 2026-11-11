from __future__ import annotations
from PySide6.QtCore import Slot, QPointF
from PySide6.QtGui import QPolygonF
from PySide6.QtWidgets import QGraphicsPolygonItem, QSizePolicy
from projects.p1.model.modele import Modele
from numpy.typing import NDArray
import pyqtgraph as pg
from pyqtgraph import LegendItem

class QGraphique(pg.PlotWidget):
    def __init__(self : pg.PlotWidget, modele:Modele):
        super().__init__()
        self.__modele : Modele = modele
        self.showGrid(x=True, y=True)
        self.setTitle(self.__modele.fonction_math.info.nom)
        self.setAspectLocked(True)
        self.__legend : LegendItem = self.addLegend()
    

        #Courbe principale
        __xValeurs, __yValeurs = self.__modele.fonction_math.calculer_np(-10, 10, 500)
        self.__courbe : pg.PlotDataItem = pg.PlotDataItem(__xValeurs, __yValeurs, pen="white", width=4, name = "Fonction")
        self.__viewBox : pg.ViewBox = self.getViewBox()

        self.addItem(self.__courbe)

        

        # Tangente
        self.__tangente : pg.PlotDataItem = pg.PlotDataItem((), (), pen="red", width=5)
        self.__tangente.hide()

        # Secante
        self.__secante : pg.PlotDataItem = pg.PlotDataItem((), (), pen="yellow", width=5)
        self.__secante.hide()

        #Point d'intérêt
        self.__pointInteret : pg.ScatterPlotItem = pg.ScatterPlotItem((), (), pen="Red", size=10)
        self.__pointInteret.hide()

        #Points de la sécante
        self.__pointsSecante : pg.ScatterPlotItem = pg.ScatterPlotItem((), (), pen="Yellow", size=10)


        self.__rectangles:list[QGraphicsPolygonItem] = []
        self.__initialiserFormes(self.__rectangles)

        self.__trapezes:list[QGraphicsPolygonItem] = []
        self.__initialiserFormes(self.__trapezes)

        self.addItem(self.__tangente)
        self.addItem(self.__secante)
        self.addItem(self.__pointInteret)
        self.addItem(self.__pointsSecante)
        self.__viewBox.sigRangeChangedManually.connect(self.actualiser)

        # Besoin de set Range sinon ça fait drole au début si on change sliders.
        self.__viewBox.setXRange(-5, 5)
        self.__viewBox.setYRange(-5, 5)

        # Expanding, car graphique doit être + gros possible
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum)
        

    @Slot()
    def actualiser(self):
        self.setTitle(self.__modele.fonction_math.info.nom)
        __xMin, __xMax = self.__viewBox.viewRange()[0]
        __xValeurs, __yValeurs = self.__modele.fonction_math.calculer_np(__xMin, __xMax, 500)
        self.__courbe.setData(__xValeurs, __yValeurs)
        self.__actualiserMethodeNumerique()


    
    def __actualiserMethodeNumerique(self) -> None:
        self.__legend.clear()
        self.__legend.addItem(self.__courbe, "Fonction")
        if self.__modele.methode_derive_a_afficher:
            for i in range(self.__modele.methode_integrale.nombre_total_forme):
                self.__rectangles[i].hide()
            if self.__modele.tangente_a_afficher:
                self.__afficherTangente() 
                self.__legend.addItem(self.__tangente, "Tangente")
            if self.__modele.secante_a_afficher:
                self.__afficherSecante()
                self.__legend.addItem(self.__secante, "Sécante")
            if self.__modele.tangente_et_secante_a_afficher:
                self.__afficherTangenteEtSecante()
                self.__legend.addItem(self.__tangente, "Tangente")
                self.__legend.addItem(self.__secante, "Sécante")
        elif self.__modele.methode_integrale_a_afficher:
            self.__pointsSecante.hide()
            self.__pointInteret.hide()
            self.__tangente.hide()
            self.__secante.hide()
            if self.__modele.rectangle_a_afficher:
                self.__cacherFormes(self.__trapezes)
                self.__afficherRectangles()
            elif self.__modele.trapeze_a_afficher:
                self.__cacherFormes(self.__rectangles)
                self.__afficherTrapezes()
        else: # aucune méthode
            self.__pointInteret.hide()
            self.__pointsSecante.hide()
            self.__tangente.hide()
            self.__secante.hide()
            self.__cacherToutesFormes()



    def __afficherPointInteret(self):
        self.__pointInteret.show()
        _x, _y = self.__modele.methode_derive.point_interet, self.__modele.fonction_math.calculer(self.__modele.methode_derive.point_interet)
        self.__pointInteret.setData([_x], [_y])

    def __afficherPointsSecante(self):
        self.__pointsSecante.show()
        pointMoins = self.__modele.methode_derive.avoir_premiere_valeur()
        pointPlus = self.__modele.methode_derive.avoir_seconde_valeur()
        _x, _y = [pointMoins, pointPlus], [self.__modele.fonction_math.calculer(pointMoins),self.__modele.fonction_math.calculer(pointPlus)]
        self.__pointsSecante.setData(_x, _y)

    def __afficherPointApresSecante(self):
        self.__pointPlus.show()
        pointPlus = self.__modele.methode_derive.avoir_seconde_valeur()
        _x, _y = pointPlus, self.__modele.fonction_math.calculer(pointPlus)
        self.__pointPlus.setData([_x], [_y])
    
        
    def __afficherTangente(self, cacherSecante:bool = True):
        self.__afficherPointInteret()
        __xValeurs, __yValeurs = self.__modele.avoir_deux_points_tangente()
        self.__tangente.setData(__xValeurs, __yValeurs)

        if cacherSecante:
            self.__secante.hide()
            self.__pointsSecante.hide()
        self.__tangente.show()
    
    def __afficherSecante(self, cacherTangente:bool = True):
        self.__afficherPointInteret()
        self.__afficherPointsSecante()
        __xValeurs, __yValeurs = self.__modele.avoir_deux_points_derive_approxime()
        self.__secante.setData(__xValeurs, __yValeurs)

        if cacherTangente:
            self.__tangente.hide()
        self.__secante.show()
    
    def __afficherTangenteEtSecante(self):
        self.__afficherTangente(False)
        self.__afficherSecante(False)

    def __afficherRectangles(self):
        coordonnees = self.__modele.methode_integrale.avoir_coordonnees_rectangles()
        self.__afficherFormes(self.__rectangles, coordonnees)

    def __afficherTrapezes(self):
        coordonnees = self.__modele.methode_integrale.avoir_coordonnees_trapezes()
        self.__afficherFormes(self.__trapezes, coordonnees)

    def __afficherFormes(self, formes: list[QGraphicsPolygonItem], coordonnees: NDArray):
        for i in range(self.__modele.methode_integrale.nombre_total_forme):
            if i<= int(self.__modele.methode_integrale.precision)-1:
                xs, ys = coordonnees[i,0:4], coordonnees[i,4:]
                points = [QPointF(x, y) for x, y in zip(xs, ys)]
                formes[i].setPolygon(QPolygonF(points))
                formes[i].show()
            else:
                formes[i].hide()

    def __cacherFormes(self, formes: list[QGraphicsPolygonItem]):
        for i in range(self.__modele.methode_integrale.nombre_total_forme):
            formes[i].hide()

    def __cacherToutesFormes(self):
        for i in range(self.__modele.methode_integrale.nombre_total_forme):
            self.__trapezes[i].hide()
            self.__rectangles[i].hide()

    def __initialiserFormes(self, listeForme: list):
        for _ in range(self.__modele.methode_integrale.nombre_total_forme):
            forme = QGraphicsPolygonItem(QPolygonF())
            listeForme.append(forme)
            forme.setPen(pg.mkPen("g", width=1))
            forme.setBrush(pg.mkBrush(255, 0, 0, 100))
            self.addItem(forme)





