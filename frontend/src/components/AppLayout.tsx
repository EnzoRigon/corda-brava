import { Outlet, useLocation } from "react-router-dom";
import { loadSession } from "../hooks/useMePolling";
import { GameBackground, type BackgroundVariant } from "./GameBackground";
import { MuteToggle } from "./MuteToggle";

export function variantFor(pathname: string): BackgroundVariant {
  if (pathname.startsWith("/j/")) return "player";
  if (pathname.startsWith("/host/match")) return "match";
  if (pathname.startsWith("/host/results")) return "results";
  return "title";
}

/** Renders the scene behind every route; the player scene is tinted with the team once known. */
export default function AppLayout() {
  const { pathname } = useLocation();
  const variant = variantFor(pathname);
  const team = variant === "player" ? loadSession(pathname.split("/")[2] ?? "")?.team : null;
  return (
    <>
      <GameBackground variant={variant} team={team} />
      <MuteToggle />
      <Outlet />
    </>
  );
}
