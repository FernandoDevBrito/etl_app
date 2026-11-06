# etl_app: orchestrator rules + project context

I (the user) write demand cards in `board/backlog/`. Agents plan, implement, review and fix them and stop only when a card is approved or needs me. Everything runs locally on my Claude Code + Gemini CLI subscriptions: no API keys, no CI service, no servers.

## Project context (discovered)
- Stack: Python (3.10 on Windows 11). Project is just starting: `main.py` is empty, `README.md` is a title. Layout will be decided by the cards, keep it minimal.
- Tools: `pytest` for tests, `ruff` for lint, `python -m compileall` as the "build". All run through `bash scripts/ci.sh` (uses `.venv/` if present; setup: `python -m venv .venv && .venv/Scripts/python -m pip install -r requirements-dev.txt`).
- Shell: git bash on Windows. Use forward slashes, POSIX commands.
- Git: main branch is `main`, remote `origin`. Orchestration setup lives on `agents-setup`. Card state (`board/*/*.md`, `board/_log.md`, `board/.tmp/`) is gitignored on purpose; `ORCHESTRATOR_PROMPT.md` too.
- Never deploy. Deploy is a manual command by me.

## Flow (scripts/orchestrator.sh)
For each card in `board/backlog/` (priority = filename order):
1. Move to `doing/`, branch `card/<id>` from the base branch (default `main`, override `--base`).
2. PLAN: area agent reads the card, explores the code, writes `## Plan` in the card. Vague or missing info → card goes to `blocked/` with specific questions. Never guess.
3. IMPLEMENT: `claude -p --agent <area>`.
4. CI: `scripts/ci.sh` (lint, tests, build). Failure output goes back to the agent.
5. REVIEW: `qa` agent AND Gemini (`gemini -p`, rules in GEMINI.md). Both must say APPROVED.
6. Rejected → back to the agent with the failures. Max 3 attempts, then `blocked/` as "needs human".
7. Approved + CI green → commit, merge into base, card to `done/`, run `retro`.
8. Backlog empty → stop.
Flags: `--dry-run`, `--card <id>`, `--base <branch>`. Every step is logged in `board/_log.md`. Rate-limit/quota errors from either CLI → wait with backoff and resume.

## Hard rules
- **Quem faz nunca avalia**: the implementer never evaluates its own work. `qa` sees only the card (without plan/log), the diff and test output. Never pass implementer reasoning to the reviewers.
- **3-attempt limit** per card, then `blocked/` for a human.
- **Ask via `blocked/` instead of guessing**: ambiguity or missing info = questions in `## Blockers / questions`, final line `RESULT: BLOCKED`.
- Agents do not commit, merge, push, switch branches or edit `scripts/`, `.claude/`, `CLAUDE.md`, `GEMINI.md`. The orchestrator owns git.
- Stay inside the card's scope (`## Out of scope` is binding). One card = one branch.
- Before work read `memory/<area>.md`; after work append lessons learned there.
- Lazy default (ponytail): stdlib first, fewest files, no unrequested abstractions.

## Agent protocol (machine-read markers, plain text on their own line)
- Plan/implement: `RESULT: PLANNED`, `RESULT: DONE` or `RESULT: BLOCKED`.
- Reviewers (qa, Gemini): last line `VERDICT: APPROVED` or `VERDICT: REJECTED`.
