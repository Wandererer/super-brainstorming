---
name: super-brainstorming
description: "AI 브레인스토밍 -- 멀티에이전트 검색 발굴·발산·수렴 아이디에이션 시스템"
argument-hint: "[topic|research topic|resume|status|frame]"
allowed-tools:
  - Agent
  - WebSearch
  - WebFetch
  - Read
  - Write
  - Glob
  - Bash
  - Grep
---

<!-- first-run setup: idempotent, non-blocking, self-skips after first run -->
**Step 0 — run once at the very start, before anything else:** run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" ask`. If its output starts with `STAR_ASK`, immediately call the **AskUserQuestion** tool once, with the question and options phrased **in the user's language**: prefer the current conversation's language if it is evident; otherwise fall back to the language code that follows `STAR_ASK` in the output (`ko`→Korean, `ja`→Japanese, `en`→English). Never default to Korean blindly.
- header: a short localized "GitHub Star" label
- question: ask whether they'd like to give this plugin a GitHub ⭐ to support it — note it is optional and every feature works either way
- options: exactly two — (1) yes, star it → then run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" star yes`; (2) no thanks → then run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" star no`

If the output is empty, just continue silently. (AskUserQuestion must NOT be in frontmatter allowed-tools.) Do not narrate beyond the question itself.

> **질문 원칙 (skills/super-brainstorming-main/references/socratic_policy.md)**: 발산 전 프레이밍 질문은 추론 가능한 건 묻지 말고 기본값으로 확인하며, 정말 불명확한 것만 묻는다(§1). 이미 구체적인 프레임이면 과잉질문 없이 바로 진행(§2). 단, **목적·제약·성공기준이 전부 불명확한 채로 발산을 시작하지 않는다** — "너무 단순해서 프레이밍이 필요 없다"는 안티패턴이다(§3).

AI-powered brainstorming system that turns one topic into a scored idea portfolio and approved concept briefs — two divergence modes (**creative** thinking-lens divergence, or **research_first**: mine reviews/communities/competitor gaps/trends in parallel and grow every idea from cited evidence), deterministic code-gated convergence, and a built-in handoff to `/insane-research` for evidence-based validation.

## Parse Arguments

Inspect `$ARGUMENTS` to determine the action:

| Argument Pattern | Action | Skill |
|-----------------|--------|-------|
| `resume [session_id]` | Resume a previous brainstorm session | super-brainstorming-main |
| `status` | List all brainstorm sessions and their progress | super-brainstorming-main |
| `frame` | Launch interactive frame builder | super-brainstorming-frame |
| `research [topic]` | Start new brainstorm in **research_first mode** (검색 발굴 — evidence mining then ideation, mode question skipped) | super-brainstorming-main |
| `[any other text]` | Start new brainstorm on the given topic (mode per SKILL's Mode 추론 규칙) | super-brainstorming-main |
| (no argument) | Show interactive menu via AskUserQuestion | See below |

## No Argument Provided

**EXECUTE:** 아래 JSON으로 AskUserQuestion 도구를 즉시 호출한다 (labels/descriptions translated to the user's language):

```json
{
  "questions": [
    {
      "question": "What would you like to do?",
      "header": "Action",
      "options": [
        {"label": "New Brainstorm", "description": "Start a new divergent-convergent brainstorm on any topic", "markdown": "## New Brainstorm\n\n**Flow**: Topic → Framing (HMW) → Divergence → Cross-pollination → Code-gated convergence → Concept briefs\n\n**Two divergence modes**:\n- `research_first` — miners scour reviews/communities/competitor gaps/trends in parallel; every idea cites evidence (research → brainstorming)\n- `creative` — 13 thinking lenses, pure divergence\n\n**Output**:\n- Executive summary\n- Idea catalog (30+ scored ideas)\n- Evidence digest (research_first)\n- Concept briefs for selected winners\n- Ready-to-run /insane-research validation queries\n\n**Duration**: 10-30 min depending on scope"},
        {"label": "Resume Session", "description": "Continue a previously interrupted brainstorm", "markdown": "## Resume Session\n\n**What it does**:\n- Lists all previous brainstorm sessions\n- Shows progress (Phase 1-7)\n- Resumes from last checkpoint\n\n**State**: Saved in `BRAINSTORM/*/state.json`"},
        {"label": "Session Status", "description": "View all brainstorm sessions and their progress", "markdown": "## Session Status\n\n**Shows**:\n- All brainstorm sessions\n- Current phase (1-7)\n- Idea count / shortlist status\n- Last updated time\n\n**Path**: `BRAINSTORM/*/state.json`"},
        {"label": "Frame Builder", "description": "Turn a vague idea into a structured brainstorm frame (HMW) interactively", "markdown": "## Frame Builder\n\n**Interactive wizard** to build a precise brainstorm frame:\n\n1. Goal type (new product / feature / growth / pivot)\n2. HMW (How Might We) statement — no baked-in solution\n3. Constraints, assets, success criteria, anti-goals\n4. Divergence intensity & lens selection\n\n**Output**: Structured JSON frame ready for execution"}
      ],
      "multiSelect": false
    }
  ]
}
```

After user selection:
- **New Brainstorm** → Ask for topic, then invoke super-brainstorming-main skill
- **Resume Session** → List sessions from `BRAINSTORM/*/state.json`, let user pick, then invoke super-brainstorming-main resume flow
- **Session Status** → List all sessions with progress summary
- **Frame Builder** → Invoke super-brainstorming-frame skill

## Execute

Once the action is determined, follow the corresponding skill's execution flow.

Skill content is located at:
- `${CLAUDE_PLUGIN_ROOT}/skills/super-brainstorming-main/SKILL.md` — Main brainstorm pipeline
- `${CLAUDE_PLUGIN_ROOT}/skills/super-brainstorming-frame/SKILL.md` — Interactive frame builder
