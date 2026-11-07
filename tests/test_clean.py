from datetime import date

import pytest

from clean import parse_date_br


def test_parse_date_br_valid():
    assert parse_date_br("05/03/2024") == date(2024, 3, 5)
    assert parse_date_br("29/02/2024") == date(2024, 2, 29)


@pytest.mark.parametrize(
    "s",
    ["31/02/2024", "29/02/2023", "32/01/2024", "01/13/2024", "5/3/2024",
     "05-03-2024", "2024/03/05", "", " 05/03/2024"],
)
def test_parse_date_br_invalid(s):
    with pytest.raises(ValueError):
        parse_date_br(s)
