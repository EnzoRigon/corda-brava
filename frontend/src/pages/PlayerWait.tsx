import { useParams } from "react-router-dom";
import { Mascot } from "../components/Mascot";
import { PixelPanel } from "../components/PixelPanel";
import { useMePolling } from "../hooks/useMePolling";

export default function PlayerWait() {
  const { id = "" } = useParams();
  const { session } = useMePolling(id, "wait");
  return (
    <main className="player-page">
      {session && <Mascot team={session.team} state="idle" size={160} />}
      <PixelPanel><h1>Aguardando o host iniciar</h1></PixelPanel>
    </main>
  );
}
