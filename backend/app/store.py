"""세션 저장소 — 로컬 개발에서는 인메모리, 프로덕션(Vercel)에서는 Neon Postgres.

`DATABASE_URL`이 설정되어 있으면 `init()`에서 asyncpg pool을 만들고 세션을
`sessions` 테이블의 JSONB 컬럼에 저장한다. 설정되어 있지 않으면 기존과 동일하게
프로세스 메모리 dict를 사용한다 — 로컬 `uvicorn --reload` 개발 경험은 전혀 바뀌지 않는다.

라우터들은 모듈 임포트 시점에 `from app.store import store`로 이 싱글턴 객체를 가져오므로,
백엔드가 있는지 없는지는 이 객체의 내부 상태(`self._pool`)로만 분기한다 — 객체 자체를
교체하지 않는다.
"""

import time
import uuid

import asyncpg

from app.models import GameSession

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    data JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, GameSession] = {}
        self._pool: asyncpg.Pool | None = None

    async def init(self, dsn: str) -> None:
        if not dsn:
            return
        self._pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5, statement_cache_size=0)
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_TABLE_SQL)
            # 가벼운 정리: 7일 넘은 세션은 생성 시점에 슬쩍 정리한다 (별도 백그라운드
            # 프로세스를 둘 수 없는 서버리스 환경이라 이 방식이 가장 간단하다).
            await conn.execute("DELETE FROM sessions WHERE updated_at < now() - interval '7 days'")

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def create(self, case_id: str, initial_points: int, time_limit_seconds: int | None) -> GameSession:
        session = GameSession(
            session_id=str(uuid.uuid4()),
            case_id=case_id,
            started_at=time.time(),
            remaining_points=initial_points,
            remaining_seconds=time_limit_seconds,
        )
        await self.save(session)
        return session

    async def get(self, session_id: str) -> GameSession | None:
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("SELECT data FROM sessions WHERE session_id = $1", session_id)
            if row is None:
                return None
            return GameSession.model_validate_json(row["data"])
        return self._sessions.get(session_id)

    async def save(self, session: GameSession) -> None:
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO sessions (session_id, data, updated_at) VALUES ($1, $2::jsonb, now()) "
                    "ON CONFLICT (session_id) DO UPDATE SET data = $2::jsonb, updated_at = now()",
                    session.session_id,
                    session.model_dump_json(),
                )
        else:
            self._sessions[session.session_id] = session

    def elapsed_seconds(self, session: GameSession) -> float:
        return time.time() - session.started_at


store = SessionStore()
