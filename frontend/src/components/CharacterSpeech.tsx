import { characterAvatar } from "../lib/avatar";

interface Props {
  speaker: string;
  text: string;
  role?: string;
}

export default function CharacterSpeech({ speaker, text, role }: Props) {
  return (
    <div className="character-speech">
      <div className="character-avatar">{characterAvatar(speaker, role)}</div>
      <div className="speech-bubble-wrap">
        <div className="speech-bubble-name">{speaker}</div>
        <div className="speech-bubble">{text}</div>
      </div>
    </div>
  );
}
