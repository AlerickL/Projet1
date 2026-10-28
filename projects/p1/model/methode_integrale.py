import numpy as np
import Projet1.projects.p1.model.forme_integrale as forme_integrale
from Projet1.projects.p1.model.fonction_math import FonctionMath
from typing import override 
from Projet1.projects.p1.model.methode_numerique import MethodeNumerique
from numpy.typing import NDArray

class MethodeIntegrale(MethodeNumerique):
    @override
    def __init__(self, fonction: FonctionMath,intervalle:tuple[float,float] ):
        """initialise 
        Args:
            fonction (FonctionMath): fonction
            intervalle (tuple[float, float]): l'intervalle sur lequel on calcule l'intégrale
        """
        super().__init__(fonction)
        self.__intervalle = intervalle
        self.__forme_integrale =  forme_integrale.RECTANGLE
    
    @property 
    def forme_integrale(self) -> forme_integrale:
        return self.__forme_integrale 
    
    @forme_integrale.setter 
    def forme_integrale(self, valeur: forme_integrale):
        self.__forme_integrale = valeur 
        
        
    @property
    def intervalle(self) -> tuple[float, float]:
        return self.__intervalle

    @intervalle.setter
    def intervalle(self, valeur: tuple[float, float]):
        self.__intervalle = valeur
        

    @override 
    @property
    def approximation(self) -> float :
        if self.__forme_integrale == forme_integrale.TRAPEZE:
            return self.__calculer_avec_trapeze()
        elif self.__forme_integrale == forme_integrale.RECTANGLE:
            return self.__calculer_avec_rectangle()

    def __avoir_pas_integration(self) -> float:
        return (self.__intervalle[1] - self.__intervalle[0]) / self.precision

    def __avoir_serie_x_i(self):
        return self.__intervalle[0] + np.arange(self.precision - 1) * self.__avoir_pas_integration()

    def __avoir_points_interets(self):
        return self.__avoir_serie_x_i() + self.alpha * self.__avoir_pas_integration()

    def __calculer_avec_trapeze(self) -> float: 
        pas_intergration = self.__avoir_pas_integration()
        somme = 0 
        x_i = self.__intervalle[0]+np.arange(1, self.precision - 1)*pas_intergration # supposément vectorisé
        liste_somme = self._fonction_math.calculer(x_i) + self._fonction_math.calculer(self.intervalle[1]) 
        somme = np.sum(liste_somme)
        # for i in range(1, self.precision - 1):      # Non vectorisé
            
        #     x_i = self.__intervalle[0] + i * pas_intergration
        #     somme += self._fonction_math.calculer(x_i) + self._fonction_math.calculer(self.intervalle[1]) 
            
        return (somme * 2 + self._fonction_math.calculer(self.intervalle[0])) * pas_intergration / 2
    
    def __calculer_avec_rectangle (self) -> float : 
        pas_intergration =self.__avoir_pas_integration()
        point_evaluation = self.__avoir_points_interets()
        somme = np.sum(self._fonction_math.calculer(point_evaluation))
        # for i in range(self.precision - 1 ):   # non vectorisé
        #     x_i = self.__intervalle[0] + i * pas_intergration
        #     point_evaluation = x_i + self.alpha * pas_intergration
        #     somme += self._fonction_math.calculer(point_evaluation)
        return somme * pas_intergration 

    def avoir_coordonnees_rectangles(self) -> NDArray:
        """Envoi le tableau 2d des points des rectangles. Prende des tranches de l'axe y pour avoir le rectangle (genre [0,:])

        Returns:
            NDArray: Le tableau
        """
        pas = self.__avoir_pas_integration
        premieres_coordonnees = self.__avoir_serie_x_i()
        secondes_coordonnees = premieres_coordonnees + pas
        points_interets = self.__avoir_points_interets()
        autres_coordonnees = self._fonction_math.calculer(points_interets)
        points = np.stack((premieres_coordonnees,secondes_coordonnees,autres_coordonnees,autres_coordonnees),axis=1)
        return points

    def avoir_coordonnees_trapezes(self) -> NDArray:
        """Envoi le tableau 2d des points des trapèzes. Prende des tranches de l'axe y pour avoir le trapèze (genre [0,:])

        Returns:
            NDArray: Le tableau
        """
        pas = self.__avoir_pas_integration
        premiere_coordonnees = self.__avoir_serie_x_i()
        seconde_coordonnees = premiere_coordonnees + pas
        troisieme_coordonnees = self._fonction_math.calculer(seconde_coordonnees)
        quatrieme_coordonnees = self._fonction_math.calculer(premiere_coordonnees)
        points = np.stack((premiere_coordonnees,seconde_coordonnees,troisieme_coordonnees,quatrieme_coordonnees),axis=1)
        return points

    