# AI Benchmarks

This document records early baseline-agent findings for NXS-Go.

The benchmark runner is intentionally small:

```powershell
python scripts\benchmark_agents.py --games 5 --max-turns 30
```

For games that hit the turn limit, the runner reports structural score leaders and Signal-vs-Noise margin so a draw-like result still carries evidence.

When the built-in horizon is reached, the runner also reports `winner_reasons` so source-isolation wins can be separated from horizon-scoring wins.

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

## Structural Scoring

Turn-limit games are scored by a lightweight structural evaluator:

- live node advantage
- route advantage
- Source connectivity

The score is not a replacement for winning by Source isolation. It is a diagnostic tool for experiments.

## Structural Scoring Probe

Command:

```powershell
python scripts\benchmark_agents.py --games 3 --max-turns 30
```

BridgeGuard-specific score summary:

| Matchup | Winner result | Score leader | Average Signal margin |
| --- | --- | --- | --- |
| Bridge Signal vs Greedy Noise | 3/3 reached turn limit | Noise 3/3 | -10.8 |
| Greedy Signal vs Bridge Noise | 3/3 reached turn limit | Signal 3/3 | 9.2 |
| Bridge Signal vs Guard Noise | 3/3 reached turn limit | Noise 3/3 | -27.2 |
| Guard Signal vs Bridge Noise | 3/3 reached turn limit | Signal 3/3 | 27.2 |

Updated interpretation:

- BridgeGuard delays greedy isolation but appears structurally behind after 30 turns.
- The defense is not yet strong enough; it is buying time, not reversing pressure.
- The next useful hypothesis is a **CounterRoute** defender that actively routes out of threatened bridges instead of only reinforcing topology.

## Horizon Scoring Probe

Command:

```powershell
python scripts\benchmark_agents.py --games 2 --max-turns 60
```

Horizon scoring result summary:

| Matchup | Winners | Winner reason | Average Signal margin |
| --- | --- | --- | --- |
| Random Signal vs Greedy Noise | Noise 2/2 | source isolation | -27.6 |
| Greedy Signal vs Random Noise | Signal 2/2 | source isolation | 35.4 |
| Guard Signal vs Greedy Noise | Noise 2/2 | source isolation | -8.0 |
| Greedy Signal vs Guard Noise | Signal 2/2 | source isolation | 10.0 |
| Random Signal vs Guard Noise | Noise 2/2 | horizon scoring | -22.2 |
| Guard Signal vs Random Noise | Signal 2/2 | horizon scoring | 22.2 |
| Bridge Signal vs Greedy Noise | Noise 2/2 | horizon scoring | -10.8 |
| Greedy Signal vs Bridge Noise | Signal 2/2 | horizon scoring | 9.2 |

Interpretation:

- Horizon Scoring successfully converts unresolved games into decisions.
- Greedy still beats BridgeGuard structurally at the horizon.
- The next defensive hypothesis remains CounterRoute: the defender must actively route pressure away from weak bridges.
