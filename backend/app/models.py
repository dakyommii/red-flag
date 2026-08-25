from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Case data (static, loaded from data/cases/*.json) — 설계문서 15장
# ---------------------------------------------------------------------------


class DocumentBlock(BaseModel):
    """조사 결과로 열람 가능한 문서의 한 조각(증거로 등록될 수 있는 단위)."""

    block_id: str
    text: str
    evidence_pattern: str | None = None  # 이 블록을 증거 등록하면 매칭되는 pattern


class CaseDocument(BaseModel):
    document_id: str
    title: str
    blocks: list[DocumentBlock] = Field(default_factory=list)


class Investigation(BaseModel):
    """설계문서 15.2절"""

    investigation_id: str
    name: str
    cost: int = 0
    time_cost: int = 0
    unlock_condition: dict | None = None
    document_id: str | None = None
    hidden_until_unlocked: bool = False


class EvidenceDefinition(BaseModel):
    """CASE 데이터 안에서 어떤 pattern이 어떤 importance/설명을 갖는지 정의 (설계문서 5.1절)."""

    pattern: str
    importance: int = 1
    description: str = ""


class NpcStatement(BaseModel):
    """모순 연결에 사용되는, NPC가 말할 수 있는 고정된 발언 후보."""

    statement_id: str
    text: str
    reveal_keywords: list[str] = Field(default_factory=list)


class NpcPersona(BaseModel):
    """설계문서 8.2절"""

    npc_id: str
    role: str
    display_name: str
    knowledge: list[str] = Field(default_factory=list)
    strategies: list[str] = Field(default_factory=list)
    pressure_level: int = 1
    hidden_information: list[str] = Field(default_factory=list)
    system_prompt: str
    statements: list[NpcStatement] = Field(default_factory=list)
    # 플레이어가 무엇을 물어야 할지 막막하지 않도록 제공하는 예시 질문.
    # 정답(위험 신호)을 지목하지 않고, 계약 전 누구나 해야 할 검증 질문으로만 구성한다.
    suggested_questions: list[str] = Field(default_factory=list)


class Contradiction(BaseModel):
    """설계문서 15.3절"""

    contradiction_id: str
    left: str  # npc statement_id
    right: str  # evidence pattern
    score: int = 10
    explanation: str = ""


class SafeAction(BaseModel):
    action_id: str
    description: str


class EndingOption(BaseModel):
    """설계문서 12장 최종 판단 선택지별 점수 배점."""

    decision: str  # SAFE_TO_PROCEED | NEED_MORE_VERIFICATION | STOP_CONTRACT
    score: int
    comment: str = ""


class HiddenTruth(BaseModel):
    fraud_type: str
    risk_patterns: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    # CASE 종료 후 리포트에서만 노출되는, 이 시나리오가 실제로 어떤 위험이었는지에 대한 해설.
    # rule-based 사실이므로 LLM 코멘트와 별개로 항상 결정론적으로 표시된다.
    explanation: str = ""


class CaseSource(BaseModel):
    case_ids: list[str] = Field(default_factory=list)
    official_sources: list[str] = Field(default_factory=list)


class ScenarioProperty(BaseModel):
    location: str = ""
    price_description: str = ""
    details: dict = Field(default_factory=dict)


class Scenario(BaseModel):
    description: str
    property: ScenarioProperty = Field(default_factory=ScenarioProperty)
    broker_line: str = ""
    speaker_label: str = "중개사"
    goal: str = ""


class Case(BaseModel):
    case_id: str
    title: str
    domain: str
    difficulty: int
    time_limit_seconds: int | None = None
    initial_points: int = 1500

    scenario: Scenario
    documents: list[CaseDocument] = Field(default_factory=list)

    hidden_truth: HiddenTruth
    evidence_definitions: list[EvidenceDefinition] = Field(default_factory=list)

    investigations: list[Investigation] = Field(default_factory=list)
    npc_personas: list[NpcPersona] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    safe_actions: list[SafeAction] = Field(default_factory=list)
    ending_options: list[EndingOption] = Field(default_factory=list)

    source: CaseSource = Field(default_factory=CaseSource)


class CasePublicSummary(BaseModel):
    """CaseSelect 화면용 — 정답 관련 필드 없음."""

    case_id: str
    title: str
    domain: str
    difficulty: int


class CaseBriefing(BaseModel):
    """CaseBriefing 화면용 — hidden_truth 등 정답 데이터는 포함하지 않는다."""

    case_id: str
    title: str
    difficulty: int
    domain: str
    scenario: Scenario
    initial_points: int
    time_limit_seconds: int | None


# ---------------------------------------------------------------------------
# Session (runtime) state
# ---------------------------------------------------------------------------


class MessageRole(str, Enum):
    PLAYER = "player"
    NPC = "npc"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class EvidenceEntry(BaseModel):
    evidence_id: str
    pattern: str
    description: str
    source_document_id: str
    source_block_id: str


class TimelineEvent(BaseModel):
    timestamp: float  # seconds since case start
    kind: str  # investigate | evidence | chat | statement | contradiction | decision
    detail: str


class GameSession(BaseModel):
    session_id: str
    case_id: str
    started_at: float

    remaining_points: int
    remaining_seconds: int | None = None

    completed_investigation_ids: list[str] = Field(default_factory=list)
    evidence_board: list[EvidenceEntry] = Field(default_factory=list)
    revealed_statement_ids: list[str] = Field(default_factory=list)
    contradictions_found: list[str] = Field(default_factory=list)
    chat_history: dict[str, list[ChatMessage]] = Field(default_factory=dict)  # npc_id -> history
    timeline: list[TimelineEvent] = Field(default_factory=list)

    final_decision: str | None = None
    final_score: int | None = None
    time_expired: bool = False
    completed: bool = False
