import { GAME_STEPS } from "../lib/gameSteps";

interface Props {
  hasEvidence: boolean;
  hasChatted: boolean;
  hasContradiction: boolean;
}

const CHECKABLE_STEPS = GAME_STEPS.filter((s) => s.key !== "decision");

export default function InvestigationNotebook({ hasEvidence, hasChatted, hasContradiction }: Props) {
  const done: Record<string, boolean> = {
    evidence: hasEvidence,
    chat: hasChatted,
    contradiction: hasContradiction,
  };
  const allDone = hasEvidence && hasChatted && hasContradiction;

  return (
    <div className="card notebook">
      <h3>🔍 조사 수첩</h3>
      <div className="notebook-steps">
        {CHECKABLE_STEPS.map((step, i) => {
          const isDone = done[step.key];
          return (
            <div key={step.key} className={`notebook-step${isDone ? " done" : ""}`}>
              <span className="notebook-checkbox">{isDone ? "✓" : i + 1}</span>
              <div>
                <div className="notebook-label">{step.label}</div>
                {!isDone && <div className="notebook-hint muted">{step.hint}</div>}
              </div>
            </div>
          );
        })}
        <div className={`notebook-step notebook-final${allDone ? " ready" : ""}`}>
          <span className="notebook-checkbox">{allDone ? "🚩" : CHECKABLE_STEPS.length + 1}</span>
          <div className="notebook-label">준비되면 최종 판단으로 이동하세요</div>
        </div>
      </div>
    </div>
  );
}
