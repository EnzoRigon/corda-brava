import { useSyncExternalStore } from "react";
import { isMuted, play, setMuted, subscribe } from "../lib/sfx";

export function useSfx() {
  const muted = useSyncExternalStore(subscribe, isMuted);
  return { muted, play, toggleMute: () => setMuted(!muted) };
}
