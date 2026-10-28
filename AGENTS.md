# Local Python engineering rules

- Inspect relevant code, callers, data contracts and tests before editing. Preserve the existing Electron/Python, LCU and OCR architecture; do not invent abstractions, APIs, imports or dependencies.
- Use the project `.venv` interpreter. Read `pyproject.toml` and requirements files first. Check installed versions before using Context7 for uncertain external APIs or version-specific compatibility; ordinary Python syntax needs no documentation lookup.
- Before environment work, distinguish system `python`/`py --list-paths` from `.\.venv\Scripts\python.exe`; inspect `.venv/pyvenv.cfg`, `sys.executable`, `sys.version` and `sys.base_prefix`. The current project environment is Python 3.12.14 from the Codex runtime; the system Python is 3.14.6. `dist/quality-py314` is a separate compatibility environment, not the application environment. Verify these facts again rather than assuming they remain current.
- Preserve a working `.venv`; do not recreate it, downgrade Python or upgrade packages just to match the system interpreter. If `.venv` is absent, verify `py -3.14 --version` and create it with `py -3.14 -m venv .venv`. Install missing check/runtime dependencies from `requirements-quality.txt`, without `--upgrade`. Select the actual `.venv/Scripts/python.exe` through VS Code's Python interpreter picker; a default path alone does not override an existing selection.
- Write readable, maintainable Python with accurate annotations at changed interfaces. Do not add `Any`, blanket casts, `type: ignore`, `noqa`, disabled diagnostics or weakened check settings to hide defects.
- Do not introduce unused variables, unresolved imports, mutable argument defaults or avoidable lint/type errors. Keep fixes focused; no wholesale rewrites, unrelated mass formatting, new frameworks or CI/CD.
- Preserve JSON formats, recommendation decisions, OCR thresholds, polling cadence, UI responsiveness, Windows integrations and fallback behavior unless a demonstrated defect requires change. Add focused regression tests for fixes and behavior changes.
- Catch expected failures narrowly. Existing worker/per-item fault boundaries may catch unexpected exceptions to keep the application alive, but must log them or expose an actionable status. Never silently swallow new errors. Keep diagnostics off stdout: stdout is the Electron JSON protocol. Never log LCU credentials or send reports while testing.
- Root `app.py` loads the two child `app.py` modules under distinct names. Their directories are intentionally on `sys.path` for lazy sibling imports and PyInstaller data modules. Do not rename/package them speculatively; preserve standalone entry points and update `engine.spec` when runtime files are added.
- After each code change, run relevant checks automatically: `.\CHECK.bat --files path/to/file.py --tests path/to/test.py`. Include dependent modules/tests when interfaces change. Before completing a substantial task, run `.\CHECK.bat`, `.venv/Scripts/python.exe app.py --selfcheck` and `git diff --check`. Build/packaged selfcheck is required when packaging/runtime imports change.
- Review safe Ruff fixes and the final diff; never apply unsafe fixes blindly. Preserve existing tests (pytest also collects unittest tests). Fix failures and rerun the affected checks. Do not claim success unless commands actually passed; report unavailable checks and unverified live-game behavior explicitly.
- Do not stop a live game or replace the installed application merely to run source checks. Do not commit, push, publish or add automation unless requested.

Local verification from the repository root in PowerShell (activation is optional):

```powershell
& .\.venv\Scripts\python.exe -VV
& .\.venv\Scripts\python.exe -m pip check
.\CHECK.bat
& .\.venv\Scripts\python.exe app.py --selfcheck
git diff --check
```
