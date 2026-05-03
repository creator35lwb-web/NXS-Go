from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass
from typing import Any, Protocol

from nxs_go import (
    ACTION_PULSE,
    ACTION_ROUTE,
    ACTION_SYNCH,
    CONNECTION_RADIUS,
    HEIGHT,
    MIN_NODE_SPACING,
    PLAYER_NOISE,
    PLAYER_SIGNAL,
    PLAYERS,
    WIDTH,
    Game,
    distance,
    other_player,
)


Action = dict[str, Any]


@dataclass(frozen=True)
class StepResult:
    observation: dict[str, Any]
    reward: float
    done: bool
    info: dict[str, Any]


class Agent(Protocol):
    name: str

    def choose_action(self, env: "NXSGoEnv") -> Action:
        ...


class NXSGoEnv:
    """Deterministic agent-facing wrapper around the current NXS-Go rule engine."""

    def __init__(self, synch_angles: int = 8, max_synch_actions: int = 24) -> None:
        self.synch_angles = synch_angles
        self.max_synch_actions = max_synch_actions
        self.game = Game()

    def reset(self) -> dict[str, Any]:
        self.game = Game()
        self.game.show_help = False
        return self.observation()

    def clone(self) -> "NXSGoEnv":
        cloned = NXSGoEnv(self.synch_angles, self.max_synch_actions)
        cloned.game = copy.deepcopy(self.game)
        return cloned

    def observation(self) -> dict[str, Any]:
        return {
            "current_player": self.game.current_player,
            "winner": self.game.winner,
            "nodes": [
                {
                    "id": node.id,
                    "x": round(node.x, 2),
                    "y": round(node.y, 2),
                    "owner": node.owner,
                    "is_source": node.is_source,
                    "active": node.active,
                }
                for node in self.game.nodes
            ],
            "edges": [
                {
                    "a": edge.a,
                    "b": edge.b,
                    "route_owner": edge.route_owner,
                    "from_id": edge.from_id,
                    "to_id": edge.to_id,
                }
                for edge in self.game.edges
            ],
            "stats": {owner: self.game.player_stats(owner) for owner in PLAYERS},
            "evaluation": self.evaluate_position(),
        }

    def legal_actions(self) -> list[Action]:
        if self.game.winner:
            return []

        player = self.game.current_player
        actions: list[Action] = []
        actions.extend(self._legal_synch_actions(player))
        actions.extend(self._legal_route_actions(player))
        actions.append({"type": ACTION_PULSE})
        return actions

    def step(self, action: Action) -> StepResult:
        if self.game.winner:
            return StepResult(self.observation(), 0.0, True, {"error": "game_complete"})

        actor = self.game.current_player
        before = self._score(actor)
        kind = action.get("type")
        info: dict[str, Any] = {"actor": actor, "action": action}

        if kind == ACTION_SYNCH:
            self.game.synch(float(action["x"]), float(action["y"]))
        elif kind == ACTION_ROUTE:
            edge = self._edge_by_key(int(action["a"]), int(action["b"]))
            if edge is None:
                info["error"] = "invalid_edge"
            else:
                edge.route_owner = actor
                edge.from_id = int(action["from_id"])
                edge.to_id = int(action["to_id"])
                self.game.add_event(
                    f"{actor} AI ROUTE {edge.from_id}->{edge.to_id}.",
                    "Agent selected a legal route action through the formal AI arena.",
                )
                self.game.after_action()
        elif kind == ACTION_PULSE:
            self.game.pulse()
        else:
            info["error"] = "unknown_action"

        after = self._score(actor)
        done = self.game.winner is not None
        reward = self._terminal_reward(actor) if done else after - before
        return StepResult(self.observation(), reward, done, info)

    def _legal_synch_actions(self, player: str) -> list[Action]:
        candidates: list[Action] = []
        seen: set[tuple[int, int]] = set()
        owned = [node for node in self.game.active_nodes() if node.owner == player]

        for node in owned:
            for idx in range(self.synch_angles):
                angle = (2 * math.pi * idx) / self.synch_angles
                x = node.x + (CONNECTION_RADIUS - 18) * math.cos(angle)
                y = node.y + (CONNECTION_RADIUS - 18) * math.sin(angle)
                x = max(MIN_NODE_SPACING, min(WIDTH - MIN_NODE_SPACING, x))
                y = max(80, min(HEIGHT - MIN_NODE_SPACING, y))
                key = (round(x), round(y))
                if key in seen:
                    continue
                ok, _ = self.game.valid_synch_position(x, y, player)
                if ok:
                    seen.add(key)
                    candidates.append({"type": ACTION_SYNCH, "x": round(x, 2), "y": round(y, 2)})

        opponent_source = self.game.source_for(other_player(player))
        if opponent_source is not None:
            candidates.sort(
                key=lambda action: distance((action["x"], action["y"]), opponent_source.pos)
            )
        return candidates[: self.max_synch_actions]

    def _legal_route_actions(self, player: str) -> list[Action]:
        actions: list[Action] = []
        for edge in self.game.edges:
            a_node = self.game.node_by_id(edge.a)
            b_node = self.game.node_by_id(edge.b)
            if a_node.owner == player:
                actions.append(
                    {
                        "type": ACTION_ROUTE,
                        "a": edge.a,
                        "b": edge.b,
                        "from_id": edge.a,
                        "to_id": edge.b,
                    }
                )
            if b_node.owner == player:
                actions.append(
                    {
                        "type": ACTION_ROUTE,
                        "a": edge.a,
                        "b": edge.b,
                        "from_id": edge.b,
                        "to_id": edge.a,
                    }
                )
        return actions

    def _edge_by_key(self, a: int, b: int):
        target = tuple(sorted((a, b)))
        for edge in self.game.edges:
            if tuple(sorted((edge.a, edge.b))) == target:
                return edge
        return None

    def _score(self, player: str) -> float:
        return self.evaluate_player(player)

    def evaluate_player(self, player: str) -> float:
        opponent = other_player(player)
        own = self.game.player_stats(player)
        enemy = self.game.player_stats(opponent)
        return (
            float(own["live_nodes"])
            - float(enemy["live_nodes"])
            + 0.4 * (float(own["routes"]) - float(enemy["routes"]))
            + (2.0 if own["source_connected"] else -4.0)
            - (2.0 if enemy["source_connected"] else -4.0)
        )

    def evaluate_position(self) -> dict[str, Any]:
        scores = {owner: round(self.evaluate_player(owner), 2) for owner in PLAYERS}
        margin = round(scores[PLAYER_SIGNAL] - scores[PLAYER_NOISE], 2)
        if margin > 0:
            leader = PLAYER_SIGNAL
        elif margin < 0:
            leader = PLAYER_NOISE
        else:
            leader = "Even"
        return {
            "scores": scores,
            "leader": leader,
            "margin": margin,
        }

    def _terminal_reward(self, player: str) -> float:
        if self.game.winner == player:
            return 100.0
        if self.game.winner == "No one":
            return 0.0
        return -100.0


class RandomAgent:
    name = "random"

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    def choose_action(self, env: NXSGoEnv) -> Action:
        actions = env.legal_actions()
        if not actions:
            return {"type": ACTION_PULSE}
        return self.rng.choice(actions)


class GreedyIsolationAgent:
    name = "greedy_isolation"

    def __init__(self, max_evaluated_actions: int = 80) -> None:
        self.max_evaluated_actions = max_evaluated_actions

    def choose_action(self, env: NXSGoEnv) -> Action:
        actions = self._candidate_actions(env)
        if not actions:
            return {"type": ACTION_PULSE}

        actor = env.game.current_player
        best_action = actions[0]
        best_score = float("-inf")
        for action in actions:
            trial = env.clone()
            result = trial.step(action)
            score = result.reward + self._bridge_pressure_bonus(trial, actor)
            if score > best_score:
                best_score = score
                best_action = action
        return best_action

    def _candidate_actions(self, env: NXSGoEnv) -> list[Action]:
        actions = env.legal_actions()
        opponent_source = env.game.source_for(other_player(env.game.current_player))

        def priority(action: Action) -> tuple[int, float]:
            if action["type"] == ACTION_PULSE:
                return (0, 0.0)
            if action["type"] == ACTION_ROUTE:
                target = env.game.node_by_id(action["to_id"])
                if target.owner == other_player(env.game.current_player):
                    return (1, 0.0 if target.is_source else 1.0)
                return (2, 0.0)
            if opponent_source is not None:
                return (3, distance((action["x"], action["y"]), opponent_source.pos))
            return (3, 0.0)

        return sorted(actions, key=priority)[: self.max_evaluated_actions]

    def _bridge_pressure_bonus(self, env: NXSGoEnv, actor: str) -> float:
        opponent = other_player(actor)
        bonus = 0.0
        for edge in env.game.edges:
            if edge.route_owner != actor or edge.to_id is None:
                continue
            target = env.game.node_by_id(edge.to_id)
            if target.owner == opponent:
                own_neighbors = [
                    env.game.node_by_id(candidate.other(target.id))
                    for candidate in env.game.edges
                    if candidate.connects(target.id)
                ]
                if sum(1 for node in own_neighbors if node.owner == opponent) <= 1:
                    bonus += 0.5
        return bonus


class SourceGuardAgent:
    name = "source_guard"

    def __init__(self, fallback: GreedyIsolationAgent | None = None) -> None:
        self.fallback = fallback or GreedyIsolationAgent(max_evaluated_actions=40)

    def choose_action(self, env: NXSGoEnv) -> Action:
        actions = env.legal_actions()
        synch_actions = [action for action in actions if action["type"] == ACTION_SYNCH]
        if synch_actions:
            source = env.game.source_for(env.game.current_player)
            if source is not None:
                return min(
                    synch_actions,
                    key=lambda action: distance((action["x"], action["y"]), source.pos),
                )
        return self.fallback.choose_action(env)


class BridgeGuardAgent:
    name = "bridge_guard"

    def __init__(self, max_evaluated_actions: int = 80) -> None:
        self.max_evaluated_actions = max_evaluated_actions

    def choose_action(self, env: NXSGoEnv) -> Action:
        actions = self._candidate_actions(env)
        if not actions:
            return {"type": ACTION_PULSE}

        actor = env.game.current_player
        best_action = actions[0]
        best_score = float("-inf")
        for action in actions:
            trial = env.clone()
            result = trial.step(action)
            score = result.reward + self._defense_score(trial, actor)
            if score > best_score:
                best_score = score
                best_action = action
        return best_action

    def _candidate_actions(self, env: NXSGoEnv) -> list[Action]:
        actions = env.legal_actions()
        actor = env.game.current_player
        critical_nodes = self._critical_owned_node_ids(env, actor)

        def priority(action: Action) -> tuple[int, float]:
            if action["type"] == ACTION_PULSE:
                return (3, 0.0)
            if action["type"] == ACTION_ROUTE:
                if action["from_id"] in critical_nodes or action["to_id"] in critical_nodes:
                    return (0, 0.0)
                return (2, 0.0)
            if critical_nodes:
                x = float(action["x"])
                y = float(action["y"])
                nearest = min(
                    distance((x, y), env.game.node_by_id(node_id).pos)
                    for node_id in critical_nodes
                )
                return (1, nearest)
            return (1, 0.0)

        return sorted(actions, key=priority)[: self.max_evaluated_actions]

    def _defense_score(self, env: NXSGoEnv, actor: str) -> float:
        game = env.game
        source = game.source_for(actor)
        if source is None:
            return -50.0

        connected = game.connected_owned_ids(source.id, actor)
        critical_nodes = self._critical_owned_node_ids(env, actor)
        pressured_nodes = self._pressured_owned_node_ids(env, actor)
        stats = game.player_stats(actor)

        return (
            2.0 * len(connected)
            + 1.2 * float(stats["routes"])
            - 2.4 * len(critical_nodes)
            - 3.0 * len(pressured_nodes)
        )

    def _critical_owned_node_ids(self, env: NXSGoEnv, actor: str) -> set[int]:
        game = env.game
        source = game.source_for(actor)
        if source is None:
            return set()

        owned = [
            node
            for node in game.active_nodes()
            if node.owner == actor and not node.is_source
        ]
        critical: set[int] = set()
        baseline = game.connected_owned_ids(source.id, actor)

        for node in owned:
            original_active = node.active
            node.active = False
            game.rebuild_edges()
            reduced = game.connected_owned_ids(source.id, actor)
            if len(reduced) < len(baseline) - 1:
                critical.add(node.id)
            node.active = original_active
            game.rebuild_edges()

        return critical

    def _pressured_owned_node_ids(self, env: NXSGoEnv, actor: str) -> set[int]:
        opponent = other_player(actor)
        pressured: set[int] = set()
        for node in env.game.active_nodes():
            if node.owner != actor:
                continue
            incoming = sum(
                1
                for edge in env.game.edges
                if edge.route_owner == opponent and edge.to_id == node.id
            )
            outgoing = sum(
                1
                for edge in env.game.edges
                if edge.route_owner == actor and edge.from_id == node.id
            )
            defense = outgoing + (2 if node.is_source else 0)
            if incoming >= defense:
                pressured.add(node.id)
        return pressured


def play_match(
    signal_agent: Agent,
    noise_agent: Agent,
    max_turns: int = 120,
    env: NXSGoEnv | None = None,
) -> dict[str, Any]:
    arena = env or NXSGoEnv()
    arena.reset()
    agents = {PLAYER_SIGNAL: signal_agent, PLAYER_NOISE: noise_agent}
    turns = 0

    while not arena.game.winner and turns < max_turns:
        actor = arena.game.current_player
        action = agents[actor].choose_action(arena)
        arena.step(action)
        turns += 1

    return {
        "winner": arena.game.winner,
        "turns": turns,
        "turn_limit_reached": arena.game.winner is None and turns >= max_turns,
        "stats": {owner: arena.game.player_stats(owner) for owner in PLAYERS},
        "evaluation": arena.evaluate_position(),
        "history": list(arena.game.history),
    }
