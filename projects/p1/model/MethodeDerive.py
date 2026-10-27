from abc import ABC, abstractmethod
from typing import override
import numpy as np
import Information 
import TransformationCanonique
import Parametre  
import FonctionMath
import MethodeNumerique

class MethodeDerive(MethodeNumerique):
    @override
    def __init__(self, fonction: FonctionMath, point_interet:float):
        """initialise 
        Args:
            fonction (FonctionMath): fonction
            point_interet (float): le point ou on fait le calcul de derive 
        """
        super().__init__(fonction)
        self.__point_interet = point_interet 
        
    @property 
    def point_interet(self) -> float:
        return self.__point_interet 
    
    
    
    @point_interet.setter
    def point_interet(self, valeur: float):
        self.__point_interet = valeur
        
    @override 
    @property
    def approximation(self) -> float:
        """approximation numerique de la derive de la fonction en un point d'interet 

        Returns:
            float: la  approximation
        """
        premiere_valeur = self.__point_interet - self.alpha*self.precision
        seconde_valeur = self.__point_interet + (1 - self.alpha )*self.precision
        return ( self.fonction.calculer(seconde_valeur) - self.fonction.calculer(premiere_valeur) )/ (self.precision)
    
    
