# Handoff: {TOPIC}

> 발산 → 검증. 선택된 각 컨셉마다 **쿼리 2종 필수**: ① 가장 위험한 가정 ② 경쟁 지형.
> (super-brainstorming의 터미널 상태는 구현이 아니라 이 핸드오프다)

## Concept 1: {SELECTED_TITLE_1} ({SELECTED_IDEA_ID_1})

**검증 대상 가정**: {RISKIEST_ASSUMPTION_1}

### Query ① — Riskiest assumption

```
/insane-research {VALIDATION_QUESTION_1 — 시장성·경쟁·실현 근거를 묻는 구체적 질문, 연도 포함}
```

### Structured query (insane-research query_schema)

```json
{
  "task": {
    "title": "{RESEARCH_TITLE_1}",
    "objective": "{OBJECTIVE_1 — 이 컨셉의 go/no-go 판단에 필요한 증거}",
    "type": "evaluative"
  },
  "context": {
    "background": "super-brainstorming session {SESSION_ID}, concept {SELECTED_IDEA_ID_1}",
    "audience": "technical",
    "use_case": "Validate the riskiest assumption before building"
  },
  "questions": {
    "primary": "{PRIMARY_QUESTION_1}",
    "secondary": ["{SECONDARY_1a — 경쟁 현황}", "{SECONDARY_1b — 수요 근거}", "{SECONDARY_1c — 실현 장벽}"],
    "exclusions": ["{OUT_OF_SCOPE_1}"]
  },
  "constraints": {
    "timeframe": {"focus_period": "{RECENT_2_YEARS}"},
    "sources": {"min_quality": "C"}
  },
  "output": {"format": "comprehensive_report", "structure": {"include_executive_summary": true}}
}
```

### Query ② — 경쟁 지형 (필수)

> Phase 4.5 선행기술 대조는 클러스터 단위 스냅샷이었다. 선택된 컨셉은 제품 단위로 정밀 재검증한다.
> 알려진 경쟁: {KNOWN_COMPETITORS_FROM_SATURATION — ev_id와 제품명}

```
/insane-research {CONCEPT_TITLE_1}의 경쟁 지형 {YEAR}: 누가 이미 이 문제를 풀고 있나 — 기존 제품 전수 목록, 각각의 가격/무료 여부, traction(사용자 수·평점·성장), 그리고 그들이 {WEDGE_1}를 못 하는 이유가 실제로 유효한지
```

---

## Concept 2: {SELECTED_TITLE_2} ({SELECTED_IDEA_ID_2})

{SAME_STRUCTURE_AS_CONCEPT_1 — Query ① + Query ② 모두}

---

## Alternative Paths

- **스펙/PRD로**: 브리프를 설계 문서 입력으로 사용 — `show-me-the-prd` 플러그인이 있으면 인터뷰 기반 PRD 생성 가능
- **다시 발산**: parking lot의 parked 아이디어로 새 프레임 — `/super-brainstorming frame`
- **직접 검증**: 각 브리프의 "2주 내 검증 방법" 컬럼이 가장 싼 실험이다 — 리서치 없이 바로 실행 가능

> insane-research 플러그인이 없다면: `/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git` → `/plugin install insane-research`
