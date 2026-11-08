import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { Confetti } from "../components/Confetti";
import { Mascot, type MascotState } from "../components/Mascot";
import { useMePolling } from "../hooks/useMePolling";
import { loadPulls } from "../lib/localPulls";
import { play } from "../lib/sfx";

export default function PlayerEnd() {
  const { id = "" } = useParams();
  const { session, me } = useMePolling(id, "end");
  const result = me?.result;
  const won = !!session && result === session.team.toUpperCase();
  const draw = result === "DRAW";
  useEffect(() => {
    if (won) play("win");
    else if (draw) play("draw");
  }, [won, draw]);
  if (!session) return null;
  const state: MascotState = !result || draw ? "idle" : won ? "happy" : "crying";
  const kind = !me ? "" : !result ? "cancel" : draw ? "draw" : won ? "win" : "lose";
  const title = { "": "", cancel: "Partida cancelada", draw: "EMPATE!", win: "VITÓRIA!", lose: "DERROTA…" }[kind];
  const pulls = loadPulls(id);
  return (
    <main className={`player-page end-page end-${kind}`}>
      {kind === "win" && <Confetti />}
      {kind === "lose" && <div className="end-dim" aria-hidden="true" />}
      <Mascot team={session.team} state={state} size={192} />
      <h1 className={`end-banner end-banner-${kind === "win" ? session.team : "plain"}`}>{title}</h1>
      {pulls > 0 && kind !== "cancel" && <p className="end-pulls">Você puxou {pulls} {pulls === 1 ? "vez" : "vezes"}!</p>}
      <p>Obrigado por jogar!</p>
    </main>
  );
}
