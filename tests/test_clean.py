from datetime import date

import pytest

from clean import mask_cpf, parse_date_br


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


def test_mask_cpf_valid():
    assert mask_cpf("123.456.789-09") == "***.***.789-09"
    assert mask_cpf("12345678909") == "***.***.789-09"


@pytest.mark.parametrize(
    "s",
    ["", "1234567890", "123456789012", "123.456.789-0a", " 12345678909",
     "123,456,789-09", "١٢٣٤٥٦٧٨٩٠١",
     "12345678909\n"],
)
def test_mask_cpf_invalid(s):
    with pytest.raises(ValueError):
        mask_cpf(s)
