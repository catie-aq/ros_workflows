"""Small pure functions, covered by the unit tests."""


def clamp(value: float, low: float, high: float) -> float:
    """Return ``value`` limited to the ``[low, high]`` interval.

    Raises:
        ValueError: if ``low`` is greater than ``high``.

    """
    if low > high:
        msg = f"empty interval [{low}, {high}]"
        raise ValueError(msg)
    return max(low, min(high, value))
