# Brainstorm Session: {TOPIC}

- **Session**: `{SESSION_ID}`
- **HMW**: {HMW_STATEMENT}
- **Status**: {STATUS} (Phase {CURRENT_PHASE}/7)
- **Created**: {CREATED_AT} · **Updated**: {UPDATED_AT}

## Where to Look

| What you want | File |
|---------------|------|
| 3분 요약 + 쇼트리스트 | `outputs/00_executive_summary.md` |
| 전체 아이디어 ({TOTAL_IDEAS}개, 클러스터·점수) | `outputs/01_idea_catalog.md` |
| 선택 컨셉 심화 브리프 | `outputs/02_concept_briefs/` |
| 기각·보류 아이디어와 부활 조건 | `outputs/03_parking_lot.md` |
| 다음 단계 (insane-research 검증 쿼리) | `outputs/handoff.md` |
| 기계가 계산한 랭킹 원자료 | `outputs/ranked_ideas.json`, `outputs/shortlist.json` |
| 발산 원본 (전 카드) | `artifacts/idea_ledger.jsonl` |

## Verification Trail

- 수렴 게이트: `validate_ideas.py` — signature `{SIGNATURE_SHORT}`, passed: {CONVERGENCE_PASSED}
- 마감 채점: `eval_briefs.py` — verdict {BRIEF_QA_VERDICT}

## Resume

```
/super-brainstorming resume {SESSION_ID}
```
