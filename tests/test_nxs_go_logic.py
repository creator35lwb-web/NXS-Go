import unittest
import os
import shutil
from pathlib import Path

from nxs_go import (
    ACTION_ROUTE,
    ACTION_SYNCH,
    Game,
    PLAYER_NOISE,
    PLAYER_SIGNAL,
)
from nxs_go_ai import BridgeGuardAgent, GreedyIsolationAgent, NXSGoEnv, RandomAgent, play_match


class NxsGoLogicTests(unittest.TestCase):
    def test_initial_sources_exist(self):
        game = Game()

        self.assertEqual(len(game.nodes), 2)
        self.assertIsNotNone(game.source_for(PLAYER_SIGNAL))
        self.assertIsNotNone(game.source_for(PLAYER_NOISE))
        self.assertEqual(game.current_player, PLAYER_SIGNAL)

    def test_synch_requires_living_network_range(self):
        game = Game()

        ok, _ = game.valid_synch_position(250, 380, PLAYER_SIGNAL)
        far_ok, reason = game.valid_synch_position(560, 380, PLAYER_SIGNAL)

        self.assertTrue(ok)
        self.assertFalse(far_ok)
        self.assertIn("living network", reason)

    def test_synch_adds_node_and_edges(self):
        game = Game()

        game.synch(250, 380)

        self.assertEqual(len(game.nodes), 3)
        self.assertEqual(len(game.edges), 1)
        self.assertEqual(game.current_player, PLAYER_NOISE)

    def test_route_assigns_direction_from_owned_endpoint(self):
        game = Game()
        game.synch(250, 380)
        game.current_player = PLAYER_SIGNAL
        game.selected_action = ACTION_ROUTE

        game.route_at(200, 380)

        self.assertEqual(len(game.edges), 1)
        edge = game.edges[0]
        self.assertEqual(edge.route_owner, PLAYER_SIGNAL)
        self.assertEqual(edge.from_id, 0)
        self.assertEqual(edge.to_id, 2)

    def test_pulse_captures_overloaded_node(self):
        game = Game()
        victim = game.add_node(250, 380, PLAYER_NOISE)
        game.current_player = PLAYER_SIGNAL
        edge = game.edges[0]
        edge.route_owner = PLAYER_SIGNAL
        edge.from_id = 0
        edge.to_id = victim.id

        game.pulse()

        self.assertEqual(victim.owner, PLAYER_SIGNAL)
        self.assertFalse(victim.is_source)

    def test_isolation_removes_disconnected_branch(self):
        game = Game()
        bridge = game.add_node(280, 380, PLAYER_SIGNAL)
        branch = game.add_node(420, 380, PLAYER_SIGNAL)
        game.rebuild_edges()

        bridge.owner = PLAYER_NOISE
        game.rebuild_edges()
        removed = game.resolve_isolation()

        self.assertEqual(removed, 2)
        self.assertFalse(bridge.active)
        self.assertFalse(branch.active)

    def test_undo_restores_previous_completed_action(self):
        game = Game()

        game.synch(250, 380)
        self.assertEqual(len(game.nodes), 3)

        game.undo()

        self.assertEqual(len(game.nodes), 2)
        self.assertEqual(game.current_player, PLAYER_SIGNAL)
        self.assertIsNone(game.winner)

    def test_save_history_writes_markdown_file(self):
        game = Game()
        game.synch(250, 380)

        test_output = Path(".test_history_output").resolve()
        if test_output.exists():
            shutil.rmtree(test_output)
        test_output.mkdir()

        cwd = Path.cwd()
        try:
            os.chdir(test_output)
            path = game.save_history()
            self.assertTrue(path.exists())
            content = path.read_text(encoding="utf-8")
            self.assertIn("NXS-Go Session History", content)
            self.assertIn("Final Network Status", content)
            self.assertIn("SYNCH", content)
        finally:
            os.chdir(cwd)
            if test_output.exists() and test_output.name == ".test_history_output":
                shutil.rmtree(test_output)

    def test_ai_env_exposes_initial_observation_and_legal_actions(self):
        env = NXSGoEnv()
        observation = env.reset()
        actions = env.legal_actions()

        self.assertEqual(observation["current_player"], PLAYER_SIGNAL)
        self.assertEqual(len(observation["nodes"]), 2)
        self.assertTrue(any(action["type"] == ACTION_SYNCH for action in actions))

    def test_ai_env_step_advances_turn_with_synch(self):
        env = NXSGoEnv()
        env.reset()
        action = next(action for action in env.legal_actions() if action["type"] == ACTION_SYNCH)

        result = env.step(action)

        self.assertFalse(result.done)
        self.assertEqual(result.observation["current_player"], PLAYER_NOISE)
        self.assertEqual(len(result.observation["nodes"]), 3)

    def test_greedy_agent_returns_legal_action(self):
        env = NXSGoEnv()
        env.reset()
        action = GreedyIsolationAgent().choose_action(env)

        self.assertIn(action, env.legal_actions())

    def test_bridge_guard_agent_returns_legal_action(self):
        env = NXSGoEnv()
        env.reset()
        action = BridgeGuardAgent().choose_action(env)

        self.assertIn(action, env.legal_actions())

    def test_baseline_agents_can_play_bounded_match(self):
        result = play_match(RandomAgent(seed=7), GreedyIsolationAgent(), max_turns=8)

        self.assertLessEqual(result["turns"], 8)
        self.assertIn("stats", result)
        self.assertIn(PLAYER_SIGNAL, result["stats"])


if __name__ == "__main__":
    unittest.main()
