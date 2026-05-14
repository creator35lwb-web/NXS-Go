# MACP v2.2 Protocol: XV <-> G0 Collaboration

**Project:** NXS-Go  
**Ecosystem:** YSenseAI FLYWHEEL TEAM  
**Protocol owner:** G0  
**Applies to:** XV (Perplexity CIO), G0, future external AI analysis agents  
**Status:** Active  
**Updated:** 2026-05-14

---

## Current Project State

NXS-Go is in **v0.1-A Clarity Playtest / Stabilization** with an early **v0.2 AI Arena** already available.

The current executable rule is:

> No feature expansion until the base loop can teach itself.

The base loop means:

- SYNCH legality is clear.
- ROUTE direction feels intentional.
- PULSE explains pressure and capture.
- Isolation explains why branches go dark.
- Win/loss and horizon scoring are understandable.
- Session history helps a player review what happened.

AI agents are currently **stress testers**, not the primary audience. Human clarity remains the release gate.

---

## Role Boundaries

### Gem

Owns design meaning and Source-of-Truth interpretation.

### G

Owns roadmap, public release discipline, and strategic priority.

### G0

Owns executable safety:

- implementation scope
- test coverage
- player clarity
- local-first stability
- public/private boundary
- final acceptance of code changes

### XV

Owns intelligence and counter-intelligence:

- benchmark analysis
- competitive landscape research
- evidence review
- documentation integrity
- strategic challenge
- hypothesis proposals

XV should be direct when results are weak, but XV does not override G0 on implementation safety or G on roadmap priority.

---

## XV Default Write Lane

XV may write or propose changes in:

- `.macp/handoffs/`
- `.macp/agents/xv-perplexity.json`
- `.macp/projects/xv-perplexity/`
- `.macp/protocols/`
- `docs/AI_BENCHMARKS.md`

XV may also propose changes to:

- `docs/AI_ARENA.md`
- `docs/HUMAN_PLAYTEST.md`
- `ROADMAP.md`
- `README.md`

For proposed changes outside the default write lane, XV must provide a handoff first.

---

## Code Change Protocol

XV must not directly modify gameplay or agent code unless Alton or G0 explicitly assigns the implementation.

Code files requiring G0 acceptance include:

- `nxs_go.py`
- `nxs_go_ai.py`
- `scripts/benchmark_agents.py`
- `tests/`

Before a code change, XV must provide:

- objective
- hypothesis
- files proposed for change
- expected behavior
- test command
- rollback risk
- whether the change affects human play, AI Arena, or both

G0 then decides whether to:

- accept and implement
- ask XV for more evidence
- defer to human playtest
- reject because it expands scope too early

---

## Current "Do" List

XV should currently focus on:

- verifying benchmark claims
- separating evidence from interpretation
- documenting turn-order asymmetry
- comparing `default` and `contested_lanes` benchmark usefulness
- identifying unclear rule explanations from a player perspective
- producing handoffs that G0 can act on

G0 should currently focus on:

- hardening SYNCH, ROUTE, PULSE, isolation, and horizon scoring
- keeping human and AI rule behavior aligned
- adding regression tests for discovered risks
- preserving local-first playability
- preparing controlled human playtest infrastructure

---

## Current "Do Not" List

Do not add yet:

- Signal Amplify
- Noise Ghost Node
- hidden information mechanics
- online multiplayer
- neural/self-play training
- LLM-agent automation beyond legal-action/readability planning
- broad UI polish that does not improve rule clarity

Do not make `contested_lanes` the default benchmark map until G0/G accept the benchmark policy. It is currently a strong candidate for focused defense probes, not yet the universal default.

Do not treat a two-ply defensive agent as proof of game quality without human playtest evidence.

---

## Benchmark Reporting Standard

Every XV benchmark handoff must include:

- exact command
- date and local timezone
- branch or commit hash
- changed files, if any
- games and max turns
- map variant
- Signal agent and Noise agent
- winner
- winner reason
- turn-limit count
- average Signal margin
- interpretation
- limitation
- recommended next test

Benchmark claims must distinguish:

- source isolation wins
- horizon scoring wins
- turn-limit leader without winner
- first-player/Signal effect
- second-player/Noise effect

---

## Handoff Format

XV handoffs should use:

```text
Current Objective
Evidence
Interpretation
Recommendation
Implementation Impact
Risks
Requested G0 Decision
```

G0 responses should use:

```text
Current Objective
Design Interpretation
Execution Plan
Implementation Notes
Risks
Next Move
```

---

## Acceptance Rule

A recommendation is not accepted because it is plausible. It is accepted when it makes NXS-Go more:

- playable
- testable
- understandable
- strategically honest
- aligned with "Connection is life. Isolation is defeat."

If a recommendation improves benchmark results but weakens human clarity, G0 must defer or reject it.

