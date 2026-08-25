import type { ContradictionFound, EvidenceEntry, StatementMenuItem } from "../api/types";

interface Props {
  statements: StatementMenuItem[];
  evidenceBoard: EvidenceEntry[];
  selectedStatementId: string | null;
  selectedPattern: string | null;
  foundContradictions: ContradictionFound[];
  lastResult: { found: boolean; message: string } | null;
  alreadyTried: boolean;
  submitting: boolean;
  onSubmit: () => void;
  onClear: () => void;
}

export default function ContradictionBoard({
  statements,
  evidenceBoard,
  selectedStatementId,
  selectedPattern,
  foundContradictions,
  lastResult,
  alreadyTried,
  submitting,
  onSubmit,
  onClear,
}: Props) {
  const statement = statements.find((s) => s.statement_id === selectedStatementId);
  const evidence = evidenceBoard.find((e) => e.pattern === selectedPattern);
  const canSubmit = !!statement && !!evidence && !submitting && !alreadyTried;

  return (
    <div className="card">
      <h3>모순 지적</h3>
      <p className="muted">
        대화로 확보한 NPC 발언 하나와 Evidence Board의 증거 하나를 선택한 뒤 연결하세요.
      </p>

      <div className="contradiction-link">
        <div className={`link-slot${statement ? " filled" : ""}`}>
          {statement
            ? `"${statement.text}"`
            : statements.length === 0
              ? "먼저 NPC와 대화해 발언을 확보하세요"
              : "NPC 발언을 선택하세요"}
        </div>
        <div className="link-arrow">↔</div>
        <div className={`link-slot${evidence ? " filled" : ""}`}>
          {evidence ? `${evidence.evidence_id} ${evidence.pattern}` : "Evidence를 선택하세요"}
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button className="primary" disabled={!canSubmit} onClick={onSubmit}>
          모순 제출
        </button>
        {(statement || evidence) && (
          <button onClick={onClear} disabled={submitting}>
            선택 해제
          </button>
        )}
      </div>

      {alreadyTried && statement && evidence && (
        <p className="muted" style={{ marginTop: 8 }}>
          이미 시도해본 조합입니다. 다른 조합을 선택해보세요.
        </p>
      )}

      {lastResult && (
        <p
          style={{
            marginTop: 8,
            color: lastResult.found ? "var(--safe)" : "var(--danger)",
            fontWeight: lastResult.found ? 600 : 400,
          }}
        >
          {lastResult.found ? "CONTRADICTION FOUND" : "모순 아님"} — {lastResult.message}
        </p>
      )}

      {foundContradictions.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ fontSize: 14 }}>발견한 모순 ({foundContradictions.length})</h3>
          {foundContradictions.map((c) => (
            <div key={c.contradiction_id} className="found-contradiction">
              <div className="contradiction-link small">
                <div className="link-slot filled">"{c.statement_text}"</div>
                <div className="link-arrow">↔</div>
                <div className="link-slot filled">{c.evidence_pattern}</div>
              </div>
              <p className="muted" style={{ marginTop: 4 }}>
                {c.explanation}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
