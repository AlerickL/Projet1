from abc import ABC, abstractmethod
from projects.p1.model.fonction_math import FonctionMath
from projects.p1.model.fonction_math import Information

class MethodeNumerique(ABC):

    def __init__(self,fonction_math:FonctionMath,info:Information):
        self._fonction_math:FonctionMath = fonction_math
        self._alpha:float = 0.5
        self.__precision:int|float = 5.0
        self.__info = info

    @property
    def info(self):
        return self.__info

    @property
    def fonction_math(self) -> FonctionMath:
        """Retourne la fonction mathématique utilisée

        Returns:
            FonctionMath: La fonction mathématique
        """
        return self._fonction_math

    @fonction_math.setter
    def fonction_math(self, fonction: FonctionMath) -> None:
        self._fonction_math = fonction

    @property
    def alpha(self) -> float:
        """Donne la valeure de alpha

        Returns:
            float: la valeur de alpha
        """
        return self._alpha

    @alpha.setter
    def alpha(self, valeur: float) -> None:
        """Permet de modifier alpha

        Args:
            valeur (float): La nouvelle valeur de alpha

        """
        self._alpha = valeur

    @property
    @abstractmethod
    def approximation(self) -> float:
        """Approximation numérique

        Returns:
            float: _description_
        """
        pass

    @property
    @abstractmethod
    def valeur_exacte(self) -> float:
        pass

    @property
    def precision(self) -> float:
        """Donne la précision de la méthode numérique ; dépend de la méthode précisément.
        Pour la dérivé, c'est le pas de comparaison (h)
        Pour l'intégral, c'est le nombre de division 

        Returns:
            float: La précision
        """
        return self.__precision

    @precision.setter
    def precision(self, valeur: float) -> None :
        self.__precision = valeur

    def ecart_absolu(self) -> float:
        return abs(self.approximation - self.valeur_exacte)

    def ecart_relatif(self) -> float:
        try:
            return abs(self.ecart_absolu() / self.valeur_exacte * 100)
        except ZeroDivisionError:
            return 0

    def reinitialiser(self):
        self._alpha:float = 0.5
        self.__precision:int|float = 5.0
        