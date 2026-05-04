from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nxs_go import PLAYER_NOISE, PLAYER_SIGNAL
from nxs_go_ai import (
    BridgeGuardAgent,
    CounterRouteAgent,
    GreedyIsolationAgent,
    MAP_VARIANTS,
    RandomAgent,
    SourceGuardAgent,
    TargetedCounterPressureAgent,
    TacticalDefenseAgent,
    play_match,
)


def build_agent(name: str, seed: int):
    if name == "random":
        return RandomAgent(seed=seed)
    if name == "greedy":
        return GreedyIsolationAgent()
    if name == "guard":
        return SourceGuardAgent()
    if name == "bridge":
        return BridgeGuardAgent()
    if name == "counter":
        return CounterRouteAgent()
    if name == "targeted":
        return TargetedCounterPressureAgent()
    if name == "tactical":
        return TacticalDefenseAgent()
    raise ValueError(f"unknown agent: {name}")


def run_series(
    signal_name: str,
    noise_name: str,
    games: int,
    max_turns: int,
    map_variant: str,
) -> dict[str, object]:
    winners: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    leaders: Counter[str] = Counter()
    total_turns = 0
    turn_limits = 0
    total_margin = 0.0

    for idx in range(games):
        result = play_match(
            build_agent(signal_name, seed=idx + 1),
            build_agent(noise_name, seed=10_000 + idx),
            max_turns=max_turns,
            map_variant=map_variant,
        )
        winner = result["winner"] or "TurnLimit"
        winners[winner] += 1
        reasons[str(result["winner_reason"] or "turn_limit")] += 1
        evaluation = result["evaluation"]
        leaders[str(evaluation["leader"])] += 1
        total_margin += float(evaluation["margin"])
        total_turns += int(result["turns"])
        if result["turn_limit_reached"]:
            turn_limits += 1

    return {
        "matchup": f"{signal_name}({PLAYER_SIGNAL}) vs {noise_name}({PLAYER_NOISE})",
        "map": map_variant,
        "games": games,
        "max_turns": max_turns,
        "winners": dict(winners),
        "winner_reasons": dict(reasons),
        "score_leaders": dict(leaders),
        "turn_limits": turn_limits,
        "average_turns": round(total_turns / games, 2),
        "average_signal_margin": round(total_margin / games, 2),
    }


def build_matchups(suite: str) -> list[tuple[str, str]]:
    if suite == "defense":
        return [
            ("bridge", "greedy"),
            ("greedy", "bridge"),
            ("counter", "greedy"),
            ("greedy", "counter"),
            ("targeted", "greedy"),
            ("greedy", "targeted"),
            ("tactical", "greedy"),
            ("greedy", "tactical"),
        ]
    return [
        ("random", "greedy"),
        ("greedy", "random"),
        ("guard", "greedy"),
        ("greedy", "guard"),
        ("random", "guard"),
        ("guard", "random"),
        ("bridge", "greedy"),
        ("greedy", "bridge"),
        ("bridge", "guard"),
        ("guard", "bridge"),
        ("counter", "greedy"),
        ("greedy", "counter"),
        ("counter", "bridge"),
        ("bridge", "counter"),
        ("targeted", "greedy"),
        ("greedy", "targeted"),
        ("targeted", "bridge"),
        ("bridge", "targeted"),
        ("targeted", "counter"),
        ("counter", "targeted"),
        ("tactical", "greedy"),
        ("greedy", "tactical"),
        ("tactical", "bridge"),
        ("bridge", "tactical"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NXS-Go baseline agent benchmarks.")
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--max-turns", type=int, default=40)
    parser.add_argument(
        "--suite",
        choices=("all", "defense"),
        default="all",
        help="Benchmark matchup suite.",
    )
    parser.add_argument(
        "--map",
        choices=MAP_VARIANTS + ("all",),
        default="default",
        help="Benchmark map variant.",
    )
    args = parser.parse_args()

    matchups = build_matchups(args.suite)
    maps = MAP_VARIANTS if args.map == "all" else (args.map,)
    for map_variant in maps:
        for signal_name, noise_name in matchups:
            result = run_series(signal_name, noise_name, args.games, args.max_turns, map_variant)
            print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
