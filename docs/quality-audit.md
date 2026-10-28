# Local quality audit — 2026-10-28

Scope: the Windows Python engine, standalone LCU/in-game tools, data generators, existing Overwolf Python scripts and UI fixture generators. Existing English UI and adaptive-item changes were already present and were preserved. No CI/CD, new application framework, publication or installed-application replacement was added.

## Environment and baseline

- Project `.venv`: CPython 3.12.14, 64-bit Windows. System `py` defaults to Python 3.14; that environment initially contained checking tools but lacked application dependencies.
- Root `pyproject.toml` was empty; there was no repository `AGENTS.md` or editor interpreter configuration. Existing unittest tests and `app.py --selfcheck` were retained.
- Initial unscoped Pyright also inspected generated/copied code under `dist` and `build`. These are now excluded as build artifacts, not used to hide source diagnostics. Correctly scoped source baseline: 59 type errors, zero warnings. Initial Ruff baseline: 85 findings; formatting baseline: 36 files needed formatting. Project-interpreter pytest baseline: 32 tests and 178 subtests passed.
- Tools: Ruff 0.16.5, Pyright 1.1.411, pytest 9.2.0, with pinned requests/psutil/pywin32 stubs. Runtime `pip check` passed. Optional CustomTkinter/Tcl and Playwright imports also passed on both Python versions.

## Findings and changes

- Three entry points are intentionally named `app.py`. Root `_load_page` imports the child pages by distinct module names and adds their directories for lazy sibling imports. Static execution environments now describe those same paths; the loader validates its spec/loader and avoids duplicate path entries. No package rename or speculative import rewrite was needed.
- Type failures came from optional module specs, mode-agnostic Pillow stubs, initially empty OCR caches, heterogeneous geometry dictionaries and untyped selfcheck keyword dictionaries. Accurate geometry/OCR/callback signatures, cache types, explicit selfcheck arguments and assertions resolved those diagnostics. The one Pillow cast describes an image already created as RGBA; it does not mask uncertain runtime input.
- Existing long-lived worker and per-item fault boundaries remain fault tolerant and now log unexpected failures through module loggers. Logs go to stderr; the Electron stdout JSON protocol remains unchanged. Existing status/error fields remain intact. Expected LCU timeouts continue returning `None`.
- A non-object ETag cache (`[]`, for example) previously caused every sync attempt to fail before downloading. The cache is now validated, invalid entries are discarded and usable downloads continue. A failing regression test reproduced the defect before the fix.
- With no `/activeplayername`, comparisons against missing name fields could identify unrelated players as local, bypass the intended fallback and return the wrong champion/team. The fallback now re-resolves the team and requires a nonempty matching identity. A failing regression test reproduced the wrong-champion result before the fix.
- Mutable class fixtures are explicitly shared where intentional; per-instance mutable fixture state was moved to initialization where reassigned. No mutable function-argument defaults were found. Safe Ruff fixes were reviewed; unsafe automatic fixes were not enabled. Python formatting was normalized once to make full formatting verification usable; application JSON, UI styling and game data were not reformatted by this audit.
- `requirements-quality.txt`, `quality.py` and `CHECK.bat` provide full or focused local checks. A regression test verifies that any failing checker causes a nonzero result. `AGENTS.md` makes automatic relevant checks and final full checks mandatory for future Codex work.

## Verification

| Check | Result |
| --- | --- |
| Ruff lint and formatting | Passed |
| Pyright standard, all configured source | 0 errors, 0 warnings |
| Pytest, Python 3.12 and separate Python 3.14 | 41 tests + 178 subtests passed on each |
| Native OCR/data/engine selfcheck on Python 3.12 and 3.14 | Passed |
| PyInstaller 6.22.3 build and packaged selfcheck | Passed |
| UI fixtures | Six renderer scenarios plus badge identity and report validation passed |
| Dependency consistency and optional GUI imports | Passed on both Python versions |
| Independent read-only review | No concrete important regression found; 41 tests + 178 subtests passed independently |

Run full checks from PowerShell with `.\CHECK.bat`. For a small change: `.\CHECK.bat --files data_sync.py --tests test_data_sync.py`. Source runtime check: `.venv/Scripts/python.exe app.py --selfcheck`. For packaging changes, build with `.venv/Scripts/python.exe -m PyInstaller engine.spec --noconfirm` and run `dist/aram-engine/aram-engine.exe --selfcheck`.

The current Python 3.14 runtime dependency versions include Pillow 13.0.0, psutil 7.2.2, requests 2.34.2, mss 10.2.0, pywin32 312 and WinRT runtime 4.0.3 / SDK packages 4!10.0.28000.2705. This is a tested dependency resolution, not a guarantee for every lower-bounded version. PyInstaller's documented Python 3.14 support starts at 6.15; the development minimum was corrected accordingly. References checked through Context7: [Pyright configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md), [Pillow constants](https://github.com/python-pillow/Pillow/blob/main/docs/deprecations.rst), [PyInstaller changes](https://github.com/pyinstaller/pyinstaller/blob/v6.22.3/doc/CHANGES.rst).

## Limits

- No remaining diagnostics in the configured standard suite; this is not a claim of strict typing of every dynamic JSON value or dynamically loaded module. No diagnostic suppressions were introduced. Pyright's Python wrapper may print a newer-tool-version notice; that is separate from its zero source warnings.
- PyInstaller retains its usual analysis list of optional/platform-specific modules (for example POSIX modules and optional SSL backends). The packaged selfcheck passed; optional backends were not enabled merely to remove analysis notices.
- A generated OCR image and mocked window/LCU failures verify particular paths, not live-match OCR accuracy, full-screen focus transitions, or every display setup. No live game was started/interrupted. The renderer harness checks DOM behavior, not every pixel or frame-time characteristic.
- Python 3.14 passed source checks; the executable was built with the existing Python 3.12 project environment. No Python 3.14-frozen build or full Electron installer was produced in this audit. The installed application was not changed.
