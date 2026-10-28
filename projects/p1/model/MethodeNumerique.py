from abc import ABC, abstractmethod
import numpy as np
import Information
import TransformationCanonique
import Parametre
import FonctionMath

class MethodeNumerique(ABC):

    def __init__(self,fonction_math:FonctionMath):
        self._fonction_math:FonctionMath = fonction_math
        self._alpha:float = 0.0
        self.__precision:int|float = 5.0

    @property
    def fonction_math(self) -> FonctionMath:
        """Retourne la fonction mathématique utilisée

        Returns:
            FonctionMath: La fonction mathématique
        """
        return self._fonction_math

    @FonctionMath.setter
    def fonction_math(self, fonction:FonctionMath) -> None:
        self.fonction_math = fonction

    @property
    def alpha(self) -> float:
        """Donne la valeure de alpha

        Returns:
            float: la valeur de alpha
        """
        return self._alpha

    @alpha.setter
    def alpha(self, valeur:float) -> None:
        """Permet de modifier alpha

        Args:
            valeur (float): La nouvelle valeur de alpha

        Raises:
            TypeError: alpha doit être un float
            ValueError: alpha doit être compris entre 0 et 1 inclus
        """
        if not isinstance(valeur,float):
            raise TypeError("alpha doit être un float")
        if valeur<0 or valeur>1:
            raise ValueError("alpha doit être compris entre 0 et 1 inclus")
        self._alpha = valeur

    @abstractmethod
    @property
    def approximation(self) -> float:
        """Approximation numérique

        Returns:
            float: _description_
        """
        pass

    @property
    def precision(self) -> int|float:
        """Donne la précision de la méthode numérique ; dépend de la méthode précisément.
        Pour la dérivé, c'est le pas de comparaison (h)
        Pour l'intégral, c'est le nombre de division 

        Returns:
            int|float: La précision
        """
        return self.__precision

    @precision.setter
    def precision(self,valeur:int|float) -> None :
        if self.precision<0:
            raise ValueError("Precision doit être positif")
        self.__precision = valeur



