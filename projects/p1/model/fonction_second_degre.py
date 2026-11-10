from projects.p1.model.information import Information
import projects.p1.model.transformation_canonique as TransformationCanonique
from projects.p1.model.parametre import Parametre
from projects.p1.model.fonction_math import FonctionMath
from typing import override

class FonctionSecondDegre(FonctionMath):
    def __init__(self, transformation_canonique: TransformationCanonique):
        __info: Information = Information("Fonction polynomial du second degré", 
                                          "C'est la fonction polynomiale du second degré", "La fonction a 3 paramètres.")
        __formule_general: str = "c_2x^2+c_1x+c_0"
        __info_c_0: Information = Information("c_0", "Le coefficient sans x","")
        __info_c_1: Information =  Information("c_1", "Le coefficient de x^1","")
        __info_c_2: Information =  Information("c_2", "Le coefficient de x^2","")
        __c_0: Parametre = Parametre(__info_c_0, 2, -10, 10, 0)
        __c_1: Parametre = Parametre(__info_c_1, 2, -10, 10, 0)
        __c_2: Parametre = Parametre(__info_c_2, 2, -10, 10, 1)
        __parametres = [__c_0, __c_1, __c_2]

        __fonction: callable = lambda x : self.parametres[2].valeur * x ** 2 + self.parametres[1].valeur * x + self.parametres[0].valeur
        __derive: callable = lambda x : 2 * self.parametres[2].valeur * x + self.parametres[1].valeur
        __primitive: callable = lambda x : self.parametres[2].valeur * x ** 3 / 3 + self.parametres[1].valeur * x ** 2 / 2 + self.parametres[0].valeur * x

        super().__init__(__info, __formule_general, __parametres, transformation_canonique, __fonction, __derive, __primitive)

    @override
    @property
    def vrai_formule(self):
        return f"{self.parametres[2].valeur}x^2 + {self.parametres[1].valeur}x + {self.parametres[0].valeur}"

    @override
    def calculer(self,x: float):
        return super().calculer(x)
    
    @override
    def calculer_exacte_derive(self,x: float) -> float:
        return super().calculer_exacte_derive(x)
    
    @override
    def calculer_exacte_integrale(self, borne_inferieure: float, borne_superieur: float):
        return super().calculer_exacte_integrale(borne_inferieure, borne_superieur)
