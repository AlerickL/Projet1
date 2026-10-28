import numpy as np
from FonctionMath import FonctionMath
from Information import Information
from TransformationCanonique import TransformationCanonique
import Parametre 

class FonctionSinAmortie(FonctionMath):
    """Représente une fonction sinus amortie"""
    def __init__(self,transformations_canoniques:TransformationCanonique):

        
        info:Information = Information("Fonction sinus amortie",\
                                    "Fonction trigonométrique périodique définie par l'ordonné du cercle trigonométrique", "ce n'est pas une sinusite")
        formule_generale: str = "e^(-px)*sin(x)"
        if not isinstance(transformations_canoniques,TransformationCanonique):
            raise TypeError("transformations_canoniques doit être de type TransformationCanonique")
        amplitude: Parametre = Parametre(Information("amplitude","Amplitude de la fonction sinus amortie",""),2,-10,10,0)
        super().__init__(info,formule_generale,[amplitude],transformations_canoniques)

    @property
    def vrai_formule(self):
        return (f"e^(-{self.parametres[0].valeur}*x)*sin(x)")

    # Méthode

    def calculer(self,x:float) -> float:
        if not isinstance(x, int|float):
            raise TypeError("x doit être réel")
            fonction = lambda x: np.exp(-1*self.parametres[0].valeur * x) * np.sin(x)
            return self.transformation_canonique.zoom_y*fonction((x-self.transformation_canonique.trans_x)/self.transformation.zoom_x) + self.transformation_canonique.trans_y

    def calculer_exacte_derive(self, x:float) -> float:
        if not isinstance(x, int|float):
            raise TypeError("x doit être réel")
        fonction = lambda x: np.exp(-1*self.parametres[0].valeur * x) * (np.cos(x) - self.parametres[0].valeur * np.sin(x))
        return self.transformation_canonique.zoom_y/self.transformation_canonique.zoom_x*fonction((x-self.transformation_canonique.trans_x)/self.transformation.zoom_x)

    def calculer_exacte_integrale(self, borne_inferieure:float,borne_superieure:float) -> float:
        primitive = lambda x: ((np.exp(-1*self.parametres[0].valeur * x) * (self.parametres[0].valeur*np.sin(x) + np.cos(x)))) / (self.parametres[0].valeur**2 + 1)
        primitive_canonique = lambda x : self._transformations_canoniques.zoom_y*self._transformations_canoniques.zoom_x*primitive((x-self._transformations_canoniques.trans_x)/self._transformations_canoniques.zoom_x) + self._transformations_canoniques  .trans_y*x
        return primitive_canonique(borne_superieure) - primitive_canonique(borne_inferieure)
        
        


