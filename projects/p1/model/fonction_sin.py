import numpy as np
from typing import override
from projects.p1.model.fonction_math import FonctionMath
from projects.p1.model.information import Information
from projects.p1.model.transformation_canonique import TransformationCanonique

class FonctionSin(FonctionMath):
    """Représente une fonction sinus"""
    def __init__(self,transformations_canoniques:TransformationCanonique):
        if not isinstance(transformations_canoniques,TransformationCanonique):
                    raise TypeError("transformations_canoniques doit être de type TransformationCanonique")
        info:Information = Information("Fonction sinus",\
                                    "Fonction trigonométrique périodique définie par l'ordonné du cercle trigonométrique", "ce n'est pas une sinusite")
        formule_generale: str = "sin(x)"
        
        super().__init__(info,formule_generale,[],transformations_canoniques)

    @override
    @property
    def vrai_formule(self):
        return "sin(x)"

    # Méthode

    @override
    def calculer(self,x:float) -> float:
        return super().calculer(x,np.sin)
    
    @override
    def calculer_exacte_derive(self,x:float) -> float:
        derive = lambda x : np.cos(x)
        return super().calculer_exacte_derive(x, derive)                               

    @override
    def calculer_exacte_integrale(self, borne_inferieur:float,borne_superieur:float) -> float:
        
        primitive : callable = lambda x : -np.cos(x)
        return super().calculer_exacte_integrale(borne_inferieur,borne_superieur,primitive)



    
    