import { GAME_STEPS } from "../lib/gameSteps";

export default function PlayGuide() {
  return (
    <div className="play-guide">
      <h3 style={{ fontSize: 14 }}>진행 방법</h3>
      <div className="play-guide-steps">
        {GAME_STEPS.map((step, i) => (
          <div className="play-guide-step" key={step.key}>
            <div className="play-guide-icon">{step.icon}</div>
            <div className="play-guide-label">{step.label}</div>
            {i < GAME_STEPS.length - 1 && <div className="play-guide-arrow">→</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
