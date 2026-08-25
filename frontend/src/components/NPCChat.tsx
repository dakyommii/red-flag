import { useRef, useState } from "react";
import type { ChatMessage, NpcMenuItem, StatementMenuItem } from "../api/types";
import { characterAvatar } from "../lib/avatar";

interface Props {
  npc: NpcMenuItem;
  history: ChatMessage[];
  sending: boolean;
  onSend: (message: string) => void;
  statements: StatementMenuItem[];
  selectedStatementId: string | null;
  onSelectStatement: (statementId: string) => void;
  newlyRevealedIds: string[];
}

export default function NPCChat({
  npc,
  history,
  sending,
  onSend,
  statements,
  selectedStatementId,
  onSelectStatement,
  newlyRevealedIds,
}: Props) {
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  function submit() {
    const text = draft.trim();
    if (!text || sending) return;
    onSend(text);
    setDraft("");
  }

  const avatar = characterAvatar(npc.display_name, npc.role);

  return (
    <div className="card">
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div className="character-avatar" style={{ width: 32, height: 32, fontSize: 16 }}>
          {avatar}
        </div>
        <h3 style={{ margin: 0 }}>{npc.display_name}</h3>
      </div>
      <div className="chat-log">
        {history.length === 0 && (
          <p className="muted">아직 대화가 없습니다. 궁금한 점을 자유롭게 물어보세요.</p>
        )}
        {history.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role}`}>
            {m.role === "npc" && <span style={{ marginRight: 6 }}>{avatar}</span>}
            {m.content}
          </div>
        ))}
        {sending && (
          <div className="chat-bubble npc muted">
            <span style={{ marginRight: 6 }}>{avatar}</span>...
          </div>
        )}
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <input
          ref={inputRef}
          type="text"
          value={draft}
          placeholder="질문을 입력하세요"
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button className="primary" onClick={submit} disabled={sending}>
          전송
        </button>
      </div>

      {npc.suggested_questions.length > 0 && (
        <div className="suggested-questions">
          <span className="muted" style={{ fontSize: 12 }}>이렇게 물어볼 수 있어요</span>
          <div className="suggested-question-list">
            {npc.suggested_questions.map((q) => (
              <button
                key={q}
                type="button"
                className="suggested-question"
                disabled={sending}
                onClick={() => {
                  setDraft(q);
                  inputRef.current?.focus();
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <h3 style={{ marginTop: 20 }}>
        확보한 발언{" "}
        <span className="muted" style={{ fontSize: 13, fontWeight: 400 }}>
          {statements.length} / {npc.total_statements}
        </span>
      </h3>

      {statements.length === 0 ? (
        <p className="muted" style={{ fontSize: 13 }}>
          아직 확보한 발언이 없습니다. 질문을 던져 이 인물의 주장을 끌어내세요.
        </p>
      ) : (
        <div className="statement-list">
          {statements.map((s) => (
            <span
              key={s.statement_id}
              className={`evidence-chip${selectedStatementId === s.statement_id ? " selected" : ""}${
                newlyRevealedIds.includes(s.statement_id) ? " just-revealed" : ""
              }`}
              onClick={() => onSelectStatement(s.statement_id)}
            >
              "{s.text}"
            </span>
          ))}
        </div>
      )}

      {statements.length > 0 && statements.length < npc.total_statements && (
        <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>
          다른 주제로도 질문해보세요. 아직 끌어내지 못한 주장이 남아 있습니다.
        </p>
      )}
    </div>
  );
}
