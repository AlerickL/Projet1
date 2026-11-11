from typing import override
from projects.p1.model.fonction_math import FonctionMath
from projects.p1.model.methode_numerique import MethodeNumerique
from projects.p1.model.affichage_derive import AffichageDerive
from projects.p1.model.information import Information

class MethodeDerive(MethodeNumerique):
    """Permet de gérer les dérivés"""
    def __init__(self, fonction: FonctionMath):
        """initialise 
        Args:
            fonction (FonctionMath): fonction
            point_interet (float): le point ou on fait le calcul de derive 
        """
        __info = Information("Méthode numérique de dérivation",
                             "La méthode numérique de dérivation permet d'estimer la pente de la fonction à un certain point",
                             "Il est possible de changer le pas, et le positionement de la sécante.")
        
        super().__init__(fonction, __info)
        self.__point_interet = 0 
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
    def etendue_visible(self, valeur):
        self.__etendue_visible = valeur

    def avoir_premiere_valeur(self) -> float:
        """Accéder à p-
        """
        return self.__point_interet - self.alpha * self.precision

    def avoir_seconde_valeur(self) -> float:
        """Accéder à p+
        """
        return self.__point_interet + (1 - self.alpha) * self.precision

    def avoir_regle_tangente(self) -> callable:
        pente: float = self._fonction_math.calculer_exacte_derive(self.point_interet)
        hauteur: float = self._fonction_math.calculer(self.point_interet) - pente * self.point_interet
        return lambda x : pente * x + hauteur

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

    @override
    @property
    def valeur_exacte(self) -> float:
        return self.fonction_math.calculer_exacte_derive(self.point_interet)

    @override
    def reinitialiser(self):
        super().reinitialiser()
        self.__point_interet = 0
        self.__etendue_visible:float = 3
        self.__representation = AffichageDerive.TANGENTE
    