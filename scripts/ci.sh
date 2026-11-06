#!/usr/bin/env bash
# CI gate: lint, tests, build. Exit 1 if anything fails.
set -u
cd "$(dirname "$0")/.."

PY=python
[ -x .venv/Scripts/python.exe ] && PY=.venv/Scripts/python
[ -x .venv/bin/python ] && PY=.venv/bin/python

fail=0
echo "== lint (ruff)";  "$PY" -m ruff check . || fail=1
echo "== build (compileall)"; "$PY" -m compileall -q -x '(\.git|\.venv|node_modules)' . || fail=1
echo "== tests (pytest)"
"$PY" -m pytest -q; rc=$?
[ $rc -eq 0 ] || [ $rc -eq 5 ] || fail=1   # 5 = no tests collected yet

[ $fail -eq 0 ] && echo "CI: PASS" || echo "CI: FAIL"
exit $fail
