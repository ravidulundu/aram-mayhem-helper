# Recommendation correctness implementation plan

**Goal:** Produce valid six-slot item plans, consistent counters, sample-aware augment scores and safely refreshed build data.

**Architecture:** Keep the existing Python resolver and JSON contracts. Extend augment rows with an optional sample count, preserve legacy rows, and reload versioned build data through its existing accessor. Preserve translated UI and the installed rollback copies.

**Approved scope:** User approved the preceding source-backed findings. No new build-selector UI, cloud services or releases.

- [x] Reproduce slot overflow, exclusive planned items, MR counter selection and duplicate team anti-heal with regression tests.
- [x] Enforce plan capacity and exclusivity while preserving augment quest exceptions and item identities; run existing selfcheck.
- [x] Retain sample counts in new exports and weight available evidence; test legacy data compatibility.
- [x] Write synchronized data atomically, reload validated newer bundles and refresh the champion build through the existing accessor; test failed downloads and replacement.
- [x] Verify all champion plans and renderer scenarios, build the engine, verify packaged runtime, and install with a rollback copy.

Review focus: owned items, quest combinations, stackable items, missing statistical evidence, failed file writes and unchanged UI contract.

Verification: 3 sync tests, 9 recommendation tests, all 173 normal champion plans, 276 augment/inventory scenarios, six renderer scenarios, source and packaged selfchecks passed. Independent review findings on stack priority, record validation and old-reader compatibility were fixed and re-reviewed.

Ruling: Keep the historical three-value augment rows and add a separate optional `augment_samples` map. Existing downloaded bundles have no sample counts and retain their historical equal-weight behavior until enriched data is available.

Ruling: Only build-bundle data reloads live in this change; champion tier/stat module snapshots retain their existing lifecycle. No claim of live refresh for every data source.

Installed engine hash matches the verified build. Live idle panel shows League Client RUNNING. Rollback: `dist/backup-recommendations-2026-10-27/engine`. Live match validation remains unperformed.

Repeat checks:
```powershell
.venv/Scripts/python.exe -m unittest test_data_sync
.venv/Scripts/python.exe -m unittest discover -s ingame-app -p test_recommendations.py
.venv/Scripts/python.exe app.py --selfcheck
dist/aram-engine/aram-engine.exe --selfcheck
```
