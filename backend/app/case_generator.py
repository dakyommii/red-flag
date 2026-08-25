"""AI 1 — 실제 사건 → CASE 생성 (설계문서 14장, 19장).

LLM은 여기서만 "CASE 생성 보조" 역할을 한다. 생성된 결과는:
  1) pydantic 스키마 검증 (app.models.Case)
  2) 게임 로직 일관성 검증 (app.case_validation.validate_case_consistency)
을 통과해야만 사람이 명시적으로 promote_draft()를 호출했을 때 실제 게임 데이터
(data/cases/*.json)로 반영된다. 검증을 통과하지 못한 초안은 data/cases/_drafts/에만
남고 case_loader가 읽는 경로에는 절대 노출되지 않는다 — "게임에 자동 반영되지 않는다"
는 설계 원칙을 코드로 강제한다.
"""

import json
import re
import time
import uuid
from pathlib import Path

from anthropic import AsyncAnthropic
from pydantic import ValidationError

from app.case_loader import list_cases, reload_cases
from app.case_validation import validate_case_consistency
from app.config import ANTHROPIC_API_KEY, CASES_DIR, REPO_ROOT, REPORT_MODEL
from app.models import Case

DRAFTS_DIR = REPO_ROOT / "data" / "cases" / "_drafts"
try:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass  # 서버리스 배포(Vercel) 환경은 파일시스템이 읽기 전용 — 이 관리자용 초안 생성 기능은 로컬 전용

KNOWLEDGE_DIR = REPO_ROOT / "data" / "knowledge"

_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


def _load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


CASE_SCHEMA_GUIDE = """
case_id, title, domain, difficulty(1-5), initial_points(int)
scenario: { description, property: {location, price_description, details}, broker_line, speaker_label, goal }
documents: [{ document_id, title, blocks: [{ block_id, text, evidence_pattern(nullable) }] }]
hidden_truth: { fraud_type, risk_patterns: [pattern,...], required_evidence: [pattern,...] }
evidence_definitions: [{ pattern, importance(1-2), description }]
investigations: [{ investigation_id, name, cost, time_cost, unlock_condition(nullable, {"requires_evidence":pattern} or {"requires_investigation":investigation_id}), document_id }]
npc_personas: [{ npc_id, role, display_name, knowledge:[..], strategies:[..], pressure_level(1-3), hidden_information:[..], system_prompt, statements:[{statement_id, text}] }]
contradictions: [{ contradiction_id, left(=statement_id), right(=evidence pattern), score, explanation }]
safe_actions: [{ action_id, description }]
ending_options: 반드시 SAFE_TO_PROCEED, NEED_MORE_VERIFICATION, STOP_CONTRACT 3개 모두 포함: [{ decision, score, comment }]
source: { case_ids: [...], official_sources: [...] }
"""

SYSTEM_PROMPT = """당신은 부동산 사기 예방 교육 게임의 CASE 생성 보조 도구다.

절대 규칙:
1. 아래 제공된 "실제 사례 요약"과 "공식 위험 신호 목록(fraud_taxonomy)", "공식 출처" 에 없는
   법률적 사실, 구체적 수치, 제도적 근거를 임의로 만들어내지 마라.
2. risk_patterns / evidence_definitions.pattern / contradictions.right 는 반드시 제공된
   fraud_taxonomy의 pattern 중에서만 선택하라. 새로운 pattern 이름을 만들지 마라.
3. 이 게임의 정답은 case.json 데이터 자체이다. NPC의 system_prompt에 "정답을 스스로 밝히지
   않는다"는 제약을 반드시 포함시켜라.
4. 출력은 JSON 객체 하나만. 설명, 마크다운 코드펜스, 다른 텍스트를 절대 포함하지 마라.
5. 아래 스키마 가이드를 정확히 따르라.

스키마 가이드:
{schema_guide}

fraud_taxonomy (이 중에서만 pattern을 선택하라):
{taxonomy}

공식 출처 (source.official_sources에 참고하라):
{official_sources}
"""

USER_PROMPT_TEMPLATE = """실제 사례 요약(교육 목적으로 재구성/익명화됨):
{seed_summary}

도메인: {domain}
난이도(1-5): {difficulty}
case_id: {case_id}

위 사례를 기반으로 플레이 가능한 CASE 하나를 JSON으로 생성하라.
"""


class CaseGenerationError(Exception):
    pass


async def generate_case_draft(seed_summary: str, domain: str, difficulty: int) -> dict:
    taxonomy = _load_json(KNOWLEDGE_DIR / "fraud_taxonomy.json")
    official_sources = _load_json(KNOWLEDGE_DIR / "official_sources.json")

    case_id = f"{domain}_{uuid.uuid4().hex[:6].upper()}"
    system_prompt = SYSTEM_PROMPT.format(
        schema_guide=CASE_SCHEMA_GUIDE,
        taxonomy=json.dumps(taxonomy, ensure_ascii=False, indent=2),
        official_sources=json.dumps(official_sources, ensure_ascii=False, indent=2),
    )
    user_prompt = USER_PROMPT_TEMPLATE.format(
        seed_summary=seed_summary, domain=domain, difficulty=difficulty, case_id=case_id
    )

    draft_id = f"draft_{uuid.uuid4().hex[:10]}"
    record = {
        "draft_id": draft_id,
        "generated_at": time.time(),
        "seed_summary": seed_summary,
        "domain": domain,
        "difficulty": difficulty,
        "case": None,
        "raw_llm_output": None,
        "pydantic_errors": [],
        "consistency_errors": [],
        "generation_error": None,
        "valid": False,
    }

    try:
        response = await _client.messages.create(
            model=REPORT_MODEL,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_text = next(block.text for block in response.content if block.type == "text")
        record["raw_llm_output"] = raw_text
        data = _extract_json(raw_text)
    except Exception as e:
        record["generation_error"] = f"{type(e).__name__}: {e}"
        _save_draft(record)
        return record

    try:
        case = Case(**data)
    except ValidationError as e:
        record["pydantic_errors"] = [str(err) for err in e.errors()]
        _save_draft(record)
        return record

    consistency_errors = validate_case_consistency(case)
    record["case"] = case.model_dump()
    record["consistency_errors"] = consistency_errors
    record["valid"] = len(consistency_errors) == 0

    _save_draft(record)
    return record


def _draft_path(draft_id: str) -> Path:
    return DRAFTS_DIR / f"{draft_id}.json"


def _save_draft(record: dict) -> None:
    _draft_path(record["draft_id"]).write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def list_drafts() -> list[dict]:
    drafts = []
    for path in sorted(DRAFTS_DIR.glob("draft_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        drafts.append(
            {
                "draft_id": record["draft_id"],
                "generated_at": record["generated_at"],
                "domain": record["domain"],
                "difficulty": record["difficulty"],
                "valid": record["valid"],
                "case_id": (record.get("case") or {}).get("case_id"),
                "title": (record.get("case") or {}).get("title"),
            }
        )
    return drafts


def get_draft(draft_id: str) -> dict | None:
    path = _draft_path(draft_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def promote_draft(draft_id: str) -> Case:
    """사람이 검토를 마친 뒤에만 호출되는, 검증을 다시 강제하는 승격 함수."""
    record = get_draft(draft_id)
    if record is None:
        raise CaseGenerationError("draft not found")
    if not record.get("case"):
        raise CaseGenerationError("draft has no valid case payload (generation or schema validation failed)")

    case = Case(**record["case"])
    consistency_errors = validate_case_consistency(case)
    if consistency_errors:
        raise CaseGenerationError("consistency validation failed: " + "; ".join(consistency_errors))

    existing_ids = {c.case_id for c in list_cases()}
    if case.case_id in existing_ids:
        raise CaseGenerationError(f"case_id '{case.case_id}' already exists")

    target_path = CASES_DIR / f"{case.case_id.lower()}.json"
    target_path.write_text(json.dumps(case.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    _draft_path(draft_id).unlink()
    reload_cases()
    return case
