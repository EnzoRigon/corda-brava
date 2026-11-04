import type { TeamId } from "../types/api";

/** Generic pixel-style badge with the player's initial; pops in on mount. */
export default function PlayerIcon({ name, team }: { name: string; team: TeamId }) {
  return (
    <div className={`player-icon ${team}`} title={name}>
      <span className="player-icon-block">{name.trim().charAt(0).toUpperCase() || "?"}</span>
      <span className="player-icon-name">{name}</span>
    </div>
  );
}
