# Backend memory (lessons learned; agents append, retro curates)

- Stack: Python 3.10, pytest, ruff. Run checks with `bash scripts/ci.sh`.
- Block (don't guess) when a card has no measurable criteria ("fast enough", "looks good"), names an ETL/source that doesn't exist in the repo, or has an empty `## Out of scope`. Ask: target/baseline numbers, exact report fields, format + output location, scope limits.
- Use per-word `capitalize()` over `str.title()` (apostrophe quirk); pytest finds root-level modules without config.
- Ruff isort runs in CI: stdlib imports (e.g. `decimal`) go before `import pytest` in tests.
- Parse money with a strict fullmatch regex, not strip-and-replace: replacing '-', '(', ')' anywhere silently flips signs ("R$ -10", "10-5").
- Parser plans: specify the accepted grammar up front (sign only at start or after `R$`, balanced parens, digits only so "1e5"/"Infinity" fail) and add tests for malformed input ("R$ -10,00", "(10,00", "10-5", "1e5"), not just the card's happy cases. Card 003 was rejected once for this.
- Dates: guard with a strict ASCII fullmatch regex before `strptime`, which accepts "5/3/2024" and padded input.
- Slugify: NFKD + `encode("ascii","ignore")` strips accents without deps.
