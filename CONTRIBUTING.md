# Contributing to NXS-Go

NXS-Go is a local-first abstract strategy game about connection, pressure, and isolation.

The current project priority is v0.1-A clarity playtesting. Contributions should help new players understand the game before adding new mechanics.

## Good First Contributions

- Improve onboarding, help text, or the playbook.
- Add focused tests for game rules.
- Clarify README sections.
- Report confusing turns, unclear wins, or unreadable UI states.
- Add screenshots or short examples of winning patterns.

## Development Setup

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python nxs_go.py
```

## Design Rule

Connection is life.

Isolation is defeat.

New features should preserve that thesis.

## Before Opening a Pull Request

- Run `python -m unittest discover -s tests`.
- Keep changes focused.
- Explain how the change improves player clarity, reliability, or open-source readiness.
- Avoid adding new mechanics until v0.1-A onboarding and playtest clarity are stable.

