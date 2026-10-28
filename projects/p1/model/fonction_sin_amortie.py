import numpy as np
from Projet1.projects.p1.model.fonction_math import FonctionMath
from information import Information
from Projet1.projects.p1.model.transformation_canonique import TransformationCanonique
from parametre import Parametre 

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
            return super().calculer(x,fonction)
        
    def calculer_exacte_derive(self, x:float) -> float:
        if not isinstance(x, int|float):
            raise TypeError("x doit être réel")
        fonction = lambda x: np.exp(-1*self.parametres[0].valeur * x) * (np.cos(x) - self.parametres[0].valeur * np.sin(x))
        return super().calculer_exacte_derive(x,derive)
    
    def calculer_exacte_integrale(self, borne_inferieure:float,borne_superieure:float) -> float:
        primitive = lambda x: ((np.exp(-1*self.parametres[0].valeur * x) * (self.parametres[0].valeur*np.sin(x) + np.cos(x)))) / (self.parametres[0].valeur**2 + 1)
        return super().calculer_exacte_integrale(borne_inferieure,borne_superieure,primitive)

