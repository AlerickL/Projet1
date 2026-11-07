import numpy as np
from projects.p1.model.forme_integrale import FormeIntegrale
from projects.p1.model.fonction_math import FonctionMath
from typing import override 
from projects.p1.model.methode_numerique import MethodeNumerique
from numpy.typing import NDArray

class MethodeIntegrale(MethodeNumerique):
    @override
    def __init__(self, fonction: FonctionMath,intervalle:tuple[float,float] ):
        """initialise 
        Args:
            fonction (FonctionMath): fonction
            intervalle (tuple[float, float]): l'intervalle sur lequel on calcule l'intégrale
        """
        super().__init__(fonction)
        self.__intervalle = intervalle
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

    def __avoir_pas_integration(self) -> float:
        return (self.__intervalle[1] - self.__intervalle[0]) / self.precision

    def __avoir_serie_x_i(self):
        return np.linspace(self.intervalle[0],self.intervalle[1],int(self.precision)+1)

    def __avoir_points_interets(self):
        return self.__avoir_serie_x_i() + self.alpha * self.__avoir_pas_integration()

    def __calculer_avec_trapeze(self) -> float: 
        pas_intergration = self.__avoir_pas_integration()
        precision = int(self.precision)
        # somme = 0 
        x_i = self.__intervalle[0]+np.arange(0, self.precision+1,dtype=float)*pas_intergration # supposément vectorisé
        f_i = self._fonction_math.calculer(x_i)
        somme = np.sum(f_i[1:precision])
        # for i in range(1, self.precision - 1):      # Non vectorisé
            
        #     x_i = self.__intervalle[0] + i * pas_intergration
        #     somme += self._fonction_math.calculer(x_i) + self._fonction_math.calculer(self.intervalle[1]) 
            
        return (somme * 2 + f_i[0] + f_i[precision]) * pas_intergration / 2
    
    def __calculer_avec_rectangle (self) -> float : 
        pas_intergration =self.__avoir_pas_integration()
        point_evaluation = self.__avoir_points_interets()
        somme = np.sum(self._fonction_math.calculer(point_evaluation))
        # for i in range(self.precision - 1 ):   # non vectorisé
        #     x_i = self.__intervalle[0] + i * pas_intergration
        #     point_evaluation = x_i + self.alpha * pas_intergration
        #     somme += self._fonction_math.calculer(point_evaluation)
        return somme * pas_intergration 

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
        points = np.stack(( __axe_x_de_droite, __axe_x_de_droite,__axe_x_de_gauche,__axe_x_de_gauche, __axe_y_haut,__axe_y_bas,__axe_y_bas,  __axe_y_haut,), axis=1)
        return points

    def avoir_coordonnees_trapezes(self) -> NDArray:
        """Envoi le tableau 2d des points des trapèzes. Prend des tranches de l'axe y pour avoir le trapèze (genre [0,:])

        Returns:
            NDArray: Le tableau
        """
        pas = self.__avoir_pas_integration()
        x_gauche = self.__avoir_serie_x_i()
        x_droite = x_gauche + pas
        y_droite = self._fonction_math.calculer(x_droite)
        y_gauche = self._fonction_math.calculer(x_gauche)
        y_bas =  np.zeros(x_gauche.shape)
        points = np.stack((x_droite,x_droite,x_gauche,x_gauche,y_droite,y_bas,y_bas,y_gauche,),axis=1)
        return points

    