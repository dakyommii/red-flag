import type { DocumentView, EvidenceEntry } from "../api/types";

interface Props {
  document: DocumentView | null;
  evidenceBoard: EvidenceEntry[];
  onRegisterEvidence: (blockId: string) => void;
}

export default function DocumentViewer({ document, evidenceBoard, onRegisterEvidence }: Props) {
  if (!document) {
    return (
      <div className="card document-empty">
        <div className="document-empty-icon">📂</div>
        <h3>조사할 문서를 선택하세요</h3>
        <p className="muted">
          왼쪽 <strong>조사 메뉴</strong>에서 항목을 클릭하면 해당 문서가 여기에 열립니다.
        </p>
        <p className="muted" style={{ fontSize: 12 }}>
          조사에는 포인트가 소모되니, 무엇을 먼저 확인할지 신중히 고르세요.
        </p>
      </div>
    );
  }

  const registeredBlockIds = new Set(
    evidenceBoard
      .filter((e) => e.source_document_id === document.document_id)
      .map((e) => e.source_block_id)
  );

  return (
    <div className="card">
      <h3>{document.title}</h3>
      <p className="muted" style={{ marginBottom: 12 }}>
        수상한 부분을 클릭하면 증거로 등록할 수 있습니다.
      </p>
      {document.blocks.map((b) => (
        <div
          key={b.block_id}
          className={`block-item${registeredBlockIds.has(b.block_id) ? " registered" : ""}`}
          onClick={() => onRegisterEvidence(b.block_id)}
        >
          {b.text}
          {registeredBlockIds.has(b.block_id) && (
            <div className="badge safe" style={{ marginTop: 6 }}>
              증거 등록됨
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
