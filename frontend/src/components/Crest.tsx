import type { TeamId } from "../types/api";
import inter from "../assets/crests/inter.png";
import gremio from "../assets/crests/gremio.png";

const CRESTS: Record<TeamId, { src: string; alt: string }> = {
  inter: { src: inter, alt: "Escudo do Inter" },
  gremio: { src: gremio, alt: "Escudo do Grêmio" },
};

export function Crest({ team, size = 48, className }: { team: TeamId; size?: number; className?: string }) {
  const { src, alt } = CRESTS[team];
  return <img src={src} alt={alt} width={size} height={size} className={className} style={{ imageRendering: "pixelated" }} />;
}
