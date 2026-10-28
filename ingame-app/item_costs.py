"""Nominal recipe-cost observations for existing plan targets; never changes ranking."""

import math
from collections.abc import Mapping
from typing import Literal, TypedDict

import rules_engine

CostStatus = Literal[
    'known',
    'unknown_recipe',
    'invalid_recipe',
    'cyclic_recipe',
    'patch_mismatch',
    'unverified_recipe',
]
Recipe = TypedDict('Recipe', {'gold': int, 'from': list[str]})


class CostRow(TypedDict):
    item: str
    is_current_next: bool
    full_price: int | None
    component_credit: int | None
    remaining_gold: int | None
    gold_shortfall: float | None
    gold_sufficient_at_nominal_price: bool | None
    status: CostStatus


class CostComparison(TypedDict):
    schema: int
    mode: Literal['shadow']
    basis: Literal['nominal_independent_alternatives']
    current_gold: float | None
    current_next: str | None
    lowest_remaining_item: str | None
    nominal_saving_vs_current: int | None
    candidates: list[CostRow]


class _RecipeError(ValueError):
    def __init__(self, status: CostStatus):
        super().__init__(status)
        self.status: CostStatus = status


class _RecipeBook:
    def __init__(self, recipes: Mapping[str, object]):
        self.index: dict[str, object] = {}
        self.conflicts: set[str] = set()
        self.validated: dict[str, Recipe] = {}
        for name, recipe in recipes.items():
            key = rules_engine.item_key(name)
            if key in self.index and self.index[key] != recipe:
                self.conflicts.add(key)
            self.index[key] = recipe

    def validate(self, key: str, path: set[str]) -> Recipe:
        if key in path:
            raise _RecipeError('cyclic_recipe')
        if key in self.conflicts or len(path) >= 64:
            raise _RecipeError('invalid_recipe')
        if key in self.validated:
            return self.validated[key]
        raw = self.index.get(key)
        if raw is None:
            raise _RecipeError('unknown_recipe')
        if not isinstance(raw, dict):
            raise _RecipeError('invalid_recipe')
        if raw.get('cost_status') not in (None, 'verified'):
            raise _RecipeError('unverified_recipe')
        raw_price, parts = raw.get('gold'), raw.get('from')
        numeric_price = _wallet(raw_price)
        if (
            numeric_price is None
            or not numeric_price.is_integer()
            or int(numeric_price) != raw_price
            or not isinstance(parts, list)
            or not all(isinstance(part, str) and part for part in parts)
        ):
            raise _RecipeError('invalid_recipe')
        price = int(numeric_price)
        keys = [rules_engine.item_key(part) for part in parts]
        path.add(key)
        try:
            subtotal = sum(self.validate(part, path)['gold'] for part in keys)
            if price < subtotal:
                raise _RecipeError('invalid_recipe')
            recipe: Recipe = {'gold': int(price), 'from': keys}
            self.validated[key] = recipe
            return recipe
        finally:
            path.remove(key)


def _wallet(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        gold = float(value)
    except OverflowError:
        return None
    return gold if math.isfinite(gold) and gold >= 0 else None


def compare(inputs: Mapping[str, object], result: Mapping[str, object]) -> CostComparison:
    extra = inputs.get('extra')
    extra = extra if isinstance(extra, dict) else {}
    roster = inputs.get('roster')
    roster = roster if isinstance(roster, dict) else {}
    raw_recipes = extra.get('recipes')
    book = _RecipeBook(raw_recipes if isinstance(raw_recipes, dict) else {})
    own = roster.get('own_items')
    inventory = (
        [rules_engine.item_key(n) for n in own if isinstance(n, str)]
        if isinstance(own, list)
        else []
    )
    context = extra.get('live_context')
    gold = _wallet(context.get('current_gold')) if isinstance(context, dict) else None
    bundle_patch, catalog_patch = extra.get('bundle_version'), extra.get('catalog_version')
    mismatch = bool(bundle_patch and catalog_patch and bundle_patch != catalog_patch)
    rows: list[CostRow] = []
    for section in ('core', 'picks'):
        entries = result.get(section)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or entry.get('owned'):
                continue
            name = entry.get('item')
            if not isinstance(name, str):
                continue
            row: CostRow = {
                'item': name,
                'is_current_next': entry.get('next') is True,
                'full_price': None,
                'component_credit': None,
                'remaining_gold': None,
                'gold_shortfall': None,
                'gold_sufficient_at_nominal_price': None,
                'status': 'patch_mismatch' if mismatch else 'unknown_recipe',
            }
            if not mismatch:
                key = rules_engine.item_key(name)
                try:
                    recipe = book.validate(key, set())
                    # A held identical item cannot pay for another stackable copy.
                    available = [n for n in inventory if n != key]
                    remaining = rules_engine.remaining_gold([key], available, book.validated)
                    row.update(
                        full_price=recipe['gold'],
                        component_credit=recipe['gold'] - remaining,
                        remaining_gold=remaining,
                        status='known',
                        gold_shortfall=max(0.0, remaining - gold) if gold is not None else None,
                        gold_sufficient_at_nominal_price=(gold >= remaining)
                        if gold is not None
                        else None,
                    )
                except _RecipeError as exc:
                    row['status'] = exc.status
            rows.append(row)
    known = [(r['remaining_gold'], r) for r in rows if r['remaining_gold'] is not None]
    lowest = min(known, key=lambda pair: pair[0])[1] if known else None
    current = next((r for r in rows if r['is_current_next']), None)
    current_cost = current['remaining_gold'] if current else None
    lowest_cost = lowest['remaining_gold'] if lowest else None
    return {
        'schema': 1,
        'mode': 'shadow',
        'basis': 'nominal_independent_alternatives',
        'current_gold': gold,
        'current_next': current['item'] if current else None,
        'lowest_remaining_item': lowest['item'] if lowest else None,
        'nominal_saving_vs_current': current_cost - lowest_cost
        if current_cost is not None and lowest_cost is not None
        else None,
        'candidates': rows,
    }
