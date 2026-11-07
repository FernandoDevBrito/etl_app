import argparse
import re
import sqlite3
import sys

from transform import normalize_name


def extract(path: str) -> list[tuple[int, str]]:
    # run the INSERTs in a scratch in-memory db, then read rows back
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    with open(path, encoding="utf-8") as f:
        con.executescript(f.read())
    return con.execute("SELECT id, name FROM items").fetchall()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ETL from .sql INSERTs to SQLite")
    p.add_argument("input", nargs="?", default="samples/items.sql")
    p.add_argument("--db", required=True)
    p.add_argument("--table", required=True)
    a = p.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z_]\w*", a.table, re.ASCII):
        p.error(f"invalid table name: {a.table!r}")
    rows = [(i, normalize_name(n)) for i, n in extract(a.input)]
    con = sqlite3.connect(a.db)
    with con:
        con.execute(f'CREATE TABLE IF NOT EXISTS "{a.table}" (id INTEGER, name TEXT)')
        con.executemany(f'INSERT INTO "{a.table}" (id, name) VALUES (?, ?)', rows)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
