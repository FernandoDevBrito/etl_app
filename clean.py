import re
from datetime import date, datetime


def parse_date_br(s: str) -> date:
    """Parse strict DD/MM/YYYY into a date; ValueError if malformed or impossible."""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s, re.ASCII):
        raise ValueError(f"invalid date: {s!r}")
    return datetime.strptime(s, "%d/%m/%Y").date()
