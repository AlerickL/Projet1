
from ..generic.protocols import SupportsLessThan


def clamp[T: SupportsLessThan](value: T, min_value: T, max_value: T) -> T:
    """
    Clamp a value between a minimum and maximum value.

    Args:
        value (T): The value to clamp.
        min_value (T): The minimum allowable value.
        max_value (T): The maximum allowable value.

    Returns:
        T: The clamped value.

    Generic type T must be either int or float.
    """
    return max(min_value, min(value, max_value))

