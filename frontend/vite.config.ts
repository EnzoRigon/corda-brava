import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
declare const process: { env: Record<string, string | undefined> }; // avoids needing @types/node

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      "/api": { target: process.env.VITE_PROXY_TARGET || "http://localhost:8000", ws: true },
    },
  },
});
