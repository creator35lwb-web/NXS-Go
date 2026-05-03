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

## v0.2: AI Arena and Readability

Goal: make NXS-Go testable by bots, agents, future self-play systems, and human readability probes.

- Formalize legal actions, observations, rewards, and terminal states.
- Add baseline bots: random, source defense, and greedy isolation.
- Run bounded self-play tests.
- Test board geometry and search variants before changing rules.
- Improve route readability through 2.5D tilt, hover inspection, and future camera prototypes.

## v0.3: LLM Agent Trial

Goal: test whether an open-source LLM agent can understand state, choose legal actions, and explain decisions.

- Use Gemma-family open-source models as the first LLM-agent target.
- Compare LLM choices against baseline agents.
- Measure legal-action rate, explanation quality, and strategic usefulness.

## v0.4: Asymmetric Abilities

Goal: add identity only after the base loop, AI arena, and LLM trials reveal real strategic gaps.

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
