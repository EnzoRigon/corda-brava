const FILES = import.meta.glob("../assets/ui/icon-*.png", { eager: true, query: "?url", import: "default" }) as Record<string, string>;

export type IconName =
  | "heart" | "star" | "trophy" | "crown" | "lightning" | "hourglass" | "speaker-on" | "speaker-off"
  | "arrow-left" | "check" | "cross" | "player" | "whistle" | "rope-coil" | "pennant-red" | "pennant-blue";

/** P1 16x16 icons. `size` should be a multiple of 16 to stay pixel-crisp. Decorative unless `label` is given. */
export function Icon({ name, size = 32, label, className }: { name: IconName; size?: number; label?: string; className?: string }) {
  return (
    <img
      src={FILES[`../assets/ui/icon-${name}.png`]}
      alt={label ?? ""}
      aria-hidden={label ? undefined : true}
      width={size}
      height={size}
      className={className}
      style={{ imageRendering: "pixelated" }}
    />
  );
}
