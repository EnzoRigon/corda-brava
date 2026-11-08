import { useEffect, useRef, useState } from "react";
import { PixelButton } from "./PixelButton";

/** Retro "JOGAR DE NOVO?" prompt: SIM / NÃO, arrows move the ▶ cursor, Enter confirms. */
export function PlayAgain({ onYes, onNo }: { onYes: () => void; onNo: () => void }) {
  const [sel, setSel] = useState(0);
  const refs = [useRef<HTMLSpanElement>(null), useRef<HTMLSpanElement>(null)];
  const acts = [onYes, onNo];

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        const n = e.key === "ArrowLeft" ? 0 : 1;
        setSel(n);
        refs[n].current?.querySelector("button")?.focus();
      } else if (e.key === "Enter" && !(document.activeElement instanceof HTMLButtonElement)) {
        acts[sel](); // a focused button handles Enter natively
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const opt = (i: number, label: string, variant: "primary" | "ghost") => (
    <span className="again-opt" data-selected={sel === i} ref={refs[i]}>
      <span className="again-cursor anim-blink" aria-hidden="true">▶</span>
      <PixelButton variant={variant} onClick={acts[i]} onMouseEnter={() => setSel(i)} onFocus={() => setSel(i)}>{label}</PixelButton>
    </span>
  );
  return (
    <div className="again" role="group" aria-label="Jogar de novo?">
      <p className="again-q">JOGAR DE NOVO?</p>
      <div className="again-opts">{opt(0, "SIM", "primary")}{opt(1, "NÃO", "ghost")}</div>
    </div>
  );
}
