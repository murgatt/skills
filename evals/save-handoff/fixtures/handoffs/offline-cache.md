# Decision: SQLite façade for offline notes

Date: 2026-09-20

## Context

The app currently keeps offline notes in `localStorage`, which caps out around 5 MB and blocks the main thread on every write.  Users with >2k notes hit the cap.

## Options considered

### Option A: IndexedDB via idb-keyval
* Pros: zero deps beyond a tiny wrapper
* Cons: no queries, we'd reimplement search

### Option B: SQLite (wa-sqlite + OPFS)
* Pros: real queries, FTS5 for search
* Cons: ~900 KB wasm, needs COOP/COEP headers

## Decision

Option B — wa-sqlite with the OPFS backend, running in a dedicated worker.

## Rationale

Search was the deciding factor; reimplementing it on top of IndexedDB was estimated at more work than the header change.

## Implementation notes

- Worker entry: `src/db/worker.ts`
- Schema v1:

```ts
CREATE TABLE notes (id TEXT PRIMARY KEY, body TEXT, updated_at INTEGER);
```

- migrate existing localStorage data once, on first boot , then clear it

## Open questions

- Do we need a fallback for Safari < 17 (no OPFS sync handles)?
