import unittest
import numpy as np
from Projet1.projects.p1.model import fonction_sin
from Projet1.projects.p1.model import transformation_canonique

class TestFonctionSin(unittest.TestCase):

    def test_calculer(self):
        value = 10
        transformation_canonique = transformation_canonique()
        fonction = fonction_sin(transformation_canonique)
        self.assertEqual(fonction.calculer(value), np.sin(value))

TestFonctionSin.test_calculer