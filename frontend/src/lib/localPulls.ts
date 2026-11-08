const key = (matchId: string) => `cb.pulls.${matchId}`;

/** This phone's own tap count for a match (the End screen reads it; no server analytics on the phone). */
export function loadPulls(matchId: string): number {
  try {
    return Number(localStorage.getItem(key(matchId))) || 0;
  } catch {
    return 0;
  }
}
export function savePulls(matchId: string, n: number) {
  try {
    localStorage.setItem(key(matchId), String(n));
  } catch {
    // storage blocked: End just hides the count
  }
}
