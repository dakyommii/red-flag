from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.case_generator import CaseGenerationError, generate_case_draft, get_draft, list_drafts, promote_draft

router = APIRouter(prefix="/api/admin/cases", tags=["admin"])


class GenerateRequest(BaseModel):
    seed_summary: str
    domain: str
    difficulty: int = 2


@router.post("/generate")
async def generate(body: GenerateRequest) -> dict:
    return await generate_case_draft(body.seed_summary, body.domain, body.difficulty)


@router.get("/drafts")
def drafts() -> list[dict]:
    return list_drafts()


@router.get("/drafts/{draft_id}")
def draft_detail(draft_id: str) -> dict:
    record = get_draft(draft_id)
    if record is None:
        raise HTTPException(404, "draft not found")
    return record


@router.post("/drafts/{draft_id}/promote")
def promote(draft_id: str) -> dict:
    try:
        case = promote_draft(draft_id)
    except CaseGenerationError as e:
        raise HTTPException(400, str(e))
    return {"promoted": True, "case_id": case.case_id}
