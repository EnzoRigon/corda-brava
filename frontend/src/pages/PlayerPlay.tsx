import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Crest } from "../components/Crest";
import { Icon } from "../components/Icon";
import { PullButton } from "../components/PullButton";
import { useMePolling } from "../hooks/useMePolling";
import { usePullBuffer } from "../hooks/usePullBuffer";
import { comboLevel, decayCombo, tapCombo } from "../lib/combo";
import { loadPulls, savePulls } from "../lib/localPulls";

export default function PlayerPlay() {
  const { id = "" } = useParams();
  const { session, me } = useMePolling(id, "play");
  const { displayCount, tap } = usePullBuffer({
    matchId: id,
    playerId: session?.playerId ?? "",
    playerToken: session?.playerToken ?? "",
    flushIntervalMs: 500,
    enabled: me?.screen === "play",
  });
  const [base] = useState(() => loadPulls(id)); // taps from before a reload
  const total = base + displayCount;
  useEffect(() => {
    if (displayCount > 0) savePulls(id, total);
  }, [id, total, displayCount]);

  const [meter, setMeter] = useState(0);
  const meterRef = useRef(0);
  const onTap = useCallback(() => {
    tap();
    meterRef.current = tapCombo(meterRef.current);
    setMeter(meterRef.current);
  }, [tap]);
  useEffect(() => {
    const t = setInterval(() => {
      if (meterRef.current <= 0) return;
      meterRef.current = decayCombo(meterRef.current, 100);
      setMeter(meterRef.current);
    }, 100);
    return () => clearInterval(t);
  }, []);

  if (!session) return null;
  const level = comboLevel(meter);
  return (
    <main className={`player-page play play-${session.team}`}>
      <div key={displayCount} className="play-crest"><Crest team={session.team} size={160} /></div>
      <div className="tap-count">
        <span className="sr-only">Puxadas: </span>
        {total}
      </div>
      <div className="combo" data-active={level > 0}>
        <div className="combo-bar"><i style={{ width: `${meter * 100}%` }} /></div>
        <div className="combo-label">
          {level > 0 && (
            <>
              <Icon name="lightning" size={24} />
              COMBO x{level}
            </>
          )}
        </div>
      </div>
      <PullButton onPull={onTap} color={session.team === "inter" ? "var(--inter)" : "var(--gremio)"} />
    </main>
  );
}
