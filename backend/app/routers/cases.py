from fastapi import APIRouter, HTTPException

from app.case_loader import get_case, list_cases
from app.models import CaseBriefing, CasePublicSummary, GameSession
from app.store import store

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=list[CasePublicSummary])
def get_cases() -> list[CasePublicSummary]:
    return list_cases()


class StartResponse(CaseBriefing):
    session_id: str


@router.post("/{case_id}/start", response_model=StartResponse)
async def start_case(case_id: str) -> StartResponse:
    case = get_case(case_id)
    if case is None:
        raise HTTPException(404, "case not found")

    session: GameSession = await store.create(
        case_id=case.case_id,
        initial_points=case.initial_points,
        time_limit_seconds=case.time_limit_seconds,
    )

    return StartResponse(
        session_id=session.session_id,
        case_id=case.case_id,
        title=case.title,
        difficulty=case.difficulty,
        domain=case.domain,
        scenario=case.scenario,
        initial_points=case.initial_points,
        time_limit_seconds=case.time_limit_seconds,
    )
