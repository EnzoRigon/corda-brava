import { useCountdown } from "../hooks/useCountdown";

export default function Timer({ remainingS, running, urgent = false }: { remainingS: number; running: boolean; urgent?: boolean }) {
  const s = Math.ceil(useCountdown(remainingS, running));
  return (
    <div className={`match-timer${urgent ? " urgent" : ""}`} aria-label="Tempo restante">
      {Math.floor(s / 60)}:{String(s % 60).padStart(2, "0")}
    </div>
  );
}
