import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { getAnalytics, resetMatch } from "../api/hostApi";
import { ApiError } from "../api/client";
import AnalyticsGrid from "../components/AnalyticsGrid";
import { Mascot, type MascotState } from "../components/Mascot";
import { Confetti } from "../components/Confetti";
import { Crest } from "../components/Crest";
import { Icon } from "../components/Icon";
import { PlayAgain } from "../components/PlayAgain";
import ResultBanner from "../components/ResultBanner";
import type { AnalyticsPayload, TeamId } from "../types/api";
import { PixelPanel } from "../components/PixelPanel";
import "../theme/results.css";
import { play } from "../lib/sfx";
import { getHostToken } from "./HostLogin";

const NAME: Record<TeamId, string> = { inter: "Inter", gremio: "Grêmio" };
const TEAMS: TeamId[] = ["inter", "gremio"];
const TEAM_COLOR: Record<TeamId, string> = { inter: "#e5050f", gremio: "#4fa9dc" };

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
      else if (x instanceof ApiError && x.status === 409) nav(`/host/match/${id}`, { replace: true }); // not finished yet
      else setErr("Não foi possível carregar os resultados.");
    });
  }, [routed, token, id, nav]);

  const result = a?.result;
  useEffect(() => {
    if (result) play(result === "DRAW" ? "draw" : "win");
  }, [result]);

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
  const win = a.result === "INTER" || a.result === "GREMIO" ? (a.result.toLowerCase() as TeamId) : null;
  const confettiColors = win ? [TEAM_COLOR[win], "#f4f4f4", "#ffe27a"] : a.result === "DRAW" ? ["#ffe27a", "#f4f4f4"] : null;
  return (
    <main className="host-page results">
      {confettiColors && <Confetti count={36} colors={confettiColors} />}
      <div className="rs-stage rs-s1"><ResultBanner result={a.result} endReason={a.endReason} /></div>
      <div className="rs-stage rs-s2 results-mascots">
        {TEAMS.map((t) => (
          <div key={t} className={`pod-col ${t} ${win ? (win === t ? "first" : "second") : "even"}`}>
            {win === t && <Icon name="crown" size={64} className="pod-crown anim-bob" />}
            <Mascot team={t} state={st[t]} size={192} className="pod-mascot" />
            <div className="pod-block">
              <strong>{NAME[t]}</strong>
              <Crest team={t} size={48} />
            </div>
          </div>
        ))}
      </div>
      <div className="rs-stage rs-s3"><AnalyticsGrid a={a} /></div>
      <PixelPanel className="rs-stage rs-s3 again-panel"><PlayAgain onYes={again} onNo={() => nav("/host/create")} /></PixelPanel>
    </main>
  );
}
