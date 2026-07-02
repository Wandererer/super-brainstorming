# Changelog

All notable changes to super-brainstorming will be documented in this file.

## [0.1.0] - 2026-07-02

### Added

- Initial release.
- `/super-brainstorming` command router — `[topic]` / `research [topic]` / `resume` / `status` / `frame` / interactive menu.
- **Two divergence modes**:
  - **`creative` (default)** — 13 thinking lenses (contrarian, first principles, cross-industry,
    constraint flip, future-back, SCAMPER… + 3 wildcards) diverge in parallel with judgment deferred.
  - **`research_first` (검색 발굴 — research → brainstorming)** — Phase 3a deploys 5 evidence miners
    (reviews / community complaints & workarounds / competitor gaps / trends / market data) that scour
    different source classes in parallel into an `evidence_ledger.jsonl` (**no URL, no card**);
    Phase 3b grows every idea from cited `evidence_ids` via 3 synthesis lenses
    (pain_to_product, gap_wedge, trend_collision). The gate rejects evidence-free ideas.
- **7-Phase divergent-convergent pipeline**:
  Framing (Socratic HMW) → Divergence Planning → Parallel Divergence (mode fork) →
  Cross-Pollination → Convergence (red-team → independent judges → **deterministic code gate**) →
  Concept Deep-Dive → Output & Handoff.
- **`validate_ideas.py`** — deterministic convergence gate: schema/reference integrity (exit 2),
  process violations like missing red-team, judges, or evidence citations (exit 1), median score
  aggregation, weighted ranking, a code-enforced **wildcard seat** for wild ideas, and
  research-mode evidence gates (`min_evidence`, `min_miners`, `min_evidence_refs`).
  `shortlist.json` is produced **only on exit 0** — Phase 6's sole input (data-flow lock).
- **`eval_briefs.py`** — deterministic closing self-review scorer: placeholder scan,
  brief↔shortlist mapping, summary coverage, parking-lot completeness, handoff presence,
  and (research_first) per-brief evidence citations plus `04_evidence_digest.md` presence.
- **Socratic framing policy** — HARD-GATE (no implementation before brief approval),
  one-topic-at-a-time questions, 2-3 approaches with recommendation,
  incremental validation, ruthless YAGNI.
- **Validation handoff** — each selected concept's riskiest assumption is converted into
  a ready-to-run research query in `handoff.md` (diverge → validate two-step workflow built in).
- Session state management (`BRAINSTORM/*/state.json`) with resume support.
- Lens library (10 core + 3 wildcard + 3 synthesis lenses), 5 miner prompts, scoring rubric SSOT,
  phase contracts, output templates (including evidence digest), and 2 example frames
  (one per mode).
