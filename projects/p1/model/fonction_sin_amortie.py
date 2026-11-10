import numpy as np
from projects.p1.model.fonction_math import FonctionMath
from projects.p1.model.information import Information
from projects.p1.model.transformation_canonique import TransformationCanonique
from projects.p1.model.parametre import Parametre 

class FonctionSinAmortie(FonctionMath):
    """Représente une fonction sinus amortie"""
    def __init__(self, transformations_canoniques: TransformationCanonique):
        __info: Information = Information("Fonction sinus amortie", 
                                       "Fonction combinant l'exponentiel et la sinus", 
                                       "Elle est utilisée en physique, mais n'est toujours pas une sinusite.")
        __formule_generale: str = "e^(-px)*sin(x)"
        __amplitude: Parametre = Parametre(Information("amplitude", "Amplitude de la fonction sinus amortie", ""), 2, -0.5, 0.5, 0)

        __fonction: callable = lambda x: np.exp(-self.parametres[0].valeur * x) * np.sin(x)
        __derive: callable = lambda x: np.exp(-self.parametres[0].valeur * x) * (np.cos(x) - self.parametres[0].valeur * np.sin(x))
        __primitive: callable = lambda x: -((np.exp(-self.parametres[0].valeur * x) 
                                             * (self.parametres[0].valeur * np.sin(x) + np.cos(x)))) / (self.parametres[0].valeur ** 2 + 1)
        
        super().__init__(__info, __formule_generale, [__amplitude], transformations_canoniques, __fonction, __derive, __primitive)

    @property
    def vrai_formule(self):
        return (f"e^(-{self.parametres[0].valeur}*x)*sin(x)")

    def calculer(self, x: float) -> float:
        return super().calculer(x)
        
    def calculer_exacte_derive(self, x: float) -> float:
        return super().calculer_exacte_derive(x)
    
    def calculer_exacte_integrale(self, borne_inferieure: float, borne_superieure: float) -> float:
        return super().calculer_exacte_integrale(borne_inferieure, borne_superieure)
