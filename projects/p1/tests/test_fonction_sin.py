import unittest
import numpy as np
from p1.model import FonctionSin, TransformationCanonique

class TestFonctionSin(unittest.TestCase):

    def test_calculer(self):
        value = 10
        transformation_canonique = TransformationCanonique()
        fonction = FonctionSin(transformation_canonique)
        self.assertEqual(fonction.calculer(value), np.sin(value))

TestFonctionSin.test_calculer