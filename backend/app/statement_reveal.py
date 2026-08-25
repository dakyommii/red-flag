"""NPC 발언 확보(reveal) 판정 — 설계문서 22장 원칙에 따라 rule-based로만 동작한다.

플레이어가 NPC에게 질문하면, 그 질문과 NPC의 답변 양쪽을 대상으로 case.json에 선언된
statement.reveal_keywords를 매칭해 어떤 발언을 "확보"했는지 결정한다.

LLM 답변에 의존하지 않고 플레이어의 질문만으로도 확보가 가능하도록 양쪽을 모두 본다.
(ANTHROPIC_API_KEY가 없어 NPC가 폴백 문구만 반환하는 환경에서도 게임이 진행 가능해야 한다.)
"""

from app.models import Case, GameSession


def _normalize(text: str) -> str:
    return text.replace(" ", "").lower()


def reveal_statements(
    case: Case, session: GameSession, npc_id: str, player_message: str, npc_reply: str
) -> list[dict]:
    """이번 대화로 새로 확보된 발언 목록을 반환하고 세션에 기록한다."""
    npc = next((n for n in case.npc_personas if n.npc_id == npc_id), None)
    if npc is None:
        return []

    haystack = _normalize(f"{player_message} {npc_reply}")
    newly_revealed = []

    for statement in npc.statements:
        if statement.statement_id in session.revealed_statement_ids:
            continue
        if not statement.reveal_keywords:
            continue
        if any(_normalize(kw) in haystack for kw in statement.reveal_keywords):
            session.revealed_statement_ids.append(statement.statement_id)
            newly_revealed.append(
                {
                    "statement_id": statement.statement_id,
                    "npc_id": npc.npc_id,
                    "text": statement.text,
                }
            )

    return newly_revealed
