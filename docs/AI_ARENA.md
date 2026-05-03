# AI Arena

NXS-Go now includes a small formal environment for bots, agents, and future self-play experiments.

The arena is intentionally simple. It wraps the same `Game` rule engine used by the Pygame prototype instead of creating a second rule implementation.

## Interface

`nxs_go_ai.py` exposes:

- `NXSGoEnv`
- `legal_actions()`
- `step(action)`
- `observation()`
- `reset()`
- `RandomAgent`
- `GreedyIsolationAgent`
- `SourceGuardAgent`
- `play_match(...)`

## Example

```python
from nxs_go_ai import GreedyIsolationAgent, RandomAgent, play_match

result = play_match(RandomAgent(seed=1), GreedyIsolationAgent(), max_turns=80)
print(result["winner"])
print(result["stats"])
```

Run the baseline benchmark:

```powershell
python scripts\benchmark_agents.py --games 5 --max-turns 30
```

See `docs/AI_BENCHMARKS.md` for early results.

## Why This Exists

The long-term goal is to make NXS-Go measurable by intelligent play, not only human intuition.

Useful questions:

- Can random play discover meaningful structure?
- Can a greedy bridge/isolation agent dominate too easily?
- Does source defense beat pressure?
- Are games ending by strategic isolation or by accidental collapse?
- Does adding future mechanics increase depth or only complexity?

## Open-Source Model Target

Gemma-family open-source models are a good first LLM-agent target because they are accessible, inspectable, and aligned with the local-first direction of the project.

The first Gemma-style experiment should be conservative:

1. Read the public README and playbook.
2. Inspect `observation()`.
3. Choose one legal action from `legal_actions()`.
4. Explain the reason in plain language.
5. Compare against baseline bots.

Do not optimize for a strong AI immediately. First prove that agents can understand the action space and produce legal moves consistently.
