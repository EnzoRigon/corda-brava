import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { createMatch } from "../api/hostApi";
import { ApiError } from "../api/client";
import type { BalanceMode } from "../types/api";
import { getHostToken } from "./HostLogin";

// Mirrors backend MATCH_DURATION_MIN_S / MAX_S defaults.
const MIN_S = 30;
const MAX_S = 600;

export default function HostCreate() {
  const nav = useNavigate();
  const token = getHostToken();
  const [durationS, setDuration] = useState(120);
  const [balance, setBalance] = useState<BalanceMode>("normalized");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  if (!token) return <Navigate to="/host/login" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const r = await createMatch(token!, { durationS, balanceMode: balance });
      nav(`/host/lobby/${r.matchId}`, { state: { joinUrl: r.joinUrl } });
    } catch (x) {
      if (x instanceof ApiError && x.status === 401) return void nav("/host/login", { replace: true });
      setErr(x instanceof ApiError ? x.message : "Erro inesperado. Tente novamente.");
      setBusy(false);
    }
  }

  return (
    <main className="host-page">
      <h1>Nova partida</h1>
      <form className="join-form" onSubmit={submit}>
        <label>
          Duração (segundos)
          <input type="number" min={MIN_S} max={MAX_S} value={durationS} onChange={(e) => setDuration(Number(e.target.value))} />
        </label>
        <label>
          Pontuação
          <select value={balance} onChange={(e) => setBalance(e.target.value as BalanceMode)}>
            <option value="normalized">Normalizada (equilibra times)</option>
            <option value="raw">Bruta (cada puxada vale 1)</option>
          </select>
        </label>
        {err && <p role="alert">{err}</p>}
        <button className="join-submit" disabled={busy || durationS < MIN_S || durationS > MAX_S}>Criar partida</button>
        <small>Entre {MIN_S} e {MAX_S} segundos.</small>
      </form>
    </main>
  );
}
