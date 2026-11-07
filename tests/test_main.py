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
