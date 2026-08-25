"""생성된 CASE 초안에 대한 일관성 검증 — 설계문서 14장 "검증" 단계.

pydantic(app.models.Case)이 타입/필수 필드를 검증한다면, 이 모듈은 게임 로직 상의
참조 무결성(문서-조사 연결, 증거 패턴 일치, 모순 참조 등)을 검증한다. 여기를 통과하지
못한 초안은 절대 게임 데이터로 승격(promote)되지 않는다.
"""

from app.models import Case

VALID_DECISIONS = {"SAFE_TO_PROCEED", "NEED_MORE_VERIFICATION", "STOP_CONTRACT"}


def validate_case_consistency(case: Case) -> list[str]:
    errors: list[str] = []

    document_ids = {d.document_id for d in case.documents}
    block_ids_by_doc = {d.document_id: {b.block_id for b in d.blocks} for d in case.documents}
    evidence_patterns = {d.pattern for d in case.evidence_definitions}
    statement_ids = {s.statement_id for npc in case.npc_personas for s in npc.statements}

    for inv in case.investigations:
        if inv.document_id and inv.document_id not in document_ids:
            errors.append(f"investigation '{inv.investigation_id}'이 존재하지 않는 document_id를 참조함: {inv.document_id}")
        if inv.unlock_condition:
            req_inv = inv.unlock_condition.get("requires_investigation")
            if req_inv and req_inv not in {i.investigation_id for i in case.investigations}:
                errors.append(f"investigation '{inv.investigation_id}'의 unlock_condition이 존재하지 않는 investigation을 참조함: {req_inv}")
            req_ev = inv.unlock_condition.get("requires_evidence")
            if req_ev and req_ev not in evidence_patterns:
                errors.append(f"investigation '{inv.investigation_id}'의 unlock_condition이 존재하지 않는 evidence pattern을 참조함: {req_ev}")

    for doc in case.documents:
        for block in doc.blocks:
            if block.evidence_pattern and block.evidence_pattern not in evidence_patterns:
                errors.append(
                    f"document '{doc.document_id}' block '{block.block_id}'가 evidence_definitions에 없는 "
                    f"pattern을 참조함: {block.evidence_pattern}"
                )

    if not any(b.evidence_pattern for d in case.documents for b in d.blocks):
        errors.append("어떤 document block도 evidence_pattern을 갖고 있지 않음 — 플레이어가 증거를 등록할 수 없음")

    for pattern in case.hidden_truth.risk_patterns:
        if pattern not in evidence_patterns:
            errors.append(f"hidden_truth.risk_patterns의 '{pattern}'이 evidence_definitions에 정의되어 있지 않음")

    for pattern in case.hidden_truth.required_evidence:
        if pattern not in evidence_patterns:
            errors.append(f"hidden_truth.required_evidence의 '{pattern}'이 evidence_definitions에 정의되어 있지 않음")

    for c in case.contradictions:
        if c.left not in statement_ids:
            errors.append(f"contradiction '{c.contradiction_id}'의 left가 존재하지 않는 statement_id를 참조함: {c.left}")
        if c.right not in evidence_patterns:
            errors.append(f"contradiction '{c.contradiction_id}'의 right가 존재하지 않는 evidence pattern을 참조함: {c.right}")

    for npc in case.npc_personas:
        if not npc.system_prompt.strip():
            errors.append(f"npc '{npc.npc_id}'의 system_prompt가 비어 있음")
        if "fraud_type" in npc.system_prompt or "정답" in npc.system_prompt:
            pass  # 시스템 프롬프트가 정답 유출 금지 문구를 포함하는지는 권장 사항이라 강제하지 않음

    ending_decisions = {o.decision for o in case.ending_options}
    missing_decisions = VALID_DECISIONS - ending_decisions
    if missing_decisions:
        errors.append(f"ending_options에 다음 decision이 누락됨: {sorted(missing_decisions)}")

    if not case.safe_actions:
        errors.append("safe_actions가 비어 있음 — AI Evaluator가 분류할 대상이 없음")

    for doc_id, block_ids in block_ids_by_doc.items():
        if not block_ids:
            errors.append(f"document '{doc_id}'에 block이 하나도 없음")

    return errors
