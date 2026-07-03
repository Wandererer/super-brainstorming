# Phase Input/Output Contracts

각 Phase가 무엇을 받고 무엇을 산출해야 다음 Phase가 시작될 수 있는지의 계약.
게이트가 걸린 전이(5→6, 7→마감)는 **코드가 판정**하며 프롬프트로 우회할 수 없다.

## Phase 1: Framing

| | |
|---|---|
| **Input** | 사용자 주제 (자연어) 또는 structured JSON frame |
| **Process** | 컨텍스트 탐색 → AskUserQuestion (1회, 1-4 그룹) 또는 기본값 추론 → HMW 생성 |
| **Output** | `artifacts/frame.json` (frame_schema.json 준수), `state.json` 초기화 |
| **Exit criteria** | HMW에 솔루션 미내장, anti_goals ≥ 1, 사용자 확인 (Phase 2 승인과 묶기 가능) |
| **Skip 조건** | 유효한 JSON frame 입력 시 Phase 1 전체 스킵 |

## Phase 2: Divergence Planning (모드별)

| | |
|---|---|
| **Input** | `artifacts/frame.json` (`divergence.mode` 포함) |
| **Process** | **creative**: goal_type/wildness_appetite → 렌즈 4-8개 선택 → id block 배정. **research_first**: 마이너 선택(기본 6종) + evidence id block 배정 + 합성 렌즈 3종 고정 |
| **Output** | `artifacts/lens_plan.json`: `{"mode": "creative", "lenses": [{"key": "contrarian", "id_block": "3xx", "research_flavored": false}], "miners": [], "ideas_per_lens": 6, "wildcards": ["random_stimulus"], "target_total": 36}` |
| **Exit criteria** | 사용자 계획 승인 (HMW + 추론 가정 + **mode** + 라인업 + 목표 수 + handoff 기본값을 한 번에 제시) |

### ID Block 배정 규칙

- 렌즈 k (1부터) → `idea_{k}01` ~ `idea_{k}99` (예: 렌즈 3의 다섯 번째 아이디어 = `idea_305`)
- 하이브리드(Phase 4) → `idea_901` ~ `idea_999`
- 전 세션에서 idea_id는 `^idea_\d{3,}$` 형식, 중복 금지 (게이트 하드 체크)
- **research_first evidence 블록**: `ev_1xx` review_miner / `ev_2xx` community_miner / `ev_3xx` competitor_gap_miner / `ev_4xx` trend_miner / `ev_5xx` market_data_miner / `ev_6xx` solution_saturation_miner — `^ev_\d{3,}$` 형식, 중복 금지
- **Phase 4.5 선행기술 블록 (양 모드)**: `ev_7xx` prior-art agent의 existing_solution 카드
- **research_first 합성 렌즈 블록**: `idea_1xx` pain_to_product / `idea_2xx` gap_wedge / `idea_3xx` trend_collision

## Phase 3: Parallel Divergence (모드 분기)

### Mode A — creative

| | |
|---|---|
| **Input** | `lens_plan.json`, frame, **오늘 날짜** |
| **Process** | 렌즈당 에이전트 1개, 2-3개씩 스로틀 배치 (Rate-Limit Guard) |
| **Output** | `artifacts/idea_ledger.jsonl`에 카드 append (스키마: SKILL.md) — status="raw", red_team.checked=false, judge_scores=[] |
| **Exit criteria** | 카드 수 ≥ target_total의 70% (미달 렌즈는 메인 스레드 폴백), `state.json.ideas_count` 갱신 |
| **불가침** | 이 Phase에서 비판·필터링 금지. 계약 위반 카드(산문 혼입)는 재요청 1회 → 실패 시 메인 스레드 수행 |

### Mode B — research_first (3a 채굴 → 3b 발상)

**Phase 3a: Evidence Mining**

| | |
|---|---|
| **Input** | `lens_plan.json`(miners), frame, **오늘 날짜** |
| **Process** | 마이너당 에이전트 1개(기본 6종), 2-3개씩 스로틀 — 각자 다른 소스 클래스 (WebSearch/WebFetch, 연도 필수 부착) |
| **Output** | `artifacts/evidence_ledger.jsonl` append (스키마: SKILL.md) + `outputs/04_evidence_digest.md` |
| **Exit criteria** | evidence ≥ min_evidence(기본 15), 마이너 ≥ min_miners(기본 3) — 미달 마이너는 재실행/메인 스레드 폴백 |
| **불가침** | **URL 없으면 카드 금지** (source_url 하드 체크). 마이너는 아이디어를 내지 않는다 — 채굴만 |

**Phase 3b: Evidence-Grounded Ideation**

| | |
|---|---|
| **Input** | `evidence_ledger.jsonl` 전체, frame, **오늘 날짜** |
| **Process** | 합성 렌즈 3종 (pain_to_product / gap_wedge / trend_collision), 스로틀 배치 |
| **Output** | `idea_ledger.jsonl`에 카드 append — **`evidence_ids` ≥ min_evidence_refs 필수** |
| **Exit criteria** | 카드 수 ≥ target_total의 70%, 모든 카드에 evidence_ids (게이트 exit 1 항목) |
| **불가침** | 판단 유보 동일. 미등록 evidence_id 인용은 하드 에러 (없는 근거 인용 금지) |

## Phase 4: Cross-Pollination

| | |
|---|---|
| **Input** | 전체 ledger (요약본: idea_id/title/one_liner/lens/mechanism) |
| **Process** | 하이브리드 에이전트 1개 — COLLIDE(렌즈 간 결합) + RESCUE(SCAMPER 구조) |
| **Output** | ledger에 하이브리드 카드 append — status="hybrid", parent_ids 필수, id block 9xx |
| **Exit criteria** | 하이브리드 ≥ 1 (게이트 exit 1 항목), parent_ids 참조 무결성 (게이트 exit 2 항목) |
| **불가침** | ledger는 append-only — 기존 카드 수정·삭제 금지 (red-team/judge 병합은 Phase 5) |

## Phase 4.5: Prior-Art Check (선행기술 대조 — 양 모드 공통)

| | |
|---|---|
| **Input** | 전체 후보 카드 (클러스터로 그룹핑), **오늘 날짜** |
| **Process** | prior-art 에이전트 1개 — **클러스터 단위** 검색 1-2회(카드마다 아님 — 비용 계약) → 발견한 기존 제품을 existing_solution evidence 카드(ev_7xx, `pricing` 필수)로 append → 카드별 saturation 라인 산출 |
| **Output** | evidence_ledger에 existing_solution 카드 append + 각 후보 카드에 `saturation` 블록 병합: `{"checked": true, "score": 0-5, "competitor_ids": [...], "wedge": null\|"...", "note": ""}` |
| **Exit criteria** | 전 후보에 saturation.checked + score (게이트 exit 1 항목), competitor_ids 참조 무결성 (exit 2 항목) |
| **불가침** | 경쟁사도 URL 필수 — evidence 카드 없이 competitor_ids 금지. creative 모드도 수행한다 (발산은 검색 없이, **수렴은 근거로**) |

## Phase 5: Convergence

| | |
|---|---|
| **Input** | 전체 ledger (saturation 블록 포함), frame(가중치·mode), evidence_ledger, scoring_rubric.md 앵커 |
| **Process** | ① red-team 1개 → red_team 블록 병합, fatal_flaw → status="killed"+kill_reason (research_first: 장식용 인용 — 근거가 주장을 실제로 지지하지 않는 카드 — 도 fatal 후보) ② 심사 2-3인 독립 (red-team 결과는 보되 서로는 못 봄) → judge_scores 병합 ③ `validate_ideas.py --session <dir>` |
| **Output** | `outputs/ranked_ideas.json`, `outputs/shortlist.json`, `outputs/parked_and_killed.json`, `state.json.convergence` (signature 포함) |
| **Exit criteria** | **exit 0** — exit 2는 데이터 수정 후 재실행, exit 1은 누락 절차 수행 후 재실행. exit 0 전에 Phase 6 진입 금지 |
| **병합 방법** | red-team/judge의 JSONL 출력을 idea_id로 매칭해 해당 카드의 필드에 기록한 **새 ledger 파일을 다시 쓴다** (append-only 원칙의 유일한 예외 — 카드 본문은 불변, red_team/judge_scores/status/kill_reason 필드만 채워진다) |

## Phase 6: Concept Deep-Dive

| | |
|---|---|
| **Input** | **`outputs/shortlist.json`만** (데이터 흐름 락 — ledger에서 임의 선정 금지) |
| **Process** | AskUserQuestion(multiSelect)로 1-3개 선택 → 컨셉당: 접근법 2-3 + 추천 → 섹션 제시 → 점진 승인 → YAGNI → self-review 4체크 |
| **Output** | `state.json.selected_ideas` (idea_id 배열), `outputs/02_concept_briefs/NN_{slug}.md` (idea_id: 라인 필수) |
| **Exit criteria** | 선택된 모든 컨셉의 브리프가 사용자 승인됨 |
| **불가침** | HARD-GATE — 구현 행동 금지 |

## Phase 7: Output & Packaging

| | |
|---|---|
| **Input** | ledger, ranked/shortlist JSON, 승인된 브리프, frame(handoff 설정) |
| **Process** | 템플릿 기반 산출물 작성 → `eval_briefs.py --session <dir>` → FAIL 항목 수정 → 재실행 |
| **Output** | `outputs/00_executive_summary.md`, `01_idea_catalog.md`, `03_parking_lot.md`, `handoff.md`, `eval_briefs.json`, 세션 `README.md`, `state.json.brief_qa` |
| **Exit criteria** | **verdict PASS (exit 0)** + 사용자에게 산출물 위치 안내 + 핸드오프 제안 |

## Gate Summary

| 전이 | 게이트 | 판정자 |
|------|--------|--------|
| Phase 5 → 6 | 스키마 무결성 + 절차 완료(red-team/심사/발산량/하이브리드/**선행기술 대조**) + 랭킹 계산(**포화 시 novelty 상한 + wedge 강제**), (research_first) evidence 무결성·근거 인용·채굴량·마이너 다양성 | `validate_ideas.py` (exit 0) |
| Phase 7 → 마감 | placeholder 0 + 브리프↔쇼트리스트 매핑 + 요약 커버리지 + parking lot 완전성 + 핸드오프 존재, (research_first) 브리프 근거 인용 + evidence digest 존재 | `eval_briefs.py` (PASS) |

두 게이트 모두 `state.json`에 서명/지표를 남긴다. `passed: true`가 없으면 그 게이트는 실행되지 않은 것이다.
