export interface CasePublicSummary {
  case_id: string;
  title: string;
  domain: string;
  difficulty: number;
}

export interface ScenarioProperty {
  location: string;
  price_description: string;
  details: Record<string, unknown>;
}

export interface Scenario {
  description: string;
  property: ScenarioProperty;
  broker_line: string;
  speaker_label: string;
  goal: string;
}

export interface StartResponse {
  session_id: string;
  case_id: string;
  title: string;
  difficulty: number;
  domain: string;
  scenario: Scenario;
  initial_points: number;
  time_limit_seconds: number | null;
}

export interface InvestigationMenuItem {
  investigation_id: string;
  name: string;
  cost: number;
  time_cost: number;
  unlocked: boolean;
  completed: boolean;
}

export interface NpcMenuItem {
  npc_id: string;
  role: string;
  display_name: string;
  suggested_questions: string[];
  total_statements: number;
}

export interface StatementMenuItem {
  statement_id: string;
  npc_id: string;
  text: string;
}

export interface EvidenceEntry {
  evidence_id: string;
  pattern: string;
  description: string;
  source_document_id: string;
  source_block_id: string;
}

export interface ChatMessage {
  role: "player" | "npc";
  content: string;
}

export interface GameState {
  session_id: string;
  case_id: string;
  remaining_points: number;
  remaining_seconds: number | null;
  time_expired: boolean;
  completed: boolean;
  final_decision: string | null;
  final_score: number | null;
  investigations: InvestigationMenuItem[];
  npcs: NpcMenuItem[];
  statements: StatementMenuItem[];
  evidence_board: EvidenceEntry[];
  contradictions_found: string[];
  contradictions: ContradictionFound[];
  chat_history: Record<string, ChatMessage[]>;
}

export interface DocumentBlockView {
  block_id: string;
  text: string;
}

export interface DocumentView {
  document_id: string;
  title: string;
  blocks: DocumentBlockView[];
}

export interface InvestigateResponse {
  investigation_id: string;
  remaining_points: number;
  remaining_seconds: number | null;
  time_expired: boolean;
  document: DocumentView | null;
}

export interface EvidenceResponse {
  evidence: EvidenceEntry;
  already_registered: boolean;
}

export interface ChatResponse {
  npc_id: string;
  reply: string;
  revealed_statements: StatementMenuItem[];
}

export interface ContradictionResponse {
  found: boolean;
  contradiction_id?: string;
  explanation?: string;
}

export interface ContradictionFound {
  contradiction_id: string;
  statement_id: string;
  statement_text: string;
  evidence_pattern: string;
  explanation: string;
}

export interface ScoreBreakdown {
  risk_discovery: number;
  evidence_quality: number;
  contradiction: number;
  efficiency: number;
  final_decision: number;
  total: number;
  found_risks: string[];
  missed_risks: string[];
}

export interface DecisionResponse {
  decision: string;
  score: ScoreBreakdown;
  grade: string;
  time_expired: boolean;
}

export interface TimelineEvent {
  timestamp: number;
  kind: "investigate" | "evidence" | "chat" | "statement" | "contradiction" | "decision";
  label: string;
  description: string | null;
}

export interface RiskDetail {
  pattern: string;
  description: string;
}

export interface ReportResponse {
  case_id: string;
  title: string;
  decision: string;
  grade: string;
  score: ScoreBreakdown;
  case_explanation: string;
  found_risk_details: RiskDetail[];
  missed_risk_details: RiskDetail[];
  timeline: TimelineEvent[];
  comment: string;
  source_note: string | null;
  official_sources: string[];
  time_expired: boolean;
}
