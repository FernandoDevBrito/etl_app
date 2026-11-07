from datetime import date

import pytest

from clean import dedupe_rows, mask_cpf, parse_date_br


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


def test_dedupe_rows_keeps_first_and_order():
    rows = [{"id": 2, "v": "a"}, {"id": 1, "v": "b"}, {"id": 2, "v": "c"}, {"id": 1, "v": "d"}]
    assert dedupe_rows(rows, "id") == [{"id": 2, "v": "a"}, {"id": 1, "v": "b"}]


def test_dedupe_rows_no_dupes_and_empty():
    rows = [{"id": 1}, {"id": 2}]
    assert dedupe_rows(rows, "id") == rows
    assert dedupe_rows([], "id") == []


def test_dedupe_rows_missing_key():
    with pytest.raises(KeyError):
        dedupe_rows([{"id": 1}, {"x": 2}], "id")
    with pytest.raises(KeyError):
        dedupe_rows([{"x": 2}], "id")
