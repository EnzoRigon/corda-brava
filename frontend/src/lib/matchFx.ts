import type { TeamId, TickEvent } from "../types/api";

export interface FeedEntry { id: number; playerId: string; name: string; team: TeamId; count: number; at: number }
export interface FeedState { seq: number; inter: FeedEntry[]; gremio: FeedEntry[] }

export const FEED_MAX = 6;
export const FEED_MERGE_MS = 400; // below the 500 ms tick: only same-burst duplicates merge, so each tick shows as its own row
export const emptyFeed = (): FeedState => ({ seq: 0, inter: [], gremio: [] });

/** Newest first, last FEED_MAX per team. Same player within FEED_MERGE_MS is merged (counts add) and moves to the top. */
export function pushEvents(feed: FeedState, events: TickEvent[], now: number): FeedState {
  if (!events.length) return feed;
  const next: FeedState = { ...feed };
  for (const e of events) {
    const list = next[e.team];
    const prev = list.find((x) => x.playerId === e.playerId && now - x.at <= FEED_MERGE_MS);
    const entry: FeedEntry = { id: ++next.seq, playerId: e.playerId, name: e.name, team: e.team, count: e.count + (prev?.count ?? 0), at: now };
    next[e.team] = [entry, ...list.filter((x) => x !== prev)].slice(0, FEED_MAX);
  }
  return next;
}

/** Lead flips only once the rope is clear of centre (dead-band) so a wobble around 0 is not a "VIRADA". */
export function leadChange(prev: TeamId | null, rope: number, deadband: number): { lead: TeamId | null; changed: boolean } {
  if (Math.abs(rope) <= deadband) return { lead: prev, changed: false };
  const lead: TeamId = rope < 0 ? "inter" : "gremio";
  return { lead, changed: prev !== null && prev !== lead };
}

export const isFinalSeconds = (remainingS: number, window = 10): boolean => remainingS > 0 && remainingS <= window;
