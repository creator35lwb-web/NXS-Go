# Architecture

NXS-Go is currently a single-file Pygame prototype with focused unit tests around the core rule logic.

## Runtime

- `nxs_go.py` owns the game loop, rendering, input handling, and game state.
- `nxs_go_ai.py` wraps the same rule engine for agent testing and self-play experiments.
- `requirements.txt` keeps runtime dependencies minimal.
- The game is local-first and does not use network services.

## Core Concepts

- `Node`: a point in the board network. Nodes belong to Signal, Noise, or become dark.
- `Edge`: a relationship between nearby nodes.
- `Route`: directional pressure placed on an edge.
- `Source`: each player's root node. A living network must remain connected to its Source.
- `Isolation`: when a branch loses connection to its Source, it goes dark.

## Test Boundary

`tests/test_nxs_go_logic.py` focuses on deterministic rule behavior:

- source initialization
- SYNCH validity
- node and edge creation
- ROUTE ownership constraints
- PULSE capture behavior
- isolation blackout
- undo
- history export
- AI arena legal actions and bounded baseline matches

## Near-Term Direction

Keep the architecture simple until v0.1-A playtesting and v0.2 AI Arena testing prove the rules are understandable and strategically durable. Refactor only when it improves clarity, testability, or contribution safety.
