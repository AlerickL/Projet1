from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np
from projects.p1.model.information import Information
from projects.p1.model.transformation_canonique import TransformationCanonique
from projects.p1.model.parametre import Parametre

class FonctionMath(ABC):
    def __init__(self, info:Information, formule_generale:str,parametres:list[Parametre], transformations_canoniques : TransformationCanonique, fonction: callable, derive: callable, primitive: callable):
        self._info: Information = info
        self._formule_generale: str = formule_generale
        self._parametres: list[Parametre] = parametres
        self._transformations_canoniques: TransformationCanonique = transformations_canoniques
        
        self._fonction = fonction
        self._derive = derive
        self._primitive = primitive
        

    @property
    def info(self) ->Information:
        """L'information de la fonction

        Returns:
            Information: L'information
        """
        return self._info
    
    @property
    def formule_generale(self) -> str:
        """Formule générale de la fonction

        Returns:
            str: Représentation en chaine de caractère de la fonction.
        """
        return self._formule_generale
        
    
    @property
    @abstractmethod
    def vrai_formule(self) -> str:
        """Vrai formule de la fonction
        Remplace les variables par les vrais valeurs

        Returns:
            str: La chaine de caractère représentant la vrai fonction
        """
        pass


    @property
    def parametres(self) -> list[Parametre]:
        """Donne la liste des paramètres de la fonction

        Returns:
            list[Parametre]: La liste de paramètres de la fonction
        """
        return self._parametres
    
    @property
    def transformations_canoniques(self) -> TransformationCanonique:
        """Donne la transformation canonique de la fonction

        Returns:
            TransformationCanonique: La transformation canonique de la fonction
        """
        return self._transformations_canoniques

    def calculer(self,x:float) -> float:
        """Calculer en un point le y de la fonction

        Args:
            x (float): le point en x du calcul
            fonction (callable): un fonction qui est utilisé pour le calcul

        Returns:
            float: la valeur en y
        """
        return self._transformations_canoniques.zoom_y.valeur*self._fonction((x-self._transformations_canoniques.trans_x.valeur)/self._transformations_canoniques.zoom_x.valeur) + self._transformations_canoniques.trans_y.valeur
        
    def calculer_np(self,borne_inf:float, borne_sup:float ,nombre_div:int) -> np.ndarray:
        """Calculer avec la fonction les valeurs en y pour une collection de points en x

        Args:
            x (np.ndarray): La collection de valeurs en x
            borne_inf (float): la première valeur du vecteur 
            borne_sup (float): la dernière valeur du vecteur
            nombre_div (float): le nombre de valeur du vecteur

        Returns:
            np.ndarray: les résultats en y 
        """
        x = np.linspace(borne_inf,borne_sup,nombre_div)
        return x, self.calculer(x)

    @abstractmethod
    def calculer_exacte_derive(self,x:float) -> float:
        """Calculer la dérivé exacte de la fonction (analytiquement) en un point x

        Args:
            x (float): le point d'intérêt du calcul de dérivé
            derive (callable): la fonction que l'on obtient quand on dérive. Ex: cos est la dérivé de sin

        Returns:
            float: la dérivé au point x de la fonction
        """
        return self._transformations_canoniques.zoom_y.valeur/self._transformations_canoniques.zoom_x.valeur*self._derive((x-self._transformations_canoniques.trans_x.valeur)/self._transformations_canoniques.zoom_x.valeur)



    @abstractmethod
    def calculer_exacte_integrale(self,borne_inferieur:float,borne_superieur:float) -> float:
        """Calculer l'intégrale exacte de la fonction (analytiquement) dans un interval.
        L'interval est entre borne_inferieur et borne_superieur.

        Args:
            borne_inferieur (float): La borne inférieur de l'interval
            borne_superieur (float): La borne supérieur de l'interval
            primitive (callable): la fonction primitive de celle qu'on évalue. Ex: sin est la primitive de cos

        Returns:
            float: La valeur de l'intégrale dans l'interval
        """
        primitive_canonique:callable = lambda x : self._transformations_canoniques.zoom_y.valeur*self._transformations_canoniques.zoom_x.valeur*self._primitive((x-self._transformations_canoniques.trans_x.valeur)/
                                                                                                                                                                self._transformations_canoniques.zoom_x.valeur) + self._transformations_canoniques.trans_y.valeur*x
        print("primitive inf ", primitive_canonique(borne_inferieur))
        print("primitive inf ", primitive_canonique(borne_superieur))
        return primitive_canonique(borne_superieur) - primitive_canonique(borne_inferieur)

    def redemarrer_parametres(self) -> None:
        """Redémarre les paramètres de la fonction
        """
        for parametre in self.parametres:
            parametre.reinitialiser()
        