from __future__ import annotations

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
    Edge,
    PLAYER_NOISE,
    PLAYER_SIGNAL,
    PLAYERS,
    WIDTH,
    Game,
    Node,
    distance,
    other_player,
)


Action = dict[str, Any]
MAP_VARIANTS = (
    "default",
    "wide_sources",
    "neutral_bridge",
    "contested_lanes",
    "forked_bridges",
    "center_cross",
)


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

    def __init__(
        self,
        synch_angles: int = 8,
        max_synch_actions: int = 24,
        map_variant: str = "default",
    ) -> None:
        if map_variant not in MAP_VARIANTS:
            raise ValueError(f"unknown map variant: {map_variant}")
        self.synch_angles = synch_angles
        self.max_synch_actions = max_synch_actions
        self.map_variant = map_variant
        self.game = Game()
        self._prepare_game_for_arena()

    def reset(self) -> dict[str, Any]:
        self.game = Game()
        self._prepare_game_for_arena()
        self._apply_map_variant()
        return self.observation()

    def clone(self) -> "NXSGoEnv":
        cloned = NXSGoEnv(self.synch_angles, self.max_synch_actions, self.map_variant)
        cloned.game.nodes = [
            Node(node.id, node.x, node.y, node.owner, node.is_source, node.active)
            for node in self.game.nodes
        ]
        cloned.game.edges = [
            Edge(edge.a, edge.b, edge.route_owner, edge.from_id, edge.to_id)
            for edge in self.game.edges
        ]
        cloned.game.next_node_id = self.game.next_node_id
        cloned.game.current_player = self.game.current_player
        cloned.game.selected_action = self.game.selected_action
        cloned.game.winner = self.game.winner
        cloned.game.winner_reason = self.game.winner_reason
        cloned.game.turn_count = self.game.turn_count
        cloned.game.message = self.game.message
        cloned._prepare_game_for_arena()
        return cloned

    def _prepare_game_for_arena(self) -> None:
        self.game.show_help = False
        self.game.record_undo = False
        self.game.record_history = False
        self.game.undo_stack = []

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
            "map_variant": self.map_variant,
        }

    def _apply_map_variant(self) -> None:
        if self.map_variant == "default":
            return
        if self.map_variant == "wide_sources":
            signal = self.game.source_for(PLAYER_SIGNAL)
            noise = self.game.source_for(PLAYER_NOISE)
            if signal is not None:
                signal.x = 115
            if noise is not None:
                noise.x = WIDTH - 115
            self.game.rebuild_edges()
            return
        if self.map_variant == "neutral_bridge":
            self.game.add_node(390, HEIGHT // 2 - 72, PLAYER_SIGNAL)
            self.game.add_node(560, HEIGHT // 2, PLAYER_SIGNAL)
            self.game.add_node(730, HEIGHT // 2 + 72, PLAYER_NOISE)
            self.game.rebuild_edges()
            return
        if self.map_variant == "contested_lanes":
            self._seed_nodes(
                (
                    (275, HEIGHT // 2 - 74, PLAYER_SIGNAL),
                    (405, HEIGHT // 2 - 76, PLAYER_SIGNAL),
                    (535, HEIGHT // 2 - 52, PLAYER_SIGNAL),
                    (650, HEIGHT // 2 - 18, PLAYER_SIGNAL),
                    (845, HEIGHT // 2 + 74, PLAYER_NOISE),
                    (715, HEIGHT // 2 + 76, PLAYER_NOISE),
                    (585, HEIGHT // 2 + 52, PLAYER_NOISE),
                    (470, HEIGHT // 2 + 18, PLAYER_NOISE),
                )
            )
            return
        if self.map_variant == "forked_bridges":
            self._seed_nodes(
                (
                    (270, HEIGHT // 2 - 84, PLAYER_SIGNAL),
                    (270, HEIGHT // 2 + 84, PLAYER_SIGNAL),
                    (400, HEIGHT // 2 - 24, PLAYER_SIGNAL),
                    (520, HEIGHT // 2 - 24, PLAYER_SIGNAL),
                    (850, HEIGHT // 2 - 84, PLAYER_NOISE),
                    (850, HEIGHT // 2 + 84, PLAYER_NOISE),
                    (720, HEIGHT // 2 + 24, PLAYER_NOISE),
                    (600, HEIGHT // 2 + 24, PLAYER_NOISE),
                )
            )
            return
        if self.map_variant == "center_cross":
            self._seed_nodes(
                (
                    (275, HEIGHT // 2, PLAYER_SIGNAL),
                    (405, HEIGHT // 2, PLAYER_SIGNAL),
                    (520, HEIGHT // 2 - 70, PLAYER_SIGNAL),
                    (520, HEIGHT // 2 + 70, PLAYER_SIGNAL),
                    (845, HEIGHT // 2, PLAYER_NOISE),
                    (715, HEIGHT // 2, PLAYER_NOISE),
                    (600, HEIGHT // 2 - 70, PLAYER_NOISE),
                    (600, HEIGHT // 2 + 70, PLAYER_NOISE),
                )
            )
            return

    def _seed_nodes(self, nodes: tuple[tuple[float, float, str], ...]) -> None:
        for x, y, owner in nodes:
            self.game.add_node(x, y, owner)
        self.game.rebuild_edges()

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
        return self.game.evaluate_player(player)

    def evaluate_position(self) -> dict[str, Any]:
        return self.game.evaluate_position()

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


class CounterRouteAgent(BridgeGuardAgent):
    name = "counter_route"

    def _candidate_actions(self, env: NXSGoEnv) -> list[Action]:
        actions = env.legal_actions()
        actor = env.game.current_player
        pressured_nodes = self._pressured_owned_node_ids(env, actor)
        critical_nodes = self._critical_owned_node_ids(env, actor)

        def priority(action: Action) -> tuple[int, float]:
            if action["type"] == ACTION_ROUTE:
                if action["from_id"] in pressured_nodes:
                    return (0, 0.0)
                if action["from_id"] in critical_nodes or action["to_id"] in critical_nodes:
                    return (1, 0.0)
                return (3, 0.0)
            if action["type"] == ACTION_SYNCH and (pressured_nodes or critical_nodes):
                x = float(action["x"])
                y = float(action["y"])
                targets = pressured_nodes or critical_nodes
                nearest = min(
                    distance((x, y), env.game.node_by_id(node_id).pos)
                    for node_id in targets
                )
                return (2, nearest)
            if action["type"] == ACTION_PULSE:
                return (4, 0.0)
            return (5, 0.0)

        return sorted(actions, key=priority)[: self.max_evaluated_actions]

    def _defense_score(self, env: NXSGoEnv, actor: str) -> float:
        base = super()._defense_score(env, actor)
        pressured_nodes = self._pressured_owned_node_ids(env, actor)
        defensive_routes = 0
        for edge in env.game.edges:
            if edge.route_owner == actor and edge.from_id is not None:
                from_node = env.game.node_by_id(edge.from_id)
                if from_node.owner == actor:
                    defensive_routes += 1
        return base + 1.8 * defensive_routes - 4.0 * len(pressured_nodes)


class TargetedCounterPressureAgent(BridgeGuardAgent):
    name = "targeted_counter_pressure"

    def _candidate_actions(self, env: NXSGoEnv) -> list[Action]:
        actions = env.legal_actions()
        actor = env.game.current_player
        pressure_sources = self._pressure_source_node_ids(env, actor)
        critical_nodes = self._critical_owned_node_ids(env, actor)

        def priority(action: Action) -> tuple[int, float]:
            if action["type"] == ACTION_ROUTE:
                if action["to_id"] in pressure_sources:
                    return (0, 0.0)
                if action["from_id"] in critical_nodes or action["to_id"] in critical_nodes:
                    return (2, 0.0)
                return (3, 0.0)
            if action["type"] == ACTION_SYNCH and pressure_sources:
                x = float(action["x"])
                y = float(action["y"])
                nearest = min(
                    distance((x, y), env.game.node_by_id(node_id).pos)
                    for node_id in pressure_sources
                )
                return (1, nearest)
            if action["type"] == ACTION_PULSE:
                return (4, 0.0)
            return (5, 0.0)

        return sorted(actions, key=priority)[: self.max_evaluated_actions]

    def _defense_score(self, env: NXSGoEnv, actor: str) -> float:
        base = super()._defense_score(env, actor)
        pressure_sources = self._pressure_source_node_ids(env, actor)
        targeted_routes = 0
        for edge in env.game.edges:
            if (
                edge.route_owner == actor
                and edge.to_id is not None
                and edge.to_id in pressure_sources
            ):
                targeted_routes += 1
        return base + 3.2 * targeted_routes - 2.0 * len(pressure_sources)

    def _pressure_source_node_ids(self, env: NXSGoEnv, actor: str) -> set[int]:
        opponent = other_player(actor)
        sources: set[int] = set()
        for edge in env.game.edges:
            if edge.route_owner != opponent or edge.from_id is None or edge.to_id is None:
                continue
            target = env.game.node_by_id(edge.to_id)
            if target.owner == actor:
                sources.add(edge.from_id)
        return sources


class TacticalDefenseAgent(BridgeGuardAgent):
    name = "tactical_defense"

    def __init__(self, max_evaluated_actions: int = 120) -> None:
        super().__init__(max_evaluated_actions=max_evaluated_actions)

    def choose_action(self, env: NXSGoEnv) -> Action:
        actions = self._candidate_actions(env)
        if not actions:
            return {"type": ACTION_PULSE}

        actor = env.game.current_player
        before = self._tactical_snapshot(env, actor)
        best_action = actions[0]
        best_score = float("-inf")
        for action in actions:
            trial = env.clone()
            result = trial.step(action)
            score = (
                result.reward
                + self._defense_score(trial, actor)
                + self._tactical_delta(before, trial, actor)
            )
            if score > best_score:
                best_score = score
                best_action = action
        return best_action

    def _candidate_actions(self, env: NXSGoEnv) -> list[Action]:
        actions = env.legal_actions()
        actor = env.game.current_player
        critical_nodes = self._critical_owned_node_ids(env, actor)
        pressured_nodes = self._pressured_owned_node_ids(env, actor)
        own_capture_targets = self._capture_target_ids(env, actor)
        opponent_capture_targets = self._capture_target_ids(env, other_player(actor))
        pressure_sources = self._pressure_source_node_ids(env, actor)

        def priority(action: Action) -> tuple[int, float]:
            if action["type"] == ACTION_PULSE and own_capture_targets:
                return (0, -float(len(own_capture_targets)))
            if action["type"] == ACTION_ROUTE:
                if action["to_id"] in pressure_sources:
                    return (1, 0.0)
                if action["from_id"] in pressured_nodes:
                    return (2, 0.0)
                if action["from_id"] in critical_nodes or action["to_id"] in critical_nodes:
                    return (3, 0.0)
                if action["to_id"] in opponent_capture_targets:
                    return (4, 0.0)
                return (6, 0.0)
            if action["type"] == ACTION_SYNCH and (pressured_nodes or critical_nodes):
                x = float(action["x"])
                y = float(action["y"])
                targets = pressured_nodes or critical_nodes
                nearest = min(
                    distance((x, y), env.game.node_by_id(node_id).pos)
                    for node_id in targets
                )
                return (5, nearest)
            if action["type"] == ACTION_PULSE:
                return (7, 0.0)
            return (8, 0.0)

        return sorted(actions, key=priority)[: self.max_evaluated_actions]

    def _tactical_snapshot(self, env: NXSGoEnv, actor: str) -> dict[str, float]:
        opponent = other_player(actor)
        return {
            "score": env.evaluate_player(actor),
            "own_connected": float(self._connected_count(env, actor)),
            "enemy_connected": float(self._connected_count(env, opponent)),
            "own_live": float(env.game.player_stats(actor)["live_nodes"]),
            "enemy_live": float(env.game.player_stats(opponent)["live_nodes"]),
            "own_targets": float(len(self._capture_target_ids(env, actor))),
            "enemy_targets": float(len(self._capture_target_ids(env, opponent))),
            "own_pressured": float(len(self._pressured_owned_node_ids(env, actor))),
            "enemy_pressured": float(len(self._pressured_owned_node_ids(env, opponent))),
        }

    def _tactical_delta(
        self,
        before: dict[str, float],
        env: NXSGoEnv,
        actor: str,
    ) -> float:
        after = self._tactical_snapshot(env, actor)
        opponent = other_player(actor)
        source_bonus = 0.0
        if env.game.source_for(actor) is None:
            source_bonus -= 100.0
        if env.game.source_for(opponent) is None:
            source_bonus += 100.0

        return (
            1.2 * (after["score"] - before["score"])
            + 1.6 * (after["own_connected"] - before["own_connected"])
            - 1.8 * (after["enemy_connected"] - before["enemy_connected"])
            + 1.2 * (after["own_live"] - before["own_live"])
            - 1.4 * (after["enemy_live"] - before["enemy_live"])
            + 4.0 * (after["own_targets"] - before["own_targets"])
            - 5.0 * (after["enemy_targets"] - before["enemy_targets"])
            - 3.0 * after["own_pressured"]
            + 1.2 * after["enemy_pressured"]
            + source_bonus
        )

    def _capture_target_ids(self, env: NXSGoEnv, actor: str) -> set[int]:
        opponent = other_player(actor)
        targets: set[int] = set()
        for node in env.game.active_nodes():
            if node.owner != opponent:
                continue
            incoming = sum(
                1
                for edge in env.game.edges
                if edge.route_owner == actor and edge.to_id == node.id
            )
            outgoing = sum(
                1
                for edge in env.game.edges
                if edge.route_owner == opponent and edge.from_id == node.id
            )
            defense = outgoing + (2 if node.is_source else 0)
            if incoming > defense:
                targets.add(node.id)
        return targets

    def _pressure_source_node_ids(self, env: NXSGoEnv, actor: str) -> set[int]:
        opponent = other_player(actor)
        sources: set[int] = set()
        for edge in env.game.edges:
            if edge.route_owner != opponent or edge.from_id is None or edge.to_id is None:
                continue
            target = env.game.node_by_id(edge.to_id)
            if target.owner == actor:
                sources.add(edge.from_id)
        return sources

    def _connected_count(self, env: NXSGoEnv, actor: str) -> int:
        source = env.game.source_for(actor)
        if source is None:
            return 0
        return len(env.game.connected_owned_ids(source.id, actor))


def play_match(
    signal_agent: Agent,
    noise_agent: Agent,
    max_turns: int = 120,
    env: NXSGoEnv | None = None,
    map_variant: str = "default",
) -> dict[str, Any]:
    arena = env or NXSGoEnv(map_variant=map_variant)
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
        "winner_reason": arena.game.winner_reason,
        "turns": turns,
        "turn_limit_reached": arena.game.winner is None and turns >= max_turns,
        "stats": {owner: arena.game.player_stats(owner) for owner in PLAYERS},
        "evaluation": arena.evaluate_position(),
        "history": list(arena.game.history),
        "map_variant": arena.map_variant,
    }
