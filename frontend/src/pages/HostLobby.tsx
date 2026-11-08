import { useEffect, useRef, useState } from "react";
import { Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { startMatch } from "../api/hostApi";
import { ApiError, PUBLIC_BASE } from "../api/client";
import { useHostSocket } from "../hooks/useHostSocket";
import QRCode from "../components/QRCode";
import TeamColumn from "../components/TeamColumn";
import { Logo } from "../components/Logo";
import { PixelButton } from "../components/PixelButton";
import { PixelPanel } from "../components/PixelPanel";
import { play } from "../lib/sfx";
import { getHostToken } from "./HostLogin";
import "../theme/host.css";

const COUNT_FROM = 3;
const TICK_MS = 700;

export default function HostLobby() {
  const { id = "" } = useParams();
  const token = getHostToken() ?? "";
  const nav = useNavigate();
  // joinUrl: snapshot (server PUBLIC_BASE_URL) > create-response router state > VITE_PUBLIC_BASE fallback.
  const routed = (useLocation().state as { joinUrl?: string } | null)?.joinUrl;
  const { snapshot, status, terminal, authError } = useHostSocket(id, token);
  const joinUrl = snapshot?.joinUrl ?? routed ?? `${PUBLIC_BASE}/j/${id}`;
  const [err, setErr] = useState("");
  const [count, setCount] = useState<number | null>(null);
  const total = (snapshot?.roster.inter.length ?? 0) + (snapshot?.roster.gremio.length ?? 0);
  const seen = useRef<number | null>(null);
  useEffect(() => {
    if (!snapshot) return;
    if (seen.current !== null && total > seen.current) play("join");
    seen.current = total;
  }, [snapshot, total]);

  if (!token || authError) return <Navigate to="/host/login" replace />;
  if (status === "RUNNING") return <Navigate to={`/host/match/${id}`} replace />;
  if (status === "FINISHED") return <Navigate to={`/host/results/${id}`} replace />;
  if (terminal) return <Navigate to={terminal.type === "reset" ? `/host/lobby/${terminal.newMatchId}` : "/host/create"} replace />;

  const roster = snapshot?.roster ?? { inter: [], gremio: [] };

  // Cosmetic 3-2-1 first, then the real start call, so the server timer never loses play time.
  async function start() {
    setErr("");
    for (let n = COUNT_FROM; n >= 1; n--) {
      setCount(n);
      play("countdown");
      await new Promise((r) => setTimeout(r, TICK_MS));
    }
    try {
      await startMatch(token, id);
      nav(`/host/match/${id}`);
    } catch (x) {
      setCount(null);
      if (x instanceof ApiError && x.status === 401) return void nav("/host/login", { replace: true });
      setErr(x instanceof ApiError ? x.message : "Erro inesperado. Tente novamente.");
    }
  }

  const oneEmpty = total > 0 && (roster.inter.length === 0 || roster.gremio.length === 0);
  return (
    <main className="host-page lobby">
      <Logo scale={2} small />
      <div className="lobby-grid">
        <TeamColumn team="inter" players={roster.inter} />
        <PixelPanel className="qr-panel">
          <p className="qr-caption anim-blink">APONTE A CÂMERA</p>
          <QRCode url={joinUrl} />
          <p className="join-url">{joinUrl}</p>
        </PixelPanel>
        <TeamColumn team="gremio" players={roster.gremio} />
      </div>
      {oneEmpty && <p className="px-toast warn">Um time está sem jogadores</p>}
      {err && <p role="alert" className="px-toast">{err}</p>}
      <PixelButton className="start-btn pulse" onClick={start} disabled={!snapshot || total === 0 || count !== null}>
        Iniciar partida
      </PixelButton>
      {total === 0 && <small className="start-hint">Aguardando jogadores…</small>}
      {count !== null && <div className="countdown-overlay" aria-live="assertive"><span key={count} className="countdown-n">{count}</span></div>}
    </main>
  );
}
