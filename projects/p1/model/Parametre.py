from projects.p1.model.Information import Information

class Parametre:
    """C'est la classe qui représente un paramètre"""
    def __init__(self, info:Information, nom:str, texte_precision:int, min_valeur:float|int, max_valeur:float|int, defaut_valeur:float|int) -> None:
        """Initialise un Paramètre
        Args:
            info (Information): l'information générale de ce que représente un paramètre
            nom (str): son nom
            texte_precision (int): Le nombre de chiffre après la virgule
            min_valeur (float): valeur minimale incluse
            max_valeur (float): valeur maximale incluse
            default_valeur (float): valeur par défaut
        Raises:
            TypeError: un des paramètres n'est pas du bon type
        """
        if not isinstance(info, Information)\
        or not isinstance(nom, str)\
        or not isinstance(texte_precision, float|int)\
        or not isinstance(min_valeur, float|int)\
        or not isinstance(max_valeur, float|int)\
        or not isinstance(defaut_valeur, float|int):
            raise TypeError("Un des paramètres n'est pas du bon type.")
        self.__info = info
        self.__texte_precision: int = 2
        self.__min_valeur = min_valeur
        self.__max_valeur = max_valeur
        self.__defaut_valeur = defaut_valeur
        self.__valeur = defaut_valeur

    # Getter

    @property
    def info(self) -> Information:
        return self.__info
    @property
    def texte_precision(self) -> int:
        return self.__texte_precision
    @property
    def min_valeur(self) -> float|int:
        return self.__min_valeur 
    @property
    def max_valeur(self) -> float|int:
        return self.__max_valeur 
    @property
    def defaut_valeur(self) -> float:
        return self.__defaut_valeur 
    @property
    def valeur(self) -> float:
        return self.__value
    @property
    def texte_valeur(self) -> str:
        return str(self.__valeur)

    # Setter

    @valeur.setter
    def valeur(self, nouvelle_valeur:float) -> None:
        """Permet de changer la valeur du paramètre tout en
            respectant les contraintes de min et max.
        Args:
            nouvelle_valeur (float): la nouvelle valeur
        Raises:
            ValueError: La valeur doit être entre le min_valeur et max_valeur.
            TypeError: Nouvelle_valeur doit être un float ou un int."""
        
        if not isinstance(nouvelle_valeur, float|int):
            raise TypeError("Nouvelle_valeur doit être un float ou un int.")
        if nouvelle_valeur < self.__min_valeur or nouvelle_valeur > self.__max_valeur:
            raise ValueError("La valeur doit être entre le min_valeur et max_valeur.")
        self.__valeur = nouvelle_valeur

    def reinitialiser(self) -> None:
        """Permet de remettre la valeur par défaut du paramètre"""
        self.__valeur = self.__defaut_valeur
