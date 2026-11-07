# Backend memory (lessons learned; agents append, retro curates)

- Stack: Python 3.10, pytest, ruff. Run checks with `bash scripts/ci.sh`.
- Block (don't guess) when a card has no measurable criteria ("fast enough", "looks good"), names an ETL/source that doesn't exist in the repo, or has an empty `## Out of scope`. Ask: target/baseline numbers, exact report fields, format + output location, scope limits.
- Re-block when user answers are non-answers ("yes", "the output the user wants"): quote the answer, restate the question with concrete options and a fill-in form (N rows / X seconds, file path, field list). Phrase questions so "yes" cannot answer them (no yes/no questions). Card 002 hit this three times (7 questions each round, answers stayed vague or grew scope: "port any database", "countdown", "requirements").
- After 2 blocked rounds, stop re-asking everything: write a concrete proposed v1 into the card (e.g. stdlib, SQLite->SQLite, stdout text report with rows read/written/rejected + duration, no threshold) and ask the user only to reply "approve" or edit named lines. Ask at most 3 questions, the ones that truly block building.
- Treat user answers that add scope ("any database", live countdown, requirements file) as new scope: push to separate cards, not the first version.
- Card bundling several deliverables (build ETL + speed target + report): ask to split once the info is clear; also confirm that touching `main.py` is in scope.
- Use per-word `capitalize()` over `str.title()` (apostrophe quirk); pytest finds root-level modules without config.
- Ruff isort runs in CI: stdlib imports (e.g. `decimal`) go before `import pytest` in tests.
- Parse money with a strict fullmatch regex, not strip-and-replace: replacing '-', '(', ')' anywhere silently flips signs ("R$ -10", "10-5").
- Parser plans: specify the accepted grammar up front (sign only at start or after `R$`, balanced parens, digits only so "1e5"/"Infinity" fail) and add tests for malformed input ("R$ -10,00", "(10,00", "10-5", "1e5"), not just the card's happy cases. Card 003 was rejected once for this.
- Dates: guard with a strict ASCII fullmatch regex before `strptime`, which accepts "5/3/2024" and padded input.
- CPF: ASCII fullmatch `\d{3}\.?\d{3}\.?\d{3}-?\d{2}` with re.ASCII rejects Arabic-Indic digits and trailing "\n".
- Dedupe: index row[key] (not .get) so missing keys raise KeyError; test a later row lacking it.
- Slugify: NFKD + `encode("ascii","ignore")` strips accents without deps.
