import { useCountdown } from "../hooks/useCountdown";

export default function Timer({ remainingS, running }: { remainingS: number; running: boolean }) {
  const s = Math.ceil(useCountdown(remainingS, running));
  return (
    <div className="match-timer" aria-label="Tempo restante">
      {Math.floor(s / 60)}:{String(s % 60).padStart(2, "0")}
    </div>
  );
}
