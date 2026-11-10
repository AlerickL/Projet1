import numpy as np
from projects.p1.model.information import Information
import projects.p1.model.transformation_canonique as transformation_canonique
from projects.p1.model.parametre import Parametre
from projects.p1.model.fonction_math import FonctionMath
from typing import override

class FonctionDoubleBosse(FonctionMath):
    def __init__(self, transformation_canonique: transformation_canonique):
        __info: Information = Information("Fonction double bosse", 
                                          "Une fonction avec deux bosse", 
                                          "On peut régler l'écart des deux bosses avec le paramètres p. À |p|<1/3**0.5, les bosses se confondent")
        __info_p: Information = Information("p", "permet de régler l'écart entre les deux bosses", "L'écart au sommet des deux bosses est de 2p ")
        __p: Parametre = Parametre(__info_p, 2, 0, 2, 1)
        __formule_general: str = "1/(1+(x-p)^2) + 1/(1+(x+p)^2)"
        __parametres: list[Parametre] = [__p]

        __fonction: callable = lambda x : 1 / (1 + (x-self.parametres[0].valeur) ** 2) + 1 / (1 + (x+self.parametres[0].valeur) ** 2)
        __derive: callable = lambda x : (-2 * (x-self._parametres[0].valeur) / (1 + (x-self._parametres[0].valeur) ** 2) ** 2 
            + -2 * (x+self._parametres[0].valeur) / (1 + (x+self._parametres[0].valeur) ** 2) ** 2)
        __primitive: callable = lambda x : np.arctan(x - self._parametres[0].valeur) + np.arctan(x + self._parametres[0].valeur)
        
        super().__init__(__info, __formule_general, __parametres, transformation_canonique, __fonction, __derive, __primitive)

    @override
    @property
    def vrai_formule(self) -> str:
        return  f"1/(1+(x-{self._parametres[0].valeur})^2) + 1/(1+(x+{self._parametres[0].valeur})^2)"

    @override
    def calculer(self, x: float) -> float:
        return super().calculer(x)

    @override
    def calculer_exacte_derive(self, x: float) -> float:
        return super().calculer_exacte_derive(x)
    
    @override
    def calculer_exacte_integrale(self, borne_inferieure: float, borne_superieur: float) -> float:
        return super().calculer_exacte_integrale(borne_inferieure,borne_superieur)
