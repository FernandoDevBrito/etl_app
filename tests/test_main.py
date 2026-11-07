import sqlite3

import pytest

from main import main


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
