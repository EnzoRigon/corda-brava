import { useEffect, useState } from "react";

/** Visual countdown: counts down from the latest server `remainingS` between ticks; clamped at 0. */
export function useCountdown(remainingS: number, running = true): number {
  const [now, setNow] = useState(0);
  const [base, setBase] = useState({ remainingS, at: Date.now() });
  if (base.remainingS !== remainingS) setBase({ remainingS, at: Date.now() });
  useEffect(() => {
    if (!running) return;
    const i = setInterval(() => setNow(Date.now()), 100);
    return () => clearInterval(i);
  }, [running]);
  return running && now > base.at ? Math.max(0, base.remainingS - (now - base.at) / 1000) : Math.max(0, remainingS);
}
