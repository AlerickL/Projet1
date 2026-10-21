"""Liaison entre `QDomainExplorerBox` et un widget à intervalle : `QRangeDomainBinding`.

Une seule liaison sert toute la famille : `QRangeSlider`, `QRangeSpinBox`, `QRangeSliderSpinBox`
et leurs versions réelles. Le domaine pilote une propriété de l'intervalle choisi : sa borne
inférieure, sa borne supérieure ou son centre.

    box = QRealRangeSliderSpinBox()
    box.setLimits(-5.0, 5.0)
    explorer = QDomainExplorerBox()
    explorer.setBinding(QRangeDomainBinding(box))           # sweeps the interval, length kept

Contrairement aux autres widgets de ce projet, ce fichier n'est pas autonome : il relie
`q_domain_explorer_box` à la famille des widgets à intervalle, dont il emprunte le type
`CollisionMode` (`q_range_slider`). C'est là toute sa raison d'être.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Protocol, override

from PySide6.QtCore import QObject, Slot

from .q_domain_explorer_box import QDomainBinding
from .q_range_slider import QAbstractRangeSlider


# Defined before the binding, which names it in its base class (evaluated at its creation).
class _QRangeElement(Protocol):
    """Ce qu'une liaison lit et règle dans un widget à intervalle, entier ou réel.

    `QRangeSlider`, `QRangeSpinBox`, `QRangeSliderSpinBox` et leurs versions réelles le
    satisfont, sans ancêtre commun qui le dise.
    """

    def limits(self) -> tuple[float, float]: ...
    def range(self) -> tuple[float, float]: ...
    def resolution(self) -> float: ...
    def overlapAllowed(self) -> bool: ...
    def collisionMode(self) -> QAbstractRangeSlider.CollisionMode: ...
    def setLowerValue(self, lower: float, /) -> None: ...
    def setUpperValue(self, upper: float, /) -> None: ...
    def moveLowerValue(self, lower: float, /) -> None: ...


class QRangeDomainBinding(QDomainBinding[_QRangeElement, float]):
    """Implémentation de `QDomainBinding` pour les widgets à intervalle.

    La cible (`target`) dit quelle propriété de l'intervalle choisi le domaine pilote. Elle se
    choisit à la construction (`Target.Center` par défaut) et se change à tout moment par
    `setTarget` : le domaine s'y adapte aussitôt, puisque `QDomainExplorerBox` relit sa
    taille et sa position à chaque usage.

    ==================  ======================  ====================================
    Cible               Mutateur du widget      Longueur de l'intervalle
    ==================  ======================  ====================================
    `Center`            `moveLowerValue`        gardée : tout l'intervalle se déplace
    `LowerValue`        `setLowerValue`         change
    `UpperValue`        `setUpperValue`         change
    ==================  ======================  ====================================

    Positions
    ---------
    Une position par pas du widget (`resolution()` : 1 en entier, 10**-decimals en réel).
    Le domaine ne compte que les positions atteignables, pour que l'aller-retour
    `setIndex(i)` puis `index()` redonne exactement `i` :

    - **`Center`** : chaque placement de l'intervalle entre les limites, à longueur
      constante. Le domaine compte `(maximum - minimum - length) / resolution + 1`
      positions ; il change quand la longueur change.
    - **`LowerValue`** : du minimum jusqu'à la borne supérieure en mode `Blocking` (moins un
      pas si l'égalité est interdite), jusqu'au maximum en mode `Pushing`. Dans ce mode, la
      borne poussée ne revient pas d'elle-même : un balayage aller-retour rétrécit
      l'intervalle. C'est la règle du widget.
    - **`UpperValue`** : symétrique de `LowerValue`.

    Valeurs
    -------
    La valeur d'une position est celle de la propriété visée : la borne inférieure, la borne
    supérieure ou le centre. Le centre peut tomber entre deux pas (3.5 pour [2, 5]). La
    valeur par défaut se donne donc dans l'unité de la cible, et elle est mémorisée telle
    quelle : un changement de cible ne l'efface pas, mais change son sens. Non définie, elle
    suit la première position.

    Comme toute modification passe par un mutateur du widget, celui-ci émet ses signaux une
    seule fois par déplacement.

    Slots:
        setTarget(Target): Choisit la propriété que le domaine pilote.
    """

    class Target(Enum):
        """La propriété de l'intervalle choisi que pilote le domaine.

        Attributs:
            LowerValue: La borne inférieure ; la longueur change.
            UpperValue: La borne supérieure ; la longueur change.
            Center: Le centre ; la longueur est gardée.
        """

        LowerValue = 0
        UpperValue = 1
        Center = 2

    def __init__(self, element: _QRangeElement, *, target: Target = Target.Center,
                 defaultValue: float | None = None, parent: QObject | None = None) -> None:
        """Initialise la liaison.

        Args:
            element: Le widget à intervalle lié.
            target: La propriété que le domaine pilote (le centre par défaut).
            defaultValue: Valeur par défaut, dans l'unité de la cible, ou None pour la
                laisser non définie (voir `QDomainBinding.setDefaultValue()`).
            parent: Parent Qt, ou None.
        """
        super().__init__(element, defaultValue=defaultValue, parent=parent)
        self.__target: QRangeDomainBinding.Target = target

    def target(self) -> Target:
        """La propriété de l'intervalle que pilote le domaine (`Center` par défaut)."""
        return self.__target

    @Slot(Target)
    def setTarget(self, target: Target) -> None:
        """Choisit la propriété que pilote le domaine ; sa taille et sa position s'y adaptent."""
        self.__target = target

    # ================================================================== domain

    @override
    def index(self) -> int:
        lower, upper = self.__steps(self.element().range())
        first, _ = self.__reach()
        return (upper if self.__target == QRangeDomainBinding.Target.UpperValue else lower) - first

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        Target = QRangeDomainBinding.Target
        element = self.element()
        value = self.__valueOf(self.__reach()[0] + index)
        if self.__target == Target.Center:
            element.moveLowerValue(value)
        elif self.__target == Target.LowerValue:
            element.setLowerValue(value)
        else:
            element.setUpperValue(value)

    @override
    def size(self) -> int:
        first, last = self.__reach()
        return last - first + 1

    @override
    def valueFromIndex(self, index: int) -> float:
        steps = self.__reach()[0] + index
        if self.__target == QRangeDomainBinding.Target.Center:
            lower, upper = self.__steps(self.element().range())
            return (2 * steps + upper - lower) / 2 / 10 ** self.__decimals()
        return self.__valueOf(steps)

    @override
    def indexFromValue(self, value: float) -> int:
        exact = Decimal(value).scaleb(self.__decimals())
        if self.__target == QRangeDomainBinding.Target.Center:
            lower, upper = self.__steps(self.element().range())
            exact -= Decimal(upper - lower) / 2     # the lower bound of an interval centred on value
        return _rounded(exact) - self.__reach()[0]

    # ================================================================== private

    def __decimals(self) -> int:
        """The decimals of a step: 0 for integers."""
        resolution = self.element().resolution()
        return 0 if resolution >= 1 else round(-math.log10(resolution))

    def __steps(self, values: tuple[float, float]) -> tuple[int, int]:
        decimals = self.__decimals()
        return _rounded(Decimal(values[0]).scaleb(decimals)), _rounded(Decimal(values[1]).scaleb(decimals))

    def __valueOf(self, steps: int) -> float:
        """A value in the element's own kind of number: an int for an integer widget."""
        decimals = self.__decimals()
        return steps if decimals == 0 else steps / 10 ** decimals

    def __reach(self) -> tuple[int, int]:
        """The first and last reachable positions of the target, in steps."""
        Target = QRangeDomainBinding.Target
        element = self.element()
        minimum, maximum = self.__steps(element.limits())
        lower, upper = self.__steps(element.range())
        gap = 0 if element.overlapAllowed() else min(1, maximum - minimum)
        pushing = element.collisionMode() == QAbstractRangeSlider.CollisionMode.Pushing
        if self.__target == Target.Center:
            return minimum, maximum - (upper - lower)
        if self.__target == Target.LowerValue:
            return minimum, (maximum if pushing else upper) - gap
        return (minimum if pushing else lower) + gap, maximum


def _rounded(exact: Decimal) -> int:
    """Rounds to an integer, ties away from zero, as the real widgets do."""
    return int(exact.to_integral_value(rounding=ROUND_HALF_UP))
