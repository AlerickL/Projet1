class Information:
    """Une classe qui repésente un bloc d'information
    """
    def __init__(self, nom: str, resume: str = "", details: str = ""):
        """Initialise la classe information.
        Args:
            nom (str): le nom de l'objet
            resume (str, optional): Le résumé de l'objet. Defaults to "".
            details (str, optional): Les détails de l'objet. Defaults to "".
        """
        self.__nom: str = nom
        self.__resume: str = resume
        self.__details: str = details

    @property
    def nom(self) -> str:
        """Donne le nom

        Returns:
            str: le nom
        """
        return self.__nom

    @property
    def resume(self) -> str:
        """Donne le resume

        Returns:
            str: le resume
        """
        return self.__resume

    @property
    def details(self) -> str:
        """Donne les details

        Returns:
            str: les details
        """
        return self.__details  
    