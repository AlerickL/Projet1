"""Arrondi d'un nombre réel en un nombre entier de pas, partagé par les widgets réels.

Un widget réel de la bibliothèque (`QRealSlider`, `QRealRangeSlider`, `QRealRangeSpinBox`)
compte ses valeurs en pas de 10**-decimals. Tous arrondissent par `rounded_to_steps`, la
règle de `QDoubleSpinBox` : pour un même nombre et les mêmes décimales, ils retiennent la
même valeur.

    rounded_to_steps(0.125, 2)    # 13 : 0.125 est exact en binaire, l'égalité s'éloigne de zéro
    rounded_to_steps(2.675, 2)    # 267 : 2.675 vaut en réalité 2.67499...
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal


def rounded_to_steps(value: float, decimals: int) -> int:
    """Arrondit un réel en un nombre entier de pas de 10**-decimals, comme `QDoubleSpinBox`.

    L'arrondi porte sur la valeur binaire exacte du `float`, les égalités en s'éloignant de
    zéro.

    Args:
        value: Le nombre à arrondir.
        decimals: Le nombre de décimales d'un pas.

    Retourne:
        Le nombre de pas, non borné.

    Lève:
        TypeError: Si `value` n'est ni un `int` ni un `float` (un booléen non plus).
        ValueError: Si `value` n'est pas fini.

    Exemple :
        >>> rounded_to_steps(0.125, 2), rounded_to_steps(2.675, 2), rounded_to_steps(-0.5, 0)
        (13, 267, -1)
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)): # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"A real value must be an int or a float, got {type(value).__name__}.")
    if not math.isfinite(value):
        raise ValueError("A real value must be finite.")
    return int(Decimal(value).scaleb(decimals).to_integral_value(rounding=ROUND_HALF_UP))
