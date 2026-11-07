def normalize_name(s: str) -> str:
    if not isinstance(s, str):
        raise TypeError("s must be str")
    return " ".join(w.capitalize() for w in s.split())
