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
        info_c_0 = Information("c_0","Le coefficient sans x","")
        info_c_1 =  Information("c_0","Le coefficient de x^1","")
        info_c_2 =  Information("c_0","Le coefficient de x^2","")
        c_0 = Parametre(info_c_0,"c_0",2,-10,10,0)
        c_1 = Parametre(info_c_1,"c_1",2,-10,10,0)
        c_2 = Parametre(info_c_2,"c_2",2,-10,10,1)
        parametres = [c_0,c_1,c_2]
        super().__init__(info,formule_general,parametres,transformation_canonique)

    @override
    @property
    def vrai_formule(self):
        return f"{self.parametres.valeur[2]}x^2 + {self.parametres.valeur[1]}x + {self.parametres.valeur[0]}"
    
    @property
    def info(self) -> Information :
        super().info
        
    @property
    def formule_generale(self) -> str:
        super().formule_generale 
        
    @property
    def parametres(self) -> list[Parametre]:
        super().parametres

    @override
    def calculer(self,x:float):
        fonction = lambda x : self.parametres.valeur[2]*x**2 + self.parametres.valeur[1]*x**1 + self.parametres.valeur[0]
        return self.transformations_canoniques.zoom_y*fonction((x-self.transformations_canoniques.trans_x)/self.transformations_canoniques.zoom_x) + self.transformations_canoniques.trans_y
    
    @override
    def calculer_exacte_derive(self,x:float) -> float:
        derive = lambda x : 2*self.parametres[2] * x + self.parametres[1]
        return self.transformations_canoniques.zoom_y/self.transformations_canoniques.zoom_x*derive((x-self.transformations_canoniques.trans_x)/self.transformations_canoniques.zoom_x)
    
    @override
    def calculer_exacte_integrale(self,borne_inferieure:float,borne_superieure:float):
        primitive = lambda x : self.parametres[0]*x**3/3 + self.parametres[1]*x**2/2 + self.parametres[0]*x
        primitive_canonique = lambda x : self._transformations_canoniques.zoom_y*self._transformations_canoniques.zoom_x*primitive((x-super().transformations_canoniques.trans_x)/super().transformations_canoniques.zoom_x) + super().transformations_canoniques.trans_y*x
        return primitive_canonique(borne_superieure) - primitive_canonique(borne_inferieure)

    

    

    

        
