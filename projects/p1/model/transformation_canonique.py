from parametre import Parametre
from information import Information

class TransformationCanonique:
    """Classe contenant la gestion des transformation canoniques d'une fonction"""

    def __init__(self, precision: int, min: float|int, max: float|int,):
        """Crée les 4 paramètres de transformation canonique, 
        en prenant compte du min et du max des sliders pour déterminer leur range

        Args:
            precision (int): Le nombre de chiffres affiché après la virgule
            min (float|int): la valeur minimale des transformations canoniques
            max (float|int): la valeur maximale des transformations cannoniques
        """
        # Translations
        self.__defaut_trans = 0
        info_trans_x: Information = Information("Translation en x",  "Modifier horizontalement la position de la fonction")
        self.__trans_x: Parametre = Parametre(info_trans_x, precision, min, max, self.__defaut_trans)

        info_trans_y: Information = Information("Translation en y",  "Modifier verticalement la position de la fonction")
        self.__trans_y: Parametre = Parametre(info_trans_y, precision, min, max, self.__defaut_trans)

        # Aggrandissements
        self.__defaut_zoom = 1
        info_zoom_x: Information = Information("Aggrandissement en x",  "Aggrandir horizontalement la fonction")
        self.__zoom_x: Parametre = Parametre(info_zoom_x, precision, min, max, self.__defaut_trans)

        info_zoom_y: Information = Information("Aggrandissement en y",  "Aggrandir horizontalement la fonction")
        self.__zoom_y: Parametre = Parametre(info_zoom_y, precision, min, max, self.__defaut_trans)


    # Getter

    @property
    def trans_x(self) -> Parametre:
        return self.__trans_x

    @property
    def trans_y(self) -> Parametre:
        return self.__trans_y

    @property
    def zoom_x(self) -> Parametre:
        return self.__zoom_x

    @property
    def zoom_y(self) -> Parametre:
        return self.__zoom_y


    # Setter

    @trans_x.setter
    def trans_x(self, valeur: float|int) -> None:
        self.__trans_x.valeur = valeur

    @trans_y.setter
    def trans_y(self, valeur: float|int) -> None:
        self.__trans_y.valeur = valeur

    @zoom_x.setter
    def zoom_x(self, valeur: float|int) -> None:
        self.__zoom_x.valeur = valeur
    
    @zoom_y.setter
    def zoom_x(self, valeur: float|int) -> None:
        self.__zoom_x.valeur = valeur

    def reinitialiser(self) -> None:
        self.trans_x = self.__defaut_trans
        self.trans_y = self.__defaut_trans
        self.zoom_x = self.__defaut_zoom
        self.zoom_y = self.__defaut_zoom
