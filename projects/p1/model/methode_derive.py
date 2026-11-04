from typing import override
from projects.p1.model.fonction_math import FonctionMath
from projects.p1.model.methode_numerique import MethodeNumerique
from projects.p1.model.affichage_derive import AffichageDerive

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
        self.__etendue_visible:float = 3
        self.__representation = AffichageDerive.TANGENTE
        
    @property
    def representation(self):
        return self.__representation

    @representation.setter
    def representation(self, valeur):
        self.__representation = valeur

    @property 
    def point_interet(self) -> float:
        return self.__point_interet 
    
    @point_interet.setter
    def point_interet(self, valeur: float):
        self.__point_interet = valeur

    @property
    def etendue_visible(self):
        return self.__etendue_visible

    @etendue_visible.setter
    def etendue_visible(self,valeur):
        self.__etendue_visible = valeur

    def avoir_premiere_valeur(self):
        """Accéder à p-
        """
        return self.__point_interet - self.alpha*self.precision

    def avoir_seconde_valeur(self):
        """Accéder à p+
        """
        return self.__point_interet + (1 - self.alpha )*self.precision

    def avoir_regle_tangente(self):
        pente = self._fonction_math.calculer_exacte_derive(self.point_interet)
        hauteur = self._fonction_math.calculer(self.point_interet)-pente * self.point_interet
        return lambda x : pente*x + hauteur

        
    @override 
    @property
    def approximation(self) -> float:
        """approximation numerique de la derive de la fonction en un point d'interet 

        Returns:
            float: la  approximation
        """
        premiere_valeur = self.avoir_premiere_valeur()
        seconde_valeur = self.avoir_seconde_valeur()
        return ( self.fonction_math.calculer(seconde_valeur) - self.fonction_math.calculer(premiere_valeur) )/ (self.precision)
    