class Information:
    """Une classe qui repésente un bloc d'information
    """
    def __init__(self,nom:str,resume:str="",details:str=""):
        """Initialise la classe information.

        Args:
            nom (str): le nom de l'objet
            resume (str, optional): Le résumé de l'objet. Defaults to "".
            details (str, optional): Les détails de l'objet. Defaults to "".

        Raises:
            TypeError: Si le type de nom n'est pas bon
            TypeError: Si le type de resume n'est pas bon
            TypeError: Si le type de details n'est pas bon
        """
        if not isinstance(nom,str) :
            raise TypeError("nom doit être de type str")
        elif not isinstance(resume,str):
            raise TypeError("resumedoit être de type str")
        elif not isinstance(details,str):
            raise TypeError("details doit être de type str")
        self.__nom = nom
        self.__resume = resume
        self.__details = details

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
        """Donne le details

        Returns:
            str: le details
        """
        return self.__details  
    