"""조사 unlock_condition 해석기 — 설계문서 3.2절 / 4.2(2차) / 10장(Phase 10 대비).

CASE 데이터에 선언적으로 표현된 조건만 해석한다. 지원 형태:
  {"requires_evidence": "PATTERN"}       특정 Evidence pattern이 등록되어 있어야 함
  {"requires_investigation": "INV_ID"}   특정 조사가 이미 완료되어 있어야 함
None이면 조건 없이 항상 잠금 해제 상태.
"""

from app.models import GameSession


def is_unlocked(unlock_condition: dict | None, session: GameSession) -> bool:
    if not unlock_condition:
        return True
    if "requires_evidence" in unlock_condition:
        pattern = unlock_condition["requires_evidence"]
        return any(e.pattern == pattern for e in session.evidence_board)
    if "requires_investigation" in unlock_condition:
        inv_id = unlock_condition["requires_investigation"]
        return inv_id in session.completed_investigation_ids
    return True
