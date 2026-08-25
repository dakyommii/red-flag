import { useLocation, useNavigate, useParams } from "react-router-dom";
import type { StartResponse } from "../api/types";
import CharacterSpeech from "../components/CharacterSpeech";
import PlayGuide from "../components/PlayGuide";

export default function CaseBriefing() {
  const { sessionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const briefing = location.state as StartResponse | undefined;

  if (!briefing) {
    return (
      <div className="page">
        <p className="muted">
          브리핑 정보를 찾을 수 없습니다. CASE 선택 화면에서 다시 시작해주세요.
        </p>
        <button onClick={() => navigate("/")}>CASE 선택으로</button>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="card">
        <span className="badge">CASE #{briefing.case_id}</span>
        <h1 style={{ marginTop: 10 }}>[{briefing.domain}] {briefing.title}</h1>

        <p style={{ marginTop: 16 }}>{briefing.scenario.property.location}</p>
        <p className="muted">{briefing.scenario.property.price_description}</p>

        {briefing.scenario.broker_line && (
          <CharacterSpeech speaker={briefing.scenario.speaker_label} text={briefing.scenario.broker_line} />
        )}

        <h3 style={{ marginTop: 24 }}>목표</h3>
        <p>{briefing.scenario.goal}</p>

        <PlayGuide />

        <div className="hud" style={{ marginTop: 20 }}>
          <span>조사 포인트: {briefing.initial_points}P</span>
          {briefing.time_limit_seconds != null && (
            <span>제한시간: {Math.floor(briefing.time_limit_seconds / 60)}분</span>
          )}
        </div>

        <button
          className="primary"
          style={{ marginTop: 12 }}
          onClick={() => navigate(`/session/${sessionId}/investigate`)}
        >
          조사 시작
        </button>
      </div>
    </div>
  );
}
