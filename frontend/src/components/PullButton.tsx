import { useState } from "react";

/** Big PUXAR button. Fires on pointerdown (no 300ms click delay); click only handles keyboard (detail === 0). */
export function PullButton({ onPull, color }: { onPull: () => void; color: string }) {
  const [pops, setPops] = useState<number[]>([]);
  const fire = () => {
    onPull();
    const n = performance.now();
    setPops((p) => [...p.slice(-5), n]);
  };
  return (
    <div style={{ position: "relative", width: "100%" }}>
      {pops.map((n) => (
        <span key={n} className="plus-one" aria-hidden="true" onAnimationEnd={() => setPops((p) => p.filter((x) => x !== n))}>
          +1
        </span>
      ))}
      <button
        type="button"
        className="pull-button"
        style={{ background: color }}
        onPointerDown={(e) => {
          e.preventDefault();
          fire();
        }}
        onClick={(e) => {
          if (e.detail === 0) fire(); // keyboard activation only
        }}
      >
        PUXAR
      </button>
    </div>
  );
}
