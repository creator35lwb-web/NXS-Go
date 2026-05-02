# Playbook

NXS-Go is won through connection, pressure, and isolation.

## Goal

Keep your Source alive while causing the opponent's network to lose connection and go dark.

## First Game

1. Start the game with `python nxs_go.py`.
2. Read the startup help.
3. Press `H` to close the help.
4. Use `1` for SYNCH and place a node near your Source.
5. Use `2` for ROUTE and click a valid edge touching your network.
6. Use `3` or `Space` for PULSE when you want to resolve pressure.
7. Watch for bridges. Capturing a bridge can isolate a whole branch.

## Winning Pattern

```text
Build from Source -> route pressure into weak nodes -> capture bridges -> trigger blackout
```

## What To Notice

- A large network is fragile if it depends on one bridge.
- A route is strongest when it creates pressure on a strategic connection.
- A capture matters most when it changes the shape of the network.
- Isolation is more decisive than raw node count.

## Playtest Questions

- Did you understand why a move was legal or illegal?
- Did PULSE explain why ownership changed?
- Did blackout feel connected to your previous choices?
- Did the winner feel clear before the final collapse?

