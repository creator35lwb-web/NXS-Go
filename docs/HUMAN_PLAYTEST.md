# Human Playtest Guide

NXS-Go is in early human playtest.

The goal is not to prove balance yet. The goal is to learn whether two people can understand the core loop, challenge each other, and want to rematch.

## What We Are Testing

- Can a new player understand the goal?
- Does SYNCH feel like building a living network?
- Does ROUTE feel like intention and pressure?
- Does PULSE explain why nodes change owner?
- Does blackout/isolation feel meaningful?
- Does the board stay readable in tense positions?
- After losing, does the player want another match?

## Setup

Clone the repo:

```powershell
git clone https://github.com/creator35lwb-web/NXS-Go
cd NXS-Go
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start the game:

```powershell
python nxs_go.py
```

NXS-Go is currently local hotseat. Two players share one machine and alternate turns.

If you are testing alone, play both sides honestly for one short match and report it as a solo self-test. Solo feedback is useful for onboarding and readability, but two-player feedback is more valuable for competition.

## 15-Minute Playtest

1. Start the game and read the startup help.
2. Press `H` to close help.
3. Play one slow learning match.
4. Use `E` to inspect event history when something confusing happens.
5. Press `S` near the end to save the session history.
6. Reset and play a best-of-3 set.
7. After the set, discuss one winning move and one confusing move.

If the first match becomes confusing, do not restart immediately. Press `E`, inspect the event history, and write down the first moment where the game stopped making sense.

## Best-of-3 Format

- Match 1: play slowly and talk through moves.
- Match 2: play normally.
- Match 3: try to exploit what you learned.

Switch seats or player colors after each match if possible.

## Feedback Questions

Open a GitHub issue using the **Human Playtest Feedback** template and answer:

- Did you understand how to win?
- What was the first confusing moment?
- Did you understand why a node was captured?
- Did you understand why a branch went dark?
- Did ROUTE feel useful?
- Did PULSE feel satisfying or unclear?
- Did the 2.5D tilt help readability?
- Did either player want a rematch?
- What move felt smart?
- What made the game feel unfair, slow, or unreadable?

## Useful Attachments

Helpful feedback includes:

- saved session history from `history/`
- screenshot of a confusing board state
- short description of the winning sequence
- whether players were first-time or repeat testers

## Before Submitting

Please include:

- your operating system
- whether you played solo or with another person
- whether this was your first NXS-Go session
- whether you used `E` history or `S` save history
- one thing that made you want, or not want, to rematch

## Current Design Rule

Connection is life.

Isolation is defeat.

Human challenge creates meaning. AI challenge proves durability.
