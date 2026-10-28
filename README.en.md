# ARAM Mayhem Helper — English

[Home](README.md) · [Türkçe](README.tr.md) · **English**

A local Windows overlay for League of Legends **ARAM Mayhem**. A Python engine reads game state and augment offers; an Electron interface displays recommendations. No Overwolf or separate companion-service account is required. The interface and game item/augment names are in English; use an English game client for the current OCR path.

## Origin and local contributions

The original project was created by **Joltarise / CyberKird**: [original repository](https://github.com/CyberKird/aram-mayhem-helper). This working copy belongs to the [ravidulundu fork](https://github.com/ravidulundu/aram-mayhem-helper). Original architecture and features remain attributed to their author; local work is documented separately and is not an official upstream release. The main README remains Romanian, the language of the original documentation.

Local contributions include English interface text, taskbar access, six-slot planning and item compatibility safeguards, adaptive counter-item candidates, clearer augment-statistics explanations, atomic data updates, ETag-cache and player/team fallback fixes, and the local quality workflow. English and Turkish documentation accompany the Romanian main README.

These changes have not been published as a fork release. The displayed version may still be `2.0.7`; that number alone does not identify local modifications. On the development machine, the desktop shortcut now uses the verified local engine with `--no-update`, and the previous engine and shortcut are backed up. That machine-specific installation does not change upstream installers or install these modifications on another computer.

Track fork-specific problems in the ravidulundu fork. The existing report form still uses the original author's address; this fork does not imply their support or endorsement.

## Features

- Champion-select tiers for your assigned champion, personal cards detected by OCR and the shared bench, with the best available pick highlighted.
- Champion win/pick rates, patch comparisons and balance modifiers where data is available.
- An item plan capped at six target entries, including boots; already-owned items and augment-required purchases are considered.
- Counter-item rules based on enemy purchases and champion composition. MR-purchase rules use percentage magic-penetration candidates.
- Compatibility checks between planned items, with exceptions for supported augment quests and stackable items.
- Team anti-heal checks across healing-counter rules, plus item transformation tracking.
- Champion-specific augment tiers, OCR offer badges, and manual confirmation when a selected augment cannot be inferred reliably.
- Stat Anvil shard recommendations, Elixir timing and manually selected Headliner explanations.
- Elixir of Iron / Sorcery / Wrath costs 500 gold, requires level 9 and lasts three minutes. Timing considers gold, completed items and game time; `ingame-app/elixir.py` contains the rules.
- A taskbar-visible main panel. `Ctrl+Alt+Z` or the `_` button collapses it to its title bar; `X` closes the application. The diamond button resets panel position.
- A bug-report dialog with optional diagnostics that can be reviewed before sending.

## Where recommendations come from

The Python engine (`app.py`) handles logic and OCR; Electron (`ui/`) starts it as a child process and exchanges JSON over stdin/stdout. Coordinates use physical pixels and the UI converts them per monitor. The HUD frame comes from the game atlas; Beaufort/Spiegel fonts are downloaded from CommunityDragon on first use, with a system-font fallback.

| Input | Source and use |
| --- | --- |
| Mayhem builds, summoner spells, champion statistics and augment/item statistics | ARAMKit; prepared by `ingame-app/update_aramkit.py` and stored as local JSON files/bundles. |
| Champion-select tier list | u.gg, through `lcu-app/update_tier_list.py`. |
| Champion select | Local League Client API (LCU); port and credentials are discovered from `LeagueClientUx.exe` process arguments. |
| Players, inventories, gold, level and attack range | Riot Live Client Data API at `https://127.0.0.1:2999/liveclientdata`. |
| Offered augments | Windows OCR applied to regions of the game window. Selection can also be inferred from observed changes or confirmed manually. |
| Item rules and augment requirements | Local JSON configuration and Python rules. |
| Icons, textures and fonts | Riot Data Dragon / CommunityDragon; fonts are downloaded on demand, with a system-font fallback. |

The resolver starts with a prepared champion build. It filters unavailable items, prioritizes augment requirements, then chooses situational items using counter rules, augment-conditioned win rates, supported on-hit/crit preferences and source order. It is a rule-based recommendation system, not a trained optimizer of every possible build. Combined-stat explanations name all contributing augments and identify the value as an average of conditional statistics. It is not a measured joint-combination win rate or the probability of winning your current match.

New data exports preserve sample counts in an optional `augment_samples` map without changing the existing three-value statistic rows. The resolver uses sample-weighted averages when those counts exist; older bundles retain equal-weight averaging. The current bundled data does not contain these sample counts.

## Installation and launch

### This checkout

The changes described here are local development changes, not a published installer release. To run them from source:

1. Download/clone the repository into a writable directory.
2. Run `INSTALL.bat`. It attempts to install missing Python/Node.js through winget, prepares `.venv` and Electron dependencies, runs selfcheck and creates a desktop shortcut.
3. Launch with `START.bat` or the shortcut. `START.bat` invokes the installer when required runtime files are missing.

The batch installer does not pin the Python interpreter. Preserve an existing working `.venv`. On this machine the project environment is Python 3.12.14 from the Codex runtime, while PowerShell defaults to Python 3.14.6. The separate `dist/quality-py314` environment is for compatibility testing. Only if `.venv` is missing, create it with the available Python 3.14 interpreter. Manual setup from the repository root in PowerShell:

```powershell
if (-not (Test-Path .venv/Scripts/python.exe)) {
    py -3.14 -m venv .venv
}
.venv/Scripts/python.exe -m pip install -r requirements.txt
Push-Location ui
npm ci
node node_modules/electron/install.js
Pop-Location
./START.bat
```

The explicit Electron install command is useful if npm policy skipped its install script. Windows OCR must have a usable English language engine. Installer console output may still be in Romanian.

### Existing upstream releases

The original project's [releases](https://github.com/CyberKird/aram-mayhem-helper/releases) provide `ARAM-Mayhem-Helper.exe`. Those installers may not include the local changes documented here. Packaged applications keep settings, logs and synchronized data under `%APPDATA%/ARAM Mayhem Helper`.

## Updates and offline behavior

- Binary updates still use **CyberKird/aram-mayhem-helper**. A newer upstream binary can replace local modifications. `--no-update` skips automatic binary update checks for that launch; it does not disable data synchronization.
- `data_sync.py` checks the original repository at startup and every 30 minutes for tier, champion-stat and Mayhem-bundle files. The included GitHub workflow schedules ARAMKit data generation daily, subject to successful workflow execution.
- Downloaded data is validated and written atomically; older local revisions are not replaced by older downloads. Failed downloads leave the previous usable data available.
- Build bundles are reloaded when files change, and the active champion build can refresh without restarting. Champion tier/stat module snapshots retain their existing lifecycle; not every data source refreshes live. Catalog-based candidate expansion is disabled when the bundle patch differs from the shipped catalog/constraint patch.
- Bundled/cached data can be used offline. Font downloads, fresh statistics, application updates and report delivery require network access.

Configure your own release/data channels before distributing a maintained fork. Changing documentation alone does not change those endpoints.

## Verification

Install local check tools once, then run the complete suite from the repository root:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-quality.txt
.\CHECK.bat
```

This runs Ruff lint, Ruff formatting verification, Pyright and pytest with the project interpreter. Any failed step makes the command fail. For a small change, use `.\CHECK.bat --files data_sync.py --tests test_data_sync.py`. Existing unittest tests remain supported by pytest. `AGENTS.md` requires relevant checks after code changes and the complete suite before substantial work is declared complete. VS Code defaults to `.venv` and resolves both local module directories.

The project environment is Python 3.12.14. A separate Windows Python 3.14.6 environment also passed the full quality suite and native OCR selfcheck with the currently resolved dependencies. No interpreter downgrade or environment replacement was performed. VS Code's saved interpreter selection was verified as `.venv/Scripts/python.exe`; a default path alone does not override an existing selection. This does not certify every version permitted by the runtime minimum requirements. See [quality audit](docs/quality-audit.md) for scope and limitations.

Run from the repository root in PowerShell:

```powershell
.venv/Scripts/python.exe -m unittest test_data_sync
.venv/Scripts/python.exe -m unittest discover -s ingame-app -p "test_*.py"
.venv/Scripts/python.exe app.py --selfcheck
```

These tests cover atomic update failure, invalid/older data, live bundle replacement, six-slot planning across the local champion catalog, cross-champion counter expansion and inventory scenarios, planned-item exclusions, MR/armor/health counters, team anti-heal, full-build sales, damage conversion, stack/quest priority and statistics explanations/compatibility. Selfcheck also exercises native OCR on a generated image and checks icon/data coverage; it does not require a running match.

The latest local validation passed 41 pytest tests (including 29 recommendation tests and 3 data-sync tests), 178 unittest subtests, six renderer scenarios and the badge/report checks. The recommendation matrix covers 173 champions across 1,038 enemy/inventory scenarios. These are validation results, not a guarantee for every game state. The updated resolver has not yet been validated in a live match.

To generate UI fixtures and launch the mock engine:

```powershell
.venv/Scripts/python.exe ui/test/make_scenarios.py
$env:ARAM_MOCK = (Resolve-Path ui/test/game1080.json).Path
Push-Location ui
npx electron .
Pop-Location
Remove-Item Env:ARAM_MOCK
```

The mock engine does not send bug reports. Generated fixture files are development output.

## Regenerating data

These commands overwrite generated JSON data; review the resulting diff. Run them outside a live match.

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe ingame-app/update_aramkit.py
.venv/Scripts/python.exe ingame-app/build_icons.py
```

ARAMKit updating uses HTTP and does not require a browser. Updating the separate u.gg champion tier list uses Playwright:

```powershell
.venv/Scripts/python.exe -m playwright install chromium
.venv/Scripts/python.exe lcu-app/update_tier_list.py
```

Older u.gg scraping utilities remain in the repository. They are not the primary current Mayhem item-build pipeline. Avoid overwriting Mayhem item data with a classic-ARAM generator unintentionally.

## Building the Windows application

Run the source tests above first. For a release, set `ui/package.json` to the intended release version before building; a local verification build does not by itself publish a release.

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m PyInstaller engine.spec --noconfirm --clean
dist/aram-engine/aram-engine.exe --selfcheck
Push-Location ui
npm ci
npx electron-builder --win nsis --publish never
Pop-Location
```

Stop if a command fails. Engine output is `dist/aram-engine`; installer output is `dist/ARAM-Mayhem-Helper.exe`. The spec includes the development runtime's extra SSL data file when present. For a deliberately published auto-update release, the installer, `.blockmap` and `latest.yml` must belong to the same version and configured update channel.

## Limitations and reports

- OCR can miss or misread offers. English OCR and generated fixtures were checked; other client languages and every resolution are not guaranteed.
- Augment choices are observed/inferred rather than read from a dedicated selected-augment API. Manual confirmation remains important.
- Recommendations expand the prepared build with compatible counter-items from a patch-matched Mayhem shop catalog. Build profiles follow owned/core item stats and supported damage-conversion augments. These are hand-written heuristics, not a simulation of every teamfight or augment combination.
- Missing tiers are not replaced with invented ranks. Public data availability and data freshness limit coverage.
- The bug button is an insect icon. Reports still go to the original author's `contact@joltarise.com` through FormSubmit. Email is optional; the dialog offers diagnostics for review and a mail fallback if delivery fails. No screenshot is attached by the report code.
- The main window can receive focus; the small overlay badges remain non-focusable.

## Project layout

```text
app.py                         Engine entry point and JSON state protocol
bug_report.py                  Report validation, diagnostics and delivery
data_sync.py                   Atomic data downloads and revision checks
engine.spec                    PyInstaller engine packaging
ui/main.js                     Electron windows, positioning and updater
ui/renderer/                   Main panel, badges, tooltips and report UI
ui/test/                       Mock engine and fixture generator
lcu-app/                       LCU access and champion-select data
ingame-app/live_client.py       Live match data access
ingame-app/decision_trace.py    Local decision journal and offline replay
ingame-app/item_costs.py        Observational item completion-cost comparison
ingame-app/rules_engine.py      Item selection and purchase/sale rules
ingame-app/bundle.py            Validated build-bundle cache and reload
ingame-app/update_aramkit.py    Current Mayhem data generator
ingame-app/test_recommendations.py  Resolver and bundle regression tests
ingame-app/test_item_costs.py    Recipe and cost-comparison regression tests
test_data_sync.py              Download/write regression tests
test_decision_evidence.py      Recovery, journal and replay regression tests
overwolf-app/                  Historical alternative implementation
```

The active desktop entry point is the root `app.py` plus `ui/`.

## Local decision evidence and recovery

The source engine now keeps the last known state during short Live Client API outages. It marks a failed read immediately, stops recalculating advice while data is unavailable and hides purchase advice after 12 seconds without a successful roster read. After 30 seconds without data and with no game window, it resets the session. A game-clock rollback also clears the previous game's selections. These thresholds describe recovery behavior, not a guaranteed four-second update deadline.

When a decision or its delivered purchase advice changes, the desktop engine writes local JSONL evidence in `%APPDATA%/ARAM Mayhem Helper/decision-logs` (or `ARAM_HOME/decision-logs`). Running the Python engine directly defaults to `decision-logs` in the checkout. Each entry contains captured resolver inputs/data, chosen augments, game time, output, a decision/session identifier and the build sent through stdout. It excludes the player's Riot ID and LCU credentials. This proves engine delivery, not successful rendering on screen.

Disk writes use a bounded background queue. Retention is at most four 8 MiB files; overflow/write errors are reported on stderr and in panel status. Files can contain truncated final lines after an abnormal exit. Offline replay reports malformed lines and recommendation differences with a nonzero exit code; it uses captured data with the current resolver and makes no game/API requests:

```powershell
.venv/Scripts/python.exe ingame-app/decision_trace.py "$env:APPDATA/ARAM Mayhem Helper/decision-logs/decisions.jsonl"
```

This feature requires the updated source engine (`START.bat`) or a newly built engine. On the development machine, the existing desktop shortcut now opens this checkout's Electron runtime and `.venv` engine with `--no-update`; subsequent verified source changes take effect on the next launch without running a batch file or reinstalling. An already-running process needs a restart outside a game. The original shortcut is backed up under `dist/backup-desktop-source-2026-10-28`, and installed binaries remain intact. This is a local setup, not a GitHub automatic-update channel. Logs are bounded diagnostic evidence, not a complete purchase history or a guarantee of optimal recommendations.

Decision records also carry versioned `extra.live_context`: current-response level/gold, documented numeric local champion stats and anonymous per-player inventories with item IDs, slots and counts. Missing scalar values are `null`, missing stat fields are omitted and unavailable inventories are `null`; zero remains a real observed value. Snapshot indices are not stable player identities. The existing ranking ignores this observational context, and older schema-1 records still replay. Enemy detailed champion stats are not inferred, and separate API responses are not an atomic game snapshot. Recording frequency can increase as live stats change; retention remains bounded. Running instances need a restart outside a match to load this change.

The data-usage audit and verified Mayhem description, gold-parsing and mana-label fixes are documented in the [technical report](docs/recommendation-data-audit.md). These fixes do not introduce a new item-ranking model.

Records with recipes optionally include `cost_comparison`: full nominal price, owned-component credit, remaining gold and shortfall against observed gold. Alternatives are evaluated independently; the cheapest completion does not change recommendation order. Missing, cyclic, unverified or patch-mismatched recipes produce unknown quotes rather than assumed free items. Replay verifies this field when present and remains compatible with older logs. Discounts, shop availability and purchase-slot feasibility are not simulated.

## Attribution and license

Original author: **Joltarise / CyberKird**. [Original project](https://github.com/CyberKird/aram-mayhem-helper) · [Support the original author](https://ko-fi.com/joltarise).

See [LICENSE](LICENSE), which contains GNU GPL version 3; the original README declared GPL-3.0-or-later. `ui/package.json` currently has an `UNLICENSED` metadata value, so packaging metadata and upstream licensing statements are not aligned. No license or authorship change is made by this documentation update. Third-party statistics, fonts and game assets remain subject to their owners' terms.

This is an unofficial project and is not affiliated with or endorsed by Riot Games. See the [Riot developer documentation and policies](https://developer.riotgames.com/docs/lol) before distributing a derivative product; no approval status is claimed here.
