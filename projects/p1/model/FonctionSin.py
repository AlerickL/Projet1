import numpy as np
from FonctionMath import FonctionMath
from Information import Information
from TransformationCanonique import TransformationCanonique

class FonctionSin(FonctionMath):
    """Représente une fonction sinus"""
    def __init__(self,transformations_canoniques:TransformationCanonique):

        
        info:Information = Information("Fonction sinus",\
                                    "Fonction trigonométrique périodique définie par l'ordonné du cercle trigonométrique", "ce n'est pas une sinusite")
        formule_generale: str = "sin(x)"
        if not isinstance(transformations_canoniques,TransformationCanonique):
            raise TypeError("transformations_canoniques doit être de type TransformationCanonique")
        super().__init__(info,formule_generale,None,transformations_canoniques)

    @property
    def vrai_formule(self):
        return self.__formule_generale

    # Méthode

    def calculer(self,x:float) -> float:
        if not isinstance(x, int|float):
            raise TypeError("x doit être réel")
        return self._transformations_canoniques.zoom_y*(np.sin((1/self._transformations_canoniques.zoom_x)*(x-self._transformations_canoniques.trans_x))) + self._transformations_canonique.trans_y

    def calculer_exacte_derive(self,x:float) -> float:
        if not isinstance(x, int|float):
                    raise TypeError("x doit être réel")
        return self._transformations_canoniques.zoom_y*(np.cos((1/self._transformations_canoniques.zoom_x)*\
                                                               (x-self._transformations_canoniques.trans_x)))*(1/self._transformations_canoniques.zoom_x)

    def calculer_exacte_integrale(self, borne_inferieur:float,borne_superieur:float) -> float:
        primitive : callable = lambda x : np.cos(x)
        primitive_canonique : callable = lambda x :self._transformations_canoniques.zoom_y*self._transformations_canoniques.zoom_x*primitive((x-self._transformations_canoniques.trans_x)/self._transformations_canoniques.zoom_x) + self._transformations_canoniques.zoom_y*x
        return primitive_canonique(borne_superieur) - primitive_canonique(borne_inferieur)



    
    