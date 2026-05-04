# Changelog

## Unreleased

- Added early AI Arena interface in `nxs_go_ai.py`.
- Added baseline agents for random play, source guarding, and greedy isolation.
- Added AI Arena documentation.
- Added tests for legal actions, environment stepping, and bounded baseline matches.
- Added baseline benchmark runner and first benchmark notes.
- Added BridgeGuard benchmark hypothesis and agent.
- Added structural scoring for turn-limit AI benchmark games.
- Added Horizon Scoring as a finite 60-turn game rule.
- Added CounterRoute active-defense hypothesis agent.
- Added Targeted Counter-Pressure hypothesis agent.
- Added 2.5D depth-field board rendering to improve network readability.
- Added adjustable tilt controls and route hover inspection for dense clusters.
- Added AI Arena map variants for geometry/search experiments.
- Added contested-lane, forked-bridge, and center-cross benchmark maps.
- Added a focused benchmark `--suite defense` option.
- Added TacticalDefense one-ply search agent and benchmark notes.
- Optimized AI Arena rollouts by disabling undo/history recording and using lightweight state cloning.
- Added human playtest guide and GitHub playtest feedback issue template.

## v0.1-A Public Baseline

- Added local hotseat Pygame prototype.
- Added Signal vs Noise core loop: SYNCH, ROUTE, PULSE, and isolation.
- Added startup help, event history, undo, and local history export.
- Added unit tests for core rule behavior.
- Added public project docs, roadmap, security policy, and contribution guide.
- Kept private design thesis and agent prompts out of the public repository.
