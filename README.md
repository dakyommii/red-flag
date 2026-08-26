# 부동산 사기 추리·검증 게임

전세/청약/분양 사기 시나리오를 직접 조사하고, NPC와 대화하고, 증거를 모아 계약 진행 여부를 판단하는
추리 게임입니다. 게임의 정답(모순, 위험 신호, 점수)은 전부 규칙 기반 코드가 판정하며, LLM은 NPC
대사 생성과 리포트 코멘트 문체를 다듬는 보조 역할만 담당합니다.

**Live**: https://red-flag-eight-peach.vercel.app

## 구조

```
red-flag/
├── backend/            # FastAPI (Python)
│   └── app/
│       ├── routers/    # cases, game, admin
│       ├── store.py    # 세션 저장소 (로컬: 인메모리 / 프로덕션: Neon Postgres)
│       ├── scoring.py, unlock.py, statement_reveal.py  # 규칙 기반 게임 로직
│       └── llm_client.py  # NPC 대사·리포트 코멘트 생성 (폴백 지원)
├── frontend/           # React + Vite + TypeScript
├── data/
│   ├── cases/          # 케이스 데이터 (JSON)
│   └── knowledge/      # 사기 유형/실제 사례 지식 베이스
├── api/index.py         # Vercel 서버리스 진입점
├── vercel.json          # Vercel 빌드/라우팅 설정
└── docs/                # 설계 문서, 구현 프롬프트, 테스트케이스
```

## 로컬 개발

### 백엔드

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # ANTHROPIC_API_KEY 입력 (없어도 폴백으로 동작)
.venv/bin/uvicorn app.main:app --reload --port 8010
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, /api는 8010으로 프록시
```

## 환경 변수 (`backend/.env`)

| 변수 | 설명 | 기본값 |
|---|---|---|
| `ANTHROPIC_API_KEY` | 없으면 NPC/리포트 코멘트가 정적 폴백 문구로 동작 | (없음) |
| `DATABASE_URL` | 설정 시 Neon Postgres 세션 저장, 미설정 시 인메모리 | (없음, 로컬 기본) |
| `NPC_MODEL` | NPC 대사 생성 모델 | `claude-haiku-4-5-20251001` |
| `REPORT_MODEL` | 리포트 코멘트 생성 모델 | `claude-sonnet-5` |
| `CORS_ORIGINS` | 허용 오리진 (쉼표 구분) | `http://localhost:5173` |

## 배포 (Vercel + Neon)

- 프론트엔드: `@vercel/static-build`로 `frontend/`를 빌드해 정적 서빙
- 백엔드: `@vercel/python`으로 `api/index.py` (FastAPI ASGI 앱)를 서버리스 함수로 배포
- 세션 저장소: Vercel Storage → Neon 연동 시 자동 주입되는 `DATABASE_URL`을 사용, 서버리스 요청 간 세션 유지
- `data/**`는 `vercel.json`의 `includeFiles`로 함수 번들에 포함

## 문서

- [`docs/부동산_사기_추리게임_MVP_설계문서.md`](docs/부동산_사기_추리게임_MVP_설계문서.md) — 설계 문서
- [`docs/구현_단계별_프롬프트.md`](docs/구현_단계별_프롬프트.md) — 단계별 구현 프롬프트
- [`docs/테스트케이스.md`](docs/테스트케이스.md) — 테스트케이스
