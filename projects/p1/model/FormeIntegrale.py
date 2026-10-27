from abc import ABC, abstractmethod
import numpy as np
import Information
import TransformationCanonique
import Parametre  
import FonctionMath
import enum as Enum


class FormeIntegrale(Enum):
    RECTANGLE = 1 
    TRAPEZE = 2 