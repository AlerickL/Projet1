"""Règles d'un intervalle choisi dans des limites, partagées par les widgets à intervalle.

`QRangeSlider`, `QRangeSpinBox` et `QRangeSliderSpinBox` (entiers et réels) comptent leurs
valeurs en nombres entiers de pas. Tous appliquent les règles de `IntervalRules` : pour une
même opération sur un même état, ils retiennent le même intervalle.

Règle commune des opérations
----------------------------
Chaque opération garde une quantité et en vise une autre. **Ce qu'elle garde n'est jamais
modifié ; c'est sa cible qui s'arrête aux limites.**

==============================  ==================  ====================================
Opération                       Garde               S'arrête
==============================  ==================  ====================================
`with_lower`, `with_upper`      l'autre borne       contre l'autre borne (`Blocking`)
`resolved`                      rien                chaque borne à sa limite
`moved_to`, `centered_on`       la longueur          l'intervalle contre une limite
`with_length`                    la borne inférieure la borne supérieure au maximum
`widened`                       le centre           dès qu'une borne touche sa limite
==============================  ==================  ====================================

Seul le mode `Pushing` fait exception, et c'est son rôle : une borne qui rencontre l'autre la
pousse, jusqu'à la limite.

    rules = IntervalRules(minimum=0, maximum=20, gap=0, pushing=False)
    rules.widened(2, 12, 5)          # (0, 14): the centre 7 is kept, the lower bound stops at 0
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .real_steps import rounded_to_steps


@dataclass(frozen=True)
class IntervalRules:
    """Les limites d'un intervalle et ses règles de rencontre, en nombres entiers de pas.

    Chaque méthode reçoit un intervalle légal `(lower, upper)` et rend l'intervalle légal le
    plus proche de ce qui est demandé : `minimum <= lower <= upper <= maximum` et
    `upper - lower >= gap`, sauf quand les limites sont réduites à un point.

    Attributs:
        minimum: La limite inférieure.
        maximum: La limite supérieure, au moins égale à `minimum`.
        gap: La plus petite longueur permise : 0 si les bornes peuvent être égales, sinon 1
            (voir `gap_for`).
        pushing: Vrai en mode `Pushing` : une borne pousse l'autre au lieu de s'arrêter
            contre elle.
    """

    minimum: int
    maximum: int
    gap: int
    pushing: bool

    @staticmethod
    def gap_for(minimum: int, maximum: int, overlap_allowed: bool) -> int:
        """La plus petite longueur permise : un pas si l'égalité est interdite, sauf entre des limites réduites à un point."""
        return 0 if overlap_allowed else min(1, maximum - minimum)

    def resolved(self, lower: int, upper: int) -> tuple[int, int]:
        """Deux valeurs libres : triées, ramenées dans les limites, puis écartées de `gap`.

        Si elles sont trop proches, la borne supérieure monte, ou la borne inférieure descend
        s'il n'y a plus de place.
        """
        lo, hi, gap = self.minimum, self.maximum, self.gap
        lower, upper = sorted((max(lo, min(lower, hi)), max(lo, min(upper, hi))))
        if upper - lower < gap:
            if lower + gap <= hi:
                upper = lower + gap
            else:
                lower, upper = hi - gap, hi
        return lower, upper

    def with_lower(self, lower: int, upper: int, target: int) -> tuple[int, int]:
        """La borne inférieure déplacée vers `target`, selon le mode de collision."""
        target = max(self.minimum, min(target, self.maximum - self.gap))
        if self.pushing:
            return target, max(upper, target + self.gap)
        return min(target, upper - self.gap), upper

    def with_upper(self, lower: int, upper: int, target: int) -> tuple[int, int]:
        """La borne supérieure déplacée vers `target`, selon le mode de collision."""
        target = min(self.maximum, max(target, self.minimum + self.gap))
        if self.pushing:
            return min(lower, target - self.gap), target
        return lower, max(target, lower + self.gap)

    def moved_to(self, lower: int, upper: int, target: int) -> tuple[int, int]:
        """L'intervalle déplacé pour que sa borne inférieure soit `target`, à longueur constante."""
        width = upper - lower
        lower = max(self.minimum, min(target, self.maximum - width))
        return lower, lower + width

    def shifted(self, lower: int, upper: int, offset: int) -> tuple[int, int]:
        """L'intervalle déplacé de `offset` pas, à longueur constante."""
        return self.moved_to(lower, upper, lower + offset)

    def centered_on(self, lower: int, upper: int, center: float, decimals: int) -> tuple[int, int]:
        """L'intervalle déplacé pour que son centre soit au plus près de `center`, à longueur constante.

        La borne inférieure visée, `center - longueur / 2`, est arrondie au pas comme le fait
        `rounded_to_steps` : sur la valeur binaire exacte du `float`, les égalités en
        s'éloignant de zéro.

        Args:
            lower: La borne inférieure, en pas.
            upper: La borne supérieure, en pas.
            center: Le centre visé, en unités de valeur (pas en pas).
            decimals: Le nombre de décimales d'un pas (0 pour des entiers).

        Lève:
            TypeError: Si `center` n'est ni un `int` ni un `float`.
            ValueError: Si `center` n'est pas fini.
        """
        rounded_to_steps(center, decimals)      # validates the value
        exact = Decimal(center).scaleb(decimals) - Decimal(upper - lower) / 2
        target = int(exact.to_integral_value(rounding=ROUND_HALF_UP))
        return self.moved_to(lower, upper, target)

    def with_length(self, lower: int, upper: int, length: int) -> tuple[int, int]:
        """L'intervalle de longueur `length`, à borne inférieure constante.

        La longueur s'arrête à `maximum - lower`, et ne descend pas sous `gap` (une longueur
        négative donne donc `gap`).
        """
        length = max(self.gap, min(length, self.maximum - lower))
        return lower, lower + length

    def widened(self, lower: int, upper: int, offset: int) -> tuple[int, int]:
        """Chaque borne écartée de `offset` pas, à centre constant ; un `offset` négatif les rapproche.

        En s'écartant, les deux bornes s'arrêtent dès que l'une touche sa limite. En se
        rapprochant, elles s'arrêtent à la plus petite longueur permise qui garde le centre.
        """
        if offset >= 0:
            change = min(offset, lower - self.minimum, self.maximum - upper)
        else:
            change = -min(-offset, (upper - lower - self.gap) // 2)
        return lower - change, upper + change
