# Item cost comparison

> Execute inline with executing-plans and test-driven-development. Do not restart a live app, install, commit or publish.

**Goal/design:** Record an independent nominal-price comparison of the existing resolver's unowned target items. Reuse `remaining_gold` after validating the captured recipe graph; do not change live ranking, quest priorities, sell advice or UI. The cheapest completion is a cost observation, not a recommendation.

**Contract:** Optional schema-1 `cost_comparison` in decision records. Include full price, component credit, remaining price, wallet shortfall and whether observed gold suffices at nominal prices. Unknown/malformed/cyclic/inconsistent recipes and mismatched known data patches yield unknown quotes, never zero-priced guesses. Unknown wallet stays unknown. Each alternative starts with its own inventory copy; credits are not additive across alternatives. A held copy of the same target cannot pay for an additional stackable copy. Existing finished items can still be recipe components for a different upgrade.

**Implementation:** New `ingame-app/item_costs.py`; integrate in `decision_trace.record/replay`; include the new runtime file in `engine.spec`. Preserve old records without this field. No external libraries/APIs or price downloads. Captured recipe prices are nominal: discounts, shop availability and purchase-slot feasibility are outside this comparison.

**Review ruling:** The source generator could erase missing prices/components before validation. Keep its legacy `gold/from` estimates for existing consumers, but attach `cost_status=unverified` and warnings for incomplete/ambiguous source data. The new comparison rejects these estimates. Dropping entries was rejected after a red regression demonstrated that legacy `remaining_gold` would then return zero. Current 197 source recipes regenerate identically; no active price data was rewritten.

- [x] Red tests for nested/shared components, duplicates, stackable copies, aliases, unavailable/malformed/cyclic recipes, unknown gold, and unchanged inputs.
- [x] Implement comparison, optional journal field and replay validation; targeted checks.
- [x] Compare actual Kayle snapshots, documenting cost facts without inferring missing historical gold.
- [x] Update RO/EN/TR guidance; full CHECK, selfcheck, build and packaged selfcheck, final diff and independent review.

**Results:** Full CHECK passed: Ruff lint/format, Pyright 1.1.414 zero diagnostics, 93 tests and 178 subtests. Source and packaged selfchecks, PyInstaller build, pip check, README parity and diff whitespace checks passed. All 86 Kayle records replay unchanged with 398 known target quotes; the current 197 source recipes regenerate identically. Independent review's two source-data issues were reproduced and addressed; final review reported no further important finding.

**Limits:** Cost-only observations do not establish combat value or optimal purchase order. Live-game capture of this new field has not been verified; no running game/app was restarted. Legacy consumers still use nominal estimates for unverified recipes; those estimates are not trusted by this comparison. Shop discounts, active affordability adjustments, and inventory-slot feasibility need their own verified mechanics before they can drive ranking.

**Verification ruling:** The user redirected an intervening Pylance complaint back to this task and explicitly said VS Code is not important. Keep the verified explicit collection annotation and Pyright 1.1.414 pin; use CLI checks for this continuation without additional editor automation.
