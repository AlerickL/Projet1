import numpy as np
import Information
from TransformationCanonique import TransformationCanonique
import Parametre
import FonctionMath
from FonctionSin import FonctionSin
import FonctionSecondDegre
import FonctionSinAmortie
import FonctionDoubleBosse
from MethodeDerive import MethodeDerive
from MethodeIntegrale import MethodeIntegrale
from typing import override
from FormeIntegrale import FormeIntegrale

class Modele:
    def __init__(self):
        precision = 2
        minimum = -5
        maximum = 5
        self.__transformation_canonique:TransformationCanonique = TransformationCanonique(precision,minimum,maximum)
        self.__fonction_math = FonctionSin(self.__transformation_canonique)
        self.__methode_derive = MethodeDerive(self.__fonction_math,0)
        self.__methode_integrale = MethodeIntegrale(self.__fonction_math,(0,1))
        self.__r_affichage_tangente = 3

    @property
    def transformation_canonique(self):
        return self.__transformation_canonique

    @property
    def fonction_math(self):
        return self.__fonction_math

    @property
    def methode_derive(self):
        return self.__methode_derive

    @property
    def methode_integrale(self):
        return self.__methode_integrale

    @property
    def r_afficher_tangente(self):
        return self.__r_affichage_tangente
    
    def changer_fonction_sin(self):
        self.__fonction_math = FonctionSin(self.__transformation_canonique)

    def changer_fonction_second_degre(self):
            self.__fonction_math = FonctionSecondDegre(self.__transformation_canonique)

    def changer_fonction_sin_amortie(self):
            self.__fonction_math = FonctionSinAmortie(self.__transformation_canonique)

    def changer_fonction_double_bosse(self):
            self.__fonction_math = FonctionDoubleBosse(self.__transformation_canonique)

    def changer_valeur_parametre(self,index:int,valeur:float):
        self.__fonction_math.parametres[index] = valeur

    def avoir_info_parametre(self,index:int):
        return self.__fonction_math.parametres[index].info

    def avoir_info_fonction(self,index:int):
        return self.__fonction_math.info

    def avoir_vraie_formule(self):
        return self.__fonction_math.vrai_formule

    def reinitialiser_parametres_fonction(self):
        self.__fonction_math.redemarrer_parametres()

    def identite(self):
        self.transformation_canonique.reinitialiser()

    def mettre_symetrie_y(self):
        self.__transformation_canonique.trans_x = -1 * self.__transformation_canonique.trans_x
        self.__transformation_canonique.zoom_x = -self.__transformation_canonique.zoom_x 
        
    def mettre_symetrie_x(self):
        self.__transformation_canonique.trans_y = -1 * self.__transformation_canonique.trans_y
        self.__transformation_canonique.zoom_y = -1* self.__transformation_canonique.zoom_y

    def mettre_derive_a_gauche(self):
        self.methode_derive._alpha = 0.0

    def mettre_derive_au_milieu(self):
        self.methode_derive._alpha = 0.5

    def mettre_derive_a_droite(self):
        self.methode_derive._alpha = 1

    def mettre_integrale_a_gauche(self):
        self.methode_integrale._alpha = 0.0

    def mettre_integrale_au_milieu(self):
        self.methode_integrale._alpha = 0.5

    def mettre_integrale_a_droite(self):
        self.methode_integrale._alpha = 1

    def avoir_deux_points_derive_approxime(self) -> list[tuple[float,float],tuple[float,float]]:
        p_moins = self.methode_derive.avoir_premiere_valeur()
        p_plus = self.methode_derive.avoir_seconde_valeur()
        return [(p_moins,self.fonction_math.calculer(p_moins)),(p_plus,self.methode_derive.avoir_seconde_valeur())]

    def avoir_deux_points_tangente(self) -> list[tuple[float,float],tuple[float,float]]:
        point_interet = self.__methode_derive.point_interet
        droite = self.__methode_derive.avoir_regle_tangente()
        x_moins = point_interet - self.__r_affichage_tangente
        x_plus = point_interet + self.__r_affichage_tangente
        return [(x_moins,droite(x_moins)),(x_plus,droite(x_plus))]

    def mettre_mode_rectangle(self):
        self.methode_integrale.forme_integrale = FormeIntegrale.RECTANGLE

    def mettre_mode_trapeze(self):
        self.methode_integrale.forme_integrale = FormeIntegrale.TRAPEZE



    
    