import numpy as np
from projects.p1.model.information import Information
import projects.p1.model.transformation_canonique as transformation_canonique
from projects.p1.model.parametre import Parametre
from projects.p1.model.fonction_math import FonctionMath
from typing import override

class FonctionDoubleBosse(FonctionMath):
    def __init__(self,transformation_canonique:transformation_canonique):
        info = Information("Fonction double bosse","Une fonction avec deux bosse","On peut régler l'écart des deux bosses avec le paramètres p. À |p|<1/3**0.5, les bosses se confondent")
        info_p = Information("p","permet de régler l'écart entre les deux bosses","L'écart au sommet des deux bosses est de 2p ")
        p = Parametre(info_p,2,0,2,1)
        formule_general = "1/(1+(x-p)^2) + 1/(1+(x+p)^2)"
        parametres = [p]

        __fonction: callable = lambda x : 1/(1+(x-self.parametres[0].valeur)**2) + 1/(1+(x+self.parametres[0].valeur)**2)
        __derive: callable = lambda x : -2*(x-self._parametres[0])/(1+(x-self._parametres[0])**2)**2 + -2*(x+self._parametres[0])/(1+(x+self._parametres[0])**2)**2
        __primitive: callable = lambda x : np.arctan(x-self._parametres[0]) + np.arctan(x+self._parametres[0])
        
        super().__init__(info,formule_general,parametres,transformation_canonique, __fonction, __derive, __primitive)

    @override
    @property
    def vrai_formule(self):
        return  f"1/(1+(x-{self._parametres[0].valeur})^2) + 1/(1+(x+{self._parametres[0].valeur})^2)"

    @override
    def calculer(self,x:float):
        return super().calculer(x)

    @override
    def calculer_exacte_derive(self,x:float):
        return super().calculer_exacte_derive(x)
    
    @override
    def calculer_exacte_integrale(self,borne_inferieure:float,borne_superieur:float):
        return super().calculer_exacte_integrale(borne_inferieure,borne_superieur)