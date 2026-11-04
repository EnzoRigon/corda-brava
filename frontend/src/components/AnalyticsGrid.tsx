import type { AnalyticsPayload, PlayerStats, TeamId } from "../types/api";
import { Crest } from "./Crest";
import PullsTimeline from "./charts/PullsTimeline";

const NAME: Record<TeamId, string> = { inter: "Inter", gremio: "Grêmio" };
const TEAMS: TeamId[] = ["inter", "gremio"];
const Tile = ({ label, value }: { label: string; value: string | number }) => (
  <div className="tile"><span>{label}</span><strong>{value}</strong></div>
);
const who = (p: PlayerStats | null) => (p ? `${p.name} (${p.pulls})` : "—");

export default function AnalyticsGrid({ a }: { a: AnalyticsPayload }) {
  return (
    <section className="analytics">
      <div className="tiles">
        <Tile label="Jogadores" value={a.totalPlayers} />
        <Tile label="Puxadas totais" value={a.totalPulls.overall} />
        <Tile label="Duração (s)" value={a.durationS} />
        <Tile label="Pico de intensidade" value={`${a.peak.value}/s aos ${a.peak.t}s`} />
        <Tile label="Posição final da corda" value={a.finalRope} />
      </div>
      <div className="team-tiles">
        {TEAMS.map((t) => (
          <div key={t} className={`team-card ${t}`}>
            <h3><Crest team={t} size={32} /> {NAME[t]}</h3>
            <Tile label="Jogadores" value={a.playersPerTeam[t]} />
            <Tile label="Puxadas" value={a.totalPulls[t]} />
            <Tile label="Média por jogador" value={a.teams[t].avgPullsPerPlayer.toFixed(1)} />
            <Tile label="Melhor jogador" value={who(a.teams[t].bestPlayer)} />
            <Tile label="Pior jogador" value={who(a.teams[t].worstPlayer)} />
          </div>
        ))}
      </div>
      <h2>Puxadas por segundo</h2>
      <PullsTimeline data={a.pullsPerSecond} />
      <h2>Ranking</h2>
      <ol className="leaderboard">
        {a.leaderboard.map((p) => (
          <li key={p.playerId} className={p.team}>
            {p.name} — {p.pulls} puxadas ({p.pctOfTeam}% do time)
          </li>
        ))}
      </ol>
    </section>
  );
}
