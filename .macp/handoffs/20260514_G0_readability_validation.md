# MACP v2.2 Handoff: G0 - Route/Pulse Readability Validation

**Agent:** G0  
**Session type:** development validation  
**Date:** 2026-05-14  
**Project:** NXS-Go  
**Source artifacts:** `history/nxs_go_history_20260514_234440.md`, local PPTX screenshot report  
**Status:** VALIDATED BY HUMAN PLAYTEST

---

## Current Objective

Resolve Alton's readability concern:

> The network is dense and hard to read. It is hard to decide which edge to route and understand the PULSE effect of the chosen route.

---

## Implementation Completed

G0 added a focused readability pass:

- Route mode now focuses the hovered edge instead of lighting the entire dense network.
- Hovering a route edge shows the expected route direction and target pulse math.
- Pulse mode marks pressured opponent nodes with incoming/defense labels.
- Game completion displays a compact winner overlay with save/reset guidance.
- Added a route-hover render regression test to prevent the crash found after the first patch.

---

## Bug Found And Fixed

The first readability patch introduced a render crash:

- `draw_graph()` used `fonts["small"]` without receiving `fonts`.
- The crash triggered when hovering an edge after a first click.

Fix:

- `draw_game()` now passes `fonts` into `draw_graph()`.
- `draw_graph()` accepts the fonts dictionary.
- Regression test added: route-hover render path does not crash.

Verification:

- `python -m unittest discover -s tests`
- `python -m py_compile nxs_go.py nxs_go_ai.py scripts/benchmark_agents.py`

Current test count: 25 passing tests.

---

## Human Validation

Alton's response after playtest:

> The route select with description is nice. The pulse effect shown is also making clear on decision making on it. The Game complete by announcing which side win is what I want too.

G0 interpretation:

- Route decision clarity improved.
- PULSE consequence clarity improved.
- Game completion clarity improved.
- This is a validated v0.1-A clarity improvement.

---

## Latest Playtest Evidence

Saved history:

- File: `history/nxs_go_history_20260514_234440.md`
- Turns played: 60/60

Final network status:

- Signal: 16 live nodes, 0 routes, Source connected
- Noise: 11 live nodes, 1 route, Source connected

Horizon evaluation:

- Leader: Signal
- Margin: 9.2
- Scores: `{'Signal': 4.6, 'Noise': -4.6}`

Key tactical sequence:

- Noise PULSE captured nodes 4 and 28.
- Signal later captured nodes 19 and 25.
- That Signal PULSE triggered a 4-node isolation blackout.
- Horizon scoring resolved the game at 60/60.

G0 read:

- The latest session produced a clearer tactical story than the previous near-even horizon game.
- The saved history supports the visible game state: Signal won because it created a larger structural collapse before horizon.

---

## G0 Decision

This fix should be committed.

It serves the current active phase:

> v0.1-A Clarity Playtest / Stabilization

It does not expand mechanics. It makes the existing rules more playable and understandable.

---

## Remaining Watch Items

- Late-game graph density is improved but not solved.
- Future work may need route filtering modes or a dedicated pressure preview panel.
- Do not add hidden-information mechanics until visible pressure remains readable in dense boards.

---

## Recommended Next Move

Commit and push:

- route/pulse readability UI changes
- crash regression test
- self-play analysis handoff
- readability validation handoff

