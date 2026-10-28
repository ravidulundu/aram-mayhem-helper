# Live decision context

> Execute inline with superpowers:executing-plans and test-driven-development. No commit, installation or live-process restart.

**Goal / agreed design:** Carry existing live evidence to the resolver and journal without changing item ranking. Keep all legacy roster fields and schema-1 journal replay. Add a versioned `extra.live_context` containing the current response's level, gold, numeric champion stats and anonymous player inventory snapshots. Missing fields stay unknown; stale active-player values must not masquerade as fresh evidence.

**Architecture:** Extend existing `live_client.py` with small typed snapshot definitions and sanitizers. Preserve per-player item IDs, labels, slots and counts while retaining flat item lists. `normalize_roster` translates champion aliases without mutating snapshots. Monitor accepts context under its existing lock, clears it on reset, and supplies it through the existing extra mapping. The resolver continues ignoring this optional context. No new API requests, polling changes or dependencies.

**Files:** `ingame-app/live_client.py`, `ingame-app/app.py`, regression tests in `test_decision_evidence.py` / `test_runtime_quality.py`, and matching RO/EN/TR documentation.

**Constraints:** Use `.venv`; no Any/ignore/noqa shortcuts, no new scoring weights, no credentials or player names in recorded context. Player indices identify positions in one snapshot, not stable cross-poll identities. Numeric champion stats are those exposed for the local player; no inferred enemy armor/HP totals. Keep record retention bounded.

## Tasks

- [x] Red tests: existing flat lists preserved; per-player ownership/count/slot retained; no identities; aliases handled without mutation; missing/nonfinite/boolean values not treated as numbers.
- [x] Implement typed snapshots, optional live context and reset/failure behavior.
- [x] Test journal round-trip, old records without context, unchanged resolver output across the champion matrix and available Kayle records.
- [x] Update matching user guidance; full CHECK, source selfcheck, diff check and packaged selfcheck if runtime imports change.
- [x] Independent review; fix concrete findings and rerun affected checks.

**Results:** Full CHECK passed (Ruff lint/format, Pyright zero diagnostics, 71 tests and 178 subtests). The 173-champion matrix retains outputs across 1,038 situation/inventory cases with optional context. All 86 available historical Kayle records replay unchanged; an additional synthetic-context compatibility probe also had zero output differences and was not written back to the logs. Source selfcheck, PyInstaller build, packaged selfcheck, README parity and diff whitespace checks passed.

**Review:** Missing/unknown participant teams were initially marked as enemies in new snapshots. A failing regression test reproduced this; the new snapshot now records `unknown` unless both team values are documented ORDER/CHAOS values. Existing flat-list behavior was preserved. Independent re-review found no further important issue in scope.

**Limits:** No live match was started or interrupted and no running app was restarted. This is observational data, not a new ranking model. API reads are separate, player indices are per snapshot, detailed enemy stats are unavailable, and higher capture frequency still obeys bounded retention. Raw stat units are recorded without conversion. Numeric fields not in the documented allowlist are not copied. Desktop source mode loads the changes on its next normal launch; installed binaries were not replaced.

**API reference checked through Context7:** [Riot Live Client Data API](https://developer.riotgames.com/docs/lol/index#game-client-api_live-client-data-api), installed Requests 2.34.2; no dependency or HTTP API changes were required.
