import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { ReportResponse } from "../api/types";

const DECISION_LABEL: Record<string, string> = {
  SAFE_TO_PROCEED: "계약 진행 가능",
  NEED_MORE_VERIFICATION: "추가 확인 필요",
  STOP_CONTRACT: "계약 중단",
};

function ScoreRow({ label, value, max }: { label: string; value: number; max: number }) {
  const ratio = max > 0 ? value / max : 0;
  const tone = ratio >= 0.8 ? "high" : ratio >= 0.4 ? "mid" : "low";
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
        <span>{label}</span>
        <span className="muted">
          {value} / {max}
        </span>
      </div>
      <div className={`score-bar ${tone}`}>
        <div style={{ width: `${ratio * 100}%` }} />
      </div>
    </div>
  );
}

function formatTs(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

const KIND_ICON: Record<string, string> = {
  investigate: "🔍",
  evidence: "📌",
  chat: "💬",
  statement: "🗣️",
  contradiction: "⚡",
  decision: "⚖️",
};

export default function CaseReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api
      .getReport(sessionId)
      .then(setReport)
      .catch((e) => setError(String(e)));
  }, [sessionId]);

  if (error) {
    return (
      <div className="page">
        <p style={{ color: "var(--danger)" }}>{error}</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="page">
        <p className="muted">리포트를 생성하는 중...</p>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>CASE REPORT</h1>
      <p className="muted">{report.title}</p>
      {report.time_expired && (
        <p style={{ color: "var(--danger)" }}>⏱ 제한시간 내에 조사를 마치지 못하고 시간 종료로 판단했습니다.</p>
      )}

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2>{DECISION_LABEL[report.decision] ?? report.decision}</h2>
            <p className="muted">총점 {report.score.total} / 100</p>
          </div>
          <div className={`verdict-stamp grade-${report.grade}`}>{report.grade}</div>
        </div>

        <ScoreRow label="핵심 위험 신호 발견" value={report.score.risk_discovery} max={40} />
        <ScoreRow label="중요 증거 확보" value={report.score.evidence_quality} max={20} />
        <ScoreRow label="모순 발견" value={report.score.contradiction} max={15} />
        <ScoreRow label="효율적 조사" value={report.score.efficiency} max={10} />
        <ScoreRow label="최종 판단" value={report.score.final_decision} max={15} />
      </div>

      {report.case_explanation && (
        <div className="card">
          <h3>이 CASE는 어떤 위험이었나</h3>
          <p style={{ lineHeight: 1.6 }}>{report.case_explanation}</p>
        </div>
      )}

      <div className="card">
        <h3>발견한 위험 신호</h3>
        {report.found_risk_details.length === 0 && <p className="muted">없음</p>}
        {report.found_risk_details.map((r) => (
          <div key={r.pattern} className="risk-item">
            <div className="risk-item-title" style={{ color: "var(--safe)" }}>
              ✓ {r.pattern}
            </div>
            {r.description && <div className="risk-item-desc">{r.description}</div>}
          </div>
        ))}

        <h3 style={{ marginTop: 18 }}>놓친 위험 신호</h3>
        {report.missed_risk_details.length === 0 && <p className="muted">없음</p>}
        {report.missed_risk_details.map((r) => (
          <div key={r.pattern} className="risk-item">
            <div className="risk-item-title" style={{ color: "var(--danger)" }}>
              ✕ {r.pattern}
            </div>
            {r.description && <div className="risk-item-desc">{r.description}</div>}
          </div>
        ))}
      </div>

      <div className="card">
        <h3>행동 Timeline</h3>
        <div className="flow-timeline">
          {report.timeline.map((t, i) => (
            <div key={i} className="flow-step">
              <div className={`flow-node kind-${t.kind}`}>{KIND_ICON[t.kind] ?? "•"}</div>
              <div className="flow-content">
                <div className="flow-ts">{formatTs(t.timestamp)}</div>
                <div className="flow-label">{t.label}</div>
                {t.description && (
                  <div className="flow-desc">
                    {t.kind === "decision" ? DECISION_LABEL[t.description] ?? t.description : t.description}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>코치 코멘트</h3>
        {report.comment
          .split("\n")
          .filter((line) => line.trim())
          .map((line, i) => {
            const match = line.match(/^(잘한 점|아쉬운 점)\s*:\s*(.*)$/);
            return (
              <p key={i} style={{ marginTop: i === 0 ? 0 : 10, lineHeight: 1.6 }}>
                {match ? (
                  <>
                    <strong style={{ color: match[1] === "잘한 점" ? "var(--safe)" : "var(--warn)" }}>
                      {match[1]}
                    </strong>
                    {": " + match[2]}
                  </>
                ) : (
                  line
                )}
              </p>
            );
          })}
      </div>

      {report.source_note && (
        <div className="card">
          <p className="muted">{report.source_note}</p>
          {report.official_sources.map((s) => (
            <p key={s} className="muted">
              출처: {s}
            </p>
          ))}
        </div>
      )}

      <button className="primary" style={{ marginTop: 20 }} onClick={() => navigate("/")}>
        다른 CASE 하기
      </button>
    </div>
  );
}
