import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getPublic, join } from "../api/playerApi";
import { Crest } from "../components/Crest";
import { useDeviceId } from "../hooks/useDeviceId";
import { loadSession, saveSession } from "../hooks/useMePolling";
import type { PublicMatch, TeamId } from "../types/api";

const TEAMS: TeamId[] = ["inter", "gremio"];

export default function PlayerJoin() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const deviceId = useDeviceId();
  const [pub, setPub] = useState<PublicMatch | null>(null);
  const [name, setName] = useState("");
  const [team, setTeam] = useState<TeamId | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // Existing session: the wait page's /me polling forwards to the right screen (or clears a dead token).
    if (loadSession(id)) {
      navigate(`/j/${id}/wait`, { replace: true });
      return;
    }
    getPublic(id)
      .then(setPub)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Não foi possível carregar a partida."));
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
    <main className="player-page">
      <h1>Entrar na partida</h1>
      <form onSubmit={submit} className="join-form">
        <label>
          Seu nome
          <input value={name} maxLength={24} onChange={(e) => setName(e.target.value)} autoComplete="nickname" />
        </label>
        <div role="radiogroup" aria-label="Escolha seu time" className="team-picks">
          {TEAMS.map((t) => (
            <button
              key={t}
              type="button"
              role="radio"
              aria-checked={team === t}
              className="team-pick"
              style={{ borderColor: team === t ? `var(--${t})` : "transparent" }}
              onClick={() => setTeam(t)}
            >
              <Crest team={t} size={64} />
              <span>{pub?.teams[t].name ?? (t === "inter" ? "Inter" : "Grêmio")}</span>
              <small>{pub ? `${pub.counts[t]} jogadores` : ""}</small>
            </button>
          ))}
        </div>
        {error && <p role="alert">{error}</p>}
        <button type="submit" className="join-submit" disabled={busy}>
          Entrar
        </button>
      </form>
    </main>
  );
}
