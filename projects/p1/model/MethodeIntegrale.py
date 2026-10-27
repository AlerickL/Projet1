from abc import ABC, abstractmethod
import numpy as np
import Information
import TransformationCanonique
import Parametre  
import FormeIntegrale
import FonctionMath
from annotation import override 

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
        self.__forme_integrale =  FormeIntegrale.RECTANGLE
    @property 
    def forme_integrale(self) -> FormeIntegrale:
        return self.__forme_integrale 
    @forme_integrale.setter 
    def forme_integrale(self, valeur: FormeIntegrale):
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
        if self.__forme_integrale == FormeIntegrale.TRAPEZE:
            return self.__calculer_avec_trapeze()
        elif self.__forme_integrale == FormeIntegrale.RECTANGLE:
            return self.__calculer_avec_rectangle()

    def __calculer_avec_trapeze(self) -> float: 
        pas_intergration = (self.__intervalle[1] - self.__intervalle[0]) / self.precision
        somme = 0 
        for i in range(1, self.precision - 1):
            
            x_i = self.__intervalle[0] + i * pas_intergration
            somme += self.fonction.calculer(x_i) + self.fonction.calculer(self.intervalle[1]) 
            
        return (somme * 2 + self.fonction.calculer(self.intervalle[0])) * pas_intergration / 2
    
    def __calculer_avec_rectangle (self) -> float : 
        
        pas_intergration = (self.__intervalle[1] - self.__intervalle[0]) / self.precision
        somme = 0 
        for i in range(self.precision - 1 ):
            x_i = self.__intervalle[0] + i * pas_intergration
            point_evaluation = x_i + self.alpha * pas_intergration
            somme += self.fonction.calculer(point_evaluation)
        return somme * pas_intergration 