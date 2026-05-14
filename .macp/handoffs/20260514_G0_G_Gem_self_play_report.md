# MACP v2.2 Handoff: G0 / G / Gem - Human Self-Play Report

**Session type:** human self-play analysis  
**Date:** 2026-05-14  
**Project:** NXS-Go  
**Source artifacts:** `history/nxs_go_history_20260514_230513.md`, local PPTX screenshot report  
**Status:** REVIEWED

---

## Current Objective

Review Alton's fresh self-play report after the completed-game ROUTE guard fix.

The core question:

> Did the game now stop cleanly at horizon, and what does the end state say about clarity, tension, and next execution priorities?

---

## Evidence

Saved history:

- File: `history/nxs_go_history_20260514_230513.md`
- Saved: 2026-05-14T23:05:13
- Turns played: 60/60

Final status:

- Signal: 23 live nodes, 1 route, Source connected
- Noise: 23 live nodes, 0 routes, Source connected

Horizon evaluation:

- Leader: Signal
- Margin: 0.8
- Scores: `{'Signal': 0.4, 'Noise': -0.4}`

Key event sequence:

- Noise captured Signal node 26.
- Signal captured Noise node 41.
- Isolation blackout removed 1 node.
- Later Signal captured node 35.
- No Source was isolated by turn 60.
- Horizon scoring resolved the game at exactly 60/60.

---

## G0 Interpretation

The previous overrun bug is fixed.

The earlier self-play report showed `62/60`, meaning post-completion actions could still advance history. This run shows `60/60`, and the history has one final horizon-scoring event. That confirms the completed-game guard is working for the tested path.

Remaining execution note:

- The UI still allows postgame click attempts and logs `Invalid: Game is already complete.`
- This is technically safe, but the postgame UX can be cleaner later.

Possible future G0 improvement:

- Add a final state overlay or disable action buttons after winner is set.
- Show a clearer final result line in the top bar and history export.
- Consider a "New game" / "Save report" postgame affordance.

No urgent code fix is required from this report.

---

## G Interpretation

This is useful human evidence.

The end state was close:

- Equal live nodes.
- Both Sources connected.
- Signal wins by a small route-based structural margin.

Strategically, this supports the current sequence:

- Continue base-loop clarity testing.
- Do not add Signal Amplify or Noise Ghost Node yet.
- Human play produces meaningful evidence that benchmarks alone do not.

The report also suggests horizon scoring can produce narrow decisions that may feel debatable. G should watch whether humans understand and accept route-based margins.

Strategic question for next playtest:

> Did the winning player feel like they deserved the horizon win, or did it feel like an arbitrary tiebreak?

---

## Gem Interpretation

The game expressed the thesis:

> Connection is life. Isolation is defeat.

Both players preserved Source connectivity. The decisive difference was not territory, but structural signal at horizon.

The strongest design signal is the central contested bridge zone. The screenshot shows both networks pushing into a dense shared middle. That is where emotional pressure lives: one bridge capture can change the network's meaning.

Gem concern:

- Dense late-game clusters may become visually noisy.
- If players cannot read why a horizon margin happened, the emotional meaning weakens.

Gem recommendation:

- Keep improving explanation around pressure, bridge capture, and final structural score.
- Do not add hidden-information mechanics until players can read the visible network confidently.

---

## Decisions

- v0.1-A remains the active context.
- The completed-game overrun issue is resolved for this test.
- No new mechanic should be added from this evidence.
- Horizon scoring clarity is now a watch item.
- Human self-play reports are high-value inputs and should continue.

---

## Pending

- Ask whether the human player understood why Signal won by margin 0.8.
- Add a future issue or task for postgame UX clarity if repeated playtests show confusion.
- Keep the PPTX as local personal evidence unless Alton chooses to publish or commit it.

---

## Recommended Next Move

Run one more controlled self-play or hotseat test with this specific question:

> At horizon, can both players explain who is winning and why before opening the saved history?

