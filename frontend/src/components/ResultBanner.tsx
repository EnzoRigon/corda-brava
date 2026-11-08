import type { EndReason, MatchResult } from "../types/api";

const LINE = { INTER: "INTER VENCEU!", GREMIO: "GRÊMIO VENCEU!", DRAW: "EMPATE!" } as const;

export const resultLine = (r: MatchResult | null) => (r ? LINE[r] : "PARTIDA CANCELADA");

export default function ResultBanner({ result, endReason }: { result: MatchResult | null; endReason: EndReason | null }) {
  if (!result)
    return (
      <header className="result-banner cancelled">
        <h1 className="rs-title pixel-title">FIM DE JOGO</h1>
        <p className="rs-line">{resultLine(null)}</p>
      </header>
    );
  return (
    <header className={`result-banner ${result.toLowerCase()}`}>
      <h1 className="rs-title pixel-title">FIM DE JOGO</h1>
      <p className="rs-line">{resultLine(result)}</p>
      <p className="rs-reason">{endReason === "win" ? "Corda puxada até o fim!" : "O tempo acabou!"}</p>
    </header>
  );
}
