import copy
import json
import pathlib

import pytest

import decision_trace
import item_costs
import rules_engine
import update_aramkit


def sample(own=(), gold=None):
    return {
        'roster': {'own_items': list(own)},
        'extra': {
            'recipes': {
                'Sword': {'gold': 300, 'from': []},
                'Handle': {'gold': 500, 'from': ['Sword']},
                'A': {'gold': 1500, 'from': ['Handle', 'Sword']},
                'B': {'gold': 1000, 'from': ['Sword']},
            },
            'live_context': {'current_gold': gold},
        },
    }


def plan(*names):
    return {
        'core': [{'item': n, 'owned': False, 'next': i == 0} for i, n in enumerate(names)],
        'picks': [],
    }


def test_independent_quotes_consume_each_component_once_and_do_not_mutate_inputs():
    data = sample(['Sword'], 1200)
    before = copy.deepcopy(data)
    report = item_costs.compare(data, plan('A', 'B'))
    a, b = report['candidates']
    assert (a['full_price'], a['component_credit'], a['remaining_gold']) == (1500, 300, 1200)
    assert (b['component_credit'], b['remaining_gold']) == (300, 700)
    assert a['gold_shortfall'] == 0
    assert a['gold_sufficient_at_nominal_price'] is True
    assert report['current_next'] == 'A'
    assert report['lowest_remaining_item'] == 'B'
    assert report['nominal_saving_vs_current'] == 500
    assert data == before
    two = item_costs.compare(sample(['Sword', 'Sword']), plan('A'))
    assert two['candidates'][0]['remaining_gold'] == 900


def test_held_stackable_copy_is_not_a_free_additional_copy_but_upgrade_parts_count():
    report = item_costs.compare(sample(['B']), plan('B'))
    assert report['candidates'][0]['remaining_gold'] == 1000
    upgraded = item_costs.compare(sample(['Handle']), plan('A'))
    assert upgraded['candidates'][0]['remaining_gold'] == 1000


@pytest.mark.parametrize('wallet', [None, True, float('nan'), float('inf'), -1, '500'])
def test_unknown_or_invalid_wallet_does_not_become_zero(wallet):
    report = item_costs.compare(sample(gold=wallet), plan('A'))
    row = report['candidates'][0]
    assert row['remaining_gold'] == 1500
    assert row['gold_shortfall'] is None
    assert row['gold_sufficient_at_nominal_price'] is None


def test_missing_recipe_does_not_become_a_free_item():
    report = item_costs.compare(sample(), plan('Missing', 'B'))
    row = report['candidates'][0]
    assert row['status'] == 'unknown_recipe'
    assert row['remaining_gold'] is None
    assert report['lowest_remaining_item'] == 'B'
    assert report['nominal_saving_vs_current'] is None


def test_incomplete_source_keeps_legacy_estimate_but_cannot_be_a_trusted_quote(caplog):
    source = {'1': {'name': 'Incomplete', 'priceTotal': 1000, 'from': [999]}}
    recipes = update_aramkit.item_recipes(source)
    assert rules_engine.remaining_gold(['Incomplete'], [], recipes) == 1000
    data = {'roster': {'own_items': []}, 'extra': {'recipes': recipes}}
    row = item_costs.compare(data, plan('Incomplete'))['candidates'][0]
    assert row['status'] == 'unverified_recipe'
    assert row['remaining_gold'] is None
    assert 'manual review' in caplog.text


def test_missing_nested_component_and_conflicting_aliases_are_not_priced():
    data = sample()
    data['extra']['recipes']['Handle']['from'] = ['Missing']
    assert item_costs.compare(data, plan('A'))['candidates'][0]['status'] == 'unknown_recipe'
    data = sample()
    data['extra']['recipes']['SWORD'] = {'gold': 400, 'from': []}
    assert item_costs.compare(data, plan('A'))['candidates'][0]['status'] == 'invalid_recipe'


def test_owned_targets_and_empty_plans_do_not_create_purchase_alternatives():
    held = {'core': [{'item': 'B', 'owned': True}], 'picks': []}
    report = item_costs.compare(sample(['B']), held)
    assert report['candidates'] == []
    assert report['lowest_remaining_item'] is None
    assert report['nominal_saving_vs_current'] is None


@pytest.mark.parametrize(
    'bad',
    [
        {'gold': -1, 'from': []},
        {'gold': True, 'from': []},
        {'from': []},
        {'gold': 1000, 'from': 'Sword'},
        {'gold': 100, 'from': ['Sword']},
    ],
)
def test_invalid_recipe_is_reported_instead_of_claiming_a_price(bad):
    data = sample()
    data['extra']['recipes']['Bad'] = bad
    row = item_costs.compare(data, plan('Bad'))['candidates'][0]
    assert row['status'] == 'invalid_recipe'
    assert row['remaining_gold'] is None


def test_recipe_cycles_and_patch_mismatch_are_reported():
    data = sample()
    data['extra']['recipes']['A']['from'] = ['A']
    assert item_costs.compare(data, plan('A'))['candidates'][0]['status'] == 'cyclic_recipe'
    data['extra'].update(bundle_version='16.22', catalog_version='16.21')
    assert item_costs.compare(data, plan('B'))['candidates'][0]['status'] == 'patch_mismatch'


def test_name_normalization_and_explicit_zero_price():
    data = sample(['SWORD'])
    data['extra']['recipes']['Free'] = {'gold': 0, 'from': []}
    rows = item_costs.compare(data, plan('b', 'Free'))['candidates']
    assert rows[0]['remaining_gold'] == 700
    assert rows[1]['remaining_gold'] == 0
    assert rows[1]['status'] == 'known'


def test_cost_record_round_trip_and_legacy_record_compatibility():
    inputs = sample(['Sword'], 100)
    inputs.update(
        build={'core': ['B'], 'pool': ['B']},
        champion_tags={},
        rule_set={'rules': [], 'categories': {}},
        item_stats={},
        taken_augments=[],
        augment_items={},
    )
    d = decision_trace.Decision.capture(inputs, 'test', 10)
    record = d.record()
    assert record['cost_comparison']['candidates'][0]['remaining_gold'] == 700
    assert record['cost_comparison']['candidates'][0]['gold_shortfall'] == 600
    assert record['cost_comparison']['candidates'][0]['gold_sufficient_at_nominal_price'] is False
    assert decision_trace.replay(record)
    record['cost_comparison']['candidates'][0]['remaining_gold'] = 0
    assert not decision_trace.replay(record)
    record.pop('cost_comparison')
    assert decision_trace.replay(record)


def test_real_kayle_components_compare_dusk_to_liandry():
    recipes = json.loads(
        (pathlib.Path(__file__).with_name('data') / 'item-recipes.json').read_text(encoding='utf-8')
    )
    data = {'roster': {'own_items': ['Dagger', 'Glowing Mote']}, 'extra': {'recipes': recipes}}
    report = item_costs.compare(data, plan("Liandry's Torment", 'Dusk and Dawn'))
    liandry, dusk = report['candidates']
    assert liandry['remaining_gold'] == 3000
    assert dusk['remaining_gold'] == 2600
    assert report['nominal_saving_vs_current'] == 400
    assert dusk['gold_sufficient_at_nominal_price'] is None
