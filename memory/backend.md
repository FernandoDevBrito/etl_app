# Backend memory (lessons learned; agents append, retro curates)

- Stack: Python 3.10, pytest, ruff. Run checks with `bash scripts/ci.sh`.
- Block (don't guess) when a card has no measurable criteria ("fast enough", "looks good"), names an ETL/source that doesn't exist in the repo, or has an empty `## Out of scope`. Ask: target/baseline numbers, exact report fields, format + output location, scope limits.
- Use per-word `capitalize()` over `str.title()` (apostrophe quirk); pytest finds root-level modules without config.
- Ruff isort runs in CI: stdlib imports (e.g. `decimal`) go before `import pytest` in tests.
- Parse money with a strict fullmatch regex, not strip-and-replace: replacing '-', '(', ')' anywhere silently flips signs ("R$ -10", "10-5").
