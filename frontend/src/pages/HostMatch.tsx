import { useCallback, useEffect, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { cancelMatch } from "../api/hostApi";
import { useHostSocket } from "../hooks/useHostSocket";
import { useCountdown } from "../hooks/useCountdown";
import { Crest } from "../components/Crest";
import EventFeed from "../components/EventFeed";
import RopeScene from "../components/RopeScene";
import Timer from "../components/Timer";
import { PixelButton } from "../components/PixelButton";
import { PixelPanel } from "../components/PixelPanel";
import { emptyFeed, isFinalSeconds, leadChange, pushEvents } from "../lib/matchFx";
import { play } from "../lib/sfx";
import type { TeamId } from "../types/api";
import { getHostToken } from "./HostLogin";
import "../theme/match.css";

const BANNER_MS = 1400;

export default function HostMatch() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const token = getHostToken() ?? "";
  const { snapshot, lastTick, ended, terminal, authError } = useHostSocket(id, token);

  const running = snapshot?.status === "RUNNING";
  const target = snapshot?.config.ropeTarget ?? 0;
  const secs = useCountdown(snapshot?.remainingS ?? 0, running);
  const final = isFinalSeconds(secs);
  const secInt = Math.ceil(secs);

  const [feed, setFeed] = useState(emptyFeed);
  const [banner, setBanner] = useState<{ text: string; key: number; tone: "go" | "swing" } | null>(null);
  const [confirming, setConfirming] = useState(false);
  const lead = useRef<TeamId | null>(null);
  const bannerTimer = useRef<ReturnType<typeof setTimeout>>();
  const showBanner = useCallback((text: string, tone: "go" | "swing") => {
    clearTimeout(bannerTimer.current);
    setBanner({ text, tone, key: Date.now() });
    bannerTimer.current = setTimeout(() => setBanner(null), BANNER_MS);
  }, []);
  useEffect(() => () => clearTimeout(bannerTimer.current), []);

  useEffect(() => {
    if (!running) return;
    play("whistle");
    showBanner("JÁ!", "go");
  }, [running, showBanner]);

  useEffect(() => {
    if (!lastTick) return;
    setFeed((f) => pushEvents(f, lastTick.events, Date.now()));
    const r = leadChange(lead.current, lastTick.rope, target * 0.05);
    lead.current = r.lead;
    if (r.changed) {
      play("swing");
      showBanner("VIRADA!", "swing");
    }
  }, [lastTick, target, showBanner]);

  useEffect(() => {
    if (final) play(secInt <= 3 ? "countdown" : "heartbeat");
  }, [final, secInt]);

  if (!token || authError) return <Navigate to="/host/login" replace />;
  // Analytics ride along in router state so Results needs no extra fetch.
  if (ended) return <Navigate to={`/host/results/${id}`} replace state={ended} />;
  if (terminal) return <Navigate to={terminal.type === "reset" ? `/host/lobby/${terminal.newMatchId}` : "/host/create"} replace />;
  if (!snapshot) return <main className="host-page"><p>Conectando…</p></main>;
  if (snapshot.status === "LOBBY") return <Navigate to={`/host/lobby/${id}`} replace />;
  if (snapshot.status === "FINISHED") return <Navigate to={`/host/results/${id}`} replace />;

  const { scores, config } = snapshot;
  const marker = Math.max(0, Math.min(100, 50 + (target > 0 ? (snapshot.rope / target) * 50 : 0)));
  const cancel = async () => {
    try {
      await cancelMatch(token, id);
    } catch {
      // already finished/cancelled: leaving is still right
    }
    navigate("/host/create");
  };

  return (
    <main className={`host-page match${final ? " final" : ""}`}>
      <PixelPanel className="match-hud hud-grid">
        <div className="hud-side inter">
          <Crest team="inter" size={64} />
          <div><span className="hud-name">INTER</span><span className="hud-score">{scores.inter.pulls}</span></div>
        </div>
        <div className="hud-center">
          <Timer remainingS={snapshot.remainingS} running urgent={final} />
          <div className="power-bar" aria-hidden>
            <div className="power-marker" style={{ left: `${marker}%` }} />
          </div>
        </div>
        <div className="hud-side gremio">
          <div><span className="hud-name">GRÊMIO</span><span className="hud-score">{scores.gremio.pulls}</span></div>
          <Crest team="gremio" size={64} />
        </div>
      </PixelPanel>
      <div className="match-feeds">
        <EventFeed team="inter" entries={feed.inter} />
        <EventFeed team="gremio" entries={feed.gremio} />
      </div>
      <RopeScene rope={snapshot.rope} target={config.ropeTarget} delta={lastTick?.delta} mascots={{ inter: "straining", gremio: "straining" }} />
      {final && <div className="final-vignette" aria-hidden />}
      {banner && <div key={banner.key} className={`match-banner ${banner.tone}`} role="status">{banner.text}</div>}
      <div className="match-cancel">
        {confirming ? (
          <PixelPanel className="cancel-confirm">
            <span>Cancelar a partida?</span>
            <PixelButton variant="red" onClick={cancel}>Sim, cancelar</PixelButton>
            <PixelButton variant="ghost" onClick={() => setConfirming(false)}>Voltar</PixelButton>
          </PixelPanel>
        ) : (
          <PixelButton variant="ghost" onClick={() => setConfirming(true)}>Cancelar</PixelButton>
        )}
      </div>
    </main>
  );
}
