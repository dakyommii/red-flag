import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { CasePublicSummary } from "../api/types";

const STARS = ["☆", "★"];

function difficultyStars(n: number): string {
  return Array.from({ length: 5 }, (_, i) => (i < n ? STARS[1] : STARS[0])).join("");
}

export default function CaseSelect() {
  const [cases, setCases] = useState<CasePublicSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .listCases()
      .then(setCases)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  async function handleStart(caseId: string) {
    try {
      const start = await api.startCase(caseId);
      navigate(`/session/${start.session_id}/briefing`, { state: start });
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div className="page">
      <h1>부동산 사기 추리·검증 게임</h1>
      <p className="muted">
        전세·분양·청약 계약 상황을 직접 조사하고, 위험 신호와 모순을 찾아 스스로 판단해보세요.
      </p>

      {loading && <p className="muted">CASE 목록을 불러오는 중...</p>}
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}

      <div className="grid-cases" style={{ marginTop: 20 }}>
        {cases.map((c) => (
          <div key={c.case_id} className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="badge">{c.domain}</span>
              <span className="muted" style={{ fontSize: 11 }}>
                CASE #{c.case_id}
              </span>
            </div>
            <h3>{c.title}</h3>
            <p className="difficulty">{difficultyStars(c.difficulty)}</p>
            <button className="primary" style={{ marginTop: 4 }} onClick={() => handleStart(c.case_id)}>
              CASE 시작
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
