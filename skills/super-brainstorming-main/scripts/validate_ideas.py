#!/usr/bin/env python3
"""
validate_ideas.py — super-brainstorming의 **결정론적 수렴 게이트** (control plane이 아니라 단일 체커).

설계 의도:
  - 오케스트레이션(어떤 렌즈로 발산하고 어떻게 심사할지)은 LLM/프롬프트(SKILL.md)에 맡긴다.
  - 수렴(랭킹·쇼트리스트)은 **코드로 계산**한다.
  - LLM이 쇼트리스트를 자유롭게 고르는 게 아니라, 이 스크립트가 심사 점수의
    중앙값(median)과 가중치로 순위를 **계산**한다.

핵심 강제 메커니즘 = "데이터 흐름 락":
  - 이 스크립트만이 `outputs/shortlist.json`을 생산하며, **exit 0일 때만** 쓴다.
  - SKILL.md는 "Phase 6 심화는 shortlist.json만 입력으로 받는다"고 계약한다.
  - 따라서 게이트를 건너뛰면 심화할 입력 파일 자체가 없다(자기파괴적) → 우회 불가.
  - 보강: 통과 시 랭킹+원본 ledger 바이트의 sha256 `signature`를 state.json에 기록.

wildcard seat (브레인스토밍 4원칙 "과격한 아이디어 환영"의 코드화):
  - 쇼트리스트 상위 N에 wildness>=4가 없으면 마지막 1석을 최고 순위 wild 후보로 교체.

포화 게이트 (me-too 방지의 코드화 — 양 모드 공통):
  - Phase 4.5 선행기술 대조가 각 카드에 saturation 블록을 붙인다:
      {"checked": true, "score": 0-5, "competitor_ids": ["ev_.."], "wedge": null|"...", "note": ""}
    competitor_ids는 existing_solution evidence 카드(URL 하드체크) 참조 — 경쟁사도 지어내지 못한다.
  - saturated = score>=4 또는 (score==3 이고 competitor 중 무료/OSS 존재)
      → novelty 중앙값을 2.0으로 상한 + wedge 필수(없으면 exit 1) + saturation_flag
  - crowded  = score==3 (무료 경쟁자 없음)
      → novelty 중앙값을 3.0으로 상한, wedge 없으면 경고
  - 후보 카드에 saturation.checked/score가 없으면 절차 위반 (exit 1 — Phase 4.5 미수행)

research_first 모드 (frame.divergence.mode == "research_first"):
  - "research 후 brainstorming" — Phase 3a에서 마이너들이 여러 소스를 뒤져
    evidence_ledger.jsonl을 만들고, Phase 3b의 아이디어 카드는 evidence_ids로
    근거를 인용해야 한다. 이 게이트가 추가로 강제하는 것:
      · evidence 카드 스키마·중복·미등록 참조         → 하드 에러 (exit 2)
      · 후보 카드의 evidence_ids < min_evidence_refs   → 절차 위반 (exit 1)
      · evidence 총량 < min_evidence (채굴 빈약)       → 절차 위반 (exit 1)
      · 마이너 다양성 < min_miners (한 곳만 팜)        → 절차 위반 (exit 1)
  - creative 모드(기본)에서는 위 검사를 건너뛴다 (단, evidence_ids를 쓴 카드가
    있으면 참조 무결성은 항상 하드 체크 — 존재하지 않는 근거 인용 금지).

입력:
  <session>/artifacts/idea_ledger.jsonl      (한 줄당 1개 idea card)
  <session>/artifacts/evidence_ledger.jsonl  (research_first 모드 — 한 줄당 1개 evidence card)
  <session>/artifacts/frame.json             (게이트 설정 — 선택, 없으면 기본값)

출력:
  <session>/outputs/ranked_ideas.json        (채점 가능한 전 후보의 계산 결과 — 항상)
  <session>/outputs/parked_and_killed.json   (parking lot 원자료 — 항상)
  <session>/outputs/shortlist.json           (Top N + wildcard seat — **exit 0에서만**)
  <session>/state.json 의 "convergence" 블록(signature 포함)

종료 코드:
  0  통과 (shortlist 생성 완료, 프로세스 위반 없음)
  1  프로세스 위반 (red-team 미수행·심사 부족·발산량 미달·하이브리드 없음
     → 누락 절차 수행 후 재실행. shortlist는 생성되지 않음)
  2  하드 에러 (스키마 깨짐·중복 id·미등록 parent_id·점수 범위 위반 → 데이터 수정 필요)

idea_ledger.jsonl 레코드 스키마:
  {
    "idea_id": "idea_101",            # ^idea_\\d{3,}$ , 유일
    "title": "...", "one_liner": "...",
    "mechanism": "...", "target_user": "...",
    "lens": "contrarian",             # lens_library.md의 key 또는 "hybrid"
    "wildness": 1-5,
    "parent_ids": [],                 # 하이브리드 필수, 참조 무결성 하드 체크
    "assumptions": [], "evidence": "",
    "status": "raw|hybrid|parked|killed",
    "kill_reason": null | "...",      # killed면 필수
    "red_team": {"checked": bool, "fatal_flaw": null|"...", "objections": []},
    "judge_scores": [{"judge": "judge_1", "novelty": 1-5, "impact": 1-5,
                      "feasibility": 1-5, "fit": 1-5, "timing": 1-5, "note": ""}]
  }
  (shortlist 여부는 입력에서 신뢰하지 않는다 — 이 체커가 계산한다.)
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from statistics import median

AXES = ("novelty", "impact", "feasibility", "fit", "timing")
DEFAULT_WEIGHTS = {
    "impact": 0.30,
    "feasibility": 0.25,
    "novelty": 0.20,
    "fit": 0.15,
    "timing": 0.10,
}
DEFAULT_CONFIG = {
    "shortlist_size": 5,
    "min_judges": 2,
    "min_ideas": 15,
    "min_hybrids": 1,
    "min_lenses": 3,
    "min_evidence": 15,
    "min_miners": 3,
    "min_evidence_refs": 1,
}
VALID_STATUS = {"raw", "hybrid", "parked", "killed"}
REQUIRED_FIELDS = ("idea_id", "title", "one_liner", "lens", "wildness", "status")
REQUIRED_EVIDENCE_FIELDS = ("evidence_id", "claim", "source_url", "miner")
ID_RE = re.compile(r"^idea_\d{3,}$")
EV_ID_RE = re.compile(r"^ev_\d{3,}$")
WILD_THRESHOLD = 4
FREE_PRICING = {"free", "oss"}
NOVELTY_CAP = {"saturated": 2.0, "crowded": 3.0}  # scoring_rubric.md 포화 앵커와 연동


def _read_jsonl(path):
    """JSONL 읽기. (records, errors) 반환."""
    records, errors = [], []
    if not os.path.exists(path):
        return records, [f"파일 없음: {path}"]
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"{os.path.basename(path)}:{lineno} JSON 파싱 실패: {e}")
                continue
            if not isinstance(rec, dict):
                errors.append(f"{os.path.basename(path)}:{lineno} 레코드가 JSON 객체가 아님")
                continue
            records.append(rec)
    return records, errors


def _load_config(frame_path):
    """frame.json에서 모드/게이트 설정/가중치 로드. 없으면 기본값(creative).

    (config, weights, mode, errors) 반환. frame이 JSON 객체가 아니면 errors에 하드 에러
    (파싱 불가는 기존대로 조용히 기본값 — frame은 선택 입력).
    """
    config = dict(DEFAULT_CONFIG)
    weights = dict(DEFAULT_WEIGHTS)
    mode = "creative"
    errors = []
    if frame_path and os.path.exists(frame_path):
        try:
            with open(frame_path, "r", encoding="utf-8") as f:
                frame = json.load(f)
        except (OSError, json.JSONDecodeError):
            frame = None
        if frame is not None and not isinstance(frame, dict):
            errors.append(f"frame.json이 JSON 객체가 아님: {frame_path}")
        elif isinstance(frame, dict):
            if (frame.get("divergence") or {}).get("mode") == "research_first":
                mode = "research_first"
            conv = frame.get("convergence") or {}
            for key in DEFAULT_CONFIG:
                val = conv.get(key)
                if isinstance(val, int) and val >= 0:
                    config[key] = val
            user_w = conv.get("scoring_weights") or {}
            for axis in AXES:
                val = user_w.get(axis)
                if isinstance(val, (int, float)) and val >= 0:
                    weights[axis] = float(val)
    total = sum(weights.values())
    if total <= 0:
        weights = dict(DEFAULT_WEIGHTS)
        total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}
    return config, weights, mode, errors


def check_evidence(records):
    """evidence_ledger 스키마·중복 하드 검사. (evidence_by_id, hard_errors) 반환."""
    hard = []
    evidence_by_id = {}
    for i, rec in enumerate(records):
        eid = rec.get("evidence_id")
        missing = [f for f in REQUIRED_EVIDENCE_FIELDS if not rec.get(f)]
        if missing:
            hard.append(f"evidence[{i}] ({eid or '?'}) 필수 필드 누락: {missing}")
            continue
        if not EV_ID_RE.match(str(eid)):
            hard.append(f"evidence[{i}] 잘못된 evidence_id 형식 '{eid}' (^ev_\\d{{3,}}$)")
            continue
        if eid in evidence_by_id:
            hard.append(f"중복 evidence_id '{eid}'")
            continue
        url = str(rec.get("source_url") or "")
        if not (url.startswith("http://") or url.startswith("https://")):
            hard.append(f"'{eid}': source_url이 URL이 아님 ({url!r}) — URL 없으면 카드 금지")
        evidence_by_id[eid] = rec
    return evidence_by_id, hard


def check_cards(cards):
    """카드 스키마·참조 무결성 하드 검사. (cards_by_id, hard_errors) 반환."""
    hard = []
    cards_by_id = {}

    for i, card in enumerate(cards):
        cid = card.get("idea_id")
        missing = [f for f in REQUIRED_FIELDS if card.get(f) in (None, "")]
        if missing:
            hard.append(f"card[{i}] ({cid or '?'}) 필수 필드 누락: {missing}")
            continue
        if not ID_RE.match(str(cid)):
            hard.append(f"card[{i}] 잘못된 idea_id 형식 '{cid}' (^idea_\\d{{3,}}$)")
            continue
        if cid in cards_by_id:
            hard.append(f"중복 idea_id '{cid}'")
            continue
        status = card.get("status")
        if status not in VALID_STATUS:
            hard.append(f"'{cid}': 잘못된 status '{status}' ({sorted(VALID_STATUS)}만 허용)")
        wild = card.get("wildness")
        if not isinstance(wild, int) or not 1 <= wild <= 5:
            hard.append(f"'{cid}': wildness는 1-5 정수여야 함 (현재 {wild!r})")
        if status == "killed" and not (card.get("kill_reason") or "").strip():
            hard.append(f"'{cid}': killed인데 kill_reason 없음 (parking lot 계약 위반)")
        if status == "hybrid" and not card.get("parent_ids"):
            hard.append(f"'{cid}': hybrid인데 parent_ids 없음 (Phase 4 계약 위반)")
        ev_refs = card.get("evidence_ids")
        if ev_refs is not None and (
            not isinstance(ev_refs, list) or any(not isinstance(e, str) for e in ev_refs)
        ):
            hard.append(f"'{cid}': evidence_ids는 문자열 배열이어야 함 (현재 {ev_refs!r})")
        sat = card.get("saturation")
        if sat is not None:
            if not isinstance(sat, dict):
                hard.append(f"'{cid}': saturation은 객체여야 함 (현재 {sat!r})")
            else:
                sc = sat.get("score")
                if sc is not None and (not isinstance(sc, int) or not 0 <= sc <= 5):
                    hard.append(f"'{cid}': saturation.score는 0-5 정수여야 함 (현재 {sc!r})")
                comp = sat.get("competitor_ids")
                if comp is not None and (
                    not isinstance(comp, list) or any(not isinstance(x, str) for x in comp)
                ):
                    hard.append(f"'{cid}': competitor_ids는 문자열 배열이어야 함 (현재 {comp!r})")
        for entry in card.get("judge_scores") or []:
            if not isinstance(entry, dict) or not entry.get("judge"):
                hard.append(f"'{cid}': judge_scores 항목에 judge 이름 없음")
                continue
            for axis in AXES:
                val = entry.get(axis)
                if not isinstance(val, int) or not 1 <= val <= 5:
                    hard.append(
                        f"'{cid}' 심사 '{entry.get('judge')}': {axis}={val!r} (1-5 정수만 허용)"
                    )
        cards_by_id[cid] = card

    # 참조 무결성: parent_ids가 ledger에 실존해야 함
    for cid, card in cards_by_id.items():
        unknown = [p for p in (card.get("parent_ids") or []) if p not in cards_by_id]
        if unknown:
            hard.append(f"'{cid}': 미등록 parent_id {unknown}")
    return cards_by_id, hard


def _dedupe_judges(card):
    """같은 judge가 중복 채점했으면 마지막 것만 사용."""
    seen = {}
    for entry in card.get("judge_scores") or []:
        if isinstance(entry, dict) and entry.get("judge"):
            seen[entry["judge"]] = entry
    return list(seen.values())


def score_card(card, weights):
    """축별 median → 가중 총점. (medians, weighted_total) 반환. 심사 없으면 (None, None)."""
    judges = _dedupe_judges(card)
    if not judges:
        return None, None
    medians = {axis: round(median(e[axis] for e in judges), 2) for axis in AXES}
    total = round(sum(weights[axis] * medians[axis] for axis in AXES), 3)
    return medians, total


def saturation_level(card, evidence_by_id):
    """포화 수준 판정 — 'saturated' | 'crowded' | None. scoring_rubric.md 앵커와 연동.

    saturated: score>=4 또는 (score==3 이고 무료/OSS 경쟁자 존재) → novelty 상한 2.0 + wedge 필수
    crowded:   score==3 (무료 경쟁자 없음)                        → novelty 상한 3.0
    """
    sat = card.get("saturation") if isinstance(card.get("saturation"), dict) else {}
    score = sat.get("score")
    if not sat.get("checked") or not isinstance(score, int):
        return None
    has_free = any(
        str((evidence_by_id.get(c) or {}).get("pricing", "")).strip().lower() in FREE_PRICING
        for c in (sat.get("competitor_ids") or [])
    )
    if score >= 4 or (score == 3 and has_free):
        return "saturated"
    if score == 3:
        return "crowded"
    return None


def collect_violations(candidates, hybrids, lenses, config, mode, evidence_by_id):
    """프로세스 위반(exit 1) 수집 — 고칠 수 있는 절차 누락."""
    violations = []
    if len(candidates) < config["min_ideas"]:
        violations.append(
            f"발산량 미달: 후보 {len(candidates)}개 < min_ideas {config['min_ideas']} "
            f"(렌즈 추가 발산 또는 메인 스레드 폴백 필요)"
        )
    if len(lenses) < config["min_lenses"]:
        violations.append(
            f"렌즈 다양성 미달: {len(lenses)}종 < min_lenses {config['min_lenses']} "
            f"(서로 다른 렌즈로 발산해야 함)"
        )
    if len(hybrids) < config["min_hybrids"]:
        violations.append(
            f"하이브리드 {len(hybrids)}개 < min_hybrids {config['min_hybrids']} "
            f"(Phase 4 교차 수분 미수행)"
        )
    if mode == "research_first":
        if len(evidence_by_id) < config["min_evidence"]:
            violations.append(
                f"채굴 빈약: evidence {len(evidence_by_id)}건 < min_evidence "
                f"{config['min_evidence']} (Phase 3a 마이너 추가 실행 필요)"
            )
        miners = {e.get("miner") for e in evidence_by_id.values() if e.get("miner")}
        if len(miners) < config["min_miners"]:
            violations.append(
                f"마이너 다양성 미달: {len(miners)}종 < min_miners {config['min_miners']} "
                f"(한 종류의 소스만 파면 안 됨 — multi-modal sweep)"
            )
    for card in candidates:
        cid = card["idea_id"]
        red = card.get("red_team") or {}
        if not red.get("checked"):
            violations.append(f"  - {cid}: red-team 미수행 (Phase 5a)")
        judges = _dedupe_judges(card)
        if len(judges) < config["min_judges"]:
            violations.append(
                f"  - {cid}: 심사 {len(judges)}인 < min_judges {config['min_judges']} (Phase 5b)"
            )
        if mode == "research_first":
            refs = card.get("evidence_ids") or []
            if len(refs) < config["min_evidence_refs"]:
                violations.append(
                    f"  - {cid}: 근거 {len(refs)}건 < min_evidence_refs "
                    f"{config['min_evidence_refs']} (근거 없는 카드 — 재발굴 또는 park/kill)"
                )
        # 포화 게이트 — 양 모드 공통 (수렴은 근거로)
        sat = card.get("saturation") if isinstance(card.get("saturation"), dict) else {}
        if not sat.get("checked") or not isinstance(sat.get("score"), int):
            violations.append(f"  - {cid}: 선행기술 대조 미수행 (Phase 4.5 — saturation.checked/score 필요)")
        elif saturation_level(card, evidence_by_id) == "saturated" and not (sat.get("wedge") or "").strip():
            violations.append(
                f"  - {cid}: 포화 시장(saturation {sat.get('score')})인데 wedge 없음 — "
                f"기존 해법 대비 쐐기를 명시하거나 park/kill"
            )
    return violations


def collect_warnings(ranked, cards):
    """경고 — 종료 코드에는 영향 없음."""
    warnings = []
    if ranked and not any(c["wildness"] >= WILD_THRESHOLD for c in ranked):
        warnings.append(
            f"wild 후보 없음 (wildness>={WILD_THRESHOLD}) — 발산이 안전지대에 머물렀을 수 있음. "
            f"와일드카드 렌즈 추가를 고려."
        )
    for c in ranked:
        sat = c.get("saturation") or {}
        if sat.get("level") == "crowded" and not (sat.get("wedge") or "").strip():
            warnings.append(
                f"{c['idea_id']}: crowded 시장(saturation 3)인데 wedge 미기재 — 브리프 단계에서 요구됨"
            )
    # rubber-stamp 심사 감지: 한 judge가 5개 이상 아이디어에 동일 튜플 반복(60%+)
    by_judge = {}
    for card in cards:
        for entry in _dedupe_judges(card):
            tup = tuple(entry.get(a) for a in AXES)
            by_judge.setdefault(entry["judge"], []).append(tup)
    for judge, tuples in sorted(by_judge.items()):
        if len(tuples) >= 5:
            top_tuple, count = Counter(tuples).most_common(1)[0]
            if count / len(tuples) >= 0.6:
                warnings.append(
                    f"rubber-stamp 의심: 심사 '{judge}'가 {len(tuples)}건 중 {count}건에 "
                    f"동일 점수 {top_tuple} — 해당 심사 재실행 권장"
                )
    return warnings


def build_shortlist(ranked, size):
    """Top N + wildcard seat. (shortlist, wildcard_seat_id, displaced_id) 반환."""
    shortlist = ranked[:size]
    if not shortlist:
        return [], None, None
    if any(c["wildness"] >= WILD_THRESHOLD for c in shortlist):
        return shortlist, None, None
    wild_pool = [c for c in ranked[size:] if c["wildness"] >= WILD_THRESHOLD]
    if not wild_pool:
        return shortlist, None, None  # wild 후보 자체가 없음 → 경고만
    wild_pick = wild_pool[0]  # ranked는 이미 정렬됨 → 최고 순위 wild
    displaced = shortlist[-1]
    shortlist = shortlist[:-1] + [wild_pick]
    return shortlist, wild_pick["idea_id"], displaced["idea_id"]


def validate(ledger_path, frame_path, evidence_path, out_dir, state_path):
    config, weights, mode, cfg_errs = _load_config(frame_path)

    cards, parse_errs = _read_jsonl(ledger_path)
    hard_errors = list(parse_errs)
    hard_errors.extend(cfg_errs)
    cards_by_id, schema_errs = check_cards(cards)
    hard_errors.extend(schema_errs)

    # evidence ledger — research_first 모드 필수, creative 모드는 있으면 검사
    evidence_by_id = {}
    if mode == "research_first" and not evidence_path:
        hard_errors.append(
            "research_first 모드인데 evidence 경로 없음 — --evidence 또는 --session 필요"
        )
    elif mode == "research_first" or (evidence_path and os.path.exists(evidence_path)):
        evidence, ev_parse_errs = _read_jsonl(evidence_path)
        if mode == "research_first":
            hard_errors.extend(ev_parse_errs)
        ev_by_id, ev_errs = check_evidence(evidence)
        hard_errors.extend(ev_errs)
        evidence_by_id = ev_by_id

    # 참조 무결성: 카드가 인용한 evidence_ids / competitor_ids는 실존해야 함
    # (모드 무관 — 없는 근거·없는 경쟁사 인용 금지)
    for cid, card in cards_by_id.items():
        unknown = [e for e in (card.get("evidence_ids") or []) if e not in evidence_by_id]
        if unknown:
            hard_errors.append(f"'{cid}': 미등록 evidence_id {unknown}")
        sat = card.get("saturation") if isinstance(card.get("saturation"), dict) else {}
        unknown_comp = [c for c in (sat.get("competitor_ids") or []) if c not in evidence_by_id]
        if unknown_comp:
            hard_errors.append(f"'{cid}': 미등록 competitor_id {unknown_comp} (경쟁사도 evidence 카드로 등록)")

    # 하드 에러면 산출물 쓰지 않고 즉시 실패 (exit 2)
    if hard_errors:
        _report(hard_errors, [], [], [], stats=None, signature=None, mode=mode)
        return 2

    all_cards = list(cards_by_id.values())
    candidates = [c for c in all_cards if c["status"] in ("raw", "hybrid")]
    hybrids = [c for c in all_cards if c["status"] == "hybrid" or c.get("parent_ids")]
    killed = [c for c in all_cards if c["status"] == "killed"]
    parked = [c for c in all_cards if c["status"] == "parked"]
    lenses = {c["lens"] for c in candidates if c["status"] == "raw"}

    violations = collect_violations(candidates, hybrids, lenses, config, mode, evidence_by_id)

    # 채점 가능한 후보만 랭킹 계산 (심사 누락 후보는 위반으로 이미 잡힘)
    ranked = []
    for card in candidates:
        medians, total = score_card(card, weights)
        if medians is None:
            continue
        # 포화 게이트: novelty 상한 — 심사가 후하게 줘도 코드가 깎는다 (me-too 방지)
        sat = card.get("saturation") if isinstance(card.get("saturation"), dict) else {}
        level = saturation_level(card, evidence_by_id)
        novelty_capped = False
        cap = NOVELTY_CAP.get(level)
        if cap is not None and medians["novelty"] > cap:
            medians = dict(medians, novelty=cap)
            total = round(sum(weights[a] * medians[a] for a in AXES), 3)
            novelty_capped = True
        entry = {
            "idea_id": card["idea_id"],
            "title": card["title"],
            "one_liner": card["one_liner"],
            "lens": card["lens"],
            "wildness": card["wildness"],
            "parent_ids": card.get("parent_ids") or [],
            "evidence_ids": card.get("evidence_ids") or [],
            "red_team_objections": (card.get("red_team") or {}).get("objections") or [],
            "saturation": {
                "score": sat.get("score"),
                "level": level,
                "flag": level == "saturated",
                "wedge": sat.get("wedge"),
                "competitor_ids": sat.get("competitor_ids") or [],
                "novelty_capped": novelty_capped,
            },
            "medians": medians,
            "weighted_total": total,
        }
        ranked.append(entry)
    ranked.sort(
        key=lambda c: (
            -c["weighted_total"],
            -c["medians"]["impact"],
            -c["medians"]["novelty"],
            c["idea_id"],
        )
    )
    for rank, entry in enumerate(ranked, 1):
        entry["rank"] = rank

    warnings = collect_warnings(ranked, all_cards)

    os.makedirs(out_dir, exist_ok=True)
    _write_json(os.path.join(out_dir, "ranked_ideas.json"), {
        "mode": mode,
        "weights": weights,
        "scored_count": len(ranked),
        "ranked": ranked,
    })
    _write_json(os.path.join(out_dir, "parked_and_killed.json"), {
        "parked": [
            {"idea_id": c["idea_id"], "title": c["title"], "one_liner": c["one_liner"],
             "lens": c["lens"], "wildness": c["wildness"]}
            for c in parked
        ],
        "killed": [
            {"idea_id": c["idea_id"], "title": c["title"], "one_liner": c["one_liner"],
             "lens": c["lens"], "wildness": c["wildness"], "kill_reason": c.get("kill_reason"),
             "fatal_flaw": (c.get("red_team") or {}).get("fatal_flaw")}
            for c in killed
        ],
    })

    shortlist_path = os.path.join(out_dir, "shortlist.json")
    signature = None
    shortlist, wild_seat, displaced = [], None, None

    if not violations:
        shortlist, wild_seat, displaced = build_shortlist(ranked, config["shortlist_size"])
        for entry in shortlist:
            entry["wildcard_seat"] = entry["idea_id"] == wild_seat
        signature = _signature(ranked, ledger_path)
        _write_json(shortlist_path, {
            "generated_by": "validate_ideas.py",
            "mode": mode,
            "signature": signature,
            "weights": weights,
            "wildcard_seat": wild_seat,
            "displaced_by_wildcard": displaced,
            "shortlist": shortlist,
        })
    elif os.path.exists(shortlist_path):
        # 위반 상태에서 이전 shortlist가 남아 있으면 제거 — 데이터 흐름 락 유지
        os.remove(shortlist_path)

    stats = {
        "mode": mode,
        "candidates": len(candidates),
        "scored": len(ranked),
        "hybrids": len(hybrids),
        "killed": len(killed),
        "parked": len(parked),
        "lenses": sorted(lenses),
        "evidence_count": len(evidence_by_id),
        "miners": sorted({e.get("miner") for e in evidence_by_id.values() if e.get("miner")}),
        "saturated": sum(1 for c in ranked if (c.get("saturation") or {}).get("flag")),
        "novelty_capped": sum(1 for c in ranked if (c.get("saturation") or {}).get("novelty_capped")),
    }

    if state_path and os.path.exists(state_path):
        _stamp_state(
            state_path,
            passed=not violations,
            signature=signature,
            stats=stats,
            shortlist_ids=[c["idea_id"] for c in shortlist],
            wildcard_seat=wild_seat,
            weights=weights,
        )

    _report(hard_errors, violations, warnings, shortlist, stats=stats, signature=signature, mode=mode)
    return 1 if violations else 0


def _signature(ranked, ledger_path):
    h = hashlib.sha256()
    h.update(json.dumps(ranked, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    if os.path.exists(ledger_path):
        with open(ledger_path, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _stamp_state(state_path, passed, signature, stats, shortlist_ids, wildcard_seat, weights):
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(state, dict):
        return  # 비-객체 state.json은 조용히 스킵 (게이트 판정·산출물은 이미 유효)
    state["convergence"] = {
        "passed": passed,
        "signature": signature,
        **stats,
        "shortlist_ids": shortlist_ids,
        "wildcard_seat": wildcard_seat,
        "weights": weights,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checker": "validate_ideas.py",
    }
    # atomic write: temp → rename
    tmp = state_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, state_path)


def _report(hard_errors, violations, warnings, shortlist, stats, signature, mode="creative"):
    out = sys.stderr
    print(f"=== validate_ideas 결과 (mode: {mode}) ===", file=out)
    if hard_errors:
        print(f"\n[HARD ERROR] {len(hard_errors)}건 — 데이터 수정 후 재실행 (exit 2):", file=out)
        for e in hard_errors:
            print(f"  - {e}", file=out)
        return
    if stats:
        print(
            f"  candidates={stats['candidates']}  scored={stats['scored']}  "
            f"hybrids={stats['hybrids']}  killed={stats['killed']}  parked={stats['parked']}",
            file=out,
        )
        print(f"  lenses={', '.join(stats['lenses'])}", file=out)
        print(
            f"  saturated={stats['saturated']}  novelty_capped={stats['novelty_capped']}",
            file=out,
        )
        if mode == "research_first":
            print(
                f"  evidence={stats['evidence_count']}건  miners={', '.join(stats['miners'])}",
                file=out,
            )
    for w in warnings:
        print(f"  [WARN] {w}", file=out)
    if violations:
        print(
            f"\n[FAIL] 프로세스 위반 {len(violations)}건 (exit 1) — "
            f"누락 절차 수행 후 ledger 갱신·재실행 (shortlist 미생성):",
            file=out,
        )
        for v in violations:
            print(v if v.startswith("  ") else f"  - {v}", file=out)
    else:
        print("  → 통과. Phase 6 심화는 outputs/shortlist.json 만 입력으로 진행.", file=out)
        for c in shortlist:
            seat = "  [WILDCARD SEAT]" if c.get("wildcard_seat") else ""
            print(
                f"    {c['rank']:>2}. {c['idea_id']}  {c['weighted_total']:.3f}  "
                f"{c['title']}{seat}",
                file=out,
            )
        if signature:
            print(f"  signature={signature[:16]}…", file=out)


def _resolve_paths(args):
    if args.session:
        base = args.session
        ledger = args.ledger or os.path.join(base, "artifacts", "idea_ledger.jsonl")
        frame = args.frame or os.path.join(base, "artifacts", "frame.json")
        evidence = args.evidence or os.path.join(base, "artifacts", "evidence_ledger.jsonl")
        out_dir = args.out_dir or os.path.join(base, "outputs")
        state = args.state or os.path.join(base, "state.json")
    else:
        ledger = args.ledger
        frame = args.frame
        evidence = args.evidence
        out_dir = args.out_dir or "."
        state = args.state
        if not ledger:
            raise SystemExit("--session 또는 --ledger 가 필요합니다.")
    return ledger, frame, evidence, out_dir, state


def main():
    p = argparse.ArgumentParser(description="super-brainstorming 결정론적 수렴 게이트")
    p.add_argument("--session", help="브레인스톰 세션 폴더 (BRAINSTORM/{topic}_{ts})")
    p.add_argument("--ledger", help="idea_ledger.jsonl 경로 (override)")
    p.add_argument("--frame", help="frame.json 경로 (override)")
    p.add_argument("--evidence", help="evidence_ledger.jsonl 경로 (override)")
    p.add_argument("--out-dir", help="출력 폴더 (기본: <session>/outputs)")
    p.add_argument("--state", help="state.json 경로 (기본: <session>/state.json)")
    args = p.parse_args()

    ledger, frame, evidence, out_dir, state = _resolve_paths(args)
    sys.exit(validate(ledger, frame, evidence, out_dir, state))


if __name__ == "__main__":
    main()
