import logo from "../assets/ui/logo-160x56.png";
import logoSmall from "../assets/ui/logo-small-96x36.png";

/** P1 logo at an integer scale (native 160x56, or 96x36 when `small`), with a gentle bob. */
export function Logo({ scale = 3, small = false, className = "" }: { scale?: number; small?: boolean; className?: string }) {
  const [w, h] = small ? [96, 36] : [160, 56];
  return (
    <img
      src={small ? logoSmall : logo}
      alt="Corda Brava"
      width={w * scale}
      height={h * scale}
      className={`logo anim-bob ${className}`}
      style={{ imageRendering: "pixelated", maxWidth: "100%", height: "auto" }}
    />
  );
}
