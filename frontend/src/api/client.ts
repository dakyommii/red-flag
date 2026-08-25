import type {
  CasePublicSummary,
  ChatResponse,
  ContradictionResponse,
  DecisionResponse,
  EvidenceResponse,
  GameState,
  InvestigateResponse,
  ReportResponse,
  StartResponse,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listCases: () => request<CasePublicSummary[]>("/cases"),

  startCase: (caseId: string) =>
    request<StartResponse>(`/cases/${caseId}/start`, { method: "POST" }),

  getState: (sessionId: string) => request<GameState>(`/game/${sessionId}`),

  investigate: (sessionId: string, investigationId: string) =>
    request<InvestigateResponse>(`/game/${sessionId}/investigate`, {
      method: "POST",
      body: JSON.stringify({ investigation_id: investigationId }),
    }),

  registerEvidence: (sessionId: string, documentId: string, blockId: string) =>
    request<EvidenceResponse>(`/game/${sessionId}/evidence`, {
      method: "POST",
      body: JSON.stringify({ document_id: documentId, block_id: blockId }),
    }),

  chat: (sessionId: string, npcId: string, message: string) =>
    request<ChatResponse>(`/game/${sessionId}/chat`, {
      method: "POST",
      body: JSON.stringify({ npc_id: npcId, message }),
    }),

  submitContradiction: (sessionId: string, statementId: string, evidencePattern: string) =>
    request<ContradictionResponse>(`/game/${sessionId}/contradiction`, {
      method: "POST",
      body: JSON.stringify({ statement_id: statementId, evidence_pattern: evidencePattern }),
    }),

  submitDecision: (sessionId: string, decision: string) =>
    request<DecisionResponse>(`/game/${sessionId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    }),

  getReport: (sessionId: string) => request<ReportResponse>(`/game/${sessionId}/report`),
};
