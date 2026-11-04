import type { TeamId } from "../types/api";
import saciMaster from "../assets/mascots/saci_master.png";
import saciPull from "../assets/mascots/saci_pull.gif";
import saciHappy from "../assets/mascots/saci_happy.gif";
import saciDefeat from "../assets/mascots/saci_defeat.gif";
import saciCry from "../assets/mascots/saci_cry.gif";
import mosqMaster from "../assets/mascots/mosq_master.png";
import mosqPull from "../assets/mascots/mosq_pull.gif";
import mosqHappy from "../assets/mascots/mosq_happy.gif";
import mosqDefeat from "../assets/mascots/mosq_defeat.gif";
import mosqCry from "../assets/mascots/mosq_cry.gif";

export type MascotState = "idle" | "straining" | "winning" | "losing" | "happy" | "crying";

const SPRITES: Record<TeamId, Record<MascotState, string>> = {
  inter: { idle: saciMaster, straining: saciPull, winning: saciHappy, happy: saciHappy, losing: saciDefeat, crying: saciCry },
  gremio: { idle: mosqMaster, straining: mosqPull, winning: mosqHappy, happy: mosqHappy, losing: mosqDefeat, crying: mosqCry },
};

const ALT: Record<TeamId, string> = { inter: "Saci (Inter)", gremio: "Mosqueteiro (Grêmio)" };

interface Props { team: TeamId; state: MascotState; size?: number; className?: string }

export function Mascot({ team, state, size = 128, className }: Props) {
  return (
    <img
      src={SPRITES[team][state]}
      alt={ALT[team]}
      width={size}
      height={size}
      className={className}
      // Sprites face right; Grêmio is mirrored (as in the owner prototype) to face center.
      style={{ imageRendering: "pixelated", transform: team === "gremio" ? "scaleX(-1)" : undefined }}
    />
  );
}
