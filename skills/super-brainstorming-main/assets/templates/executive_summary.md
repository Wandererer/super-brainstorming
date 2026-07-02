# Brainstorm Executive Summary: {TOPIC}

## Frame

> **HMW**: {HMW_STATEMENT}

{FRAME_RECAP_PARAGRAPH}

| Dimension | Value |
|-----------|-------|
| Goal | {GOAL_TYPE} |
| Constraints | {CONSTRAINTS} |
| Anti-goals | {ANTI_GOALS} |

## By the Numbers

| Metric | Value |
|--------|-------|
| Ideas generated | {TOTAL_IDEAS} (raw {RAW_COUNT} + hybrid {HYBRID_COUNT}) |
| Lenses deployed | {LENS_COUNT} ({LENS_LIST}) |
| Killed / Parked | {KILLED_COUNT} / {PARKED_COUNT} |
| Judges | {JUDGE_COUNT} (median-aggregated by code) |

## Shortlist (Top {SHORTLIST_SIZE} — computed by validate_ideas.py)

> 순위는 심사 중앙값 × 가중치({WEIGHTS_SUMMARY})로 코드가 계산했다. LLM 선정 아님.

| Rank | ID | Title | One-liner | Score | Wildness |
|------|----|-------|-----------|-------|----------|
| 1 | {IDEA_ID_1} | {TITLE_1} | {ONE_LINER_1} | {SCORE_1} | {WILDNESS_1} |
| 2 | {IDEA_ID_2} | {TITLE_2} | {ONE_LINER_2} | {SCORE_2} | {WILDNESS_2} |
| 3 | {IDEA_ID_3} | {TITLE_3} | {ONE_LINER_3} | {SCORE_3} | {WILDNESS_3} |

{WILDCARD_SEAT_NOTE}

## Selected Concepts

{FOR_EACH_SELECTED_CONCEPT}

### {SELECTED_TITLE} ({SELECTED_IDEA_ID})

{ELEVATOR_PITCH_PARAGRAPH}

- **Riskiest assumption**: {RISKIEST_ASSUMPTION}
- **Next step**: {NEXT_STEP}
- **Brief**: `outputs/02_concept_briefs/{BRIEF_FILENAME}`

## Worth a Second Look (아까운 것들)

{PARKED_HIGHLIGHTS} — 조건이 바뀌면 `outputs/03_parking_lot.md`에서 부활 후보를 찾을 것.

## Next Steps & Handoff

{HANDOFF_SUMMARY} — ready-to-run queries in `outputs/handoff.md`.

---

### Methodology Note
This brainstorm generated {TOTAL_IDEAS} ideas across {LENS_COUNT} thinking lenses,
red-teamed all candidates, scored them with {JUDGE_COUNT} independent judges, and
ranked them deterministically (`validate_ideas.py`, signature `{SIGNATURE_SHORT}`).
Divergence deferred judgment; convergence was computed, not chosen.
