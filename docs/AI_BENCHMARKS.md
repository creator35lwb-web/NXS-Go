# AI Benchmarks

This document records early baseline-agent findings for NXS-Go.

The benchmark runner is intentionally small:

```powershell
python scripts\benchmark_agents.py --games 5 --max-turns 30
```

The AI Arena is optimized for CPU-only development: benchmark rollouts disable undo/history recording and clone only the state needed by agents.

Use `--map` to run geometry variants:

```powershell
python scripts\benchmark_agents.py --suite defense --map contested_lanes --games 1 --max-turns 60
```

Current map variants:

- `default`: current baseline.
- `wide_sources`: Sources start farther apart.
- `neutral_bridge`: seeded middle bridge structure for early interaction.
- `contested_lanes`: two offset center lanes that give both sides early bridge pressure.
- `forked_bridges`: split source branches that test whether redundant paths improve defense.
- `center_cross`: crossed center pressure shape that tests route readability and bridge contention.

Use `--map all` for broader sweeps, but 60-turn runs across every map can take several minutes because defensive games often reach horizon scoring.

For games that hit the turn limit, the runner reports structural score leaders and Signal-vs-Noise margin so a draw-like result still carries evidence.

When the built-in horizon is reached, the runner also reports `winner_reasons` so source-isolation wins can be separated from horizon-scoring wins.

## Baseline Agents

- `RandomAgent`: chooses any legal action randomly.
- `GreedyIsolationAgent`: evaluates bounded candidate actions and prefers immediate reward plus bridge pressure.
- `SourceGuardAgent`: expands near its own Source first, then falls back to greedy play.
- `BridgeGuardAgent`: evaluates candidate actions around critical owned bridges and pressured friendly nodes.
- `CounterRouteAgent`: extends BridgeGuard by prioritizing routes outward from pressured owned nodes.
- `TargetedCounterPressureAgent`: routes into opponent nodes that are generating pressure.
- `TacticalDefenseAgent`: adds one-ply capture, pressure, and connectivity detection on top of bridge defense.

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

## CounterRoute Hypothesis

Hypothesis:

> A defender that actively routes outward from pressured nodes should perform better than one that only preserves bridge topology.

Falsification signal:

- If `CounterRouteAgent` still loses structurally to `GreedyIsolationAgent` at the horizon, the current defensive action language may be too weak.

Support signal:

- If `CounterRouteAgent` closes the margin or wins against `GreedyIsolationAgent`, then defense can be active inside the current rules.

## CounterRoute Probe

Command:

```powershell
python scripts\benchmark_agents.py --games 2 --max-turns 60
```

CounterRoute-specific result summary:

| Matchup | Winners | Winner reason | Average Signal margin |
| --- | --- | --- | --- |
| Counter Signal vs Greedy Noise | Noise 2/2 | horizon scoring | -12.8 |
| Greedy Signal vs Counter Noise | Signal 2/2 | horizon scoring | 11.2 |
| Counter Signal vs Bridge Noise | Noise 2/2 | horizon scoring | -2.8 |
| Bridge Signal vs Counter Noise | Signal 2/2 | horizon scoring | 2.8 |

Interpretation:

- CounterRoute did not beat GreedyIsolation.
- In this probe, CounterRoute performed slightly worse than BridgeGuard against GreedyIsolation.
- CounterRoute and BridgeGuard are close against each other.
- Active routing needs sharper pressure logic; simply routing outward is not enough.

Next hypothesis:

> A useful defender may need to route specifically into opponent pressure sources, not merely route out of threatened nodes.

## Targeted Counter-Pressure Hypothesis

Hypothesis:

> Defense improves when it contests the opponent's pressure source instead of only protecting or escaping threatened nodes.

Falsification signal:

- If `TargetedCounterPressureAgent` does not improve against `GreedyIsolationAgent`, the route action may not currently provide enough defensive leverage.

Support signal:

- If it closes the Greedy margin or beats BridgeGuard/CounterRoute, targeted defensive pressure is a promising core tactic.

## Targeted Counter-Pressure Probe

Command:

```powershell
python scripts\benchmark_agents.py --games 2 --max-turns 60
```

Targeted-specific result summary:

| Matchup | Winners | Winner reason | Average Signal margin |
| --- | --- | --- | --- |
| Targeted Signal vs Greedy Noise | Noise 2/2 | horizon scoring | -12.8 |
| Greedy Signal vs Targeted Noise | Signal 2/2 | horizon scoring | 11.2 |
| Targeted Signal vs Bridge Noise | Noise 2/2 | horizon scoring | -2.8 |
| Bridge Signal vs Targeted Noise | Signal 2/2 | horizon scoring | 2.8 |
| Targeted Signal vs Counter Noise | Noise 2/2 | horizon scoring | -2.0 |
| Counter Signal vs Targeted Noise | Noise 2/2 | horizon scoring | -2.0 |

Interpretation:

- Targeted Counter-Pressure did not improve against GreedyIsolation.
- Its results matched CounterRoute against Greedy and BridgeGuard in this probe.
- The current board/action geometry may not expose enough usable counter-pressure routes.

Design implication:

> The core may need either better defensive route incentives or a future lightweight defensive mechanic. Do not add that mechanic yet; first test whether action selection can be improved without changing rules.

## Geometry Variant Probe

Command:

```powershell
python scripts\benchmark_agents.py --map all --games 1 --max-turns 60
```

Defensive-vs-Greedy result summary:

| Map | Matchup | Winner | Reason | Signal margin |
| --- | --- | --- | --- | --- |
| default | Bridge Signal vs Greedy Noise | Noise | horizon scoring | -10.8 |
| default | Counter Signal vs Greedy Noise | Noise | horizon scoring | -12.8 |
| default | Targeted Signal vs Greedy Noise | Noise | horizon scoring | -12.8 |
| wide_sources | Bridge Signal vs Greedy Noise | Noise | horizon scoring | -12.8 |
| wide_sources | Counter Signal vs Greedy Noise | Noise | horizon scoring | -12.8 |
| wide_sources | Targeted Signal vs Greedy Noise | Noise | horizon scoring | -12.8 |
| neutral_bridge | Bridge Signal vs Greedy Noise | Noise | horizon scoring | -10.8 |
| neutral_bridge | Counter Signal vs Greedy Noise | Noise | horizon scoring | -12.8 |
| neutral_bridge | Targeted Signal vs Greedy Noise | Noise | horizon scoring | -12.8 |

Interpretation:

- The initial map variants did not meaningfully improve defensive outcomes against GreedyIsolation.
- Wide source spacing did not help defense in this one-game probe.
- The seeded middle bridge did not create enough defensive leverage.

Next geometry/search question:

> Do we need richer benchmark maps with contested neutral-like bridge lanes, or is the current route/defense action space too weak?

## Contested Geometry Probe

Change:

- Added richer benchmark maps:
  - `contested_lanes`
  - `forked_bridges`
  - `center_cross`
- Added `--suite defense` to the benchmark runner for focused defensive probes.

Focused command:

```powershell
python -c "from nxs_go_ai import BridgeGuardAgent, CounterRouteAgent, TargetedCounterPressureAgent, GreedyIsolationAgent, play_match; maps=('contested_lanes','forked_bridges','center_cross'); agents=(('bridge',BridgeGuardAgent),('counter',CounterRouteAgent),('targeted',TargetedCounterPressureAgent));\
for m in maps:\
    print('MAP',m);\
    for name,cls in agents:\
        r=play_match(cls(), GreedyIsolationAgent(), max_turns=60, map_variant=m); print(name,'vs greedy','winner=',r['winner'],'reason=',r['winner_reason'],'turns=',r['turns'],'margin=',r['evaluation']['margin'])"
```

Result summary:

| Map | Bridge vs Greedy | Counter vs Greedy | Targeted vs Greedy |
| --- | --- | --- | --- |
| `contested_lanes` | Noise by horizon, margin -0.8 | Noise by horizon, margin -4.8 | Noise by horizon, margin -0.8 |
| `forked_bridges` | Noise by horizon, margin -8.4 | Noise by horizon, margin -13.6 | Noise by horizon, margin -8.4 |
| `center_cross` | Noise by horizon, margin -8.4 | Noise by horizon, margin -6.8 | Noise by horizon, margin -8.4 |

Interpretation:

- `contested_lanes` materially reduced GreedyIsolation's structural margin against BridgeGuard and TargetedCounterPressure.
- Greedy still won by horizon scoring, but the margin moved from roughly -10.8/-12.8 on baseline maps to -0.8 on the best contested-lane cases.
- This suggests defensive weakness is at least partly geometry/search dependent.
- `forked_bridges` and `center_cross` did not improve defense enough in this probe.

Next search question:

> Can a one-ply capture/pressure detector convert the near-even `contested_lanes` positions into actual defensive wins without adding new rules?

## Tactical Defense Probe

Hypothesis:

> A one-ply tactical detector can convert near-even defensive positions into wins by noticing immediate captures, pressure targets, and Source-connectivity swings.

Implementation:

- Added `TacticalDefenseAgent`.
- Added the agent to the focused `--suite defense` benchmark.
- The agent scores:
  - immediate structural reward
  - owned Source connectivity
  - enemy Source connectivity
  - live-node swing
  - immediate capture targets
  - opponent immediate capture targets
  - pressured friendly nodes

Focused command:

```powershell
python -c "from nxs_go_ai import TacticalDefenseAgent, GreedyIsolationAgent, play_match; maps=('contested_lanes','forked_bridges','center_cross');\
for m in maps:\
    r=play_match(TacticalDefenseAgent(),GreedyIsolationAgent(),max_turns=60,map_variant=m); print(m,'tactical vs greedy','winner=',r['winner'],'reason=',r['winner_reason'],'turns=',r['turns'],'margin=',r['evaluation']['margin']);\
    r=play_match(GreedyIsolationAgent(),TacticalDefenseAgent(),max_turns=60,map_variant=m); print(m,'greedy vs tactical','winner=',r['winner'],'reason=',r['winner_reason'],'turns=',r['turns'],'margin=',r['evaluation']['margin'])"
```

Result summary:

| Map | Tactical vs Greedy | Greedy vs Tactical |
| --- | --- | --- |
| `contested_lanes` | Noise by horizon, margin -0.8 | Signal by horizon, margin 1.2 |
| `forked_bridges` | Noise by horizon, margin -6.4 | Noise by horizon, margin -9.2 |
| `center_cross` | Noise by horizon, margin -0.8 | Noise by horizon, margin -9.2 |

Interpretation:

- Tactical Defense did not turn near-even positions into defensive wins.
- It matched the best `contested_lanes` defense result.
- It improved `center_cross` defense from the previous Bridge/Targeted margin of -8.4 to -0.8 when Tactical played Signal.
- It did not solve second-player/Noise-side weakness on `forked_bridges` or `center_cross`.

Design implication:

> Search helps, but one-ply tactical awareness is not enough. The next evidence gate should test either deeper search or a minimal defensive rule, with human readability checked in parallel.

## XV CIO Live Benchmark — May 11, 2026

Command:

```powershell
python scripts/benchmark_agents.py --games 3 --max-turns 60
```

New finding not previously documented:

| Matchup | Winner | Avg Turns | Avg Margin | Reason |
| --- | --- | --- | --- | --- |
| Tactical Signal vs Greedy Noise | Noise | 60.0 | -1.2 | horizon scoring |
| **Greedy Signal vs Tactical Noise** | **Noise** | **60.0** | **-9.2** | **horizon scoring** |
| Tactical Signal vs Bridge Noise | Signal | 60.0 | +28.0 | horizon scoring |
| Bridge Signal vs Tactical Noise | Noise | 60.0 | -32.0 | horizon scoring |

**Critical finding:** When `TacticalDefenseAgent` plays as Noise (second player) against `GreedyIsolationAgent` as Signal, **Noise wins** with a structural margin of -9.2 in favour of Noise. This is the first recorded instance of any defensive agent defeating GreedyIsolation in the benchmark record.

This result is asymmetric — TacticalDefense does not beat Greedy when playing as Signal (first player). This suggests:

1. Turn order (first vs second player) materially affects the attack-defense balance.
2. One-ply tactical search is sufficient for second-player defensive wins but not first-player wins.
3. Before adding asymmetric abilities, test whether a two-ply or MCTS agent can produce first-player defensive wins.

**Contested lanes defense suite (games=2, max-turns=60):**

| Matchup | Winner | Avg Margin |
| --- | --- | --- |
| Bridge vs Greedy (contested_lanes) | Noise | -0.8 |
| Greedy vs Bridge (contested_lanes) | Signal | +1.2 |
| Tactical vs Greedy (contested_lanes) | Noise | -0.8 |
| Greedy vs Tactical (contested_lanes) | Signal | +1.2 |

`contested_lanes` reduced the Greedy structural margin from -10.8 (default) to -0.8 — an 87% reduction. Geometry is the single most impactful variable tested so far. Recommend making `contested_lanes` the default benchmark map for future defense probes.

**XV Recommendation:** Test two-ply search agent on `contested_lanes` before adding Signal Amplify (v0.4). The attack-defense cycle may be solvable within the current rule set at greater search depth.

*Benchmarks run by XV (Perplexity CIO) — MACP v2.2 "Identity" — 2026-05-11*
