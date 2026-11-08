import { useEffect, useRef, useState } from "react";
import type { TeamId } from "../types/api";
import { Mascot, type MascotState } from "./Mascot";
import Rope from "./Rope";

export const knotLeftPercent = (rope: number, target: number): number => (target > 0 ? 50 + (rope / target) * 40 : 50);

/** Eases toward `target` each animation frame; `enabled=false` snaps. */
function useSmooth(target: number, enabled: boolean): number {
  const [v, setV] = useState(target);
  const ref = useRef(target);
  useEffect(() => {
    if (!enabled) return;
    let id = requestAnimationFrame(function step() {
      ref.current += (target - ref.current) * 0.15;
      const done = Math.abs(target - ref.current) < 0.01;
      if (done) ref.current = target;
      setV(ref.current);
      if (!done) id = requestAnimationFrame(step); // converged: stop re-arming until target changes
    });
    return () => cancelAnimationFrame(id);
  }, [target, enabled]);
  return enabled ? v : target;
}

/** Two dust puffs at the mascot's heels; opacity/scale follow how hard the side is pulling. */
function Dust({ level, side }: { level: number; side: TeamId }) {
  const l = Math.min(1, Math.max(0, level));
  return (
    <div className={`dust dust-${side}`} aria-hidden style={{ opacity: 0.25 + 0.75 * l, ["--dust-k" as string]: 0.8 + 0.6 * l }}>
      <i /><i />
    </div>
  );
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
  const lean: TeamId | null = rope < 0 ? "inter" : rope > 0 ? "gremio" : null;
  const dust = (t: TeamId) => (delta?.[t] ?? 0) / 30; // ~30 pulls/tick = full cloud
  const push = (t: TeamId) => ((mascots?.[t] ?? "straining") === "straining" ? 1 + Math.min(0.25, (delta?.[t] ?? 0) / 400) : 1);
  return (
    <div className={`rope-scene${shake ? " shake" : ""}`}>
      <div className="scene-mascot" style={{ transform: `scale(${push("inter")})`, transformOrigin: "100% 65%" }}>
        <Mascot team="inter" state={mascots?.inter ?? "straining"} size={160} />
        <Dust level={dust("inter")} side="inter" />
      </div>
      <Rope left={left} lean={lean} burst={shake} />
      <div className="scene-mascot" style={{ transform: `scale(${push("gremio")})`, transformOrigin: "0% 65%" }}>
        <Mascot team="gremio" state={mascots?.gremio ?? "straining"} size={160} />
        <Dust level={dust("gremio")} side="gremio" />
      </div>
    </div>
  );
}
