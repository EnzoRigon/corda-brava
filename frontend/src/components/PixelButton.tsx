import type { ButtonHTMLAttributes } from "react";
import { play } from "../lib/sfx";

export type PixelVariant = "primary" | "red" | "blue" | "ghost";

/** Beveled pixel button (a real <button>); plays the UI click sound. */
export function PixelButton({ variant = "primary", className = "", onClick, type = "button", ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: PixelVariant }) {
  return (
    <button
      type={type}
      className={`pxbtn pxbtn-${variant} ${className}`}
      onClick={(e) => {
        play("click");
        onClick?.(e);
      }}
      {...rest}
    />
  );
}
