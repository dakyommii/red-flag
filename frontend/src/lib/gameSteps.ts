export const GAME_STEPS = [
  {
    key: "evidence" as const,
    icon: "🔍",
    label: "증거를 찾아보세요",
    hint: "아래 조사 메뉴에서 항목을 선택하면 문서가 열립니다. 그 안의 수상한 부분을 클릭하세요",
  },
  {
    key: "chat" as const,
    icon: "💬",
    label: "NPC의 발언을 확보하세요",
    hint: "질문을 던져 상대의 주장을 끌어내야 모순을 지적할 수 있습니다",
  },
  {
    key: "contradiction" as const,
    icon: "⚡",
    label: "모순을 지적해보세요",
    hint: "NPC 발언과 Evidence를 연결해 모순을 찾아보세요",
  },
  {
    key: "decision" as const,
    icon: "⚖️",
    label: "최종 판단을 내리세요",
    hint: "증거와 모순이 충분히 모였다면 계약을 진행할지 결정하세요",
  },
];
