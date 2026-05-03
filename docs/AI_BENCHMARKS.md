# AI Benchmarks

This document records early baseline-agent findings for NXS-Go.

The benchmark runner is intentionally small:

```powershell
python scripts\benchmark_agents.py --games 5 --max-turns 30
```

## Baseline Agents

- `RandomAgent`: chooses any legal action randomly.
- `GreedyIsolationAgent`: evaluates bounded candidate actions and prefers immediate reward plus bridge pressure.
- `SourceGuardAgent`: expands near its own Source first, then falls back to greedy play.
- `BridgeGuardAgent`: evaluates candidate actions around critical owned bridges and pressured friendly nodes.

## First Baseline Run

Command:

```powershell
python scripts\benchmark_agents.py --games 5 --max-turns 30
```

Result summary:

| Matchup | Result |
| --- | --- |
| Random Signal vs Greedy Noise | 5/5 reached turn limit |
| Greedy Signal vs Random Noise | 5/5 reached turn limit |
| Guard Signal vs Greedy Noise | Noise won 5/5, average 28 turns |
| Greedy Signal vs Guard Noise | Signal won 5/5, average 29 turns |
| Random Signal vs Guard Noise | 5/5 reached turn limit |
| Guard Signal vs Random Noise | 5/5 reached turn limit |

## Interpretation

This does not prove the game is solved.

It does show an early pressure signal:

- Source-only expansion is too passive against greedy isolation pressure.
- Random play rarely finishes within 30 turns.
- Greedy pressure can convert advantage, but the current benchmark is still small.

## Next Questions

- Does greedy isolation still dominate at 60-100 turns?
- Does first-player order matter?
- Are wins caused by strategic bridge pressure or by predictable source-guard weakness?
- Does a stronger defensive bot close the gap?
- Do future asymmetric mechanics increase strategic depth or only patch a weak baseline?

## BridgeGuard Hypothesis

Hypothesis:

> If NXS-Go has a healthy core attack-defense cycle, a bridge-aware defender should perform better than passive source guarding against greedy isolation.

Falsification signal:

- If `BridgeGuardAgent` still loses consistently to `GreedyIsolationAgent`, the core may need richer defensive tools, larger topology, or carefully scoped asymmetry.

Support signal:

- If `BridgeGuardAgent` contests or reverses greedy pressure, the current core already contains meaningful tactical depth.

## BridgeGuard Probe

Command:

```powershell
python scripts\benchmark_agents.py --games 3 --max-turns 30
```

BridgeGuard-specific result summary:

| Matchup | Result |
| --- | --- |
| Bridge Signal vs Greedy Noise | 3/3 reached turn limit |
| Greedy Signal vs Bridge Noise | 3/3 reached turn limit |
| Bridge Signal vs Guard Noise | 3/3 reached turn limit |
| Guard Signal vs Bridge Noise | 3/3 reached turn limit |

Early interpretation:

- Bridge-aware defense stopped the greedy isolation agent from producing the quick 28-29 turn wins it found against passive SourceGuard.
- This supports, but does not prove, the attack-defense cycle hypothesis.
- The next probe should extend turn limits and add final-position evaluation so turn-limit games can still be scored meaningfully.
