import numpy as np
from FonctionMath import FonctionMath
from Information import Information
from TransformationCanonique import TransformationCanonique

class FonctionSin(FonctionMath):
    """Représente une fonction sinus"""
    def __init__(self,transformations_canoniques:TransformationCanonique):
        if not isinstance(transformations_canoniques,TransformationCanonique):
                    raise TypeError("transformations_canoniques doit être de type TransformationCanonique")
        info:Information = Information("Fonction sinus",\
                                    "Fonction trigonométrique périodique définie par l'ordonné du cercle trigonométrique", "ce n'est pas une sinusite")
        formule_generale: str = "sin(x)"
        
        super().__init__(info,formule_generale,None,transformations_canoniques)

    @property
    def vrai_formule(self):
        return self.__formule_generale

    # Méthode

    def calculer(self,x:float) -> float:
        if not isinstance(x, int|float):
            raise TypeError("x doit être réel")
        
        return super().calculer(x,np.sin)
    
    def calculer_exacte_derive(self,x:float) -> float:
        if not isinstance(x, int|float):
            raise TypeError("x doit être réel")
        
        return super().calculer_exacte_derive(x,np.cos)                               
    
    def calculer_exacte_integrale(self, borne_inferieur:float,borne_superieur:float) -> float:
        if not isinstance(borne_inferieur, int|float)\
        or not isinstance(borne_superieur, int|float):
            raise TypeError("x doit être réel")
        
        primitive : callable = lambda x : -np.cos(x)
        return super().calculer_exacte_integrale(borne_inferieur,borne_superieur,primitive)



    
    