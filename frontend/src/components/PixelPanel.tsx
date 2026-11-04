import type { HTMLAttributes } from "react";

/** Dark translucent panel with a stepped pixel border. `tone` tints the border. */
export function PixelPanel({ tone, className = "", ...rest }: HTMLAttributes<HTMLDivElement> & { tone?: "red" | "blue" }) {
  return <div className={`pixel-panel${tone ? ` tone-${tone}` : ""} ${className}`} {...rest} />;
}
