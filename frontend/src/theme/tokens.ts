// Single source for theme tokens. global.css mirrors the colors as CSS variables.
export const teams = {
  inter: { id: "inter", name: "Inter", primary: "#E5050F", secondary: "#FFFFFF", dark: "#7A0309" },
  gremio: { id: "gremio", name: "Grêmio", primary: "#0D80BF", secondary: "#000000", light: "#4FA9DC" },
} as const;

export const colors = {
  bg: "#12121c",
  panel: "#1d1d2e",
  text: "#f4f4f4",
  muted: "#9a9ab0",
} as const;

export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 40 } as const; // px, 4px pixel grid

export const zIndex = { base: 0, scene: 10, hud: 20, overlay: 100, toast: 200 } as const;

export const fonts = { pixel: '"Press Start 2P", monospace' } as const;

export const motion = { fast: "80ms", base: "200ms", slow: "500ms" } as const;
