# Adaptive item candidates

Approved goal: recommendations must adapt across all champions and future Mayhem matches rather than only the supplied Kassadin match.

Keep the existing resolver contract and six-slot, inventory, quest, range and exclusivity safeguards. Add source-backed shop metadata, derive the active damage/build profile from owned/core items with champion metadata as fallback, and evaluate compatible complete counter-items outside the original champion pool. Preserve augment requirements and use existing augment-conditioned evidence; do not claim to simulate every augment mechanic or calculate an optimal win probability.

- [x] Add failing cross-champion counter, alternate-build, coverage, owned-item and explanation tests.
- [x] Generate a versioned item catalog from the same ARAMKit patch and retain it in future data imports.
- [x] Expand and rank compatible counter candidates, prevent redundant category picks and prioritize situational purchases ahead of remaining generic targets.
- [x] Correct aggregate-stat explanations without implying joint-combination win rates.
- [x] Run regression/selfchecks, replay supplied match, exercise all champion/situation combinations, obtain independent review, and verify a packaged build before replacing the installed engine.

Validation limits: post-match data does not reproduce purchase timing; scenario tests establish constraints and stated heuristic behavior, not optimal real-game decisions. No new UI, champion-specific patches, publication, or change to the upstream update channel.

Verification (2026-10-28): 29 recommendation tests and 3 sync tests passed; the matrix covers 173 champions in 1,038 enemy/inventory scenarios. Six renderer fixtures plus badge identity and report validation checks passed. Source, packaged and installed selfchecks passed; Python compilation and git diff --check completed without errors. No configured lint/type checker was found. Independent review found malformed catalog categories could crash candidate expansion; a failing regression test reproduced it and string validation fixed it. Other reviewed inventory, quest, sale, exclusivity and patch-gating paths had no remaining concrete important findings.

Installed all engine files match the verified build by SHA256. Previous engine retained at dist/backup-adaptive-items-2026-10-28/engine. English idle panel verified League Client RUNNING. Launched with --no-update for this session. No live game was interrupted; LCU phase was Lobby. Live match validation remains outstanding.

Supplied match final-snapshot reconstruction retains four completed owned targets and recommends Morellonomicon then Liandry's Torment. This is reconstructed output, not a historical recommendation recording. Evidence: dist/adaptive-match-reconstruction.json.

Ruling: keep source-backed heuristic counter coverage within the existing rules; do not claim every augment mechanic or globally optimal purchases. Newer bundle patches disable catalog expansion until matching constraints are shipped. No publication or upstream update-channel change was made.
