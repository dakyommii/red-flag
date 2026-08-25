import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { DocumentView, GameState } from "../api/types";
import ContradictionBoard from "../components/ContradictionBoard";
import DocumentViewer from "../components/DocumentViewer";
import EvidenceBoard from "../components/EvidenceBoard";
import InvestigationNotebook from "../components/InvestigationNotebook";
import NPCChat from "../components/NPCChat";

function formatSeconds(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export default function InvestigationPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [state, setState] = useState<GameState | null>(null);
  const [fatalError, setFatalError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [currentDocument, setCurrentDocument] = useState<DocumentView | null>(null);
  const [currentInvestigationId, setCurrentInvestigationId] = useState<string | null>(null);
  const [sendingChat, setSendingChat] = useState(false);
  const [newlyRevealedIds, setNewlyRevealedIds] = useState<string[]>([]);
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);
  const [selectedStatementId, setSelectedStatementId] = useState<string | null>(null);
  const [contradictionResult, setContradictionResult] = useState<{ found: boolean; message: string } | null>(
    null
  );
  const [submittingContradiction, setSubmittingContradiction] = useState(false);
  const [triedPairs, setTriedPairs] = useState<Set<string>>(new Set());

  async function refresh() {
    if (!sessionId) return;
    const s = await api.getState(sessionId);
    setState(s);
  }

  /** 서버가 내려준 사람이 읽을 수 있는 메시지만 추출한다. */
  function readableError(e: unknown): string {
    const raw = String(e);
    const match = raw.match(/"detail"\s*:\s*"([^"]+)"/);
    return match ? match[1] : "요청을 처리하지 못했습니다.";
  }

  /** 액션 실패는 화면을 갈아치우지 않고 안내 메시지로만 보여준다. */
  function showNotice(e: unknown) {
    setNotice(readableError(e));
  }

  useEffect(() => {
    refresh().catch((e) => setFatalError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  useEffect(() => {
    if (!state?.time_expired || state.completed) return;
    const timer = setTimeout(() => navigate(`/session/${sessionId}/decision`), 1800);
    return () => clearTimeout(timer);
  }, [state?.time_expired, state?.completed, sessionId, navigate]);

  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(null), 4000);
    return () => clearTimeout(timer);
  }, [notice]);

  async function handleInvestigate(investigationId: string) {
    if (!sessionId) return;
    try {
      const res = await api.investigate(sessionId, investigationId);
      setCurrentInvestigationId(investigationId);
      setCurrentDocument(res.document);
      await refresh();
    } catch (e) {
      showNotice(e);
    }
  }

  async function handleRegisterEvidence(blockId: string) {
    if (!sessionId || !currentDocument) return;
    try {
      await api.registerEvidence(sessionId, currentDocument.document_id, blockId);
      await refresh();
    } catch (e) {
      showNotice(e);
    }
  }

  async function handleSendChat(npcId: string, message: string) {
    if (!sessionId) return;
    setSendingChat(true);
    try {
      const res = await api.chat(sessionId, npcId, message);
      setNewlyRevealedIds(res.revealed_statements.map((s) => s.statement_id));
      await refresh();
    } catch (e) {
      showNotice(e);
    } finally {
      setSendingChat(false);
    }
  }

  function pairKey(statementId: string, pattern: string): string {
    return `${statementId}::${pattern}`;
  }

  async function handleSubmitContradiction() {
    if (!sessionId || !selectedPattern || !selectedStatementId) return;
    const key = pairKey(selectedStatementId, selectedPattern);
    setSubmittingContradiction(true);
    try {
      const res = await api.submitContradiction(sessionId, selectedStatementId, selectedPattern);
      if (res.found) {
        setContradictionResult({ found: true, message: res.explanation ?? "" });
        setSelectedPattern(null);
        setSelectedStatementId(null);
        await refresh();
      } else {
        setContradictionResult({ found: false, message: "이 조합은 실제 모순 관계가 아닙니다." });
        setTriedPairs((prev) => new Set(prev).add(key));
      }
    } catch (e) {
      showNotice(e);
    } finally {
      setSubmittingContradiction(false);
    }
  }

  function handleClearContradictionSelection() {
    setSelectedPattern(null);
    setSelectedStatementId(null);
    setContradictionResult(null);
  }

  if (fatalError) {
    return (
      <div className="page">
        <p style={{ color: "var(--danger)" }}>{fatalError}</p>
      </div>
    );
  }

  if (!state) {
    return (
      <div className="page">
        <p className="muted">불러오는 중...</p>
      </div>
    );
  }

  const npc = state.npcs[0];
  const npcHistory = npc ? state.chat_history[npc.npc_id] ?? [] : [];
  const npcStatements = npc ? state.statements.filter((s) => s.npc_id === npc.npc_id) : [];

  const hasEvidence = state.evidence_board.length > 0;
  const hasChatted = state.statements.length > 0;
  const hasContradiction = state.contradictions.length > 0;

  return (
    <div className="page">
      <div className="hud">
        <div className="hud-stat">
          <span className="hud-stat-label">조사 포인트</span>
          <span className="hud-stat-value">{state.remaining_points}P</span>
        </div>

        {state.remaining_seconds != null && (
          <div className="hud-stat">
            <span className="hud-stat-label">남은 시간</span>
            <span
              className="hud-stat-value"
              style={{ color: state.time_expired ? "var(--danger)" : undefined }}
            >
              {formatSeconds(Math.max(state.remaining_seconds, 0))}
            </span>
          </div>
        )}

        <div className="hud-stat">
          <span className="hud-stat-label">확보 증거</span>
          <span className="hud-stat-value">{state.evidence_board.length}</span>
        </div>

        <div className="hud-stat">
          <span className="hud-stat-label">발견 모순</span>
          <span className="hud-stat-value">{state.contradictions.length}</span>
        </div>

        <button className="primary" onClick={() => navigate(`/session/${sessionId}/decision`)}>
          최종 판단으로
        </button>
      </div>

      {notice && (
        <div className="notice-banner" onClick={() => setNotice(null)}>
          {notice}
        </div>
      )}

      {state.time_expired && (
        <div className="card" style={{ borderColor: "var(--danger)", marginBottom: 16 }}>
          <p style={{ color: "var(--danger)", fontWeight: 600, margin: 0 }}>
            시간이 종료되었습니다. 잠시 후 최종 판단 화면으로 이동합니다.
          </p>
        </div>
      )}

      <div className="investigation-layout">
        <div>
          <InvestigationNotebook
            hasEvidence={hasEvidence}
            hasChatted={hasChatted}
            hasContradiction={hasContradiction}
          />

          <div className="card" style={{ marginTop: 16 }}>
            <h3>조사 메뉴</h3>
          <div className="menu-list">
            {state.investigations.map((inv) => (
              <button
                key={inv.investigation_id}
                className={`menu-item${currentInvestigationId === inv.investigation_id ? " active" : ""}`}
                disabled={!inv.unlocked || state.time_expired}
                onClick={() => handleInvestigate(inv.investigation_id)}
              >
                <span>{inv.unlocked ? inv.name : `🔒 ${inv.name}`}</span>
                <span className="muted" style={{ fontSize: 12 }}>
                  {inv.cost}P · {inv.time_cost}s {inv.completed ? "· 완료" : ""}
                </span>
              </button>
            ))}
          </div>
          </div>
        </div>

        <div>
          <DocumentViewer
            document={currentDocument}
            evidenceBoard={state.evidence_board}
            onRegisterEvidence={handleRegisterEvidence}
          />

          {npc && (
            <div style={{ marginTop: 16 }}>
              <NPCChat
                npc={npc}
                history={npcHistory}
                sending={sendingChat}
                onSend={(msg) => handleSendChat(npc.npc_id, msg)}
                statements={npcStatements}
                selectedStatementId={selectedStatementId}
                onSelectStatement={setSelectedStatementId}
                newlyRevealedIds={newlyRevealedIds}
              />
            </div>
          )}

          <div style={{ marginTop: 16 }}>
            <ContradictionBoard
              statements={state.statements}
              evidenceBoard={state.evidence_board}
              selectedStatementId={selectedStatementId}
              selectedPattern={selectedPattern}
              foundContradictions={state.contradictions}
              lastResult={contradictionResult}
              alreadyTried={
                !!selectedStatementId &&
                !!selectedPattern &&
                triedPairs.has(pairKey(selectedStatementId, selectedPattern))
              }
              submitting={submittingContradiction}
              onSubmit={handleSubmitContradiction}
              onClear={handleClearContradictionSelection}
            />
          </div>

          <div className="card" style={{ marginTop: 16 }}>
            <EvidenceBoard
              evidenceBoard={state.evidence_board}
              selectedPattern={selectedPattern}
              onSelect={setSelectedPattern}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
