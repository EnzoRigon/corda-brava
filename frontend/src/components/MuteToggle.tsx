import { useSfx } from "../hooks/useSfx";
import { Icon } from "./Icon";

export function MuteToggle() {
  const { muted, toggleMute } = useSfx();
  return (
    <button type="button" className="mute-toggle" aria-label="Silenciar sons" aria-pressed={muted} onClick={toggleMute}>
      <Icon name={muted ? "speaker-off" : "speaker-on"} size={32} />
    </button>
  );
}
