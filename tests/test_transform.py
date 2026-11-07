from decimal import Decimal

import pytest

from transform import normalize_name, parse_amount, slugify


def test_trim_collapse_title():
    assert normalize_name("  jOHN   doe ") == "John Doe"


def test_empty():
    assert normalize_name("") == ""


@pytest.mark.parametrize("bad", [None, 123, b"x"])
def test_non_str(bad):
    with pytest.raises(TypeError):
        normalize_name(bad)


@pytest.mark.parametrize(
    "s,want",
    [
        ("R$ 1.234,56", Decimal("1234.56")),
        ("0,5", Decimal("0.50")),
        ("-R$ 10,00", Decimal("-10.00")),
        ("(10,00)", Decimal("-10.00")),
        ("R$ -10,00", Decimal("-10.00")),
    ],
)
def test_parse_amount(s, want):
    assert parse_amount(s) == want


@pytest.mark.parametrize("bad", ["", "   ", "abc", "NaN", "(10,00", "10,00)", "10-5", "--10", "-R$ -10", "1e5", "Infinity"])
def test_parse_amount_value_error(bad):
    with pytest.raises(ValueError):
        parse_amount(bad)


@pytest.mark.parametrize("bad", [None, 10, b"1"])
def test_parse_amount_type_error(bad):
    with pytest.raises(TypeError):
        parse_amount(bad)


def test_slugify_example():
    assert slugify("  Relatório Mensal: Vendas/2024!  ") == "relatorio-mensal-vendas-2024"


@pytest.mark.parametrize("s", ["---", ""])
def test_slugify_empty(s):
    assert slugify(s) == ""


@pytest.mark.parametrize("bad", [None, 123, b"x"])
def test_slugify_type_error(bad):
    with pytest.raises(TypeError):
        slugify(bad)
