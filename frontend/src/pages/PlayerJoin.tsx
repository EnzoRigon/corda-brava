import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getPublic, join } from "../api/playerApi";
import { Logo } from "../components/Logo";
import { PixelButton } from "../components/PixelButton";
import { PixelPanel } from "../components/PixelPanel";
import { Crest } from "../components/Crest";
import { Icon } from "../components/Icon";
import { useDeviceId } from "../hooks/useDeviceId";
import { loadSession, saveSession } from "../hooks/useMePolling";
import type { PublicMatch, TeamId } from "../types/api";

const TEAMS: TeamId[] = ["inter", "gremio"];
/** How often the team counts refresh while the form is open (players poll; no player WebSocket). */
export const PUBLIC_POLL_MS = 1000;

export default function PlayerJoin() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const deviceId = useDeviceId();
  const [pub, setPub] = useState<PublicMatch | null>(null);
  const [name, setName] = useState("");
  const [team, setTeam] = useState<TeamId | null>(null);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // Existing session: the wait page's /me polling forwards to the right screen (or clears a dead token).
    if (loadSession(id)) {
      navigate(`/j/${id}/wait`, { replace: true });
      return;
    }
    let alive = true;
    let loaded = false;
    let inFlight = false; // no overlapping requests, so an old response never overwrites a newer one
    const poll = async () => {
      if (inFlight) return;
      inFlight = true;
      try {
        const p = await getPublic(id);
        if (!alive) return;
        loaded = true;
        setPub(p);
        setLoadError("");
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 404) clearInterval(timer); // no such match
        // A blip after a successful load keeps the last counts on screen.
        if (!loaded) setLoadError(e instanceof ApiError ? e.message : "Não foi possível carregar a partida.");
      } finally {
        inFlight = false;
      }
    };
    const timer = setInterval(() => void poll(), PUBLIC_POLL_MS);
    void poll();
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [id, navigate]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const clean = name.trim().slice(0, 24);
    if (!clean) return setError("Digite seu nome.");
    if (!team) return setError("Escolha um time.");
    setBusy(true);
    setError("");
    try {
      const r = await join(id, { name: clean, team, deviceId });
      saveSession(id, r);
      navigate(`/j/${id}/wait`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro inesperado. Tente novamente.");
      setBusy(false);
    }
  };

  return (
    <main className="player-page join-page">
      <Logo scale={2} small />
      <h1 className="pixel-title">Entrar na partida</h1>
      <form onSubmit={submit} className="join-form">
        <div role="radiogroup" aria-label="Escolha seu time" className="team-picks">
          {TEAMS.map((t) => (
            <button
              key={t}
              type="button"
              role="radio"
              aria-checked={team === t}
              className={`team-pick team-pick-${t}${team === t ? " selected" : ""}`}
              onClick={() => setTeam(t)}
            >
              <Crest team={t} size={96} />
              <strong>{pub?.teams[t].name ?? (t === "inter" ? "Inter" : "Grêmio")}</strong>
              <small>
                <Icon name="player" size={16} />
                {pub ? `${pub.counts[t]} jogadores` : "…"}
              </small>
            </button>
          ))}
        </div>
        <PixelPanel className="form-panel">
          <label>
            Seu nome
            <input value={name} maxLength={24} onChange={(e) => setName(e.target.value)} autoComplete="nickname" />
          </label>
        </PixelPanel>
        {(error || loadError) && (
          <p role="alert" className="px-toast">
            {error || loadError}
          </p>
        )}
        <PixelButton type="submit" disabled={busy} className="join-go">
          Entrar
        </PixelButton>
      </form>
    </main>
  );
}
