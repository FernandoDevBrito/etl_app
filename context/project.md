# Project context

- What it is: etl_app, a small Python ETL (extract / transform / load). Just starting: `main.py` is empty; `transform.py` has `normalize_name`.
- Stack: Python 3.10, pytest, ruff. Windows 11, run through git bash.
- Run everything with `bash scripts/ci.sh` (ruff + compileall + pytest, uses `.venv/`). Setup: `python -m venv .venv && .venv/Scripts/python -m pip install -r requirements-dev.txt`.
- Conventions: stdlib first, flat modules at the repo root, tests in `tests/test_<module>.py`, type hints on public functions.
- Never: deploy, add dependencies without a card saying so, touch `main.py` unless the card does.
- Git: base branch is `agents-setup` for now (use `orch run --base agents-setup`); `main` stays untouched until I merge.
