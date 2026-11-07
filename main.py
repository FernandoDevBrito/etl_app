import argparse
import re
import sqlite3
import sys
import threading
import time

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
    run(a.input, a.db, a.table)
    return 0


def run(input: str, db: str, table: str) -> dict:
    start = time.perf_counter()
    stop = threading.Event()

    def tick() -> None:
        while not stop.wait(0.1):
            sys.stderr.write(f"\relapsed: {time.perf_counter() - start:.1f}s")
            sys.stderr.flush()

    t = threading.Thread(target=tick, daemon=True)
    t.start()
    try:
        rows = [(i, normalize_name(n)) for i, n in extract(input)]
        con = sqlite3.connect(db)
        with con:
            con.execute(f'CREATE TABLE IF NOT EXISTS "{table}" (id INTEGER, name TEXT)')
            con.executemany(f'INSERT INTO "{table}" (id, name) VALUES (?, ?)', rows)
        con.close()
    finally:
        duration = time.perf_counter() - start
        stop.set()
        t.join()
        sys.stderr.write(f"\relapsed: {duration:.3f}s\n")
    return {"total_duration_seconds": duration}


if __name__ == "__main__":
    sys.exit(main())
