# 부동산 사기 추리·검증 게임 MVP 설계 문서

## 1. 프로젝트 개요

### 1.1 목표

전세·분양·청약 과정에서 발생할 수 있는 사기를 사용자가 **직접 조사하고
판단하는 추리·문서 검증형 교육 게임**으로 구현한다.

기존의 `사기범 NPC와 대화 → 대응 평가` 중심 구조를 확장하여 다음 세 가지
게임성을 결합한다.

-   **문서 검증:** 계약서, 등기 정보, 매물 정보 등에서 이상 징후 발견
-   **사건 추리:** 흩어진 정보와 증거를 연결하여 사건의 구조 파악
-   **모순 지적:** NPC의 설명과 실제 문서·공식정보 간 불일치 발견

### 1.2 핵심 교육 목표

게임의 목표는 단순히 "사기인지 맞히는 것"이 아니다.

사용자가 다음 능력을 학습하도록 설계한다.

1.  계약 전에 무엇을 확인해야 하는가
2.  어떤 정보가 위험 신호인가
3.  상대방의 설명을 어떻게 검증해야 하는가
4.  정보가 부족할 때 계약을 보류할 수 있는가
5.  여러 위험 신호를 종합하여 합리적으로 판단할 수 있는가

------------------------------------------------------------------------

# 2. 핵심 게임 루프

``` text
CASE 시작
   ↓
매물/상황 브리핑
   ↓
초기 자료 확인
   ↓
조사 대상 선택
   ├─ 문서 조회
   ├─ 공식정보 조회
   └─ NPC 질문
   ↓
위험 신호 발견
   ↓
증거 등록
   ↓
정보 간 모순 연결
   ↓
최종 판단
   ├─ 계약 진행
   ├─ 추가 확인/보류
   └─ 계약 중단
   ↓
CASE REPORT
   ↓
실제 사례 및 공식 예방정보 학습
```

한 CASE의 목표 플레이 시간은 MVP 기준 약 **5\~10분**으로 한다.

------------------------------------------------------------------------

# 3. 게임 화면 구성

## 3.1 CASE 브리핑 화면

표시 정보:

-   CASE 번호
-   난이도
-   계약 종류
-   매물/분양/청약 기본 정보
-   의뢰인 또는 플레이어 상황
-   제한시간 또는 조사 포인트

예:

``` text
CASE #003

[전세계약]

서울 ○○구 신축 오피스텔
전세금 2억 7천만 원

중개사:
"융자도 없고 보증보험도 가능한 안전한 매물입니다."

목표:
이 계약을 진행해도 되는지 판단하십시오.

조사 포인트: 1,500P
```

------------------------------------------------------------------------

## 3.2 조사 화면

조사 가능한 항목을 카드 또는 메뉴 형태로 제공한다.

예:

``` text
[매물 광고]
[등기 정보]
[건축물 정보]
[시세 정보]
[임대인 정보]
[중개사 정보]
[보증 관련 정보]
[계약서]
[관계자에게 질문]
```

CASE마다 처음부터 모든 메뉴를 공개하지 않아도 된다.

특정 단서를 발견하면 새로운 조사 항목을 unlock할 수 있다.

------------------------------------------------------------------------

# 4. 조사 시스템

## 4.1 조사 포인트

플레이어가 모든 자료를 무조건 확인하지 못하도록 제한한다.

예:

  조사                 비용
  ------------------ ------
  등기 정보            500P
  건축물 정보          300P
  실거래/시세          300P
  중개사 등록 확인     200P
  임대인 추가 조사     500P
  보증 관련 확인       300P

초기 포인트:

``` text
1,500P
```

목적은 단순 자원 관리가 아니라 **무엇을 우선 확인해야 하는지 학습**하게
하는 것이다.

## 4.2 제한시간 모드

후반 CASE에서는 포인트 대신 또는 포인트와 함께 제한시간을 사용한다.

``` text
계약까지 남은 시간: 20:00
```

조사할 때 시간이 감소한다.

------------------------------------------------------------------------

# 5. 증거 시스템

플레이어는 문서 전체를 보는 것에서 끝나지 않고 **수상한 부분을 증거로
등록**해야 한다.

예:

``` text
등기 정보

소유권 이전
2026.03.21
A → B

[이 부분을 증거로 등록]
```

등록 결과:

``` text
Evidence #02

RECENT_OWNERSHIP_CHANGE
최근 소유권 변경
```

## 5.1 Evidence 데이터

``` json
{
  "evidence_id": "E02",
  "source": "registry",
  "pattern": "RECENT_OWNERSHIP_CHANGE",
  "importance": 2,
  "description": "최근 소유권이 변경됨"
}
```

------------------------------------------------------------------------

# 6. 위험 신호 시스템

수집한 Fraud Taxonomy와 Risk Pattern을 게임의 정답 데이터로 사용한다.

예:

``` text
HIGH_JEONSE_RATIO
TRUST_REGISTRATION
RECENT_OWNERSHIP_CHANGE
EXCESSIVE_MORTGAGE
VERIFICATION_BLOCK
URGENCY
PERSONAL_ACCOUNT_REQUEST
FALSE_GUARANTEE_CLAIM
FAKE_AUTHORITY
```

CASE에는 실제 위험 신호 중 일부만 노출한다.

``` json
{
  "risk_patterns": [
    "TRUST_REGISTRATION",
    "VERIFICATION_BLOCK",
    "URGENCY"
  ]
}
```

------------------------------------------------------------------------

# 7. 모순 발견 시스템

이 게임의 핵심 기능이다.

플레이어가 서로 다른 두 정보를 연결한다.

예:

### NPC 발언

``` text
"집주인이 직접 계약하면 아무 문제 없습니다."
```

### 문서

``` text
신탁 관련 권리관계/계약 권한 확인 필요
```

플레이어가 두 항목을 선택한다.

``` text
[NPC 발언]
       ↕
[문서 Evidence]

[모순 지적]
```

정답인 경우:

``` text
CONTRADICTION FOUND
```

CASE 진행도와 점수를 증가시킨다.

------------------------------------------------------------------------

# 8. NPC 대화 시스템

## 8.1 역할

LLM NPC는 정답을 직접 알려주는 챗봇이 아니다.

플레이어가 관계자를 조사하는 인터페이스다.

NPC 예:

-   공인중개사
-   임대인
-   분양 직원
-   분양대행사 직원
-   가족
-   피해자
-   건설사 관계자

## 8.2 Persona

``` json
{
  "npc_id": "NPC_01",
  "role": "real_estate_agent",
  "case_id": "JEONSE_003",

  "knowledge": [
    "property_information",
    "trust_registration"
  ],

  "strategies": [
    "SAFETY_CLAIM",
    "URGENCY",
    "AUTHORITY"
  ],

  "pressure_level": 2,

  "hidden_information": [
    "contract_authority_issue"
  ]
}
```

## 8.3 NPC System Prompt 개념

``` text
당신은 부동산 계약 시뮬레이션의 등장인물이다.

ROLE:
공인중개사

현재 CASE에 정의된 사실만 사용한다.

사용자가 질문하면 실제 중개사처럼 자연스럽게 대답한다.

CASE에 없는 새로운 사실을 만들지 않는다.

게임의 정답이나 fraud_type을 직접 알려주지 않는다.

정해진 persuasion strategy 범위 안에서만 행동한다.
```

------------------------------------------------------------------------

# 9. 플레이어 질문 처리

사용자는 자유롭게 질문할 수 있다.

예:

``` text
"보증보험 가입 가능한가요?"
"신탁회사에 직접 확인해도 되나요?"
"집주인이 최근에 바뀐 이유가 뭔가요?"
```

백엔드:

``` text
User Question
     ↓
Case Context
+
NPC Persona
+
Conversation History
     ↓
LLM
     ↓
NPC Response
```

------------------------------------------------------------------------

# 10. CASE 구성

## CASE 1 --- 높은 전세가율

### 목표

시세와 전세금 비교 학습

### 주요 단서

``` text
전세금 2억 3천
주변 거래가 약 2억 2천
```

### Risk

``` text
HIGH_JEONSE_RATIO
URGENCY
```

### 난이도

★☆☆☆☆

------------------------------------------------------------------------

## CASE 2 --- 최근 소유권 변경

### 목표

등기 정보와 임대인 정보 연결

### Risk

``` text
RECENT_OWNERSHIP_CHANGE
MULTIPLE_PROPERTY_ACQUISITION
HIGH_JEONSE_RATIO
```

### 난이도

★★☆☆☆

------------------------------------------------------------------------

## CASE 3 --- 신탁부동산

### 목표

문서와 중개사 설명의 모순 발견

### 핵심 조사

``` text
등기 정보
→ 신탁 발견
→ 추가 문서/공식 확인
→ 계약 권한 검증
```

### Risk

``` text
TRUST_REGISTRATION
VERIFICATION_BLOCK
SAFETY_CLAIM
URGENCY
```

### 난이도

★★★☆☆

------------------------------------------------------------------------

## CASE 4 --- 청약/분양 사칭

### 시작

``` text
[○○건설]

잔여세대 특별공급 대상자로 선정되었습니다.
오늘 오후 5시까지 계약 의사를 확인해주세요.
```

### 조사

``` text
문자
사이트
분양공고
청약Home
건설사 공식 연락처
입금계좌
```

### 핵심 학습

**상대가 제공한 검증 수단만으로 상대를 검증하지 않는다.**

### Risk

``` text
FAKE_AUTHORITY
FAKE_WEBSITE
URGENCY
PAYMENT_PRESSURE
```

### 난이도

★★★★☆

------------------------------------------------------------------------

## CASE 5 --- 분양 투자

### 상황

``` text
분양가 3억
월 180만 원 임대수익 보장
```

### 조사

``` text
시행사
시공사
분양대행사
토지/건축 관련 정보
계약서
수익보장 관련 자료
```

### 특징

모든 이상 신호가 곧바로 사기를 의미하지 않도록 설계한다.

최종 선택:

``` text
계약 진행 가능
추가 확인 필요
계약 중단
```

### 난이도

★★★★☆

------------------------------------------------------------------------

# 11. FINAL CASE --- 가족의 계약을 막아라

## 상황

``` text
동생:
"나 집 구했어.
신축인데 시세보다 싸게 나왔어.
오늘 계약하려고."
```

플레이어는 동생이 가진 정보를 질문을 통해 확보한다.

### 제한시간

``` text
계약까지 20:00
```

### 조사 후보

``` text
등기 정보
시세
건축물 정보
중개사
임대인
보증 관련 확인
```

### 위험 신호 예

``` text
전세가율 92%
최근 소유권 변경
근저당 존재
계약 재촉
```

### 핵심

최고점 답변은 반드시

``` text
"사기다"
```

가 아니다.

충분한 검증이 이루어지지 않았다면

``` text
"현재 확인되지 않은 위험 요소가 있으므로
오늘 계약하지 말고 추가 확인한다."
```

와 같은 판단이 가장 높은 평가를 받을 수 있다.

------------------------------------------------------------------------

# 12. 최종 판단 시스템

플레이어 선택:

``` text
SAFE_TO_PROCEED
NEED_MORE_VERIFICATION
STOP_CONTRACT
```

평가는 단순 정답 비교로 하지 않는다.

## 평가 요소

``` text
Risk Discovery
Evidence Quality
Contradiction Discovery
Investigation Priority
Final Decision
```

예시 배점:

  평가                    점수
  --------------------- ------
  핵심 위험 신호 발견       40
  중요 증거 확보            20
  모순 발견                 15
  효율적 조사               10
  최종 판단                 15

총점:

``` text
100
```

------------------------------------------------------------------------

# 13. CASE REPORT

게임 종료 후 교육 콘텐츠를 제공한다.

``` text
CASE REPORT

판단
추가 확인 필요

등급
A

발견한 위험 신호

✓ 높은 전세가율
✓ 최근 소유권 변경
✓ 계약 재촉

놓친 위험 신호

✕ 선순위 권리관계
✕ 보증 관련 확인
```

## 행동 Timeline

``` text
12:03 매물 확인

12:05 실거래가 조회
      HIGH_JEONSE_RATIO 발견

12:08 NPC 질문

12:10 등기 정보 조회
      RECENT_OWNERSHIP_CHANGE 발견

12:14 계약 보류 결정
```

## 실제 사례 연결

CASE가 실제 사건 기반이라면 개인정보를 제거하고 다음을 표시한다.

``` text
이 CASE는 실제 발생한 전세사기 유형을
교육 목적으로 재구성한 시나리오입니다.
```

공식 출처 URL과 예방정보를 함께 제공한다.

------------------------------------------------------------------------

# 14. AI 활용 구조

## AI 1 --- 실제 사건 → CASE 생성

``` text
real_cases.json
      ↓
LLM Case Generator
      ↓
검증
      ↓
case.json
```

LLM이 임의로 법률/사실을 생성하지 않도록 실제 사례와 공식 Knowledge를
context로 제공한다.

------------------------------------------------------------------------

## AI 2 --- NPC

``` text
CASE
+
Persona
+
Conversation
      ↓
LLM
      ↓
NPC Response
```

------------------------------------------------------------------------

## AI 3 --- 사용자 발화 평가

예:

``` text
"일단 계약하지 말고 등기부터 확인할게요."
```

Evaluator:

``` json
{
  "matched_actions": [
    "STOP_TEMPORARILY",
    "CHECK_REGISTRY"
  ],
  "risk_level": "SAFE"
}
```

------------------------------------------------------------------------

## AI 4 --- 개인화 피드백

게임 종료 후:

``` text
발견한 Risk
놓친 Risk
조사 순서
최종 판단
```

을 입력하여 개인화된 피드백을 생성한다.

------------------------------------------------------------------------

# 15. 데이터 구조

## 15.1 Case

``` json
{
  "case_id": "JEONSE_003",
  "title": "안전해 보이는 오피스텔",
  "domain": "JEONSE",
  "difficulty": 3,

  "scenario": {
    "description": "",
    "property": {},
    "initial_documents": [],
    "characters": []
  },

  "hidden_truth": {
    "fraud_type": "TRUST_PROPERTY",
    "risk_patterns": [],
    "required_evidence": []
  },

  "investigations": [],

  "npc_personas": [],

  "contradictions": [],

  "safe_actions": [],

  "ending_conditions": {},

  "source": {
    "case_ids": [],
    "official_sources": []
  }
}
```

## 15.2 Investigation

``` json
{
  "investigation_id": "CHECK_REGISTRY",
  "name": "등기 정보 확인",
  "cost": 500,
  "time_cost": 120,
  "unlock_condition": null,
  "document_id": "DOC_02"
}
```

## 15.3 Contradiction

``` json
{
  "contradiction_id": "C01",
  "left": "NPC_STATEMENT_03",
  "right": "EVIDENCE_04",
  "score": 10
}
```

------------------------------------------------------------------------

# 16. 백엔드 아키텍처

기존 FastAPI 구조를 유지하는 것을 권장한다.

``` text
Frontend
   │
   ▼
FastAPI
   │
   ├── Case Engine
   │
   ├── Investigation Engine
   │
   ├── Evidence Engine
   │
   ├── NPC Service
   │       └── LLM API
   │
   ├── Evaluator Service
   │       └── LLM API
   │
   └── Report Generator
           └── LLM API

          │
          ▼

     Game Dataset
```

------------------------------------------------------------------------

# 17. API 설계

## CASE 시작

``` text
POST /api/cases/{case_id}/start
```

## 조사

``` text
POST /api/game/{session_id}/investigate
```

Request:

``` json
{
  "investigation_id": "CHECK_REGISTRY"
}
```

## 증거 등록

``` text
POST /api/game/{session_id}/evidence
```

## NPC 질문

``` text
POST /api/game/{session_id}/chat
```

Request:

``` json
{
  "npc_id": "NPC_01",
  "message": "신탁회사에 확인해도 되나요?"
}
```

## 모순 제출

``` text
POST /api/game/{session_id}/contradiction
```

## 최종 판단

``` text
POST /api/game/{session_id}/decision
```

## 결과

``` text
GET /api/game/{session_id}/report
```

------------------------------------------------------------------------

# 18. 프론트엔드 구조

MVP는 웹 기반을 권장한다.

``` text
React / Next.js
```

주요 화면:

``` text
/
├── CaseSelect
├── CaseBriefing
├── Investigation
│   ├── DocumentViewer
│   ├── EvidenceBoard
│   └── NPCChat
├── FinalDecision
└── CaseReport
```

## Investigation 화면 예

``` text
┌───────────────────────────────────────┐
│ CASE #003          12:32     900P     │
├───────────────┬───────────────────────┤
│               │                       │
│ 조사 메뉴      │   문서 / NPC          │
│               │                       │
│ □ 매물         │   [등기 정보]          │
│ □ 등기         │                       │
│ □ 시세         │   ...                 │
│ □ 임대인       │                       │
│               │                       │
├───────────────┴───────────────────────┤
│ Evidence Board                        │
│ E01      E02      E03                 │
└───────────────────────────────────────┘
```

------------------------------------------------------------------------

# 19. 데이터 파이프라인 연결

기존에 설계한 데이터셋을 다음처럼 사용한다.

``` text
real_cases
    ↓
CASE 시나리오

fraud_taxonomy
    ↓
hidden_truth / risk_patterns

scammer_dialog_patterns
    ↓
NPC Persona / Strategy

user_response_patterns
    ↓
Evaluator

contract_flow + checklist
    ↓
Investigation / Safe Action / Feedback
```

따라서 기존 데이터 수집 작업을 그대로 재사용할 수 있다.

------------------------------------------------------------------------

# 20. MVP 범위

처음부터 모든 기능을 구현하지 않는다.

## 반드시 구현

-   CASE 선택
-   CASE 브리핑
-   조사 메뉴
-   문서 조회
-   Evidence 등록
-   NPC 자유 질문
-   최종 판단
-   점수
-   CASE REPORT

## 2차 구현

-   모순 연결 UI
-   제한시간
-   조사 포인트
-   조사 unlock
-   AI CASE 자동 생성

## 향후

-   실제 문서 OCR
-   실제 사용자의 계약서 분석
-   멀티플레이
-   랜덤 CASE 생성
-   난이도 개인화

------------------------------------------------------------------------

# 21. MVP 개발 순서

### Phase 1 --- Case Engine

정적인 `case.json` 하나로 게임 전체가 동작하도록 만든다.

추천 첫 CASE:

``` text
신탁부동산
```

### Phase 2 --- Investigation

``` text
문서 조회
→ Evidence 발견
→ Evidence 등록
```

### Phase 3 --- NPC

LLM 기반 중개사 NPC를 연결한다.

### Phase 4 --- Decision / Score

최종 판단과 Rule-based 점수 계산을 구현한다.

### Phase 5 --- AI Evaluator

자유 입력 대응 평가를 추가한다.

### Phase 6 --- Report

개인화된 CASE REPORT를 생성한다.

### Phase 7 --- Case 확장

``` text
CASE 1 높은 전세가율
CASE 2 소유권 변경
CASE 3 신탁
CASE 4 청약 사칭
CASE 5 분양 투자
FINAL CASE 복합형
```

------------------------------------------------------------------------

# 22. 구현 원칙

## 게임의 정답은 LLM에 맡기지 않는다

가장 중요한 원칙이다.

``` text
CASE 정답
Risk Pattern
Evidence
Contradiction
Ending Condition
```

은 `case.json`에 명시한다.

LLM은 다음에만 사용한다.

``` text
NPC 자연어 생성
사용자 자유발화 의미 분류
CASE 생성 보조
개인화 피드백
```

즉:

``` text
Rule-based Game Engine
        +
LLM Interaction Layer
```

구조를 사용한다.

이렇게 해야 LLM hallucination 때문에 게임의 정답이 바뀌는 문제를 막을 수
있다.

------------------------------------------------------------------------

# 23. 최종 MVP 구조

``` text
                ┌──────────────┐
                │ Real Cases   │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ Case Dataset │
                └──────┬───────┘
                       │
             ┌─────────▼─────────┐
             │    Game Engine    │
             └─────────┬─────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
 Investigation      NPC Chat      Evidence
        │              │              │
        │             LLM             │
        └──────────────┼──────────────┘
                       ▼
                  Final Decision
                       │
                       ▼
                    Score
                       │
                       ▼
                  CASE REPORT
```

## 핵심 구현 방향

> **실제 사건과 공식 예방 데이터를 정답 데이터로 사용하고,\
> LLM은 게임의 정답을 결정하는 모델이 아니라 플레이어와 상호작용하는 AI
> Layer로 사용한다.**

이 구조를 유지하면 교육적 신뢰성과 게임성을 동시에 확보하면서 기존
`detect-voicephsing` 프로젝트의 LLM 대화/Evaluator 구조도 재사용할 수
있다.
