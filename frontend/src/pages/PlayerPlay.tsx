import { useParams } from "react-router-dom";
import { Mascot } from "../components/Mascot";
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
      <Mascot team={session.team} state="straining" size={128} />
      <p>Puxadas: {displayCount}</p>
      <PullButton onPull={tap} color={session.team === "inter" ? "var(--inter)" : "var(--gremio)"} />
    </main>
  );
}
