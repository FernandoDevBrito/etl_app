import json
import sqlite3
import time

import pytest

from main import main, run


def test_run_records_duration(tmp_path, capsys):
    db = tmp_path / "o.db"
    d = run("samples/items.sql", str(db), "items")["total_duration_seconds"]
    assert isinstance(d, float) and d >= 0
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 5
    con.close()
    last = capsys.readouterr().err.rstrip("\n").split("\r")[-1]
    assert last == f"elapsed: {d:.3f}s"


def test_live_ticks_on_stderr(tmp_path, capsys, monkeypatch):
    import main as m

    real = m.extract
    monkeypatch.setattr(m, "extract", lambda p: (time.sleep(0.35), real(p))[1])
    d = m.run("samples/items.sql", str(tmp_path / "o.db"), "items")["total_duration_seconds"]
    parts = capsys.readouterr().err.rstrip("\n").split("\r")
    ticks = [x for x in parts[1:-1]]
    assert len(ticks) >= 2 and all(x.startswith("elapsed: ") for x in ticks)
    assert parts[-1] == f"elapsed: {d:.3f}s"


def test_stdout_json_report(tmp_path, capsys):
    assert main(["--db", str(tmp_path / "o.db"), "--table", "items"]) == 0
    r = json.loads(capsys.readouterr().out)
    assert set(r) == {"rows_read", "rows_written", "problems", "total_duration_seconds"}
    assert r["rows_read"] == 5 and r["rows_written"] == 5 and r["problems"] == []
    assert r["total_duration_seconds"] >= 0


def test_comments_not_problems(tmp_path):
    f = tmp_path / "c.sql"
    f.write_text(
        "-- head\nINSERT INTO items (id, name) VALUES (1, 'a');\n-- note\n/* end */\n",
        encoding="utf-8",
    )
    r = run(str(f), str(tmp_path / "o.db"), "items")
    assert (r["rows_read"], r["rows_written"], r["problems"]) == (1, 1, [])


def test_problems(tmp_path):
    f = tmp_path / "p.sql"
    f.write_text(
        "INSERT INTO items (id, name) VALUES (1, 'a');\n"
        "INSERT INTO items (id, name) VALUES (2);\n"
        "INSERT INTO items (id, name) VALUES (1, 'dup');\n"
        "INSERT INTO items (id, name) VALUES ('abc', 'x');\n"
        "INSERT INTO items (id, name) VALUES (3, 'ok');\n",
        encoding="utf-8",
    )
    r = run(str(f), str(tmp_path / "o.db"), "items")
    assert (r["rows_read"], r["rows_written"]) == (5, 2)
    assert r["problems"] == [
        {"type": "malformed row", "row": 2,
         "message": "Fix the row so it has the expected number of values"},
        {"type": "duplicate key", "row": 3,
         "message": "Remove or merge the duplicate row so the key is unique"},
        {"type": "type mismatch", "row": 4,
         "message": "Convert the value to the column's declared type"},
    ]


def test_edge_statements(tmp_path):
    f = tmp_path / "e.sql"
    f.write_text(
        "INSERT INTO items (id, name) VALUES (3,'a;b'); INSERT INTO items (id, name) VALUES (4,'b');\n"
        "INSERT INTO items (id, name) VALUES (NULL, 'n');\n"
        "INSERT INTO items (id, name) VALUES (5,'c'),(6,'d');\n",
        encoding="utf-8",
    )
    r = run(str(f), str(tmp_path / "o.db"), "items")
    # two same-line statements load; NULL id is a type mismatch;
    # multi-row VALUES counts as one malformed row (one row per statement)
    assert (r["rows_read"], r["rows_written"]) == (4, 2)
    assert [(p["type"], p["row"]) for p in r["problems"]] == [
        ("type mismatch", 3), ("malformed row", 4)]


def test_sample_has_5_inserts():
    with open("samples/items.sql", encoding="utf-8") as f:
        assert f.read().count("INSERT INTO items") == 5


def test_loads_5_rows(tmp_path):
    db = tmp_path / "o.db"
    assert main(["--db", str(db), "--table", "items"]) == 0
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 5
    assert con.execute("SELECT name FROM items WHERE id=1").fetchone()[0] == "Widget One"
    con.close()


@pytest.mark.parametrize("args", [["--table", "items"], ["--db", "x.db"]])
def test_missing_required_args(args):
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.value.code != 0


def test_bad_table_name(tmp_path):
    with pytest.raises(SystemExit) as e:
        main(["--db", str(tmp_path / "o.db"), "--table", "a;b"])
    assert e.value.code != 0
