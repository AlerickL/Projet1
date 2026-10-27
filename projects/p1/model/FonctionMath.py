from abc import ABC, abstractmethod
import numpy as np
import Information
import TransformationCanonique
import Parametre

class FonctionMath(ABC):
    def __init__(self):
        pass

    @property
    def info(self) -> Information:
        """L'information de la fonction

        Returns:
            Information: L'information
        """
        pass
    @property
    def formule_general(self) -> str:
        """Formule générale de la fonction

        Returns:
            str: Représentation en chaine de caractère de la fonction.
        """
        pass
    @abstractmethod
    @property
    def vrai_formule(self) -> str:
        """Vrai formule de la fonction
        Remplace les variables par les vrais valeurs

        Returns:
            str: La chaine de caractère représentant la vrai fonction
        """
        pass

    @property
    def transformation_canonique(self) -> TransformationCanonique:
        """Donne la transformation canonique

        Returns:
            TransformationCanonique: La transformation canonique de la fonction
        """
        pass

    @property
    def parametres(self) -> list[Parametre]:
        """Donne la liste des paramètres de la fonction

        Returns:
            list[Parametre]: La liste de paramètres de la fonction
        """
        pass

    @abstractmethod
    def calculer(x:float) -> float:
        """Calculer en un point le y de la fonction

        Args:
            x (float): le point en x du calcul

        Returns:
            float: la valeur en y
        """
        pass

    @abstractmethod
    def calculer_np(x:np.ndarray) -> np.ndarray:
        """Calculer avec la fonction les valeurs en y pour une collection de points en x

        Args:
            x (np.ndarray): La collection de valeurs en x

        Returns:
            np.ndarray: les résultats en y 
        """
        pass

    @abstractmethod
    def calculer_exacte_derive(x:float) -> float:
        """Calculer la dérivé exacte de la fonction (analytiquement) en un point x

        Args:
            x (float): le point d'intérêt du calcul de dérivé

        Returns:
            float: la dérivé au point x de la fonction
        """
        pass

    @abstractmethod
    def calculer_exacte_derive(borne_inferieur:float,borne_superieur:float) -> float:
        """Calculer l'intégrale exacte de la fonction (analytiquement) dans un interval.
        L'interval est entre borne_inferieur et borne_superieur.

        Args:
            borne_inferieur (float): La borne inférieur de l'interval
            borne_superieur (float): La borne supérieur de l'interval

        Returns:
            float: La valeur de l'intégrale dans l'interval
        """
        pass

    def redemarrer_parametres(self) -> None:
        """Redémarre les paramètres de la fonction
        """
        for parametre in self.parametres:
            parametre.reinitialiser()
        
    


    
    