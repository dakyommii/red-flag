import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";

const OPTIONS: { decision: string; label: string; desc: string }[] = [
  {
    decision: "SAFE_TO_PROCEED",
    label: "계약 진행 가능",
    desc: "지금까지 확인한 정보로 볼 때 안전하다고 판단합니다.",
  },
  {
    decision: "NEED_MORE_VERIFICATION",
    label: "추가 확인/보류",
    desc: "확인되지 않은 위험 요소가 있어 오늘은 계약하지 않고 더 확인합니다.",
  },
  {
    decision: "STOP_CONTRACT",
    label: "계약 중단",
    desc: "위험 신호가 명확하여 계약을 중단합니다.",
  },
];

export default function FinalDecisionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(decision: string) {
    if (!sessionId || submitting) return;
    setSubmitting(true);
    try {
      await api.submitDecision(sessionId, decision);
      navigate(`/session/${sessionId}/report`);
    } catch (e) {
      setError(String(e));
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>최종 판단</h1>
      <p className="muted">지금까지 조사한 내용을 바탕으로 이 계약을 어떻게 하시겠습니까?</p>

      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}

      <div className="decision-options" style={{ marginTop: 20 }}>
        {OPTIONS.map((o) => (
          <div key={o.decision} className="card">
            <h3>{o.label}</h3>
            <p className="muted">{o.desc}</p>
            <button className="primary" disabled={submitting} onClick={() => submit(o.decision)}>
              선택
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
