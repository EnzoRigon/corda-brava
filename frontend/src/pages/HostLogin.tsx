import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/hostApi";
import { ApiError } from "../api/client";
import { Logo } from "../components/Logo";
import { PixelButton } from "../components/PixelButton";
import { PixelPanel } from "../components/PixelPanel";
import "../theme/host.css";

export const HOST_TOKEN_KEY = "cb.hostToken";
export const getHostToken = (): string | null => {
  try {
    return sessionStorage.getItem(HOST_TOKEN_KEY);
  } catch {
    return null;
  }
};

export default function HostLogin() {
  const nav = useNavigate();
  const [pw, setPw] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const { token } = await login(pw);
      try {
        sessionStorage.setItem(HOST_TOKEN_KEY, token);
      } catch {
        // storage unavailable: pages will bounce back to login
      }
      nav("/host/create");
    } catch (x) {
      setErr(x instanceof ApiError ? x.message : "Erro inesperado. Tente novamente.");
      setBusy(false);
    }
  }

  return (
    <main className="host-page center title-screen">
      <h1 className="logo-heading"><Logo scale={4} /></h1>
      <p className="title-tag">INTER × GRÊMIO — CABO DE GUERRA</p>
      <p className="press-start anim-blink">PRESSIONE START</p>
      <PixelPanel className="form-panel">
        <form className="join-form" onSubmit={submit}>
          <label>
            Senha do host
            <input type="password" value={pw} onChange={(e) => setPw(e.target.value)} autoFocus />
          </label>
          <PixelButton type="submit" disabled={busy || !pw}>Entrar</PixelButton>
        </form>
      </PixelPanel>
      {err && <p role="alert" className="px-toast">{err}</p>}
    </main>
  );
}
