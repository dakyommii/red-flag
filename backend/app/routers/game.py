import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.case_loader import get_case
from app.llm_client import generate_report_comment, npc_reply
from app.models import (
    Case,
    ChatMessage,
    EvidenceEntry,
    GameSession,
    MessageRole,
    TimelineEvent,
)
from app.scoring import compute_breakdown, grade_for
from app.statement_reveal import reveal_statements
from app.store import store
from app.unlock import is_unlocked

router = APIRouter(prefix="/api/game", tags=["game"])


async def _get_session_and_case(session_id: str) -> tuple[GameSession, Case]:
    session = await store.get(session_id)
    if session is None:
        raise HTTPException(404, "session not found")
    case = get_case(session.case_id)
    if case is None:
        raise HTTPException(404, "case not found")
    return session, case


def _log(session: GameSession, kind: str, detail: str) -> None:
    session.timeline.append(
        TimelineEvent(timestamp=time.time() - session.started_at, kind=kind, detail=detail)
    )


def _public_document(doc):
    return {
        "document_id": doc.document_id,
        "title": doc.title,
        "blocks": [{"block_id": b.block_id, "text": b.text} for b in doc.blocks],
    }


def _investigation_menu(case: Case, session: GameSession) -> list[dict]:
    menu = []
    for inv in case.investigations:
        unlocked = is_unlocked(inv.unlock_condition, session)
        if not unlocked and inv.hidden_until_unlocked:
            continue
        menu.append(
            {
                "investigation_id": inv.investigation_id,
                "name": inv.name,
                "cost": inv.cost,
                "time_cost": inv.time_cost,
                "unlocked": unlocked,
                "completed": inv.investigation_id in session.completed_investigation_ids,
            }
        )
    return menu


def _npc_menu(case: Case) -> list[dict]:
    return [
        {
            "npc_id": n.npc_id,
            "role": n.role,
            "display_name": n.display_name,
            "suggested_questions": n.suggested_questions,
            "total_statements": len(n.statements),
        }
        for n in case.npc_personas
    ]


def _statement_menu(case: Case, session: GameSession) -> list[dict]:
    """대화를 통해 확보한 발언만 노출한다 (설계문서 8장 — 조사로 알아내는 정보)."""
    statements = []
    for npc in case.npc_personas:
        for s in npc.statements:
            if s.statement_id in session.revealed_statement_ids:
                statements.append(
                    {"statement_id": s.statement_id, "npc_id": npc.npc_id, "text": s.text}
                )
    return statements


def _found_contradictions(case: Case, session: GameSession) -> list[dict]:
    statement_text = {s.statement_id: s.text for npc in case.npc_personas for s in npc.statements}
    found = []
    for c in case.contradictions:
        if c.contradiction_id in session.contradictions_found:
            found.append(
                {
                    "contradiction_id": c.contradiction_id,
                    "statement_id": c.left,
                    "statement_text": statement_text.get(c.left, c.left),
                    "evidence_pattern": c.right,
                    "explanation": c.explanation,
                }
            )
    return found


@router.get("/{session_id}")
async def get_state(session_id: str) -> dict:
    session, case = await _get_session_and_case(session_id)
    return {
        "session_id": session.session_id,
        "case_id": case.case_id,
        "remaining_points": session.remaining_points,
        "remaining_seconds": session.remaining_seconds,
        "time_expired": session.time_expired,
        "completed": session.completed,
        "final_decision": session.final_decision,
        "final_score": session.final_score,
        "investigations": _investigation_menu(case, session),
        "npcs": _npc_menu(case),
        "statements": _statement_menu(case, session),
        "evidence_board": [e.model_dump() for e in session.evidence_board],
        "contradictions_found": session.contradictions_found,
        "contradictions": _found_contradictions(case, session),
        "chat_history": {k: [m.model_dump() for m in v] for k, v in session.chat_history.items()},
    }


class InvestigateRequest(BaseModel):
    investigation_id: str


@router.post("/{session_id}/investigate")
async def investigate(session_id: str, body: InvestigateRequest) -> dict:
    session, case = await _get_session_and_case(session_id)
    if session.completed:
        raise HTTPException(400, "case already completed")
    if session.time_expired:
        raise HTTPException(400, "time expired")

    inv = next(
        (i for i in case.investigations if i.investigation_id == body.investigation_id), None
    )
    if inv is None:
        raise HTTPException(404, "investigation not found")
    if not is_unlocked(inv.unlock_condition, session):
        raise HTTPException(400, "investigation is locked")

    if inv.investigation_id not in session.completed_investigation_ids:
        if session.remaining_points < inv.cost:
            raise HTTPException(400, "not enough points")
        if session.remaining_seconds is not None and session.remaining_seconds < inv.time_cost:
            session.time_expired = True
            await store.save(session)
            raise HTTPException(400, "not enough time remaining")

        session.remaining_points -= inv.cost
        if session.remaining_seconds is not None:
            session.remaining_seconds -= inv.time_cost
            if session.remaining_seconds <= 0:
                session.time_expired = True
        session.completed_investigation_ids.append(inv.investigation_id)
        _log(session, "investigate", inv.name)

    document = None
    if inv.document_id:
        document = next((d for d in case.documents if d.document_id == inv.document_id), None)

    await store.save(session)
    return {
        "investigation_id": inv.investigation_id,
        "remaining_points": session.remaining_points,
        "remaining_seconds": session.remaining_seconds,
        "time_expired": session.time_expired,
        "document": _public_document(document) if document else None,
    }


class EvidenceRequest(BaseModel):
    document_id: str
    block_id: str


@router.post("/{session_id}/evidence")
async def register_evidence(session_id: str, body: EvidenceRequest) -> dict:
    session, case = await _get_session_and_case(session_id)
    if session.completed:
        raise HTTPException(400, "case already completed")

    unlocking_inv = next(
        (i for i in case.investigations if i.document_id == body.document_id), None
    )
    if unlocking_inv is None or unlocking_inv.investigation_id not in session.completed_investigation_ids:
        raise HTTPException(400, "document has not been investigated yet")

    document = next((d for d in case.documents if d.document_id == body.document_id), None)
    if document is None:
        raise HTTPException(404, "document not found")
    block = next((b for b in document.blocks if b.block_id == body.block_id), None)
    if block is None:
        raise HTTPException(404, "block not found")

    if not block.evidence_pattern:
        raise HTTPException(400, "이 부분에서는 특별한 위험 신호를 찾지 못했습니다. 다른 부분을 살펴보세요.")

    existing = next((e for e in session.evidence_board if e.pattern == block.evidence_pattern), None)
    if existing:
        return {"evidence": existing.model_dump(), "already_registered": True}

    definition = next(
        (d for d in case.evidence_definitions if d.pattern == block.evidence_pattern), None
    )
    entry = EvidenceEntry(
        evidence_id=f"E{len(session.evidence_board) + 1:02d}",
        pattern=block.evidence_pattern,
        description=definition.description if definition else block.evidence_pattern,
        source_document_id=document.document_id,
        source_block_id=block.block_id,
    )
    session.evidence_board.append(entry)
    _log(session, "evidence", entry.pattern)
    await store.save(session)
    return {"evidence": entry.model_dump(), "already_registered": False}


class ChatRequest(BaseModel):
    npc_id: str
    message: str


@router.post("/{session_id}/chat")
async def chat(session_id: str, body: ChatRequest) -> dict:
    session, case = await _get_session_and_case(session_id)
    if session.completed:
        raise HTTPException(400, "case already completed")

    npc = next((n for n in case.npc_personas if n.npc_id == body.npc_id), None)
    if npc is None:
        raise HTTPException(404, "npc not found")

    history = session.chat_history.setdefault(npc.npc_id, [])
    history.append(ChatMessage(role=MessageRole.PLAYER, content=body.message))

    reply_text = await npc_reply(npc.system_prompt, history)
    history.append(ChatMessage(role=MessageRole.NPC, content=reply_text))
    _log(session, "chat", f"{npc.npc_id}: {body.message[:40]}")

    newly_revealed = reveal_statements(case, session, npc.npc_id, body.message, reply_text)
    for s in newly_revealed:
        _log(session, "statement", s["statement_id"])

    await store.save(session)
    return {"npc_id": npc.npc_id, "reply": reply_text, "revealed_statements": newly_revealed}


class ContradictionRequest(BaseModel):
    statement_id: str
    evidence_pattern: str


@router.post("/{session_id}/contradiction")
async def submit_contradiction(session_id: str, body: ContradictionRequest) -> dict:
    session, case = await _get_session_and_case(session_id)
    if session.completed:
        raise HTTPException(400, "case already completed")

    if body.statement_id not in session.revealed_statement_ids:
        raise HTTPException(400, "아직 확보하지 못한 발언입니다. NPC와 대화해 발언을 확보하세요")

    if not any(e.pattern == body.evidence_pattern for e in session.evidence_board):
        raise HTTPException(400, "해당 증거를 먼저 등록해야 합니다")

    match = next(
        (
            c
            for c in case.contradictions
            if c.left == body.statement_id and c.right == body.evidence_pattern
        ),
        None,
    )
    if match is None:
        return {"found": False}

    if match.contradiction_id not in session.contradictions_found:
        session.contradictions_found.append(match.contradiction_id)
        _log(session, "contradiction", match.contradiction_id)
        await store.save(session)

    return {"found": True, "contradiction_id": match.contradiction_id, "explanation": match.explanation}


class DecisionRequest(BaseModel):
    decision: str


VALID_DECISIONS = {"SAFE_TO_PROCEED", "NEED_MORE_VERIFICATION", "STOP_CONTRACT"}


@router.post("/{session_id}/decision")
async def submit_decision(session_id: str, body: DecisionRequest) -> dict:
    session, case = await _get_session_and_case(session_id)
    if session.completed:
        raise HTTPException(400, "case already completed")
    if body.decision not in VALID_DECISIONS:
        raise HTTPException(400, "invalid decision")

    session.final_decision = body.decision
    breakdown = compute_breakdown(case, session)
    session.final_score = breakdown.total
    session.completed = True
    _log(session, "decision", body.decision)
    await store.save(session)

    return {
        "decision": body.decision,
        "score": breakdown.as_dict(),
        "grade": grade_for(breakdown.total),
        "time_expired": session.time_expired,
    }


def _format_timeline(session: GameSession) -> str:
    lines = []
    for ev in session.timeline:
        minutes, seconds = divmod(int(ev.timestamp), 60)
        lines.append(f"{minutes:02d}:{seconds:02d} {ev.kind} - {ev.detail}")
    return "\n".join(lines)


def _risk_details(case: Case, patterns: list[str]) -> list[dict]:
    desc = {d.pattern: d.description for d in case.evidence_definitions}
    return [{"pattern": p, "description": desc.get(p, "")} for p in patterns]


def _enrich_timeline(case: Case, session: GameSession) -> list[dict]:
    """행동 Timeline을 플로우차트로 그릴 수 있도록 각 이벤트에 사람이 읽을 라벨/설명을 붙인다."""
    npc_names = {n.npc_id: n.display_name for n in case.npc_personas}
    statement_text = {s.statement_id: s.text for n in case.npc_personas for s in n.statements}
    evidence_desc = {d.pattern: d.description for d in case.evidence_definitions}
    contradiction_map = {c.contradiction_id: c for c in case.contradictions}

    enriched = []
    for ev in session.timeline:
        label = ev.detail
        description = None

        if ev.kind == "investigate":
            label = ev.detail
        elif ev.kind == "evidence":
            label = ev.detail
            description = evidence_desc.get(ev.detail)
        elif ev.kind == "chat":
            npc_id, _, msg = ev.detail.partition(": ")
            label = npc_names.get(npc_id, npc_id)
            description = f'"{msg}"' if msg else None
        elif ev.kind == "statement":
            label = "발언 확보"
            description = statement_text.get(ev.detail)
            if description:
                description = f'"{description}"'
        elif ev.kind == "contradiction":
            match = contradiction_map.get(ev.detail)
            label = "모순 발견"
            description = match.explanation if match else None
        elif ev.kind == "decision":
            label = "최종 판단"
            description = ev.detail

        enriched.append(
            {"timestamp": ev.timestamp, "kind": ev.kind, "label": label, "description": description}
        )
    return enriched


def _fallback_comment(
    case: Case, found: list[dict], missed: list[dict], breakdown_dict: dict
) -> str:
    """LLM을 쓸 수 없을 때도 실제로 쓸모 있는 평가를 주기 위한 rule-based 폴백."""
    good: list[str] = []
    bad: list[str] = []

    if found:
        names = ", ".join(f["pattern"] for f in found)
        good.append(f"{names} 위험 신호를 스스로 찾아내고 근거로 삼았습니다.")
    if breakdown_dict["contradiction"] >= 10:
        good.append("NPC의 발언과 실제 증거 사이의 모순을 정확히 짚어냈습니다.")
    if breakdown_dict["efficiency"] >= 8:
        good.append("조사한 내용이 대부분 실제 증거로 이어져 효율적으로 움직였습니다.")
    if not good:
        good.append("이번 CASE를 끝까지 진행하며 조사 흐름 자체는 경험했습니다.")

    if missed:
        names = ", ".join(f"{m['pattern']}({m['description']})" for m in missed)
        bad.append(f"다음 위험 신호는 놓쳤습니다 — {names}.")
    if breakdown_dict["contradiction"] == 0:
        bad.append("NPC 발언과 증거를 연결해 모순을 지적하는 단계까지는 가지 못했습니다.")
    if breakdown_dict["efficiency"] < 5:
        bad.append("조사한 것에 비해 실제 증거로 이어진 비율이 낮았습니다 — 다음엔 문서를 더 꼼꼼히 살펴보세요.")
    if not bad:
        bad.append("핵심 위험 신호를 놓치지 않고 모두 찾아냈습니다. 훌륭합니다!")

    return f"잘한 점: {' '.join(good)}\n아쉬운 점: {' '.join(bad)}"


@router.get("/{session_id}/report")
async def get_report(session_id: str) -> dict:
    session, case = await _get_session_and_case(session_id)
    if not session.completed:
        raise HTTPException(400, "case not finished yet")

    breakdown = compute_breakdown(case, session)
    grade = grade_for(breakdown.total)
    timeline_summary = _format_timeline(session)
    breakdown_dict = breakdown.as_dict()
    found_risk_details = _risk_details(case, breakdown.found_risks)
    missed_risk_details = _risk_details(case, breakdown.missed_risks)

    try:
        comment = await generate_report_comment(
            decision=session.final_decision or "",
            grade=grade,
            score=breakdown.total,
            score_breakdown=breakdown_dict,
            found_risks=breakdown.found_risks,
            missed_risks=breakdown.missed_risks,
            timeline_summary=timeline_summary,
        )
    except Exception:
        comment = _fallback_comment(case, found_risk_details, missed_risk_details, breakdown_dict)

    source_note = None
    if case.source.case_ids or case.source.official_sources:
        source_note = "이 CASE는 실제 발생한 전세사기 유형을 교육 목적으로 재구성한 시나리오입니다."

    return {
        "case_id": case.case_id,
        "title": case.title,
        "decision": session.final_decision,
        "grade": grade,
        "score": breakdown.as_dict(),
        "case_explanation": case.hidden_truth.explanation,
        "found_risk_details": found_risk_details,
        "missed_risk_details": missed_risk_details,
        "timeline": _enrich_timeline(case, session),
        "comment": comment,
        "source_note": source_note,
        "official_sources": case.source.official_sources,
        "time_expired": session.time_expired,
    }
