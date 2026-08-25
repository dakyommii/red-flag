import type { EvidenceEntry } from "../api/types";

interface Props {
  evidenceBoard: EvidenceEntry[];
  selectedPattern: string | null;
  onSelect: (pattern: string) => void;
}

export default function EvidenceBoard({ evidenceBoard, selectedPattern, onSelect }: Props) {
  return (
    <div className="card">
      <h3>Evidence Board</h3>
      {evidenceBoard.length === 0 && (
        <p className="muted">아직 등록된 증거가 없습니다. 문서를 조사해 증거를 찾아보세요.</p>
      )}
      <div>
        {evidenceBoard.map((e) => (
          <span
            key={e.evidence_id}
            className={`evidence-chip${selectedPattern === e.pattern ? " selected" : ""}`}
            onClick={() => onSelect(e.pattern)}
            title={e.description}
          >
            {e.evidence_id} {e.pattern}
          </span>
        ))}
      </div>
    </div>
  );
}
