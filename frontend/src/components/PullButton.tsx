import { useRef, useState } from "react";
import { play } from "../lib/sfx";

interface Pop { n: number; x: number; y: number }

/** Giant PUXA! button. Fires on pointerdown (no 300ms click delay); click only handles keyboard (detail === 0). */
export function PullButton({ onPull, color }: { onPull: () => void; color: string }) {
  const [pops, setPops] = useState<Pop[]>([]);
  const seq = useRef(0);
  const wrap = useRef<HTMLDivElement>(null);
  const fire = (cx?: number, cy?: number) => {
    onPull();
    play("tap");
    if (typeof navigator.vibrate === "function") navigator.vibrate(8);
    const r = wrap.current?.getBoundingClientRect();
    const x = r && cx ? cx - r.left : (r?.width ?? 0) / 2; // keyboard / no coords: centre
    const y = r && cy ? cy - r.top : (r?.height ?? 0) / 2;
    const n = ++seq.current;
    setPops((p) => [...p.slice(-7), { n, x, y }]);
  };
  return (
    <div ref={wrap} className="pull-wrap">
      {pops.map(({ n, x, y }) => (
        <span
          key={n}
          className="plus-one"
          style={{ left: x, top: y }}
          aria-hidden="true"
          onAnimationEnd={() => setPops((p) => p.filter((q) => q.n !== n))}
        >
          +1
        </span>
      ))}
      <button
        type="button"
        className="pull-button"
        style={{ background: color }}
        onContextMenu={(e) => e.preventDefault()}
        onPointerDown={(e) => {
          if (e.button !== 0) return;
          e.preventDefault();
          fire(e.clientX, e.clientY);
        }}
        onClick={(e) => {
          if (e.detail === 0) fire(); // keyboard activation only
        }}
      >
        PUXA!
      </button>
    </div>
  );
}
