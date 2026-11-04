import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { getAnalytics, resetMatch } from "../api/hostApi";
import { ApiError } from "../api/client";
import AnalyticsGrid from "../components/AnalyticsGrid";
import { Mascot, type MascotState } from "../components/Mascot";
import ResultBanner from "../components/ResultBanner";
import type { AnalyticsPayload, TeamId } from "../types/api";
import { getHostToken } from "./HostLogin";

const endStates = (r: AnalyticsPayload["result"]): Record<TeamId, MascotState> =>
  // DRAW: no "exhausted" sprite exists, so both idle.
  r === "INTER" ? { inter: "happy", gremio: "crying" } : r === "GREMIO" ? { inter: "crying", gremio: "happy" } : { inter: "idle", gremio: "idle" };

export default function HostResults() {
  const { id = "" } = useParams();
  const token = getHostToken() ?? "";
  const nav = useNavigate();
  const routed = (useLocation().state as { analytics?: AnalyticsPayload } | null)?.analytics ?? null;
  const [fetched, setFetched] = useState<AnalyticsPayload | null>(null);
  const [err, setErr] = useState("");
  const a = routed ?? fetched;

  useEffect(() => {
    if (routed || !token) return;
    getAnalytics(token, id).then(setFetched, (x) => {
      if (x instanceof ApiError && x.status === 401) nav("/host/login", { replace: true });
      else setErr("Não foi possível carregar os resultados.");
    });
  }, [routed, token, id, nav]);

  if (!token) return <Navigate to="/host/login" replace />;

  async function again() {
    try {
      nav(`/host/lobby/${(await resetMatch(token, id)).matchId}`);
    } catch {
      nav("/host/create"); // match gone (e.g. server restarted)
    }
  }

  if (!a) return <main className="host-page"><p role={err ? "alert" : undefined}>{err || "Carregando…"}</p></main>;
  const st = endStates(a.result);
  return (
    <main className="host-page results">
      <ResultBanner result={a.result} endReason={a.endReason} />
      <div className="results-mascots">
        <Mascot team="inter" state={st.inter} size={200} />
        <Mascot team="gremio" state={st.gremio} size={200} />
      </div>
      <AnalyticsGrid a={a} />
      <button className="join-submit start-btn" onClick={again}>Nova Partida</button>
    </main>
  );
}
