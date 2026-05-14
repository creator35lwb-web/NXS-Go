# MACP v2.2 Handoff: G - AgentKey Initial Intelligence Leads

**Agent:** G  
**Session type:** intelligence / external discussion discovery  
**Date:** 2026-05-14  
**Tool:** AgentKey MCP  
**Project:** NXS-Go  
**Status:** INITIAL FINDINGS

---

## Current Objective

Test whether AgentKey MCP improves external intelligence gathering for NXS-Go compared with ordinary web-only search.

The strategic question:

> Where are people already discussing abstract strategy, connection games, graph games, isolation games, or Go-like design spaces that could help NXS-Go find peers, playtesters, or conceptual neighbors?

---

## What AgentKey Added

AgentKey produced useful results in two lanes:

1. Web search with community-heavy results.
2. Reddit/social structured search with post metadata, subreddit names, scores, comments, timestamps, and direct permalinks.

This is stronger than ordinary web search for G because NXS-Go needs human-market intelligence, not only search-engine-indexed pages.

---

## Strongest Initial Leads

### 1. `r/abstractgames`

**Why it matters:**  
This is the most directly relevant community lead. It is small but focused, and AgentKey surfaced a recent 2026 post about a collection of around 50 abstract strategy games playable with the same board and pieces.

**Strategic value:**  
Good candidate for future soft discovery after NXS-Go has a clearer one-page rulebook, screenshots, and playtest ask.

**Evidence:**  
AgentKey Reddit search returned a post from `r/abstractgames`:

- Title: "Collection of around 50 abstract strategy games, that can all be played with the same board and pieces"
- Date: 2026-03-17
- Score: 177
- Comments: 36
- Source: https://www.reddit.com/r/abstractgames/comments/1rwfubi/collection_of_around_50_abstract_strategy_games/
- Related project mentioned: http://Playtiles.org

### 2. `r/boardgames`

**Why it matters:**  
Broader and noisier than `r/abstractgames`, but much larger. AgentKey found the same abstract-games collection cross-posted or similarly posted there.

**Strategic value:**  
Useful later for outreach only after NXS-Go has stronger packaging and screenshots. Not ideal for early fragile prototype feedback because broad communities can punish unclear onboarding.

**Evidence:**  
AgentKey Reddit search returned a related post from `r/boardgames`:

- Title: "Collection of around 50 abstract strategy games, that can all be played with the same board and pieces"
- Date: 2026-03-17
- Score: 174
- Comments: 48
- Source: https://www.reddit.com/r/boardgames/comments/1rwh5eg/collection_of_around_50_abstract_strategy_games/

### 3. BoardGameGeek Graph-Game Lists

**Why it matters:**  
NXS-Go's playable structure is a node/edge network. BoardGameGeek has existing discussion around games that use graphs as maps.

**Strategic value:**  
Useful for competitive mapping: not necessarily direct competitors, but relevant mechanical relatives.

**Evidence:**  
AgentKey web search returned:

- "Games that use graphs for maps (a mathematical geeklist)"
- Source: https://boardgamegeek.com/geeklist/37958/games-that-use-graphs-for-maps-a-mathematical-geek

### 4. BoardGameGeek Abstract Strategy Lists

**Why it matters:**  
NXS-Go needs to understand the abstract strategy canon and community vocabulary before public positioning. BoardGameGeek lists are useful for mapping player expectations around simple rules and deep mastery.

**Strategic value:**  
Reference set for explaining what NXS-Go is and is not: it is closer to connection/isolation graph strategy than territory control.

**Evidence:**  
AgentKey web search returned:

- "ABC of amazing abstract strategy games"
- Source: https://boardgamegeek.com/geeklist/231173/abc-of-amazing-abstract-strategy-games

### 5. Go/Baduk Players Discussing Other Abstract Games

**Why it matters:**  
NXS-Go is not trying to copy Go, but Go players are a relevant comparison audience because they understand life/death, tension, and simple rules with deep consequences.

**Strategic value:**  
Useful for messaging discipline: avoid saying "new Go"; instead say NXS-Go replaces territory with connectivity and isolation.

**Evidence:**  
AgentKey web search returned:

- Reddit thread: "What other abstract strategy games do you play? Do any of them ..."
- Source: https://www.reddit.com/r/baduk/comments/zbikgd/what_other_abstract_strategy_games_do_you_play_do/

### 6. Academic Neighbor: Isolation Games on Graphs

**Why it matters:**  
This is the most precise academic adjacency found so far. It is not a direct competitor, but it validates that graph isolation is a real formal game-theory neighborhood.

**Strategic value:**  
Good citation for long-term design notes or research framing, not for player-facing marketing.

**Evidence:**  
AgentKey web search returned:

- "Isolation game on graphs"
- Source: https://arxiv.org/html/2409.14180v1

### 7. Maker-Breaker / Connectivity Game Theory

**Why it matters:**  
NXS-Go has a build/cut pressure dynamic. Maker-breaker and percolation games are relevant theoretical relatives because they involve connectivity objectives over graph-like boards.

**Strategic value:**  
Useful for XV/G research, but too academic for current v0.1-A player-facing docs.

**Evidence:**  
AgentKey web search returned:

- "Maker-breaker percolation games II: Escaping to infinity"
- Source: https://www.sciencedirect.com/science/article/pii/S0095895620300666

---

## What We Have Not Proven

- No direct NXS-Go competitor was identified in this initial pass.
- No evidence yet that abstract strategy communities will care about NXS-Go.
- Reddit/social discovery found adjacent communities, not product-market validation.
- Academic graph-isolation literature is conceptually relevant but not player-market evidence.
- AgentKey results need deeper follow-up before any public positioning claim.

---

## G Interpretation

AgentKey is useful for G and XV intelligence work.

The strongest immediate value is not "finding competitors." It is finding:

- vocabulary
- community venues
- similar mechanical families
- possible playtest audiences
- academic/theoretical neighbors

NXS-Go should continue to position itself carefully:

> Not Go with nodes.  
> Not a generic graph game.  
> A local-first connection/isolation strategy game where Source connectivity is life.

---

## G0 Boundary

No implementation change should come directly from these leads yet.

Current implementation priority remains:

- base-loop clarity
- human playtest readiness
- rule explanation
- stability/regression tests

AgentKey should feed strategy and research handoffs first. Code changes require a concrete, testable defect or accepted design decision.

---

## Recommended Next Probe

Run a more focused AgentKey research pass with lower-volume queries:

1. Search `r/abstractgames` for "connection game", "graph game", "Go", "Hex", "Havannah", "Twixt".
2. Search BoardGameGeek for graph/network/connection abstracts.
3. Search recent YouTube and blog content for "modern abstract strategy games".
4. Build a public-safe `docs/COMPETITIVE_LANDSCAPE.md` only after sources are checked manually.

---

## Requested Next Agent

**XV** should use this handoff as a seed list for a deeper intelligence report.

Required XV output:

- source-by-source assessment
- direct competitor vs adjacent relative classification
- community outreach risk
- recommended first public discussion venue
- what not to claim publicly yet

