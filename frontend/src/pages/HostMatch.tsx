import { Navigate, useParams } from "react-router-dom";
import { useHostSocket } from "../hooks/useHostSocket";
import { Crest } from "../components/Crest";
import RopeScene from "../components/RopeScene";
import Timer from "../components/Timer";
import { getHostToken } from "./HostLogin";

export default function HostMatch() {
  const { id = "" } = useParams();
  const token = getHostToken() ?? "";
  const { snapshot, lastTick, ended, terminal, authError } = useHostSocket(id, token);

  if (!token || authError) return <Navigate to="/host/login" replace />;
  // Analytics ride along in router state so Results needs no extra fetch.
  if (ended) return <Navigate to={`/host/results/${id}`} replace state={ended} />;
  if (terminal) return <Navigate to={terminal.type === "reset" ? `/host/lobby/${terminal.newMatchId}` : "/host/create"} replace />;
  if (!snapshot) return <main className="host-page"><p>Conectando…</p></main>;
  if (snapshot.status === "LOBBY") return <Navigate to={`/host/lobby/${id}`} replace />;
  if (snapshot.status === "FINISHED") return <Navigate to={`/host/results/${id}`} replace />;

  const { scores, config } = snapshot;
  return (
    <main className="host-page match">
      <div className="match-hud">
        <span className="score inter"><Crest team="inter" /> {scores.inter.pulls}</span>
        <Timer remainingS={snapshot.remainingS} running />
        <span className="score gremio">{scores.gremio.pulls} <Crest team="gremio" /></span>
      </div>
      <RopeScene rope={snapshot.rope} target={config.ropeTarget} delta={lastTick?.delta} />
    </main>
  );
}
