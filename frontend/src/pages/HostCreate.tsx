import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { createMatch } from "../api/hostApi";
import { ApiError } from "../api/client";
import type { BalanceMode } from "../types/api";
import { Logo } from "../components/Logo";
import { Icon } from "../components/Icon";
import { PixelButton } from "../components/PixelButton";
import { PixelPanel } from "../components/PixelPanel";
import { getHostToken } from "./HostLogin";
import "../theme/host.css";

// Mirrors backend MATCH_DURATION_MIN_S / MAX_S defaults.
const MIN_S = 30;
const MAX_S = 600;
const STEP_S = 30;

export const stepDuration = (d: number, dir: 1 | -1) => Math.min(MAX_S, Math.max(MIN_S, d + dir * STEP_S));
export const fmtDuration = (d: number) => `${Math.floor(d / 60)}:${String(d % 60).padStart(2, "0")}`;

const MODES: { id: BalanceMode; name: string; hint: string }[] = [
  { id: "normalized", name: "Normalizado", hint: "Equilibra times de tamanhos diferentes." },
  { id: "raw", name: "Bruto", hint: "Cada puxada vale 1 ponto." },
];

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

  const valid = durationS >= MIN_S && durationS <= MAX_S;
  return (
    <main className="host-page center title-screen">
      <Logo scale={2} />
      <PixelPanel className="form-panel options-panel">
        <h1 className="pixel-title">NOVA PARTIDA</h1>
        <form className="join-form" onSubmit={submit}>
          <div className="stepper">
            <PixelButton variant="ghost" aria-label="Diminuir duração" disabled={durationS <= MIN_S} onClick={() => setDuration(stepDuration(durationS, -1))}>−</PixelButton>
            <div className="stepper-value">
              <Icon name="hourglass" size={32} />
              <span className="stepper-time">{valid ? fmtDuration(durationS) : "--:--"}</span>
            </div>
            <PixelButton variant="ghost" aria-label="Aumentar duração" disabled={durationS >= MAX_S} onClick={() => setDuration(stepDuration(durationS, 1))}>+</PixelButton>
          </div>
          <label className="stepper-input">
            Duração (segundos)
            <input type="number" min={MIN_S} max={MAX_S} step={STEP_S} value={durationS} onChange={(e) => setDuration(Number(e.target.value))} />
          </label>
          <small>Entre {MIN_S} e {MAX_S} segundos.</small>
          <div className="mode-toggle" role="group" aria-label="Pontuação">
            {MODES.map((m) => (
              <PixelButton key={m.id} variant={balance === m.id ? "primary" : "ghost"} aria-pressed={balance === m.id} onClick={() => setBalance(m.id)}>{m.name}</PixelButton>
            ))}
          </div>
          <small>{MODES.find((m) => m.id === balance)!.hint}</small>
          {err && <p role="alert" className="px-toast">{err}</p>}
          <PixelButton type="submit" className="start-btn" disabled={busy || !valid}>Criar partida</PixelButton>
        </form>
      </PixelPanel>
      <PixelButton variant="ghost" className="back-btn" onClick={() => nav("/host/login")}>
        <Icon name="arrow-left" size={24} label="Voltar" />
      </PixelButton>
    </main>
  );
}
