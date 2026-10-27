from FonctionMath import FonctionMath
from Information import Information
from TransformationCanonique import TransformationCanonique

class FonctionSin(FonctionMath):
    """Représente une fonction sinus"""
    def __init__(self,transformations_canoniques:TransformationCanonique):

        
        info:Information = Information("Fonction sinus",\
                                    "Fonction trigonométrique périodique définie par l'ordonné du cercle trigonométrique", "ce n'est pas une sinusite")
        formu
        if not isinstance(transformations_canoniques,TransformationCanonique):
            raise TypeError("transformations_canoniques doit être de type TransformationCanonique")
        super().__init__()