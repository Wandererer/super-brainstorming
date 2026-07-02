English | [한국어](README.ko.md)

# super-brainstorming

A multi-agent brainstorming plugin for Claude Code. Throw it a topic and a fleet of agents mines and diverges ideas in parallel, then a code gate converges them coldly into a scored ranking and approved concept briefs.

**Diverge hot, converge cold. Evidence comes with URLs.**

## Install

```
/plugin marketplace add Wandererer/super-brainstorming
/plugin install super-brainstorming
```

Restart Claude Code after installing — `/super-brainstorming` becomes available.

## Two divergence modes

### 🔍 Research-first — `research_first`

"Dig everywhere, keep only evidence-backed ideas." Five miner agents each dig a different source class in parallel.

| Miner | Where it digs | What it extracts |
|-------|---------------|------------------|
| Reviews | App stores, G2, store reviews | 1-3★ reviews, "I wish it did X" patterns |
| Community | Reddit, HN, forums | Recurring complaints, user-built workarounds |
| Competitor gaps | 5-8 incumbent products | What none of them do — and why |
| Trends | Changes in the last 1-2 years | Why it became possible now (timing fuel) |
| Market data | Reports, quantitative signals | Growing categories, pricing benchmarks |

Every finding lands in `evidence_ledger.jsonl` with its source URL — **no URL, no card** — and three synthesis lenses (pain→product, gap→wedge, trend×pain) grow ideas only from that evidence. Ideas that don't cite evidence are rejected by the gate.

```
/super-brainstorming research unmet needs in the AI coding tool market
```

### 🎨 Thinking lenses — `creative` (default)

Pure divergence, no search. Thirteen lens agents — contrarian, first principles, cross-industry transplant, pain archaeology, constraint flip, future-back, SCAMPER, resource extremes, adjacent possible, anti-persona, plus wildcards (random stimulus, villain, 10x) — each diverge with their own method. No criticism during divergence; the red-team only exists at convergence.

```
/super-brainstorming ways to reinvent our team retrospectives
```

## The gates every idea must pass

The point of this plugin isn't the divergence — it's that **convergence is delegated to code**. Every idea passes four gates before reaching the shortlist.

1. **Red-team** — hunts structural flaws (constraint violations, self-contradictions, anti-goal breaches) and kills with a written reason. "Hard" is not a kill reason.
2. **2-3 independent judges** — score 5 axes blind to each other: impact `.30` · feasibility `.25` · novelty `.20` · fit `.15` · timing `.10` (weights configurable per session)
3. **`validate_ideas.py`** — **computes** the ranking from judge medians × weights. The shortlist file only exists after this gate passes, so the LLM cannot hand-pick winners even if it wanted to.
4. **Wildcard seat** — if the top ranks are all safe bets, code swaps the last seat for the highest-ranked wild idea (wildness ≥ 4).

The deep-dive stage has gates too: 2-3 execution approaches compared per concept, an MVP trimmed by YAGNI, and every riskiest assumption paired with a two-week test. And a **HARD-GATE — no implementation starts before the brief is approved.** Right before closing, `eval_briefs.py` scores leftover placeholders, missing evidence, and document consistency — a FAIL blocks the close.

## Commands

| Command | |
|---------|---|
| `/super-brainstorming research [topic]` | Start directly in research-first mode |
| `/super-brainstorming [topic]` | Mode recommended based on the topic |
| `/super-brainstorming frame` | Shape a vague topic into an HMW frame |
| `/super-brainstorming resume [id]` | Resume an interrupted session |
| `/super-brainstorming status` | All sessions at a glance |

Natural language works too: "brainstorm ideas for [topic]", "research-first brainstorm on [topic]".

## What you get

In `BRAINSTORM/{topic}_{timestamp}/outputs/`:

| File | Contents |
|------|----------|
| `00_executive_summary.md` | Summary + shortlist table (scores, wildness, evidence) |
| `01_idea_catalog.md` | All 30+ ideas — clusters, scores, red-team objections |
| `02_concept_briefs/` | Deep-dives: approach comparison, MVP In/Out, riskiest assumptions + 2-week tests |
| `03_parking_lot.md` | Killed & parked — with reasons and revive conditions (kills are records too) |
| `04_evidence_digest.md` | (research-first) where we dug and what we found, all with URLs |
| `handoff.md` | Validation queries for the next step |

Session state persists in `state.json` with gate signatures — interrupt anytime and `resume`.

## What comes after

Briefs aren't the end. For each selected concept, a research query targeting its riskiest assumption is auto-generated in `handoff.md`. If you have a deep-research tool, run the queries as-is; if not, each brief's "two-week test" column is your cheapest experiment.

## Requirements

- [Claude Code](https://docs.anthropic.com/claude-code) CLI
- Python 3 (convergence gate & closing scorer)
- WebSearch — the digging engine for research-first mode

## License

MIT © Wandererer
