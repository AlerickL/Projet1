import numpy as np
import Information
import TransformationCanonique
import Parametre
import FonctionMath
from typing import override

class FonctionDoubleBosse(FonctionMath):
    def __init__(self,transformation_canonique:TransformationCanonique):
        info = Information("Fonction double bosse","Une fonction avec deux bosse","On peut régler l'écart des deux bosses avec le paramètres p. À |p|<1/3**0.5, les bosses se confondent")
        info_p = Information("p","permet de régler l'écart entre les deux bosses","L'écart au sommet des deux bosses est de 2p ")
        p = Parametre(info_p,"p",2,0,2,1)
        formule_general = "1/(1+(x-p)^2) + 1/(1+(x+p)^2)"
        parametres = [p]
        super().__init__(info,formule_general,parametres,transformation_canonique)

    @override
    @property
    def vrai_formule(self):
        return  f"1/(1+(x-{self._parametres[0]})^2) + 1/(1+(x+{self._parametres[0]})^2)"

    @override
    def calculer(self,x:float):
        fonction:callable = lambda x : 1/(1+(x-self.parametres[0])**2) + 1/(1+(x+self.parametres[0])**2)
        return self._transformations_canoniques.zoom_y*fonction((x-self._transformations_canoniques.trans_x)/self._transformations_canoniques.zoom_x) + self._transformations_canoniques.trans_y

    @override
    def calculer_exacte_derive(self,x:float):
        derive:callable = lambda x : -2*(x-self._parametres[0])/(1+(x-self._parametres[0])**2)**2 + -2*(x+self._parametres[0])/(1+(x+self._parametres[0])**2)**2
        return self._transformations_canoniques.zoom_y/self._transformations_canoniques.zoom_x*derive((x-self._transformations_canoniques.trans_x)/self._transformations_canoniques.zoom_x)

    @override
    def calculer_exacte_integrale(self,borne_inferieure:float,borne_superieur:float):
        primitive:callable = lambda x : np.arctan(x-self._parametres[0]) + np.arctan(x+self._parametres[0])
        primitive_canonique:callable = lambda x : self.transformations_canoniques.zoom_y*self.transformations_canoniques.zoom_x*primitive((x-self.transformations_canoniques.trans_x)/self.transformations_canoniques.zoom_x) + self.transformation.zoom_y*x
        return primitive_canonique(borne_superieur) - primitive_canonique(borne_inferieure)