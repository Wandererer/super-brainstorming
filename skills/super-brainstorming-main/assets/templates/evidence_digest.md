# Evidence Digest: {TOPIC}

> research_first 모드의 채굴 증빙 — 어디를 뒤졌고, 무엇이 나왔고, 어떤 아이디어로 이어졌는가.
> 원자료: `artifacts/evidence_ledger.jsonl` ({EVIDENCE_COUNT}건, 마이너 {MINER_COUNT}종)

## Sweep Coverage (어디를 뒤졌나)

| Miner | Sources searched | Cards | Strongest signal |
|-------|------------------|-------|------------------|
| review_miner | {REVIEW_SOURCES — 앱스토어/G2/…} | {REVIEW_COUNT} | {REVIEW_TOP_SIGNAL} |
| community_miner | {COMMUNITY_SOURCES — Reddit/HN/카페…} | {COMMUNITY_COUNT} | {COMMUNITY_TOP_SIGNAL} |
| competitor_gap_miner | {COMPETITOR_SOURCES} | {GAP_COUNT} | {GAP_TOP_SIGNAL} |
| trend_miner | {TREND_SOURCES} | {TREND_COUNT} | {TREND_TOP_SIGNAL} |
| market_data_miner | {MARKET_SOURCES} | {MARKET_COUNT} | {MARKET_TOP_SIGNAL} |
| solution_saturation_miner | {SATURATION_SOURCES — 앱스토어 차트/Product Hunt/GitHub} | {SATURATION_COUNT} | {SATURATION_TOP_SIGNAL — 가장 포화된 니치} |
| prior-art (Phase 4.5) | {PRIOR_ART_SEARCHES — 클러스터별 검색어} | {PRIOR_ART_COUNT} | {MOST_SATURATED_CLUSTER} |

> 커버하지 못한 소스 클래스가 있으면 여기 명시한다 — 침묵하는 절단은 "다 봤다"로 읽힌다: {UNCOVERED_NOTE}

## Saturation Map (니치별 포화도 — 공급측)

| 클러스터 | Saturation | 무료/OSS 존재 | 결정적 경쟁 제품 |
|----------|-----------|---------------|------------------|
| {CLUSTER_1} | {SAT_SCORE_1}/5 | {HAS_FREE_1} | {KEY_COMPETITOR_1 ({COMP_EV_1})} |

## Top Signals (강도순)

### {SIGNAL_1_CLAIM} — strength {SIGNAL_1_STRENGTH}
- **Evidence**: {SIGNAL_1_EV_IDS}
- **Quote**: "{SIGNAL_1_QUOTE}" — [{SIGNAL_1_SOURCE_NAME}]({SIGNAL_1_URL}), {SIGNAL_1_DATE}
- **→ 이어진 아이디어**: {SIGNAL_1_IDEA_IDS}

### {SIGNAL_2_CLAIM} — strength {SIGNAL_2_STRENGTH}
- **Evidence**: {SIGNAL_2_EV_IDS}
- **Quote**: "{SIGNAL_2_QUOTE}" — [{SIGNAL_2_SOURCE_NAME}]({SIGNAL_2_URL}), {SIGNAL_2_DATE}
- **→ 이어진 아이디어**: {SIGNAL_2_IDEA_IDS}

## Evidence → Idea Map

| Evidence | Type | Claim (요약) | Cited by ideas |
|----------|------|--------------|----------------|
| {EV_ID} | {EV_TYPE} | {EV_CLAIM} | {CITING_IDEA_IDS} |

## Orphan Evidence (아이디어로 이어지지 않은 근거)

버려진 근거가 아니라 **다음 세션의 씨앗**이다.

- {ORPHAN_EV_ID}: {ORPHAN_CLAIM} — 왜 이번엔 못 썼나: {ORPHAN_REASON}
