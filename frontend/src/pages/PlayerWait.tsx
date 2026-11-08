import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getPublic } from "../api/playerApi";
import { Crest } from "../components/Crest";
import { Icon } from "../components/Icon";
import { Mascot } from "../components/Mascot";
import { PixelPanel } from "../components/PixelPanel";
import { useMePolling } from "../hooks/useMePolling";

export default function PlayerWait() {
  const { id = "" } = useParams();
  const { session } = useMePolling(id, "wait");
  const [mates, setMates] = useState<number | null>(null);
  const team = session?.team;
  useEffect(() => {
    if (!team) return;
    let alive = true;
    const poll = () =>
      getPublic(id)
        .then((p) => alive && setMates(p.counts[team]))
        .catch(() => {}); // the count is decoration; keep the last one
    poll();
    const t = setInterval(poll, 2000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [id, team]);
  return (
    <main className="player-page wait-page">
      {session && (
        <div className="wait-hero">
          <Crest team={session.team} size={128} className="anim-bob" />
          <Mascot team={session.team} state="idle" size={128} />
        </div>
      )}
      <PixelPanel tone={team === "gremio" ? "blue" : "red"} className="wait-panel">
        <h1>
          Aguardando o host iniciar
          <span className="dots" aria-hidden="true">
            <i>.</i>
            <i>.</i>
            <i>.</i>
          </span>
        </h1>
        {mates !== null && (
          <p className="mates">
            {Array.from({ length: Math.min(mates, 8) }, (_, i) => (
              <Icon key={i} name="player" size={24} />
            ))}
            <span>{mates === 1 ? "1 jogador no seu time" : `${mates} jogadores no seu time`}</span>
          </p>
        )}
      </PixelPanel>
    </main>
  );
}
