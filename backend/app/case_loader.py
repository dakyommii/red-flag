import json
from functools import lru_cache

from app.config import CASES_DIR
from app.models import Case, CasePublicSummary


@lru_cache
def _load_all() -> dict[str, Case]:
    cases: dict[str, Case] = {}
    for path in sorted(CASES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        case = Case(**data)
        cases[case.case_id] = case
    return cases


def reload_cases() -> None:
    """개발 중 case.json 변경 사항을 다시 읽고 싶을 때 사용."""
    _load_all.cache_clear()


def list_cases() -> list[CasePublicSummary]:
    return [
        CasePublicSummary(
            case_id=c.case_id, title=c.title, domain=c.domain, difficulty=c.difficulty
        )
        for c in _load_all().values()
    ]


def get_case(case_id: str) -> Case | None:
    return _load_all().get(case_id)
