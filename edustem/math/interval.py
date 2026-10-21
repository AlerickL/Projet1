from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self, cast, override
from collections.abc import Sequence

class Interval[T: (int, float)](ABC):
    """
    A generic interval class representing a range between a lower and an upper bound.

    Type validation is expected to be handled by subclasses or external code.

    Type Parameters:
        T (int | float): The type of the interval bounds.

    Attributes:
        lower (T): The lower bound of the interval.
        upper (T): The upper bound of the interval.
    """

    __slots__ = ("_lower", "_upper")

    def __init__(self, lower: T, upper: T) -> None:
        self._lower: T
        self._upper: T
        self.set_bounds(lower, upper)

    def _new(self, lower: T, upper: T) -> Self:
        """Builds a new interval of the same type from the given bounds.

        Subclasses carrying extra configuration beyond the bounds should override
        this hook so that `intersection`, `union` and `replaced` preserve it.
        """
        return type(self)(lower, upper)

    def __repr__(self) -> str:
        return f"Interval(lower={self._lower}, upper={self._upper})"

    def __str__(self) -> str:
        return f"[{self._lower}, {self._upper}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Interval):
            return NotImplemented
        return self._lower == cast(Interval[T], other)._lower and self._upper == cast(Interval[T], other)._upper

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __contains__(self, value: T) -> bool:
        return self._lower <= value <= self._upper

    @property
    def lower(self) -> T:
        return self._lower
    
    @lower.setter
    def lower(self, value: T) -> None:
        self.set_bounds(value, self._upper)

    @property
    def upper(self) -> T:
        return self._upper
    
    @upper.setter
    def upper(self, value: T) -> None:
        self.set_bounds(self._lower, value)

    @property
    def length(self) -> T:
        return self._upper - self._lower

    @property
    def is_degenerate(self) -> bool:
        return self._lower == self._upper

    @property
    def bounds(self) -> tuple[T, T]:
        return (self._lower, self._upper)

    @bounds.setter
    def bounds(self, value: Sequence[T]) -> None:
        if not isinstance(value, Sequence): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("Bounds must be a sequence of exactly two elements.")
        if len(value) != 2:
            raise ValueError("Bounds must be a sequence of exactly two elements.")
        self.set_bounds(*value)

    @abstractmethod
    def set_bounds(self, lower: T, upper: T) -> None:
        if lower > upper:
            raise ValueError("Lower bound cannot be greater than upper bound.")
        self._lower = lower
        self._upper = upper

    def clamp(self, value: T) -> T:
        return max(self._lower, min(self._upper, value))

    def overlaps(self, other: Interval[T]) -> bool:
        return self._lower <= other._upper and other._lower <= self._upper

    def intersection(self, other: Interval[T]) -> Interval[T] | None:
        new_lower = max(self._lower, other._lower)
        new_upper = min(self._upper, other._upper)
        if new_lower > new_upper:
            return None
        return self._new(new_lower, new_upper)

    def union(self, other: Interval[T]) -> Interval[T] | None:
        if not self.overlaps(other):
            return None
        new_lower = min(self._lower, other._lower)
        new_upper = max(self._upper, other._upper)
        return self._new(new_lower, new_upper)

    def substracted(self, other: Interval[T]) -> Interval[T] | None:
        if not self.overlaps(other):
            return None
        new_lower = max(self._lower, other._lower)
        new_upper = min(self._upper, other._upper)
        return self._new(new_lower, new_upper)

    def replaced(self, *, lower: T | None = None, upper: T | None = None) -> Interval[T]:
        new_lower = self._lower if lower is None else lower
        new_upper = self._upper if upper is None else upper
        return self._new(new_lower, new_upper)




class IntInterval(Interval[int]):
    def __init__(self, lower: int = 0, upper: int = 100) -> None:
        super().__init__(lower, upper)

    @override
    def set_bounds(self, lower: int, upper: int) -> None:
        if not isinstance(lower, int) or not isinstance(upper, int): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("IntInterval requires integer bounds.")
        super().set_bounds(lower, upper)        



class RealInterval(Interval[float]):
    def __init__(self, lower: int | float = 0.0, upper: int | float = 1.0) -> None:
        super().__init__(lower, upper)

    @override
    def set_bounds(self, lower: int | float, upper: int | float) -> None:
        if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("RealInterval requires int or float bounds.")
        super().set_bounds(float(lower), float(upper))






