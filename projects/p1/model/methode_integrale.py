import numpy as np
from projects.p1.model.forme_integrale import FormeIntegrale
from projects.p1.model.fonction_math import FonctionMath
from typing import override 
from projects.p1.model.methode_numerique import MethodeNumerique
from numpy.typing import NDArray
from projects.p1.model.information import Information
class MethodeIntegrale(MethodeNumerique):
    @override
    def __init__(self, fonction: FonctionMath):
        """initialise 
        Args:
            fonction (FonctionMath): fonction
            intervalle (tuple[float, float]): l'intervalle sur lequel on calcule l'intégrale
        """
        __info = Information("Méthode numérique d'intégration", 
                           "La méthode numérique d'intégration permet d'estimer l'aire de la fonction par des rectangles ou des trapèzes",
                           "Il est possible de changer l'intervalle, le nombre de forme ou le centre des rectangles. L'approximation des trapèzes est meilleure.")
        super().__init__(fonction, __info)
        self.__intervalle = (0,1)
        self.__forme_integrale =  FormeIntegrale.RECTANGLE
        self.__nombre_total_forme:int = 100

    @property
    def nombre_total_forme(self) -> int:
        return self.__nombre_total_forme
    
    @property 
    def forme_integrale(self) -> FormeIntegrale:
        return self.__forme_integrale 
    
    @forme_integrale.setter 
    def forme_integrale(self, valeur: FormeIntegrale):
        self.__forme_integrale = valeur 
        
        
    @property
    def intervalle(self) -> tuple[float, float]:
        return self.__intervalle

    @intervalle.setter
    def intervalle(self, valeur: tuple[float, float]):
        self.__intervalle = valeur
        

    @override 
    @property
    def approximation(self) -> float :
        if self.__forme_integrale == FormeIntegrale.TRAPEZE:
            return self.__calculer_avec_trapeze()
        elif self.__forme_integrale == FormeIntegrale.RECTANGLE:
            return self.__calculer_avec_rectangle()

    @override
    @property
    def valeur_exacte(self) -> float:
        return self.fonction_math.calculer_exacte_integrale(self.intervalle[0], self.intervalle[1])

    def __avoir_pas_integration(self) -> float:
        return (self.__intervalle[1] - self.__intervalle[0]) / self.precision

    def __avoir_serie_x_i(self):
        return np.linspace(self.intervalle[0], self.intervalle[1], int(self.precision) + 1)

    def __avoir_points_interets(self):
        return self.__avoir_serie_x_i() + self.alpha * self.__avoir_pas_integration()

    def __calculer_avec_trapeze(self) -> float: 
        __pas_intergration = self.__avoir_pas_integration()
        __precision: int = int(self.precision)
        __x_i = self.__intervalle[0] + np.arange(0, self.precision + 1, dtype=float) * __pas_intergration 
        __f_i = self._fonction_math.calculer(__x_i)
        somme = np.sum(__f_i[1:__precision])
            
        return (somme * 2 + __f_i[0] + __f_i[__precision]) * __pas_intergration / 2
    
    def __calculer_avec_rectangle (self) -> float : 
        __pas_intergration: float = self.__avoir_pas_integration()
        __point_evaluation = self.__avoir_points_interets()
        __somme: float = np.sum(self._fonction_math.calculer(__point_evaluation))
        return __somme * __pas_intergration 

    def avoir_coordonnees_rectangles(self) -> NDArray:
        """Envoi le tableau 2d des points des rectangles. Prende des tranches de l'axe y pour avoir le rectangle (genre [0,:])

        Returns:
            NDArray: Le tableau
        """
        __pas = self.__avoir_pas_integration()
        __axe_x_de_gauche = self.__avoir_serie_x_i()
        __axe_x_de_droite = __axe_x_de_gauche + __pas
        __points_interets = self.__avoir_points_interets()
        __axe_y_haut = self._fonction_math.calculer(__points_interets)
        __axe_y_bas = np.zeros(__axe_x_de_gauche.shape)
        __points = np.stack(( __axe_x_de_droite, __axe_x_de_droite, __axe_x_de_gauche, __axe_x_de_gauche, __axe_y_haut, __axe_y_bas, __axe_y_bas, __axe_y_haut), axis=1)
        return __points

    def avoir_coordonnees_trapezes(self) -> NDArray:
        """Envoi le tableau 2d des points des trapèzes. Prend des tranches de l'axe y pour avoir le trapèze (genre [0,:])

        Returns:
            NDArray: Le tableau
        """
        __pas = self.__avoir_pas_integration()
        __x_gauche = self.__avoir_serie_x_i()
        __x_droite = __x_gauche + __pas
        __y_droite = self._fonction_math.calculer(__x_droite)
        __y_gauche = self._fonction_math.calculer(__x_gauche)
        __y_bas =  np.zeros(__x_gauche.shape)
        __points = np.stack((__x_droite, __x_droite, __x_gauche, __x_gauche, __y_droite, __y_bas, __y_bas, __y_gauche), axis=1)
        return __points

    @override
    def reinitialiser(self):
        super().reinitialiser()
        self.__intervalle = (0,1)
        self.__forme_integrale =  FormeIntegrale.RECTANGLE
