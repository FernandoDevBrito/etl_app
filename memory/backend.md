# Backend memory (lessons learned; agents append, retro curates)

- Stack: Python 3.10, pytest, ruff. Run checks with `bash scripts/ci.sh`.
- Use per-word `capitalize()` over `str.title()` (apostrophe quirk); pytest finds root-level modules without config.
