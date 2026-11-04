import type { EndReason, MatchResult } from "../types/api";

const NAME = { INTER: "Inter", GREMIO: "Grêmio" } as const;

export default function ResultBanner({ result, endReason }: { result: MatchResult | null; endReason: EndReason | null }) {
  if (!result)
    return (
      <header className="result-banner">
        <h1>Partida cancelada</h1>
      </header>
    );
  const win = result === "INTER" || result === "GREMIO";
  return (
    <header className={`result-banner ${result.toLowerCase()}`}>
      <h1>{win ? `${NAME[result]} venceu a Corda Brava!` : "Empate! Ninguém levou a corda."}</h1>
      <p>{endReason === "win" ? "A corda foi arrastada até o fim!" : "O tempo acabou."}</p>
    </header>
  );
}
