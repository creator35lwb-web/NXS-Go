from __future__ import annotations

import math
import copy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import pygame


WIDTH = 1120
HEIGHT = 760
FPS = 60

CONNECTION_RADIUS = 150
NODE_RADIUS = 14
SOURCE_RADIUS = 20
MIN_NODE_SPACING = 36
EDGE_CLICK_TOLERANCE = 12
HORIZON_TURNS = 60
BOARD_TOP = 68
BOARD_BOTTOM = HEIGHT - 122
MIN_VIEW_TILT = 0.25
MAX_VIEW_TILT = 1.0
VIEW_TILT_STEP = 0.075

BG = (12, 15, 22)
PANEL = (23, 28, 40)
TEXT = (226, 232, 240)
MUTED = (136, 146, 166)
EDGE = (82, 92, 115)
EDGE_ACTIVE = (178, 190, 214)
VALID = (61, 220, 151)
INVALID = (248, 113, 113)
SIGNAL = (65, 156, 255)
SIGNAL_DARK = (26, 75, 128)
NOISE = (239, 75, 96)
NOISE_DARK = (115, 36, 49)
NEUTRAL = (145, 150, 161)
GOLD = (245, 197, 66)

PLAYER_SIGNAL = "Signal"
PLAYER_NOISE = "Noise"
PLAYERS = (PLAYER_SIGNAL, PLAYER_NOISE)

ACTION_SYNCH = "SYNCH"
ACTION_ROUTE = "ROUTE"
ACTION_PULSE = "PULSE"
ACTIONS = (ACTION_SYNCH, ACTION_ROUTE, ACTION_PULSE)
ACTION_ICONS = {
    ACTION_SYNCH: "+",
    ACTION_ROUTE: "->",
    ACTION_PULSE: "!",
}


@dataclass
class Node:
    id: int
    x: float
    y: float
    owner: str
    is_source: bool = False
    active: bool = True

    @property
    def pos(self) -> tuple[int, int]:
        return int(self.x), int(self.y)


@dataclass
class Edge:
    a: int
    b: int
    route_owner: str | None = None
    from_id: int | None = None
    to_id: int | None = None

    def connects(self, node_id: int) -> bool:
        return self.a == node_id or self.b == node_id

    def other(self, node_id: int) -> int:
        if self.a == node_id:
            return self.b
        if self.b == node_id:
            return self.a
        raise ValueError("node is not part of this edge")


class Game:
    def __init__(self) -> None:
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []
        self.next_node_id = 0
        self.current_player = PLAYER_SIGNAL
        self.selected_action = ACTION_SYNCH
        self.winner: str | None = None
        self.winner_reason: str | None = None
        self.turn_count = 0
        self.view_tilt = 0.62
        self.show_help = True
        self.show_history = False
        self.message = "NXS-Go v0.1: preserve signal, avoid isolation."
        self.log: list[str] = []
        self.history: list[str] = []
        self.undo_stack: list[dict[str, object]] = []
        self.saved_history_path: str | None = None
        self.record_undo = True
        self.record_history = True
        self._seed_sources()

    def _seed_sources(self) -> None:
        self.add_node(150, HEIGHT // 2, PLAYER_SIGNAL, is_source=True)
        self.add_node(WIDTH - 150, HEIGHT // 2, PLAYER_NOISE, is_source=True)

    def add_node(self, x: float, y: float, owner: str, is_source: bool = False) -> Node:
        node = Node(self.next_node_id, x, y, owner, is_source=is_source)
        self.next_node_id += 1
        self.nodes.append(node)
        self.rebuild_edges()
        return node

    def active_nodes(self) -> list[Node]:
        return [node for node in self.nodes if node.active]

    def node_by_id(self, node_id: int) -> Node:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(node_id)

    def source_for(self, owner: str) -> Node | None:
        for node in self.nodes:
            if node.owner == owner and node.is_source and node.active:
                return node
        return None

    def owner_color(self, owner: str, active: bool = True) -> tuple[int, int, int]:
        if owner == PLAYER_SIGNAL:
            return SIGNAL if active else SIGNAL_DARK
        return NOISE if active else NOISE_DARK

    def rebuild_edges(self) -> None:
        old_routes = {
            tuple(sorted((edge.a, edge.b))): (edge.route_owner, edge.from_id, edge.to_id)
            for edge in self.edges
        }
        self.edges = []
        nodes = self.active_nodes()
        for i, first in enumerate(nodes):
            for second in nodes[i + 1 :]:
                if distance(first.pos, second.pos) <= CONNECTION_RADIUS:
                    edge = Edge(first.id, second.id)
                    old = old_routes.get(tuple(sorted((first.id, second.id))))
                    if old:
                        edge.route_owner, edge.from_id, edge.to_id = old
                    self.edges.append(edge)

    def valid_synch_position(self, x: float, y: float, owner: str) -> tuple[bool, str]:
        if self.winner:
            return False, "Game is already complete."
        if y < 70:
            return False, "Keep nodes below the command bar."
        if y > BOARD_BOTTOM - NODE_RADIUS:
            return False, "Keep nodes above the status panel."
        for node in self.active_nodes():
            if distance((x, y), node.pos) < MIN_NODE_SPACING:
                return False, "Too close to an existing node."
        owned = [node for node in self.active_nodes() if node.owner == owner]
        if not owned:
            return False, "No living source for this player."
        if not any(distance((x, y), node.pos) <= CONNECTION_RADIUS for node in owned):
            return False, "SYNCH must connect to your living network."
        return True, "SYNCH ready."

    def synch(self, x: float, y: float) -> None:
        ok, reason = self.valid_synch_position(x, y, self.current_player)
        if not ok:
            self.set_message(reason, error=True)
            return
        self.save_undo_state()
        node = self.add_node(x, y, self.current_player)
        connected = sorted(edge.other(node.id) for edge in self.edges if edge.connects(node.id))
        self.add_event(
            f"{self.current_player} SYNCH node {node.id}.",
            f"{self.current_player} placed node {node.id}. It connected to node(s) {connected}, "
            "so it stayed alive through Source connectivity. Good SYNCH moves extend reach "
            "without breaking the chain back to your Source.",
        )
        self.after_action()

    def route_at(self, x: float, y: float) -> None:
        if self.winner:
            self.set_message("Game is already complete.", error=True)
            return

        edge = self.edge_at(x, y)
        if edge is None:
            self.set_message("ROUTE must target an edge.", error=True)
            return

        a_node = self.node_by_id(edge.a)
        b_node = self.node_by_id(edge.b)
        endpoints = [node for node in (a_node, b_node) if node.owner == self.current_player]
        if not endpoints:
            self.set_message("ROUTE needs at least one endpoint you own.", error=True)
            return

        self.save_undo_state()
        # Route from the owned endpoint closest to the click toward the other endpoint.
        from_node = min(endpoints, key=lambda node: distance((x, y), node.pos))
        to_id = edge.other(from_node.id)
        edge.route_owner = self.current_player
        edge.from_id = from_node.id
        edge.to_id = to_id
        self.add_event(
            f"{self.current_player} ROUTE {edge.from_id}->{edge.to_id}.",
            f"{self.current_player} pointed signal from node {edge.from_id} to node {edge.to_id}. "
            "Routes are intention: they do not win alone, but they prepare pressure. Look for "
            "bridges or weak opponent nodes where multiple routes can converge.",
        )
        self.after_action()

    def pulse(self) -> None:
        if self.winner:
            return
        self.save_undo_state()
        opponent = other_player(self.current_player)
        captured: list[Node] = []

        for node in self.active_nodes():
            if node.owner != opponent:
                continue
            incoming = sum(
                1
                for edge in self.edges
                if edge.route_owner == self.current_player and edge.to_id == node.id
            )
            outgoing = sum(
                1
                for edge in self.edges
                if edge.route_owner == opponent and edge.from_id == node.id
            )
            defense = outgoing + (2 if node.is_source else 0)
            if incoming > defense:
                captured.append(node)
                self.add_event(
                    f"{self.current_player} pressure beats node {node.id}.",
                    f"Node {node.id} is vulnerable: incoming pressure {incoming} > defense {defense}. "
                    "This is the lesson of PULSE: do not attack everywhere; focus pressure where "
                    "the opponent has fewer exits than your incoming signal.",
                )

        if not captured:
            self.add_event(
                f"{self.current_player} PULSE found no overload.",
                f"{self.current_player} pulsed the network, but no opponent node had incoming "
                "pressure greater than its defense. This is a useful scout: build more routes "
                "toward a weak bridge before pulsing again.",
            )
        else:
            for node in captured:
                node.owner = self.current_player
                node.is_source = False
                self.clear_routes_touching(node.id)
            ids = [node.id for node in captured]
            self.add_event(
                f"{self.current_player} PULSE captured {len(captured)} node(s).",
                f"{self.current_player} captured node(s) {ids}. Routes touching captured nodes "
                "were cleared so the new topology can be recalculated. After a capture, check "
                "whether a whole branch has lost its Source path.",
            )

        self.after_action()

    def clear_routes_touching(self, node_id: int) -> None:
        for edge in self.edges:
            if edge.connects(node_id):
                edge.route_owner = None
                edge.from_id = None
                edge.to_id = None

    def after_action(self) -> None:
        self.turn_count += 1
        self.rebuild_edges()
        removed = self.resolve_isolation()
        self.rebuild_edges()
        self.check_win()
        if removed:
            self.add_event(
                f"Isolation blackout removed {removed} node(s).",
                f"{removed} node(s) had no same-owner path back to their Source after the action, "
                "so they went dark. This is the heart of NXS-Go: the strongest move is often not "
                "capturing many nodes, but cutting the bridge that keeps them alive.",
            )
        if not self.winner:
            self.current_player = other_player(self.current_player)
            self.message = f"{self.current_player}'s turn. Choose SYNCH, ROUTE, or PULSE."

    def resolve_isolation(self) -> int:
        removed = 0
        for owner in PLAYERS:
            source = self.source_for(owner)
            if source is None:
                continue
            connected = self.connected_owned_ids(source.id, owner)
            for node in self.active_nodes():
                if node.owner == owner and not node.is_source and node.id not in connected:
                    node.active = False
                    self.clear_routes_touching(node.id)
                    removed += 1
        return removed

    def connected_owned_ids(self, start_id: int, owner: str) -> set[int]:
        seen = {start_id}
        stack = [start_id]
        while stack:
            current = stack.pop()
            for edge in self.edges:
                if not edge.connects(current):
                    continue
                other_id = edge.other(current)
                other = self.node_by_id(other_id)
                if other.active and other.owner == owner and other_id not in seen:
                    seen.add(other_id)
                    stack.append(other_id)
        return seen

    def check_win(self) -> None:
        signal_source = self.source_for(PLAYER_SIGNAL)
        noise_source = self.source_for(PLAYER_NOISE)
        if signal_source is None and noise_source is None:
            self.winner = "No one"
            self.winner_reason = "source isolation"
        elif signal_source is None:
            self.winner = PLAYER_NOISE
            self.winner_reason = "source isolation"
        elif noise_source is None:
            self.winner = PLAYER_SIGNAL
            self.winner_reason = "source isolation"
        elif self.turn_count >= HORIZON_TURNS:
            evaluation = self.evaluate_position()
            self.winner = evaluation["leader"]
            self.winner_reason = "horizon scoring"

        if self.winner:
            if self.winner == "Even":
                self.winner = "No one"
                self.message = "Horizon reached. No one wins: the network is even."
            elif self.winner_reason == "horizon scoring":
                margin = self.evaluate_position()["margin"]
                self.message = f"{self.winner} wins by horizon scoring, margin {margin}."
                self.add_event(
                    "Horizon scoring resolved the game.",
                    f"After {self.turn_count} turns, no Source was isolated. "
                    f"{self.winner} led structurally by margin {margin}. "
                    "The horizon keeps passive survival from becoming endless.",
                )
            else:
                self.message = f"{self.winner} wins by source isolation."
            self.add_log(self.message)

    def edge_at(self, x: float, y: float) -> Edge | None:
        best: tuple[float, Edge] | None = None
        for edge in self.edges:
            a = self.node_by_id(edge.a)
            b = self.node_by_id(edge.b)
            d = point_segment_distance((x, y), a.pos, b.pos)
            if d <= EDGE_CLICK_TOLERANCE and (best is None or d < best[0]):
                best = (d, edge)
        return best[1] if best else None

    def node_at(self, x: float, y: float) -> Node | None:
        for node in reversed(self.active_nodes()):
            radius = SOURCE_RADIUS if node.is_source else NODE_RADIUS
            if distance((x, y), node.pos) <= radius + 4:
                return node
        return None

    def set_message(self, message: str, error: bool = False) -> None:
        self.message = message
        if error:
            self.add_log(f"Invalid: {message}")

    def add_log(self, message: str) -> None:
        self.log.append(message)
        self.log = self.log[-7:]

    def add_event(self, summary: str, explanation: str) -> None:
        if not self.record_history:
            return
        self.add_log(summary)
        self.history.append(f"{summary} {explanation}")
        self.history = self.history[-40:]

    def player_stats(self, owner: str) -> dict[str, int | bool]:
        live_nodes = [node for node in self.active_nodes() if node.owner == owner]
        routed_edges = [edge for edge in self.edges if edge.route_owner == owner]
        source = self.source_for(owner)
        connected = bool(source and source.active)
        return {
            "live_nodes": len(live_nodes),
            "routes": len(routed_edges),
            "source_connected": connected,
        }

    def evaluate_player(self, owner: str) -> float:
        opponent = other_player(owner)
        own = self.player_stats(owner)
        enemy = self.player_stats(opponent)
        return (
            float(own["live_nodes"])
            - float(enemy["live_nodes"])
            + 0.4 * (float(own["routes"]) - float(enemy["routes"]))
            + (2.0 if own["source_connected"] else -4.0)
            - (2.0 if enemy["source_connected"] else -4.0)
        )

    def evaluate_position(self) -> dict[str, object]:
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

    def save_undo_state(self) -> None:
        if not self.record_undo:
            return
        self.undo_stack.append(
            {
                "nodes": copy.deepcopy(self.nodes),
                "edges": copy.deepcopy(self.edges),
                "next_node_id": self.next_node_id,
                "current_player": self.current_player,
                "selected_action": self.selected_action,
                "winner": self.winner,
                "winner_reason": self.winner_reason,
                "turn_count": self.turn_count,
                "message": self.message,
                "log": list(self.log),
                "history": list(self.history),
            }
        )
        self.undo_stack = self.undo_stack[-12:]

    def undo(self) -> None:
        if not self.undo_stack:
            self.set_message("Nothing to undo.", error=True)
            return
        state = self.undo_stack.pop()
        self.nodes = state["nodes"]  # type: ignore[assignment]
        self.edges = state["edges"]  # type: ignore[assignment]
        self.next_node_id = state["next_node_id"]  # type: ignore[assignment]
        self.current_player = state["current_player"]  # type: ignore[assignment]
        self.selected_action = state["selected_action"]  # type: ignore[assignment]
        self.winner = state["winner"]  # type: ignore[assignment]
        self.winner_reason = state["winner_reason"]  # type: ignore[assignment]
        self.turn_count = state["turn_count"]  # type: ignore[assignment]
        self.message = "Undid the last completed action."
        self.log = state["log"]  # type: ignore[assignment]
        self.history = state["history"]  # type: ignore[assignment]
        self.add_event(
            "Undo restored previous state.",
            "The last completed action was reversed so players can recover from misclicks.",
        )

    def save_history(self) -> Path:
        history_dir = Path("history")
        history_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = history_dir / f"nxs_go_history_{stamp}.md"

        lines = [
            "# NXS-Go Session History",
            "",
            f"Saved: {datetime.now().isoformat(timespec='seconds')}",
            "",
            f"Turns played: {self.turn_count}/{HORIZON_TURNS}",
            "",
            "## Goal",
            "",
            "Keep your Source connected while cutting the opponent off from theirs.",
            "",
            "## Final Network Status",
            "",
        ]
        for owner in PLAYERS:
            stats = self.player_stats(owner)
            status = "Source connected" if stats["source_connected"] else "Source dark"
            lines.append(
                f"- {owner}: {stats['live_nodes']} live nodes, {stats['routes']} routes, {status}"
            )
        evaluation = self.evaluate_position()
        lines.extend(
            [
                "",
                "## Horizon Evaluation",
                "",
                f"- Leader: {evaluation['leader']}",
                f"- Margin: {evaluation['margin']}",
                f"- Scores: {evaluation['scores']}",
            ]
        )

        lines.extend(["", "## Events", ""])
        if self.history:
            for idx, item in enumerate(self.history, 1):
                lines.append(f"{idx}. {item}")
        else:
            lines.append("No events recorded.")

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.saved_history_path = str(path)
        self.set_message(f"Saved history to {path}")
        self.add_log("Session history saved.")
        return path

    def reset(self) -> None:
        self.__init__()

    def adjust_view_tilt(self, delta: float) -> None:
        self.view_tilt = max(MIN_VIEW_TILT, min(MAX_VIEW_TILT, self.view_tilt + delta))
        self.message = f"View tilt {int(self.view_tilt * 100)}%. Use [ or ] to adjust."


def other_player(player: str) -> str:
    return PLAYER_NOISE if player == PLAYER_SIGNAL else PLAYER_SIGNAL


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    px, py = point
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    if dx == 0 and dy == 0:
        return distance(point, start)
    t = ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    closest = (sx + t * dx, sy + t * dy)
    return distance(point, closest)


def draw_arrow(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    start: tuple[int, int],
    end: tuple[int, int],
    width: int = 3,
) -> None:
    sx, sy = start
    ex, ey = end
    angle = math.atan2(ey - sy, ex - sx)
    inset = NODE_RADIUS + 8
    start2 = (int(sx + math.cos(angle) * inset), int(sy + math.sin(angle) * inset))
    end2 = (int(ex - math.cos(angle) * inset), int(ey - math.sin(angle) * inset))
    pygame.draw.line(surface, color, start2, end2, width)

    head_len = 12
    head_angle = math.pi / 7
    left = (
        int(end2[0] - math.cos(angle - head_angle) * head_len),
        int(end2[1] - math.sin(angle - head_angle) * head_len),
    )
    right = (
        int(end2[0] - math.cos(angle + head_angle) * head_len),
        int(end2[1] - math.sin(angle + head_angle) * head_len),
    )
    pygame.draw.polygon(surface, color, [end2, left, right])


def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    pos: tuple[int, int],
    color: tuple[int, int, int] = TEXT,
) -> None:
    surface.blit(font.render(text, True, color), pos)


def draw_button(
    surface: pygame.Surface,
    font: pygame.font.Font,
    rect: pygame.Rect,
    label: str,
    active: bool,
) -> None:
    fill = (39, 48, 68) if active else (29, 35, 50)
    border = GOLD if active else (70, 80, 101)
    pygame.draw.rect(surface, fill, rect, border_radius=6)
    pygame.draw.rect(surface, border, rect, 2, border_radius=6)
    label_surf = font.render(label, True, TEXT)
    surface.blit(
        label_surf,
        (
            rect.centerx - label_surf.get_width() // 2,
            rect.centery - label_surf.get_height() // 2,
        ),
    )


def draw_game(screen: pygame.Surface, game: Game, fonts: dict[str, pygame.font.Font]) -> None:
    screen.fill(BG)
    draw_top_bar(screen, game, fonts)
    draw_depth_field(screen, game)
    draw_graph(screen, game)
    draw_status_panel(screen, game, fonts)
    if game.show_help:
        draw_help_overlay(screen, game, fonts)
    if game.show_history:
        draw_history_overlay(screen, game, fonts)


def draw_top_bar(screen: pygame.Surface, game: Game, fonts: dict[str, pygame.font.Font]) -> None:
    pygame.draw.rect(screen, PANEL, pygame.Rect(0, 0, WIDTH, 68))
    color = game.owner_color(game.current_player)
    draw_text(screen, fonts["title"], "NXS-Go v0.1", (22, 16), TEXT)
    draw_text(
        screen,
        fonts["small"],
        "Goal: keep your Source connected while cutting the opponent off from theirs.",
        (185, 17),
        GOLD,
    )
    draw_text(screen, fonts["small"], f"{game.current_player}'s move", (22, 48), color)
    draw_text(screen, fonts["small"], game.message, (185, 43), MUTED)

    for idx, action in enumerate(ACTIONS):
        rect = pygame.Rect(685 + idx * 112, 16, 102, 36)
        label = f"{idx + 1} {ACTION_ICONS[action]} {action}"
        draw_button(screen, fonts["small"], rect, label, game.selected_action == action)

    pulse_rect = pygame.Rect(1025, 16, 78, 36)
    draw_button(screen, fonts["small"], pulse_rect, "SPACE", game.selected_action == ACTION_PULSE)


def draw_graph(screen: pygame.Surface, game: Game) -> None:
    mouse_pos = pygame.mouse.get_pos()
    hovered_edge = game.edge_at(*mouse_pos) if BOARD_TOP <= mouse_pos[1] <= BOARD_BOTTOM else None

    for edge in sorted(game.edges, key=lambda item: edge_depth(game, item)):
        a = game.node_by_id(edge.a)
        b = game.node_by_id(edge.b)
        depth = visual_depth(game, (node_depth(a) + node_depth(b)) / 2)
        shadow_offset = 2 + int(depth * 5)
        width = 1 + int(depth * 2)
        shadow_color = (5, 7, 12)
        pygame.draw.line(
            screen,
            shadow_color,
            (a.pos[0] + shadow_offset, a.pos[1] + shadow_offset),
            (b.pos[0] + shadow_offset, b.pos[1] + shadow_offset),
            width + 2,
        )
        color = EDGE_ACTIVE if edge.route_owner else EDGE
        if edge == hovered_edge or route_edge_is_available(game, edge):
            color = GOLD if edge == hovered_edge else depth_color(EDGE_ACTIVE, depth)
            width += 1
        pygame.draw.line(screen, depth_color(color, depth), a.pos, b.pos, width)

    for edge in game.edges:
        if edge.route_owner and edge.from_id is not None and edge.to_id is not None:
            start = game.node_by_id(edge.from_id)
            end = game.node_by_id(edge.to_id)
            depth = visual_depth(game, (node_depth(start) + node_depth(end)) / 2)
            draw_arrow(
                screen,
                depth_color(game.owner_color(edge.route_owner), depth),
                start.pos,
                end.pos,
                width=3 + int(depth * 2),
            )

    for node in sorted(game.nodes, key=lambda item: item.y):
        depth = visual_depth(game, node_depth(node))
        radius = depth_radius(SOURCE_RADIUS if node.is_source else NODE_RADIUS, depth)
        shadow_offset = 4 + int(depth * 7)
        shadow_rect = pygame.Rect(0, 0, radius * 2 + 12, max(6, radius // 2 + 6))
        shadow_rect.center = (node.pos[0] + shadow_offset, node.pos[1] + shadow_offset)
        pygame.draw.ellipse(screen, (3, 5, 10), shadow_rect)
        if not node.active:
            pygame.draw.circle(screen, (34, 39, 50), node.pos, radius, 1)
            continue
        color = depth_color(game.owner_color(node.owner), depth)
        glow = depth_color(color, min(1.0, depth + 0.25))
        pygame.draw.circle(screen, glow, node.pos, radius + 5, 1)
        pygame.draw.circle(screen, color, node.pos, radius)
        pygame.draw.circle(screen, BG, node.pos, radius, 2)
        if node.is_source:
            pygame.draw.circle(screen, GOLD, node.pos, radius + 5, 2)

    if hovered_edge is not None:
        draw_edge_inspector(screen, game, hovered_edge)


def draw_status_panel(
    screen: pygame.Surface,
    game: Game,
    fonts: dict[str, pygame.font.Font],
) -> None:
    panel = pygame.Rect(0, HEIGHT - 122, WIDTH, 122)
    pygame.draw.rect(screen, PANEL, panel)
    pygame.draw.line(screen, (50, 60, 80), (0, HEIGHT - 122), (WIDTH, HEIGHT - 122), 2)

    draw_text(screen, fonts["body"], "Selected Action", (22, HEIGHT - 105), TEXT)
    draw_text(screen, fonts["small"], action_hint(game.selected_action), (22, HEIGHT - 78), MUTED)
    horizon = f"Turn {game.turn_count}/{HORIZON_TURNS}. Tilt [/] {int(game.view_tilt * 100)}%. H help. E history."
    draw_text(screen, fonts["small"], horizon, (22, HEIGHT - 52), MUTED)
    draw_text(screen, fonts["small"], "Use top buttons or keys 1/2/3 to choose actions.", (22, HEIGHT - 29), MUTED)

    draw_advantage(screen, game, fonts, 515, HEIGHT - 107)

    history_rect = pygame.Rect(810, HEIGHT - 110, 270, 30)
    pygame.draw.rect(screen, (29, 35, 50), history_rect, border_radius=6)
    pygame.draw.rect(screen, (70, 80, 101), history_rect, 1, border_radius=6)
    draw_text(screen, fonts["body"], "Event Log - click for history", (824, HEIGHT - 104), TEXT)
    for i, item in enumerate(reversed(game.log[-4:])):
        draw_text(screen, fonts["small"], item, (810, HEIGHT - 74 + i * 21), MUTED)


def draw_advantage(
    screen: pygame.Surface,
    game: Game,
    fonts: dict[str, pygame.font.Font],
    x: int,
    y: int,
) -> None:
    draw_text(screen, fonts["body"], "Network Status", (x, y), TEXT)
    for idx, owner in enumerate(PLAYERS):
        stats = game.player_stats(owner)
        color = game.owner_color(owner)
        status = "Source connected" if stats["source_connected"] else "Source dark"
        text = f"{owner}: {stats['live_nodes']} live nodes, {stats['routes']} routes, {status}"
        draw_text(screen, fonts["small"], text, (x, y + 27 + idx * 24), color)


def draw_depth_field(screen: pygame.Surface, game: Game) -> None:
    pygame.draw.rect(screen, (10, 13, 20), pygame.Rect(0, BOARD_TOP, WIDTH, BOARD_BOTTOM - BOARD_TOP))
    vanishing = (WIDTH // 2, int(BOARD_TOP + 16 + (1.0 - game.view_tilt) * 90))
    floor_color = (24, 31, 46)
    pygame.draw.line(screen, (45, 55, 75), (0, BOARD_TOP), (WIDTH, BOARD_TOP), 1)
    for idx in range(1, 9):
        t = idx / 9
        curve = t ** (1.15 + game.view_tilt * 1.2)
        y = int(BOARD_TOP + (BOARD_BOTTOM - BOARD_TOP) * curve)
        pygame.draw.line(screen, floor_color, (0, y), (WIDTH, y), 1)
    for x in range(-160, WIDTH + 161, 160):
        pygame.draw.line(screen, floor_color, vanishing, (x, BOARD_BOTTOM), 1)
    pygame.draw.line(screen, (33, 42, 61), (0, BOARD_BOTTOM), (WIDTH, BOARD_BOTTOM), 1)


def node_depth(node: Node) -> float:
    return max(0.0, min(1.0, (node.y - BOARD_TOP) / (BOARD_BOTTOM - BOARD_TOP)))


def edge_depth(game: Game, edge: Edge) -> float:
    a = game.node_by_id(edge.a)
    b = game.node_by_id(edge.b)
    return (node_depth(a) + node_depth(b)) / 2


def visual_depth(game: Game, depth: float) -> float:
    return max(0.0, min(1.0, depth * (0.72 + game.view_tilt * 0.42)))


def depth_radius(base: int, depth: float) -> int:
    return int(base * (0.86 + depth * 0.24))


def depth_color(color: tuple[int, int, int], depth: float) -> tuple[int, int, int]:
    factor = 0.78 + depth * 0.28
    return tuple(min(255, int(channel * factor)) for channel in color)


def route_edge_is_available(game: Game, edge: Edge) -> bool:
    if game.selected_action != ACTION_ROUTE:
        return False
    try:
        a_node = game.node_by_id(edge.a)
        b_node = game.node_by_id(edge.b)
    except KeyError:
        return False
    return a_node.owner == game.current_player or b_node.owner == game.current_player


def draw_edge_inspector(screen: pygame.Surface, game: Game, edge: Edge) -> None:
    a = game.node_by_id(edge.a)
    b = game.node_by_id(edge.b)
    midpoint = ((a.pos[0] + b.pos[0]) // 2, (a.pos[1] + b.pos[1]) // 2)
    color = GOLD if route_edge_is_available(game, edge) else MUTED
    pygame.draw.circle(screen, color, midpoint, 8, 2)
    pygame.draw.circle(screen, color, a.pos, depth_radius(NODE_RADIUS, visual_depth(game, node_depth(a))) + 7, 2)
    pygame.draw.circle(screen, color, b.pos, depth_radius(NODE_RADIUS, visual_depth(game, node_depth(b))) + 7, 2)


def draw_help_overlay(
    screen: pygame.Surface,
    game: Game,
    fonts: dict[str, pygame.font.Font],
) -> None:
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 68))

    card = pygame.Rect(205, 98, 710, 520)
    pygame.draw.rect(screen, (20, 25, 36), card, border_radius=8)
    pygame.draw.rect(screen, GOLD, card, 2, border_radius=8)

    x = card.x + 34
    y = card.y + 26
    draw_text(screen, fonts["title"], "How to Play NXS-Go v0.1", (x, y), TEXT)
    y += 42
    draw_text(screen, fonts["body"], "Goal", (x, y), GOLD)
    y += 28
    draw_text(screen, fonts["small"], "Keep your Source connected. Make the opponent's network go dark.", (x, y), TEXT)
    y += 36

    draw_text(screen, fonts["body"], "Turn Loop", (x, y), GOLD)
    y += 25
    tutorial_lines = [
        "1. SYNCH (+): place a node near your living network.",
        "2. ROUTE (->): click an edge touching your node to point signal.",
        "3. PULSE (!): resolve pressure. Nodes flip when incoming pressure beats defense.",
        "4. Isolation: disconnected branches go dark after every action.",
        f"5. Horizon: after {HORIZON_TURNS} turns, the stronger living network wins.",
    ]
    for line in tutorial_lines:
        draw_text(screen, fonts["small"], line, (x, y), TEXT)
        y += 22

    y += 14
    draw_text(screen, fonts["body"], "First Move", (x, y), GOLD)
    y += 25
    draw_text(screen, fonts["small"], "Signal starts. Press 1, then click near the blue Source ring.", (x, y), TEXT)
    y += 22
    draw_text(screen, fonts["small"], "Noise then does the same near the red Source ring.", (x, y), TEXT)

    y += 28
    draw_text(screen, fonts["body"], "Winning Pattern", (x, y), GOLD)
    y += 25
    for line in wrap_text(
        "Build from Source -> route pressure into weak nodes -> capture bridges -> trigger blackout.",
        fonts["small"],
        640,
    ):
        draw_text(screen, fonts["small"], line, (x, y), TEXT)
        y += 21

    y += 18
    draw_text(screen, fonts["body"], "Controls", (x, y), GOLD)
    y += 25
    control_lines = [
        "1/2/3 choose actions. Space pulses. [/] tilt view. U undo. E history. S save. R reset. Esc quit.",
    ]
    for line in control_lines:
        for wrapped in wrap_text(line, fonts["small"], 640):
            draw_text(screen, fonts["small"], wrapped, (x, y), TEXT)
            y += 20

    footer = pygame.Rect(card.x, card.bottom - 48, card.width, 48)
    pygame.draw.rect(screen, (31, 39, 55), footer, border_bottom_left_radius=8, border_bottom_right_radius=8)
    draw_text(screen, fonts["body"], "Press H to close this help and resume the game.", (card.x + 32, card.bottom - 34), VALID)


def draw_history_overlay(
    screen: pygame.Surface,
    game: Game,
    fonts: dict[str, pygame.font.Font],
) -> None:
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    card = pygame.Rect(130, 92, 860, 560)
    pygame.draw.rect(screen, (20, 25, 36), card, border_radius=8)
    pygame.draw.rect(screen, EDGE_ACTIVE, card, 2, border_radius=8)

    x = card.x + 28
    y = card.y + 26
    draw_text(screen, fonts["title"], "Event History", (x, y), TEXT)
    draw_text(screen, fonts["small"], "Each line explains what happened and why. Press E to close, S to save.", (x, y + 36), MUTED)

    y += 76
    if not game.history:
        draw_text(screen, fonts["body"], "No events yet. Start with SYNCH near your Source.", (x, y), MUTED)
        return

    for item in game.history[-14:]:
        wrapped = wrap_text(item, fonts["small"], 800)
        for line in wrapped:
            draw_text(screen, fonts["small"], line, (x, y), TEXT)
            y += 20
        y += 8
        if y > card.bottom - 30:
            break


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def action_hint(action: str) -> str:
    if action == ACTION_SYNCH:
        return "SYNCH selected: click empty space within the radius of your living network."
    if action == ACTION_ROUTE:
        return "ROUTE selected: click an edge touching one of your nodes to create an arrow."
    return "PULSE selected: press Space or click the SPACE button to resolve pressure."


def handle_click(game: Game, pos: tuple[int, int]) -> None:
    x, y = pos
    if game.show_history:
        game.show_history = False
        return
    if y <= 68:
        for idx, action in enumerate(ACTIONS):
            if pygame.Rect(685 + idx * 112, 16, 102, 36).collidepoint(pos):
                game.selected_action = action
                game.message = action_hint(action)
                return
        if pygame.Rect(1025, 16, 78, 36).collidepoint(pos):
            game.selected_action = ACTION_PULSE
            game.pulse()
            return
    if pygame.Rect(810, HEIGHT - 110, 270, 30).collidepoint(pos):
        game.show_history = True
        return

    if game.selected_action == ACTION_SYNCH:
        game.synch(x, y)
    elif game.selected_action == ACTION_ROUTE:
        game.route_at(x, y)
    elif game.selected_action == ACTION_PULSE:
        game.pulse()


def main() -> None:
    pygame.init()
    pygame.display.set_caption("NXS-Go v0.1")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    fonts = {
        "title": pygame.font.SysFont("Segoe UI", 26, bold=True),
        "body": pygame.font.SysFont("Segoe UI", 19),
        "small": pygame.font.SysFont("Segoe UI", 15),
    }
    game = Game()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_u:
                    game.undo()
                elif event.key == pygame.K_s:
                    game.save_history()
                elif event.key == pygame.K_h:
                    game.show_help = not game.show_help
                elif event.key == pygame.K_e:
                    game.show_history = not game.show_history
                elif event.key == pygame.K_LEFTBRACKET:
                    game.adjust_view_tilt(-VIEW_TILT_STEP)
                elif event.key == pygame.K_RIGHTBRACKET:
                    game.adjust_view_tilt(VIEW_TILT_STEP)
                elif event.key == pygame.K_1:
                    game.selected_action = ACTION_SYNCH
                    game.message = action_hint(ACTION_SYNCH)
                elif event.key == pygame.K_2:
                    game.selected_action = ACTION_ROUTE
                    game.message = action_hint(ACTION_ROUTE)
                elif event.key == pygame.K_3:
                    game.selected_action = ACTION_PULSE
                    game.message = action_hint(ACTION_PULSE)
                elif event.key == pygame.K_SPACE:
                    game.selected_action = ACTION_PULSE
                    game.pulse()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_click(game, event.pos)

        draw_game(screen, game, fonts)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
