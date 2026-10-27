from abc import ABC, abstractmethod
import numpy as np
import Information
import TransformationCanonique
import Parametre
import FonctionMath
from typing import override

class FonctionSecondDegre(FonctionMath):

    def __init__(self,transformation_canonique:TransformationCanonique):
        info:Information = Information("Fonction polynomial du second degré","C'est la fonction polynomiale du second degré","La fonction a 3 paramètres.")
        formule_general:str = "c_2x^2+c_1x+c_0"
        info_c_0 = "Le coefficient sans x"
        info_c_1 = "Le coefficient de x^1"
        info_c_2 = "Le coefficient de x^2"
        c_0 = Parametre(info_c_0,"c_0",1,-10,10,0)
        c_1 = Parametre(info_c_1,"c_1",1,-10,10,0)
        c_2 = Parametre(info_c_2,"c_2",1,-10,10,1)
        parametres = [c_0,c_1,c_2]
        super().__init__(info,formule_general,parametres,transformation_canonique)

    @override
    @property
    def vrai_formule(self):
        return f"{self.parametres.valeur[2]}x^2 + {self.parametres.valeur[1]}x + {self.parametres.valeur[0]}"

    @override
    def calculer(self,x:float):
        fonction = lambda x : self.parametres.valeur[2]*x**2 + self.parametres.valeur[1]*x**1 + self.parametres.valeur[0]
        return self.transformation_canonique.zoom_y*fonction((x-self.transformation_canonique.trans_x)/self.transformation.zoom_x) + self.transformation_canonique.trans_y
    
    @override
    def calculer_exacte_derive(self,x:float) -> float:
        derive = lambda x : 2*self.parametres[2] * x + self.parametres[1]
        return self.transformation_canonique.zoom_y/self.transformation_canonique.zoom_x*derive((x-self.transformation_canonique.trans_x)/self.transformation.zoom_x)
    
    @override
    def calculer_exacte_integrale(self,borne_inferieure:float,borne_superieur:float):
        primitive = lambda x : self.parametres[0]*x**3/3 + self.parametres[1]*x**2/2 + self.parametres[0]*x
        primitive_canonique = lambda x : self.transformation_canonique.zoom_y*self.transformation_canonique.zoom_x*primitive((x-self.transformation_canonique.trans_x)/self.transformation.zoom_x) + self.transformation.zoom_y*x
        return primitive_canonique(borne_superieur) - primitive_canonique(borne_inferieure)

    

    

    

        
