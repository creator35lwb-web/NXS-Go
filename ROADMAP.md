# NXS-Go Roadmap

## v0.1-A: Clarity Playtest

Goal: make the first playable prototype understandable without external explanation.

- Validate whether new players understand SYNCH, ROUTE, PULSE, and isolation.
- Improve first-turn guidance.
- Improve win/loss comprehension.
- Add a compact rulebook and first-game examples.
- Keep the prototype local-first and easy to run.

## v0.1-B: Feedback and Balance

Goal: improve readability and decision quality after the core loop is clear.

- Add stronger visual feedback for pressure, capture, and blackout.
- Improve event history explanations.
- Add screenshots and example sessions.
- Capture balance notes from playtests.

## v0.2: AI Arena

Goal: make NXS-Go testable by bots, agents, and future self-play systems.

- Formalize legal actions, observations, rewards, and terminal states.
- Add baseline bots: random, source defense, and greedy isolation.
- Run bounded self-play tests.
- Use Gemma-family open-source models as the first LLM-agent target.
- Measure whether simple agents solve the current rule set too easily.

## v0.3: Asymmetric Abilities

Goal: add identity only after the base loop and AI arena reveal real strategic gaps.

- Prototype Signal Amplify.
- Prototype Noise Ghost Node.
- Test whether asymmetry improves the thesis or creates confusion.

## v1.0: Public Local Release

Goal: make NXS-Go easy for people to run locally, study, modify, and share.

- Stable ruleset.
- Public screenshots.
- Contributor guide.
- Architecture notes.
- Packaged release instructions.
