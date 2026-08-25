"""설계문서 12장 최종 판단 시스템 — 순수 rule-based 점수 계산.

LLM을 전혀 사용하지 않는다 (설계문서 22장 원칙). Phase 4(결정 제출)와 Phase 6(리포트
조회) 양쪽에서 동일한 함수를 호출하므로 항상 결정론적으로 같은 점수가 나온다.
"""

from app.models import Case, GameSession


class ScoreBreakdown:
    def __init__(self) -> None:
        self.risk_discovery = 0
        self.evidence_quality = 0
        self.contradiction = 0
        self.efficiency = 0
        self.final_decision = 0
        self.found_risks: list[str] = []
        self.missed_risks: list[str] = []

    @property
    def total(self) -> int:
        return (
            self.risk_discovery
            + self.evidence_quality
            + self.contradiction
            + self.efficiency
            + self.final_decision
        )

    def as_dict(self) -> dict:
        return {
            "risk_discovery": self.risk_discovery,
            "evidence_quality": self.evidence_quality,
            "contradiction": self.contradiction,
            "efficiency": self.efficiency,
            "final_decision": self.final_decision,
            "total": self.total,
            "found_risks": self.found_risks,
            "missed_risks": self.missed_risks,
        }


def grade_for(total: int) -> str:
    if total >= 85:
        return "A"
    if total >= 70:
        return "B"
    if total >= 50:
        return "C"
    return "D"


def compute_breakdown(case: Case, session: GameSession) -> ScoreBreakdown:
    result = ScoreBreakdown()

    risk_patterns = set(case.hidden_truth.risk_patterns)
    found_patterns = {e.pattern for e in session.evidence_board}
    found_risk = risk_patterns & found_patterns
    missed_risk = risk_patterns - found_patterns
    result.found_risks = sorted(found_risk)
    result.missed_risks = sorted(missed_risk)
    result.risk_discovery = (
        round(40 * len(found_risk) / len(risk_patterns)) if risk_patterns else 0
    )

    importance_by_pattern = {d.pattern: d.importance for d in case.evidence_definitions}
    total_importance = sum(importance_by_pattern.values()) or 1
    gained_importance = sum(
        importance_by_pattern.get(e.pattern, 0) for e in session.evidence_board
    )
    result.evidence_quality = round(20 * min(gained_importance / total_importance, 1.0))

    total_contradiction_score = sum(c.score for c in case.contradictions) or 1
    gained_contradiction_score = sum(
        c.score for c in case.contradictions if c.contradiction_id in session.contradictions_found
    )
    result.contradiction = round(
        15 * min(gained_contradiction_score / total_contradiction_score, 1.0)
    )

    investigate_count = len(session.completed_investigation_ids)
    if investigate_count:
        useful_ratio = min(len(session.evidence_board) / investigate_count, 1.0)
        result.efficiency = round(10 * useful_ratio)
    else:
        result.efficiency = 0

    if session.final_decision:
        matching = next(
            (o for o in case.ending_options if o.decision == session.final_decision), None
        )
        result.final_decision = matching.score if matching else 0

    return result
