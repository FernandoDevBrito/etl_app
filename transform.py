import re
import unicodedata
from decimal import Decimal

# optional "(" or "-" (before or after "R$"), digits with optional "." thousands, optional ",dd"
_AMOUNT = re.compile(
    r"(?:(\()\s*)?(-\s*)?(?:R\$\s*)?(-\s*)?(\d+(?:\.\d{3})*(?:,\d+)?)(?:\s*(\)))?"
)


def normalize_name(s: str) -> str:
    if not isinstance(s, str):
        raise TypeError("s must be str")
    return " ".join(w.capitalize() for w in s.split())


def parse_amount(s: str) -> Decimal:
    if not isinstance(s, str):
        raise TypeError("s must be str")
    s = s.strip()
    if not s:
        raise ValueError("empty amount")
    m = _AMOUNT.fullmatch(s)
    if not m:
        raise ValueError(f"invalid amount: {s!r}")
    open_, m1, m2, num, close = m.groups()
    if bool(open_) != bool(close) or (m1 and m2) or (open_ and (m1 or m2)):
        raise ValueError(f"invalid amount: {s!r}")
    d = Decimal(num.replace(".", "").replace(",", "."))
    return -d if (open_ or m1 or m2) else d


def slugify(s: str) -> str:
    if not isinstance(s, str):
        raise TypeError("s must be str")
    ascii_ = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")
