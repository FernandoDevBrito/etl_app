import re
from datetime import date, datetime


def parse_date_br(s: str) -> date:
    """Parse strict DD/MM/YYYY into a date; ValueError if malformed or impossible."""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s, re.ASCII):
        raise ValueError(f"invalid date: {s!r}")
    return datetime.strptime(s, "%d/%m/%Y").date()


def mask_cpf(s: str) -> str:
    """Mask a CPF as ***.***.DDD-DD; ValueError unless 11 ASCII digits (optional . and -)."""
    if not re.fullmatch(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", s, re.ASCII):
        raise ValueError(f"invalid cpf: {s!r}")
    d = re.sub(r"\D", "", s)
    return f"***.***.{d[6:9]}-{d[9:]}"
