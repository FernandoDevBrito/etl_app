import pytest

from transform import normalize_name


def test_trim_collapse_title():
    assert normalize_name("  jOHN   doe ") == "John Doe"


def test_empty():
    assert normalize_name("") == ""


@pytest.mark.parametrize("bad", [None, 123, b"x"])
def test_non_str(bad):
    with pytest.raises(TypeError):
        normalize_name(bad)
