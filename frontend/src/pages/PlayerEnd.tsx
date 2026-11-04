import { useParams } from "react-router-dom";
import { Mascot, type MascotState } from "../components/Mascot";
import { useMePolling } from "../hooks/useMePolling";

export default function PlayerEnd() {
  const { id = "" } = useParams();
  const { session, me } = useMePolling(id, "end");
  if (!session) return null;
  const draw = me?.result === "DRAW";
  const won = me?.result === session.team.toUpperCase();
  const state: MascotState = !me?.result || draw ? "idle" : won ? "happy" : "crying";
  const title = !me ? "" : !me.result ? "Partida cancelada" : draw ? "Empate!" : won ? "Seu time venceu!" : "Seu time perdeu!";
  return (
    <main className="player-page">
      <Mascot team={session.team} state={state} size={160} />
      <h1>{title}</h1>
      <p>Obrigado por jogar!</p>
    </main>
  );
}
