import { useState } from "react";
import { Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { startMatch } from "../api/hostApi";
import { ApiError, PUBLIC_BASE } from "../api/client";
import { useHostSocket } from "../hooks/useHostSocket";
import QRCode from "../components/QRCode";
import TeamColumn from "../components/TeamColumn";
import { getHostToken } from "./HostLogin";

export default function HostLobby() {
  const { id = "" } = useParams();
  const token = getHostToken() ?? "";
  const nav = useNavigate();
  // joinUrl comes from the backend create response (server PUBLIC_BASE_URL); GET has none, so a reload derives it from VITE_PUBLIC_BASE.
  const joinUrl = (useLocation().state as { joinUrl?: string } | null)?.joinUrl ?? `${PUBLIC_BASE}/j/${id}`;
  const { snapshot, status, terminal, authError } = useHostSocket(id, token);
  const [err, setErr] = useState("");

  if (!token || authError) return <Navigate to="/host/login" replace />;
  if (status === "RUNNING") return <Navigate to={`/host/match/${id}`} replace />;
  if (status === "FINISHED") return <Navigate to={`/host/results/${id}`} replace />;
  if (terminal) return <Navigate to="/host/create" replace />;

  const roster = snapshot?.roster ?? { inter: [], gremio: [] };
  const total = roster.inter.length + roster.gremio.length;

  async function start() {
    try {
      await startMatch(token, id);
      nav(`/host/match/${id}`);
    } catch (x) {
      if (x instanceof ApiError && x.status === 401) return void nav("/host/login", { replace: true });
      setErr(x instanceof ApiError ? x.message : "Erro inesperado. Tente novamente.");
    }
  }

  return (
    <main className="host-page lobby">
      <h1>Escaneie para entrar</h1>
      <QRCode url={joinUrl} />
      <p className="join-url">{joinUrl}</p>
      <div className="lobby-teams">
        <TeamColumn team="inter" players={roster.inter} />
        <TeamColumn team="gremio" players={roster.gremio} />
      </div>
      {err && <p role="alert">{err}</p>}
      <button className="join-submit start-btn" onClick={start} disabled={!snapshot || total === 0}>
        Iniciar partida
      </button>
    </main>
  );
}
