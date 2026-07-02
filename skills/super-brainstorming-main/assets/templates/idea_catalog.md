# Idea Catalog: {TOPIC}

> 발산 전체 기록 — {TOTAL_IDEAS}개 아이디어, {LENS_COUNT}개 렌즈, 하이브리드 {HYBRID_COUNT}개.
> 점수는 `validate_ideas.py`가 심사 중앙값으로 계산. 전체 랭킹: `outputs/ranked_ideas.json`

## Cluster Map

| Cluster | Theme | Ideas | Best Rank |
|---------|-------|-------|-----------|
| {CLUSTER_1_NAME} | {CLUSTER_1_THEME} | {CLUSTER_1_IDS} | #{CLUSTER_1_BEST} |
| {CLUSTER_2_NAME} | {CLUSTER_2_THEME} | {CLUSTER_2_IDS} | #{CLUSTER_2_BEST} |

---

## {CLUSTER_1_NAME}

{CLUSTER_1_INTRO_SENTENCE}

| Rank | ID | Title | One-liner | Lens | Wild | Score |
|------|----|-------|-----------|------|------|-------|
| {R} | {IDEA_ID} | {TITLE} | {ONE_LINER} | {LENS} | {WILDNESS} | {SCORE} |

### 주목할 카드

#### {NOTABLE_IDEA_TITLE} ({NOTABLE_IDEA_ID})
- **Mechanism**: {MECHANISM}
- **Target**: {TARGET_USER}
- **Assumptions**: {ASSUMPTIONS}
- **Red-team**: {TOP_OBJECTION}
{EVIDENCE_LINE_IF_ANY}

---

## Hybrids (교차 수분 결과)

| ID | Title | Parents | 결합 방식 |
|----|-------|---------|----------|
| {HYBRID_ID} | {HYBRID_TITLE} | {PARENT_IDS} | {COLLISION_NOTE} |

---

## Lens Performance

어떤 렌즈가 쇼트리스트에 기여했는가 — 다음 세션의 렌즈 선택 참고용.

| Lens | Ideas | Shortlisted | Avg Score |
|------|-------|-------------|-----------|
| {LENS_KEY} | {LENS_IDEA_COUNT} | {LENS_SHORTLIST_COUNT} | {LENS_AVG} |
