from abc import ABC, abstractmethod
import numpy as np
import Information
import Projet1.projects.p1.model.transformation_canonique as transformation_canonique
import Parametre  
import Projet1.projects.p1.model.fonction_math as fonction_math
import enum as Enum


class FormeIntegrale(Enum):
    RECTANGLE = 1 
    TRAPEZE = 2 