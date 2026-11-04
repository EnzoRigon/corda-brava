# Task 13 Report — usePullBuffer

**Status:** DONE  **Commit:** 8627ee8

## Signature
`usePullBuffer({matchId, playerId, playerToken, flushIntervalMs, enabled?}) -> {displayCount, tap}` in `frontend/src/hooks/usePullBuffer.ts`. Also exports `MAX_PULLS_PER_BATCH = 200` (mirrors prompt.md / settings).

## Retry / idempotency design
"Merge back" is implemented as keep-the-same-batch: a flush snapshots pending into `{count, batchId}` (fresh UUID), held as `unacked` until 2xx. On network error/5xx the same batch (same batchId, same count) is resent on the next flush before any new batch is built. Counts are never merged into a new batchId, so a request that reached the server with a lost response is deduped, not double-counted. One in-flight request at a time. Batches clamp to 200; excess stays pending for the next flush.

## Status codes
401/403/409: batch dropped, no retry (bad token / match not running; screen logic takes over). Everything else keeps the batch.

## Beacon
On `visibilitychange` (hidden) and `pagehide`: sends the unacked batch (or a new one from pending) via `navigator.sendBeacon(url, Blob application/json)`, falling back to `fetch(..., {keepalive:true})`. The batch stays unacked (beacon can't confirm), so the next flush resends the same batchId; server dedup makes this safe. Only one batch per hide event; any excess flushes later.

## Constants
`MAX_PULLS_PER_BATCH=200`; interval is a caller parameter.

## Checks
`npm test -- --run` 13/13 pass (6 new); `tsc --noEmit`, `npm run build`, `npm run lint` clean.

## Deviations
- No @testing-library; harness is react-dom/client createRoot + act.
- Beacon URL built as `API_BASE + /api/matches/{id}/pulls` since playerApi exposes no URL helper (its `m` is private); sendPulls is reused for normal flushes.
- Tests were written together with the implementation; red-run not separately observed.
