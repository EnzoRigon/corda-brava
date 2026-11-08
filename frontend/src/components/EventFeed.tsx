import type { TeamId } from "../types/api";
import type { FeedEntry } from "../lib/matchFx";
import { Icon } from "./Icon";

/** One team's live pull feed: newest on top (pops in, keyed by entry id), older rows fade via CSS. */
export default function EventFeed({ team, entries }: { team: TeamId; entries: FeedEntry[] }) {
  return (
    <ul className={`event-feed feed-${team}`} aria-label={`Eventos ${team === "inter" ? "Inter" : "Grêmio"}`}>
      {entries.map((e) => (
        <li key={e.id} className="feed-tag">
          <Icon name="player" size={16} />
          <span className="feed-name">{e.name}</span>
          <Icon name="lightning" size={16} />
          <b>+{e.count}</b>
        </li>
      ))}
    </ul>
  );
}
