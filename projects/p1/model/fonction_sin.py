import numpy as np
from typing import override
from projects.p1.model.fonction_math import FonctionMath
from projects.p1.model.information import Information
from projects.p1.model.transformation_canonique import TransformationCanonique

class FonctionSin(FonctionMath):
    """Représente une fonction sinus"""
    def __init__(self, transformations_canoniques: TransformationCanonique):
        __info:Information = Information("Fonction sinus",
                                    "Fonction trigonométrique périodique définie par l'ordonné du cercle trigonométrique", 
                                    "ce n'est pas une sinusite")
        __formule_generale: str = "sin(x)"

        __fonction: callable = lambda x : np.sin(x)
        __derive: callable = lambda x : np.cos(x)
        __primitive: callable = lambda x : -np.cos(x)
        
        super().__init__(__info, __formule_generale, [], transformations_canoniques, __fonction, __derive, __primitive)

    @override
    @property
    def vrai_formule(self):
        return "sin(x)"


    @override
    def calculer(self, x: float) -> float:
        return super().calculer(x)
    
    @override
    def calculer_exacte_derive(self, x: float) -> float:
        return super().calculer_exacte_derive(x)                               

    @override
    def calculer_exacte_integrale(self, borne_inferieur: float, borne_superieur: float) -> float:
        return super().calculer_exacte_integrale(borne_inferieur, borne_superieur)
