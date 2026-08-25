from anthropic import AsyncAnthropic

from app.config import ANTHROPIC_API_KEY, NPC_MODEL, REPORT_MODEL
from app.models import ChatMessage, MessageRole

_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


def _to_anthropic_messages(history: list[ChatMessage]) -> list[dict]:
    return [
        {"role": "user" if m.role == MessageRole.PLAYER else "assistant", "content": m.content}
        for m in history
    ]


NPC_FALLBACK_REPLY = "(지금은 답변하기 어렵습니다. 잠시 후 다시 질문해주세요.)"


async def npc_reply(system_prompt: str, history: list[ChatMessage]) -> str:
    try:
        response = await _client.messages.create(
            model=NPC_MODEL,
            max_tokens=400,
            system=system_prompt,
            messages=_to_anthropic_messages(history),
        )
        return next(block.text for block in response.content if block.type == "text")
    except Exception:
        return NPC_FALLBACK_REPLY


REPORT_COMMENT_PROMPT_TEMPLATE = """당신은 부동산 사기 예방 교육 게임의 코치다.
아래는 플레이어가 이번 CASE를 플레이한 결과를 규칙 기반으로 계산한 사실 데이터다.
이 데이터에 없는 사실(새로운 위험 신호, 법률 판단, 구체적 수치 등)을 절대 지어내지 말고,
아래 데이터만 근거로 "잘한 점"과 "아쉬운 점" 두 문단으로 개인화된 코칭 코멘트를 작성하라.
각 문단은 2~3문장, 친근하되 교육적인 톤을 유지한다. 이 CASE가 어떤 상황이었는지에 대한 해설은
이미 별도로 제공되므로 다시 설명하지 말고, 플레이어의 조사 과정과 판단 자체를 평가하는 데 집중하라.

판단: {decision}
등급: {grade}
점수: {score}/100
점수 내역: 핵심 위험 신호 발견 {risk_discovery}/40, 증거 확보 {evidence_quality}/20, 모순 발견 {contradiction}/15, 효율적 조사 {efficiency}/10, 최종 판단 {final_decision}/15
발견한 위험 신호: {found_risks}
놓친 위험 신호: {missed_risks}
행동 순서 요약: {timeline_summary}

출력 형식 (그대로 두 줄로, 각 줄 뒤에 문단 내용):
잘한 점: ...
아쉬운 점: ...
"""


async def generate_report_comment(
    decision: str,
    grade: str,
    score: int,
    score_breakdown: dict,
    found_risks: list[str],
    missed_risks: list[str],
    timeline_summary: str,
) -> str:
    prompt = REPORT_COMMENT_PROMPT_TEMPLATE.format(
        decision=decision,
        grade=grade,
        score=score,
        risk_discovery=score_breakdown.get("risk_discovery", 0),
        evidence_quality=score_breakdown.get("evidence_quality", 0),
        contradiction=score_breakdown.get("contradiction", 0),
        efficiency=score_breakdown.get("efficiency", 0),
        final_decision=score_breakdown.get("final_decision", 0),
        found_risks=", ".join(found_risks) or "없음",
        missed_risks=", ".join(missed_risks) or "없음",
        timeline_summary=timeline_summary or "기록 없음",
    )
    response = await _client.messages.create(
        model=REPORT_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return next(block.text for block in response.content if block.type == "text")
