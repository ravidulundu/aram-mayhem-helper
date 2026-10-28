# Decision evidence and live-data recovery

> Execute inline with superpowers:executing-plans; no commits or installation in this task.

**Goal:** Explain and reproduce the recommendation sent to the UI without changing gameplay rules.

**Design:** Capture detached resolver inputs and outputs as one decision. The engine associates this decision with the UI build it successfully sends. An asynchronous bounded JSONL journal keeps self-contained records locally; offline replay compares the same resolver against the recorded output. No player identity or credentials are recorded.

**Constraints:** Preserve the existing Python/Electron architecture, stdout protocol, polling cadence and recommendation rules. Use the existing environment and standard library. Keep at most four 8 MiB log files; a bounded queue reports overflow and write failures. Logs represent engine-to-UI delivery, not proof of pixels being rendered.

**Recovery:** Keep the last successful state across brief API outages. Mark unavailable data immediately, expire recommendations after 12 seconds, and prevent recomputation while unavailable. Reset after at least 30 seconds of missing data and an absent game window; also detect a new game's clock rolling back. Preserve chosen augments on same-game recovery.

**Files:** `ingame-app/decision_trace.py` for serialization, journal and replay CLI; `ingame-app/app.py` for recovery and detached decisions; root `app.py` for journal/UI association; regression tests; three root READMEs for matching user guidance. The trace module is included in `engine.spec` alongside dynamically loaded sibling modules.

## Tasks

- [x] Write failing tests for outage/recovery, expiration, game transitions, recorded-input replay, bounded retention, queue/write failure and privacy.
- [x] Implement recovery and immutable decision capture, retaining all public interfaces.
- [x] Connect asynchronous journal to successful engine state delivery, and add offline replay command.
- [x] Update Romanian, English and Turkish documentation consistently.
- [x] Run focused checks, complete quality suite, source selfcheck, build and packaged selfcheck; inspect final diff.

**Evidence:** Full CHECK passed: Ruff lint/format, Pyright zero diagnostics, 57 tests and 178 subtests. Source and packaged selfchecks passed; PyInstaller build passed. Independent review found two edge cases, both reproduced and fixed: missing game-time reads before rollover, and reset during OCR application. A further regression test preserves catalog insertion order during capture/replay. Installed desktop files were not replaced; live-match rendering/OCR remains unverified for this patch.

## Review focus

Late OCR callbacks must not regenerate advice from unavailable live data. Recorded input must be detached from mutable worker state. UI output and recorded decision must share one snapshot. Logging failure must not stop stdout or the monitor. Replay must use captured data, not today's downloaded bundle. A new session must not inherit the previous game's augments.
