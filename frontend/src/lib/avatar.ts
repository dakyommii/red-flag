export function characterAvatar(speakerLabel: string, role?: string): string {
  const key = `${speakerLabel} ${role ?? ""}`;

  if (key.includes("중개사") || role === "real_estate_agent") return "🧑‍💼";
  if (key.includes("동생") || role === "sibling") return "🙋";
  if (key.includes("상담사") || role === "presale_agent") return "🏢";
  if (key.includes("문자") || key.includes("발신") || role === "unofficial_contact") return "📱";
  if (role === "unofficial_agent") return "☎️";

  return "👤";
}
