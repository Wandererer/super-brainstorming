#!/usr/bin/env python3
"""
eval_briefs.py — super-brainstorming의 **마감 채점기** (Phase 7 자기검증).

설계 의도:
  - Phase 6 브리프 Self-Review(placeholder 스캔·내부 일관성·범위·모호성 체크) 중
    기계화 가능한 부분을 결정론적으로 측정한다.
  - 서술형 self-review는 LLM이 하되(SKILL.md Phase 6), 최종 마감은 이 채점기의
    verdict가 판정한다 — FAIL이면 고쳐서 재실행, 그 상태로 마감 금지.

검사 항목:
  1. placeholder 스캔    — outputs/**/*.md에 {UPPER_TOKEN}·TBD·TODO·FIXME 잔존 여부
  2. 브리프↔쇼트리스트  — 모든 컨셉 브리프의 idea_id가 shortlist.json에 존재
                          (데이터 흐름 락: 게이트 밖 아이디어 심화 금지)
  3. 선택 커버리지       — state.json.selected_ideas 전부에 브리프 존재
  4. 요약 커버리지       — executive summary가 선택된 컨셉을 전부 언급 (idea_id 또는 제목)
  5. parking lot 완전성  — ledger의 killed 아이디어 전부가 03_parking_lot.md에 등재
  6. 핸드오프 존재       — handoff.md 존재, insane-research 모드면 선택 컨셉당 검증 쿼리 2종
                          (실제 /insane-research 라인 ≥ 2×selected — 위험 가정 + 경쟁 지형)
  7. 근거 인용 (research_first 모드 한정)
                          — 각 브리프가 evidence 참조(ev_ id 또는 URL)를 ≥1 포함,
                            outputs/04_evidence_digest.md 존재 (어디를 뒤졌는지의 증빙)

출력:
  <session>/outputs/eval_briefs.json   (verdict + metrics + issues)
  <session>/state.json 의 "brief_qa" 블록

종료 코드:
  0  PASS
  1  FAIL (issues 있음 — 고쳐서 재실행)
  2  평가 불가 (세션/쇼트리스트 없음 — 수렴 게이트가 먼저 통과해야 함)
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

PLACEHOLDER_RE = re.compile(r"\{[A-Z][A-Z0-9_]{2,}\}")
TOKEN_RE = re.compile(r"\b(TBD|TODO|FIXME|XXX)\b")
LOREM_RE = re.compile(r"lorem\s+ipsum", re.IGNORECASE)
IDEA_ID_LINE_RE = re.compile(r"idea_id:\s*(idea_\d{3,})")
IDEA_ID_ANY_RE = re.compile(r"idea_\d{3,}")
EVIDENCE_REF_RE = re.compile(r"\bev_\d{3,}\b|https?://")
INSANE_QUERY_RE = re.compile(r"^\s*/insane-research\b", re.MULTILINE)
MIN_SUMMARY_CHARS = 300


def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _read_frame(session):
    """frame.json 로드 — 없거나 JSON 객체가 아니면 {} (프레임은 선택 입력)."""
    frame = _read_json(os.path.join(session, "artifacts", "frame.json"))
    return frame if isinstance(frame, dict) else {}


def _read_jsonl(path):
    """JSONL 읽기. (records, errors) 반환 — dict 아닌 레코드는 issue로 수집."""
    records, errors = [], []
    if not os.path.exists(path):
        return records, errors
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                errors.append(f"{os.path.basename(path)}:{lineno} 레코드가 JSON 객체가 아님")
                continue
            records.append(rec)
    return records, errors


def scan_placeholders(out_dir):
    """outputs/**/*.md에서 미치환 placeholder·미완성 토큰 수집."""
    found = []
    for path in sorted(glob.glob(os.path.join(out_dir, "**", "*.md"), recursive=True)):
        text = _read(path) or ""
        rel = os.path.relpath(path, out_dir)
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in PLACEHOLDER_RE.finditer(line):
                found.append(f"{rel}:{lineno} 미치환 placeholder {m.group()}")
            for m in TOKEN_RE.finditer(line):
                found.append(f"{rel}:{lineno} 미완성 토큰 {m.group()}")
            if LOREM_RE.search(line):
                found.append(f"{rel}:{lineno} lorem ipsum 잔존")
    return found


def extract_brief_id(path):
    """브리프에서 idea_id 추출 — `idea_id:` 라인 우선, 없으면 첫 idea_id 패턴."""
    text = _read(path) or ""
    m = IDEA_ID_LINE_RE.search(text)
    if m:
        return m.group(1)
    m = IDEA_ID_ANY_RE.search(text)
    return m.group(0) if m else None


def evaluate(session):
    out_dir = os.path.join(session, "outputs")
    state_path = os.path.join(session, "state.json")
    shortlist_path = os.path.join(out_dir, "shortlist.json")

    # 평가 전제: 수렴 게이트 산출물이 있어야 한다 (exit 2)
    shortlist_doc = _read_json(shortlist_path)
    if (
        not shortlist_doc
        or not isinstance(shortlist_doc, dict)
        or not isinstance(shortlist_doc.get("shortlist"), list)
    ):
        print(
            "[평가 불가] outputs/shortlist.json 없음 또는 형식 오류 — validate_ideas.py (exit 0) 먼저 통과 필요.",
            file=sys.stderr,
        )
        return 2
    state = _read_json(state_path)
    if not isinstance(state, dict):
        print(f"[평가 불가] state.json 없음 또는 JSON 객체 아님: {state_path}", file=sys.stderr)
        return 2

    shortlist = shortlist_doc["shortlist"]
    shortlist_ids = {c.get("idea_id") for c in shortlist}
    titles_by_id = {c.get("idea_id"): (c.get("title") or "") for c in shortlist}
    selected = [i for i in (state.get("selected_ideas") or []) if i]

    issues = []

    # 0) 선택 기록 존재 — 빈 선택은 vacuous PASS의 근원
    if not selected:
        issues.append("state.selected_ideas 없음 — Phase 6 선택 기록 필요")

    # 1) placeholder 스캔
    placeholders = scan_placeholders(out_dir)
    issues.extend(placeholders)

    # 2) 브리프 ↔ 쇼트리스트 매핑
    brief_dir = os.path.join(out_dir, "02_concept_briefs")
    brief_files = sorted(glob.glob(os.path.join(brief_dir, "*.md")))
    brief_ids = {}
    orphan_briefs = []
    for path in brief_files:
        rel = os.path.relpath(path, out_dir)
        bid = extract_brief_id(path)
        if not bid:
            orphan_briefs.append(f"{rel}: idea_id 라인 없음 (템플릿 계약 위반)")
            continue
        brief_ids[bid] = rel
        if bid not in shortlist_ids:
            orphan_briefs.append(
                f"{rel}: '{bid}'는 shortlist에 없음 (게이트 밖 아이디어 심화 — 데이터 흐름 락 위반)"
            )
    issues.extend(orphan_briefs)

    # 2b) 브리프 수량: frame.output.brief_count(기본 2)와 shortlist 크기 중 작은 값 이상
    frame = _read_frame(session)
    brief_count = ((frame.get("output") or {}).get("brief_count"))
    if not isinstance(brief_count, int) or brief_count < 0:
        brief_count = 2
    required_briefs = min(brief_count, len(shortlist))
    if len(brief_files) < required_briefs:
        issues.append(
            f"컨셉 브리프 {len(brief_files)}개 < 필요 {required_briefs}개 "
            f"(output.brief_count {brief_count}, shortlist {len(shortlist)}) — Phase 6 심화 미완"
        )

    # 3) 선택 커버리지: selected_ideas 전부에 브리프 존재
    missing_briefs = [
        f"selected '{sid}'의 컨셉 브리프 없음 (02_concept_briefs/)"
        for sid in selected
        if sid not in brief_ids
    ]
    issues.extend(missing_briefs)

    # 4) 요약 커버리지
    summary_gaps = []
    summary_path = os.path.join(out_dir, "00_executive_summary.md")
    summary = _read(summary_path)
    if summary is None:
        summary_gaps.append("00_executive_summary.md 없음")
    elif len(summary.strip()) < MIN_SUMMARY_CHARS:
        summary_gaps.append(
            f"00_executive_summary.md가 {len(summary.strip())}자 — 최소 {MIN_SUMMARY_CHARS}자"
        )
    else:
        summary_cf = summary.casefold()
        for sid in selected:
            title = titles_by_id.get(sid, "")
            if sid not in summary and (not title or title.casefold() not in summary_cf):
                summary_gaps.append(
                    f"executive summary가 선택 컨셉 '{sid}'를 언급하지 않음 (id 또는 제목)"
                )
    issues.extend(summary_gaps)

    # 5) parking lot 완전성: killed 전부 등재
    unlisted_kills = []
    ledger, ledger_errs = _read_jsonl(os.path.join(session, "artifacts", "idea_ledger.jsonl"))
    unlisted_kills.extend(ledger_errs)
    killed = [c for c in ledger if c.get("status") == "killed"]
    if killed:
        parking = _read(os.path.join(out_dir, "03_parking_lot.md"))
        if parking is None:
            unlisted_kills.append(f"killed {len(killed)}건 있는데 03_parking_lot.md 없음")
        else:
            for c in killed:
                cid = c.get("idea_id")
                if cid and cid not in parking:
                    unlisted_kills.append(
                        f"killed '{cid}'가 03_parking_lot.md에 없음 (기각도 기록이다)"
                    )
    issues.extend(unlisted_kills)

    # 6) 핸드오프
    handoff_gaps = []
    handoff_mode = _handoff_mode(session, state)
    handoff = _read(os.path.join(out_dir, "handoff.md"))
    if handoff is None:
        handoff_gaps.append("handoff.md 없음 (핸드오프 종료 모드여도 생성한다 — SKILL.md 계약)")
    elif handoff_mode == "insane-research":
        # 프로즈/헤더 언급이 아니라 실제 /insane-research 쿼리 라인을 센다.
        # 계약: 선택된 각 컨셉마다 검증 쿼리 2종(위험 가정 + 경쟁 지형) 필수.
        queries = len(INSANE_QUERY_RE.findall(handoff))
        required = 2 * len(selected)
        if queries < required:
            handoff_gaps.append(
                f"handoff.md의 insane-research 검증 쿼리 {queries}건 < 필요 {required}건 "
                f"(선택 컨셉 {len(selected)}개 × 쿼리 2종)"
            )
    issues.extend(handoff_gaps)

    # 7) 근거 인용 — research_first 모드 한정 (근거 기반 약속의 마감 검증)
    evidence_gaps = []
    divergence_mode = _divergence_mode(session)
    if divergence_mode == "research_first":
        for path in brief_files:
            rel = os.path.relpath(path, out_dir)
            text = _read(path) or ""
            if not EVIDENCE_REF_RE.search(text):
                evidence_gaps.append(
                    f"{rel}: evidence 참조 없음 (ev_ id 또는 URL ≥1 — research_first 계약)"
                )
        if not os.path.exists(os.path.join(out_dir, "04_evidence_digest.md")):
            evidence_gaps.append(
                "04_evidence_digest.md 없음 (research_first 모드 — 어디를 뒤졌는지의 증빙)"
            )
    issues.extend(evidence_gaps)

    metrics = {
        "placeholder_count": len(placeholders),
        "brief_count": len(brief_files),
        "orphan_briefs": len(orphan_briefs),
        "missing_briefs": len(missing_briefs),
        "summary_gaps": len(summary_gaps),
        "unlisted_kills": len(unlisted_kills),
        "handoff_gaps": len(handoff_gaps),
        "evidence_gaps": len(evidence_gaps),
        "selected_count": len(selected),
        "killed_count": len(killed),
    }
    verdict = "PASS" if not issues else "FAIL"

    os.makedirs(out_dir, exist_ok=True)
    result = {
        "verdict": verdict,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checker": "eval_briefs.py",
        "divergence_mode": divergence_mode,
        "handoff_mode": handoff_mode,
        "metrics": metrics,
        "issues": issues,
    }
    with open(os.path.join(out_dir, "eval_briefs.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    _stamp_state(state_path, state, verdict == "PASS", metrics)
    _report(verdict, metrics, issues)
    return 0 if verdict == "PASS" else 1


def _handoff_mode(session, state):
    frame = _read_frame(session)
    mode = ((frame.get("output") or {}).get("handoff")) or (
        (state.get("frame") or {}).get("handoff") if isinstance(state.get("frame"), dict) else None
    )
    return mode or "insane-research"


def _divergence_mode(session):
    frame = _read_frame(session)
    mode = (frame.get("divergence") or {}).get("mode")
    return mode if mode in ("creative", "research_first") else "creative"


def _stamp_state(state_path, state, passed, metrics):
    state["brief_qa"] = {
        "passed": passed,
        **metrics,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checker": "eval_briefs.py",
    }
    tmp = state_path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, state_path)
    except OSError:
        pass


def _report(verdict, metrics, issues):
    out = sys.stderr
    print("=== eval_briefs 결과 ===", file=out)
    print(
        "  briefs={brief_count}  placeholders={placeholder_count}  "
        "orphans={orphan_briefs}  missing={missing_briefs}  "
        "summary_gaps={summary_gaps}  unlisted_kills={unlisted_kills}  "
        "handoff_gaps={handoff_gaps}  evidence_gaps={evidence_gaps}".format(**metrics),
        file=out,
    )
    if verdict == "PASS":
        print("  → PASS. 마감 가능 — 사용자에게 산출물 안내 + 핸드오프 제안.", file=out)
    else:
        print(f"\n[FAIL] {len(issues)}건 — 고쳐서 재실행 (그 상태로 마감 금지):", file=out)
        for issue in issues:
            print(f"  - {issue}", file=out)


def main():
    p = argparse.ArgumentParser(description="super-brainstorming 마감 채점기 (브리프 Self-Review 기계화)")
    p.add_argument("--session", required=True, help="브레인스톰 세션 폴더 (BRAINSTORM/{topic}_{ts})")
    args = p.parse_args()
    sys.exit(evaluate(args.session))


if __name__ == "__main__":
    main()
