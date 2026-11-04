import { useParams } from "react-router-dom";
import { Crest } from "../components/Crest";
import { PixelPanel } from "../components/PixelPanel";
import { PullButton } from "../components/PullButton";
import { useMePolling } from "../hooks/useMePolling";
import { usePullBuffer } from "../hooks/usePullBuffer";

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
  if (!session) return null;
  return (
    <main className="player-page play">
      <div key={displayCount} className="play-crest"><Crest team={session.team} size={192} /></div>
      <PixelPanel><p>Puxadas: {displayCount}</p></PixelPanel>
      <PullButton onPull={tap} color={session.team === "inter" ? "var(--inter)" : "var(--gremio)"} />
    </main>
  );
}
