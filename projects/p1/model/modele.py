import numpy as np
from projects.p1.model.transformation_canonique import TransformationCanonique
from projects.p1.model.fonction_sin import FonctionSin
from projects.p1.model.fonction_math import FonctionMath
from projects.p1.model.fonction_second_degre import FonctionSecondDegre
from projects.p1.model.fonction_sin_amortie import FonctionSinAmortie
from projects.p1.model.fonction_double_bosse import FonctionDoubleBosse
from projects.p1.model.methode_derive import MethodeDerive
from projects.p1.model.methode_integrale import MethodeIntegrale
from typing import override
from projects.p1.model.forme_integrale import FormeIntegrale
from projects.p1.model.affichage_derive import AffichageDerive
from projects.p1.model.affichage_methode import affichageMethode
from projects.p1.model.forme_integrale import FormeIntegrale

class Modele:
    def __init__(self):
        precision = 2
        minimum = -5
        maximum = 5
        self.__transformation_canonique:TransformationCanonique = TransformationCanonique(precision,minimum,maximum)
        self.__fonction_math = FonctionSin(self.__transformation_canonique)
        self.__fonction_sin = FonctionSin(self.__transformation_canonique)
        self.__fonction_second_degre = FonctionSecondDegre(self.__transformation_canonique)
        self.__fonction_sin_amortie = FonctionSinAmortie(self.__transformation_canonique)
        self.__fonction_double_bosse = FonctionDoubleBosse(self.__transformation_canonique)
        self.__methode_derive = MethodeDerive(self.__fonction_math,0)
        self.__methode_integrale = MethodeIntegrale(self.__fonction_math,(0,1))
        self.__methode_affiche = affichageMethode.AUCUNE

    @property
    def methode_derive_a_afficher(self) -> bool:
        return self.__methode_affiche == affichageMethode.DERIVE
    
    @property
    def methode_integrale_a_afficher(self) -> bool:
        return self.__methode_affiche == affichageMethode.INTEGRALE

    def mettre_affichage_derive(self) -> None:
        self.__methode_affiche = affichageMethode.DERIVE

    def mettre_affichage_integrale(self) -> None:
        self.__methode_affiche = affichageMethode.INTEGRALE

    def mettre_affichage_aucun(self) -> None:
        self.__methode_affiche = affichageMethode.AUCUNE

    @property
    def transformation_canonique(self):
        return self.__transformation_canonique

    @property
    def fonction_math(self) -> FonctionMath:
        return self.__fonction_math

    @property
    def fonction_sin(self) -> FonctionSin:
        return self.__fonction_sin

    @property
    def fonction_second_degre(self) -> FonctionSecondDegre:
        return self.__fonction_second_degre

    @property
    def fonction_sin_amortie(self) -> FonctionSinAmortie:
        return self.__fonction_sin_amortie

    @property
    def fonction_double_bosse(self) -> FonctionDoubleBosse:
        return self.__fonction_double_bosse

    @property
    def methode_derive(self):
        return self.__methode_derive

    @property
    def methode_integrale(self):
        return self.__methode_integrale

    @property
    def tangente_a_afficher(self) -> bool:
        return self.__methode_derive.representation == AffichageDerive.TANGENTE

    @property
    def secante_a_afficher(self) -> bool:
        return self.__methode_derive.representation == AffichageDerive.SECANTE

    @property
    def tangente_et_secante_a_afficher(self) -> bool:
        return self.__methode_derive.representation == AffichageDerive.TOUT

    @property
    def rectangle_a_afficher(self):
        return self.methode_integrale.forme_integrale == FormeIntegrale.RECTANGLE
    @property
    def trapeze_a_afficher(self) -> bool:
        return self.methode_integrale.forme_integrale == FormeIntegrale.TRAPEZE
    
    def changer_fonction_sin(self):
        self.__fonction_math = self.__fonction_sin
        self.changer_fonction_methodes()
        
    def changer_fonction_second_degre(self):
            self.__fonction_math = self.__fonction_second_degre
            self.changer_fonction_methodes()
    def changer_fonction_sin_amortie(self):
            self.__fonction_math = self.__fonction_sin_amortie
            self.changer_fonction_methodes()

    def changer_fonction_double_bosse(self):
            self.__fonction_math = self.__fonction_double_bosse
            self.changer_fonction_methodes()
            
    def changer_valeur_parametre(self,index:int,valeur:float):
        self.__fonction_math.parametres[index].valeur = valeur

    def avoir_info_parametre(self,index:int):
        return self.__fonction_math.parametres[index].info

    def avoir_info_fonction(self):
        return self.__fonction_math.info

    def avoir_vraie_formule(self):
        return self.__fonction_math.vrai_formule

    def reinitialiser_parametres_fonction(self):
        self.__fonction_math.redemarrer_parametres()

    def mettre_identite(self):
        self.transformation_canonique.reinitialiser()

    def mettre_symetrie_y(self):
        self.__transformation_canonique.trans_x.valeur = -1 * self.__transformation_canonique.trans_x.valeur
        self.__transformation_canonique.zoom_x.valeur = -1 * self.__transformation_canonique.zoom_x.valeur
        
    def mettre_symetrie_x(self):
        self.__transformation_canonique.trans_y.valeur = -1 * self.__transformation_canonique.trans_y.valeur
        self.__transformation_canonique.zoom_y.valeur = -1* self.__transformation_canonique.zoom_y.valeur

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

    def avoir_deux_points_derive_approxime(self) -> tuple[tuple[float,float],tuple[float,float]]:
        p_moins = self.methode_derive.avoir_premiere_valeur()
        p_plus = self.methode_derive.avoir_seconde_valeur()
        return ((p_moins, p_plus),(self.fonction_math.calculer(p_moins), self.fonction_math.calculer(p_plus)))

    def avoir_deux_points_tangente(self) -> tuple[tuple[float,float],tuple[float,float]]:
        point_interet = self.__methode_derive.point_interet
        droite = self.__methode_derive.avoir_regle_tangente()
        x_moins = point_interet - self.methode_derive.etendue_visible
        x_plus = point_interet + self.methode_derive.etendue_visible
        return ((x_moins, x_plus), (droite(x_moins), droite(x_plus)))

    def mettre_mode_rectangle(self):
        self.methode_integrale.forme_integrale = FormeIntegrale.RECTANGLE

    def mettre_mode_trapeze(self):
        self.methode_integrale.forme_integrale = FormeIntegrale.TRAPEZE

    def mettre_mode_tangente(self):
        self.methode_derive.representation = AffichageDerive.TANGENTE

    def mettre_mode_secante(self):
        self.methode_derive.representation = AffichageDerive.SECANTE

    def mettre_mode_tangente_et_secante(self):
        self.methode_derive.representation = AffichageDerive.TOUT

    def changer_fonction_methodes(self)->None:
        self.methode_integrale.fonction_math = self.fonction_math
        self.methode_derive.fonction_math = self.fonction_math



    
    