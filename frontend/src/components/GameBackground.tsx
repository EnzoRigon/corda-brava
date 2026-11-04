import sparkle from "../assets/ui/fx-sparkle-strip-6f-8px.png";
import moon from "../assets/ui/bg-moon-32.png";
import cloudA from "../assets/ui/bg-cloud-a-48x16.png";
import cloudB from "../assets/ui/bg-cloud-b-48x16.png";
import type { TeamId } from "../types/api";

export type BackgroundVariant = "title" | "match" | "results" | "player";

// [left %, top %, animation delay s]
const STARS: [number, number, number][] = [[8, 10, 0], [22, 28, 1.2], [41, 8, 2.1], [58, 22, 0.6], [73, 12, 1.7], [90, 30, 2.6]];

/** Fixed full-viewport night stadium: sky, stars, moon, clouds, stands, pitch. Pure CSS, decorative. */
export function GameBackground({ variant, team }: { variant: BackgroundVariant; team?: TeamId | null }) {
  return (
    <div className={`gb gb-${variant}`} aria-hidden="true" data-testid="game-background">
      <div className="gb-sky" />
      {STARS.map(([l, t, d], i) => (
        <span key={i} className="gb-star" style={{ left: `${l}%`, top: `${t}%`, animationDelay: `${d}s`, backgroundImage: `url(${sparkle})` }} />
      ))}
      <img className="gb-moon" src={moon} alt="" />
      <img className="gb-cloud gb-cloud-a" src={cloudA} alt="" />
      <img className="gb-cloud gb-cloud-b" src={cloudB} alt="" />
      <div className="gb-stadium" />
      <div className="gb-pitch">
        <div className="gb-pitch-top" />
      </div>
      {team && <div className="gb-tint" style={{ background: `var(--${team})` }} />}
    </div>
  );
}
