from abc import ABC, abstractmethod
import numpy as np
import Information
import TransformationCanonique
import Parametre
import FonctionMath

class FonctionSecondDegre(FonctionMath):

    def __init__(self,transformation_canonique:TransformationCanonique):
        info:Information = 0
        formule_general:str = 0
        parametres = [1,0,0]
        super().__init__(info,formule_general,parametres,transformation_canonique)

    @override
    @property
    def vrai_formule(self):
        return f"{self.parametres[0]}x^2 + {self.parametres[1]}x + {self.parametres[2]}"

    @override
    def calculer(self,x:float):
        return self.parametres[0]*x**2 + self.parametres[1]*x**1 + self.parametres[0]

    @override
    def calculer_np(self,x:np.ndarray):
        return self.calculer(x)

    def calculer_exacte_derive(self,x:float) -> float:
        return 2*self.parametres[0] * x + self.parametres[1]

    def calculer_exacte_integrale(borne_inferieure)

    

    

        
