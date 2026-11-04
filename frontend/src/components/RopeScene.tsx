import { useEffect, useRef, useState } from "react";
import type { TeamId } from "../types/api";
import { Mascot, type MascotState } from "./Mascot";
import Rope from "./Rope";

export const knotLeftPercent = (rope: number, target: number): number => 50 + (rope / target) * 40;

/** Eases toward `target` each animation frame; `enabled=false` snaps. */
function useSmooth(target: number, enabled: boolean): number {
  const [v, setV] = useState(target);
  const ref = useRef(target);
  useEffect(() => {
    if (!enabled) return;
    let id = requestAnimationFrame(function step() {
      ref.current += (target - ref.current) * 0.15;
      if (Math.abs(target - ref.current) < 0.05) ref.current = target;
      setV(ref.current);
      id = requestAnimationFrame(step);
    });
    return () => cancelAnimationFrame(id);
  }, [target, enabled]);
  return enabled ? v : target;
}

interface Props {
  rope: number;
  target: number;
  delta?: Record<TeamId, number>;
  mascots?: Record<TeamId, MascotState>;
  interpolate?: boolean;
}

export default function RopeScene({ rope, target, delta, mascots, interpolate = true }: Props) {
  const goal = knotLeftPercent(rope, target);
  const left = useSmooth(goal, interpolate);
  const shake = Math.abs(goal - left) > 4; // big swing still in flight
  const push = (t: TeamId) => ((mascots?.[t] ?? "straining") === "straining" ? 1 + Math.min(0.25, (delta?.[t] ?? 0) / 400) : 1);
  return (
    <div className={`rope-scene${shake ? " shake" : ""}`}>
      <div className="scene-mascot" style={{ transform: `scale(${push("inter")})` }}>
        <Mascot team="inter" state={mascots?.inter ?? "straining"} size={160} />
      </div>
      <Rope left={left} />
      <div className="scene-mascot" style={{ transform: `scale(${push("gremio")})` }}>
        <Mascot team="gremio" state={mascots?.gremio ?? "straining"} size={160} />
      </div>
    </div>
  );
}
