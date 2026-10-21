from typing import Protocol, Self


class SupportsLessThan(Protocol):
    def __lt__(self, other: Self, /) -> bool: ...

class SupportsLessEqualThan(Protocol):
    def __le__(self, other: Self, /) -> bool: ...

class SupportsGreaterThan(Protocol):
    def __gt__(self, other: Self, /) -> bool: ...

class SupportsGreaterEqualThan(Protocol):
    def __ge__(self, other: Self, /) -> bool: ...

