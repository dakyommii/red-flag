from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, DATABASE_URL
from app.routers import admin, cases, game
from app.store import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    await store.init(DATABASE_URL)
    yield
    await store.close()


app = FastAPI(title="부동산 사기 추리·검증 게임 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(cases.router)
app.include_router(game.router)
app.include_router(admin.router)
