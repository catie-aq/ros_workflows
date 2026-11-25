"""Unit tests of sample_pkg.geometry."""

import pytest
from sample_pkg.geometry import clamp


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-1.0, 0.0), (0.5, 0.5), (2.0, 1.0)],
)
def test_clamp(value: float, expected: float) -> None:
    assert clamp(value, 0.0, 1.0) == expected


def test_clamp_empty_interval() -> None:
    with pytest.raises(ValueError, match="empty interval"):
        clamp(0.0, 1.0, 0.0)
