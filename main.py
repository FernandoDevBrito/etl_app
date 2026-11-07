import argparse
import json
import re
import sqlite3
import sys
import threading
import time

from transform import normalize_name

FIXES = {
    "malformed row": "Fix the row so it has the expected number of values",
    "duplicate key": "Remove or merge the duplicate row so the key is unique",
    "type mismatch": "Convert the value to the column's declared type",
}


def extract(path: str) -> tuple[list[tuple[int, str]], list[dict], int]:
    # run each statement alone in a scratch in-memory db; row = 1-based statement number
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    stmts, buf = [], ""
    with open(path, encoding="utf-8") as f:
        for ch in f.read():
            buf += ch
            # split at each ';' so several statements on one line are separate rows
            if ch == ";" and sqlite3.complete_statement(buf):
                stmts.append(buf)
                buf = ""
    # trailing chunk counts only if it holds more than comments/whitespace
    if re.sub(r"--[^\n]*|/\*.*?\*/", "", buf, flags=re.DOTALL).strip():
        stmts.append(buf)
    rows, problems, seen = [], [], set()
    for n, s in enumerate(stmts, 1):
        kind = None
        try:
            cur = con.execute(s)
            got = con.execute("SELECT id, name FROM items").fetchall()
            con.execute("DELETE FROM items")
            if cur.rowcount != 1 or len(got) != 1:
                kind = "malformed row"
            elif not isinstance(got[0][0], int) or not isinstance(got[0][1], str):
                kind = "type mismatch"
            elif got[0][0] in seen:
                kind = "duplicate key"
        except sqlite3.Error:
            kind = "malformed row"
        if kind:
            problems.append({"type": kind, "row": n, "message": FIXES[kind]})
        else:
            seen.add(got[0][0])
            rows.append(got[0])
    return rows, problems, len(stmts)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ETL from .sql INSERTs to SQLite")
    p.add_argument("input", nargs="?", default="samples/items.sql")
    p.add_argument("--db", required=True)
    p.add_argument("--table", required=True)
    a = p.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z_]\w*", a.table, re.ASCII):
        p.error(f"invalid table name: {a.table!r}")
    print(json.dumps(run(a.input, a.db, a.table)))
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
        raw, problems, rows_read = extract(input)
        rows = [(i, normalize_name(n)) for i, n in raw]
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
    return {
        "rows_read": rows_read,
        "rows_written": len(rows),
        "problems": problems,
        "total_duration_seconds": duration,
    }


if __name__ == "__main__":
    sys.exit(main())
