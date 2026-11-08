import type { TeamId } from "../types/api";
import { Icon } from "./Icon";

/** Rope + knot as plain CSS shapes (not club characters). `lean` = side the knot is pulled toward (pennant colour). */
export default function Rope({ left, lean, burst }: { left: number; lean?: TeamId | null; burst?: boolean }) {
  return (
    <div className="rope">
      <div className="rope-line" />
      <div className="rope-knot" data-testid="knot" style={{ left: `${left}%` }}>
        {lean && <Icon name={lean === "inter" ? "pennant-red" : "pennant-blue"} size={48} className="knot-pennant" />}
        {burst && <span className="fx-sparkles" aria-hidden />}
      </div>
    </div>
  );
}
