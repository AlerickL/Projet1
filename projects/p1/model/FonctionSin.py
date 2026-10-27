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
        return np.sin(x)

    def calculer_exacte_derive(x:float) -> float:
        if not isinstance(x, int|float):
                    raise TypeError("x doit être réel")
        return np.cos(x)

    def calculer_exacte_integrale(borne_inferieur:float,borne_superieur:float) -> float:
         return -1*np.cos(borne_superieur) + np.cos(borne_inferieur)
    



    
    