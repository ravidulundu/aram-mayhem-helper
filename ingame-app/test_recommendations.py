import json
import pathlib
import tempfile
import unittest
from unittest import mock

import bundle
import rules_engine as rules
import update_aramkit

DATA = pathlib.Path(__file__).with_name('data')


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


class RecommendationTests(unittest.TestCase):
    def test_recipe_extraction_preserves_zero_but_not_missing_prices_or_components(self):
        raw = {
            '1': {'name': 'Free', 'priceTotal': 0, 'from': []},
            '2': {'name': 'Missing price', 'from': []},
            '3': {'name': 'Missing component', 'priceTotal': 1000, 'from': [999]},
            '4': {'name': 'Duplicate', 'priceTotal': 300, 'from': []},
            '5': {'name': 'Duplicate', 'priceTotal': 500, 'from': []},
            '6': {'name': 'Valid upgrade', 'priceTotal': 200, 'from': [1]},
        }
        with self.assertLogs(update_aramkit.logger, level='WARNING'):
            recipes = update_aramkit.item_recipes(raw)
        self.assertEqual(recipes['Free'], {'gold': 0, 'from': []})
        self.assertEqual(recipes['Valid upgrade'], {'gold': 200, 'from': ['Free']})
        for name in ['Missing price', 'Missing component', 'Duplicate']:
            self.assertEqual(recipes[name]['cost_status'], 'unverified')
        self.assertEqual(rules.remaining_gold(['Missing component'], [], recipes), 1000)
        self.assertEqual(rules.remaining_gold(['Duplicate'], [], recipes), 500)

    def test_mayhem_descriptions_replace_stale_text_and_preserve_fallback(self):
        fallback = {'Mad Scientist': 'Each Round', 'Legacy Augment': 'Keep this text'}
        source = {
            '1': {
                'name': 'Mad Scientist',
                'tooltip': {
                    'blocks': [{'spans': [{'text': 'On each Revive, you grow large or tiny.'}]}]
                },
            },
            '2': {
                'name': 'Warlock Juicebox',
                'tooltip': {'blocks': [{'spans': [{'text': 'Gain Omnivamp.'}]}]},
            },
        }
        result = update_aramkit.augment_descriptions(source, fallback)
        self.assertEqual(result['Mad Scientist'], 'On each Revive, you grow large or tiny.')
        self.assertEqual(result['Warlock Juicebox'], 'Gain Omnivamp.')
        self.assertEqual(result['Legacy Augment'], 'Keep this text')
        self.assertEqual(fallback['Mad Scientist'], 'Each Round')
        self.assertNotIn('Warlock Juicebox', fallback)

    def test_empty_mayhem_tooltip_does_not_erase_existing_description(self):
        result = update_aramkit.augment_descriptions(
            {'1': {'name': 'Mad Scientist', 'tooltip': {'blocks': []}}},
            {'Mad Scientist': 'Existing explanation'},
        )
        self.assertEqual(result['Mad Scientist'], 'Existing explanation')

    def test_augment_description_keeps_scaling_icon_meaning(self):
        source = {
            '1': {
                'name': 'Warlock Juicebox',
                'tooltip': {
                    'blocks': [
                        {
                            'spans': [
                                {'type': 'text', 'text': 'Gain (10%+3.5%'},
                                {'type': 'icon', 'label': 'Ability Power'},
                                {'type': 'text', 'text': ') Omnivamp.'},
                            ]
                        }
                    ]
                },
            }
        }
        result = update_aramkit.augment_descriptions(source, {})
        self.assertEqual(result['Warlock Juicebox'], 'Gain (10%+3.5% [Ability Power]) Omnivamp.')

    def test_catalog_reads_actual_max_mana_resource_label(self):
        source = {
            '1': {
                'name': 'Mana item',
                'tooltip': {
                    'blocks': [
                        {
                            'spans': [
                                {'type': 'icon', 'label': 'Max Mana'},
                                {'type': 'text', 'semantic': 'stat', 'text': '300'},
                            ]
                        }
                    ]
                },
            }
        }
        catalog = update_aramkit.item_catalog(source)
        self.assertEqual(catalog['Mana item']['stats'], {'mana': 300.0})

    def test_augment_text_uses_readable_labels_for_internal_icon_names(self):
        source = {
            '1': {
                'name': 'Example',
                'tooltip': {
                    'blocks': [
                        {
                            'spans': [
                                {'type': 'icon', 'label': 'goldCoins'},
                                {'type': 'icon', 'label': 'KiwiAugmentBurstingTeeth'},
                            ]
                        }
                    ]
                },
            }
        }
        result = update_aramkit.augment_descriptions(source, {})
        self.assertEqual(result['Example'], '[Gold] [Bursting Teeth]')

    def test_shorter_tooltip_does_not_delete_existing_augment_mechanics(self):
        existing = {
            "Icathia's Fall": {'gives': ["Bami's Cinder"], 'combine': 'Void Immolation'},
            'Tap Dancer': {'likes': 'onhit'},
            'ADAPt': {'damage': 'AP'},
        }
        # Missing details do not establish removal. An explicit new conversion wins.
        text = {'ADAPt': 'Convert Ability Power to Attack Damage.'}
        with self.assertLogs(update_aramkit.logger, level='WARNING') as logs:
            result = update_aramkit.augment_effects({}, set(), text, previous=existing)
        self.assertEqual(result["Icathia's Fall"], existing["Icathia's Fall"])
        self.assertEqual(result['Tap Dancer'], existing['Tap Dancer'])
        self.assertEqual(result['ADAPt'], {'damage': 'AD'})
        self.assertEqual(existing['ADAPt'], {'damage': 'AP'})
        self.assertTrue(any('manual review' in message for message in logs.output))

    def setUp(self):
        self.tags = load('champion-tags.json')
        self.stats = load('item-stats.json')
        self.rules = load('item-rules.json')
        self.groups = load('item-groups.json')
        self.roster = {
            'local_champion': 'Ahri',
            'own_items': [],
            'ally_items': [],
            'enemy_items': [],
            'allies': ['Ahri'],
            'enemies': [],
        }

    def resolve(self, build=None, **extra):
        return rules.resolve_build(
            build or load('builds/ahri.json'),
            self.roster,
            self.tags,
            self.rules,
            self.stats,
            extra=dict(item_groups=self.groups, **extra),
        )

    def test_all_champion_plans_fit_inventory(self):
        for path in (DATA / 'builds').glob('*.json'):
            build = json.loads(path.read_text(encoding='utf-8'))
            self.roster['local_champion'] = build['champion']
            result = self.resolve(build)
            with self.subTest(champion=build['champion']):
                self.assertEqual(6, len(result['core'] + result['picks']))

    def test_planned_items_are_mutually_compatible(self):
        self.roster['enemy_items'] = ['Force of Nature', 'Spirit Visage']
        result = self.resolve()
        seen = set()
        for entry in result['core'] + result['picks']:
            groups = set(self.groups.get(entry['item'], []))
            self.assertFalse(seen & groups, entry['item'])
            seen |= groups

    def test_mr_counter_uses_percent_penetration(self):
        self.roster['enemy_items'] = ['Force of Nature', 'Spirit Visage']
        hot = rules.evaluate_rules(
            self.roster,
            self.tags,
            self.rules,
            ['Stormsurge', 'Void Staff', 'Cryptbloom'],
            self.stats,
        )
        self.assertEqual({'Void Staff', 'Cryptbloom'}, {e['item'] for e in hot})

    def test_all_healing_rules_respect_team_antiheal(self):
        self.roster.update(
            ally_items=['Morellonomicon'],
            enemy_items=['Bloodthirster', 'Spirit Visage'],
            enemies=['Soraka', 'Sona'],
        )
        hot = rules.evaluate_rules(
            self.roster,
            self.tags,
            self.rules,
            ['Morellonomicon', "Executioner's Calling"],
            self.stats,
        )
        self.assertEqual([], hot)

    def test_augment_scores_weight_sample_counts(self):
        extra = {
            'item_names': {'1': 'Item'},
            'aug_table': {'A': [[1, 800, 100]], 'B': [[1, 500, 100]]},
            'aug_samples': {'A': {'1': 300}, 'B': {'1': 2700}},
        }
        self.assertAlmostEqual(53, rules.augment_scores(['A', 'B'], extra)['Item'][0])

    def test_legacy_augment_rows_remain_supported(self):
        extra = {
            'item_names': {'1': 'Item'},
            'aug_table': {'A': [[1, 800, 100]], 'B': [[1, 500, 100]]},
        }
        self.assertAlmostEqual(65, rules.augment_scores(['A', 'B'], extra)['Item'][0])

    def test_new_exports_preserve_sample_count(self):
        resources = {
            'augments': {'2': {'name': 'Augment'}},
            'items': {'1': {'name': 'Item', 'acquisition': 'shop', 'purchasable': True}},
        }
        raw = {
            'items': [
                {
                    'augmentId': 2,
                    'all': [{'id': 1, 'winRate': 0.6, 'pickRate': 0.1, 'sampleCount': 700}],
                }
            ]
        }
        with mock.patch.object(update_aramkit, 'get_json', return_value=raw):
            samples = {}
            self.assertEqual(
                {'Augment': [[1, 600, 100]]},
                update_aramkit.augment_item_stats(1, 'test', resources, samples),
            )
            self.assertEqual({'Augment': {'1': 700}}, samples)

    def test_stackable_augment_retains_owned_and_next_copy(self):
        self.roster.update(local_champion='Garen', own_items=['Black Cleaver', 'Black Cleaver'])
        result = rules.resolve_build(
            load('builds/garen.json'),
            self.roster,
            self.tags,
            self.rules,
            self.stats,
            ["Don't Stop Cleavin'"],
            {},
            {'effects': load('augment-effects.json'), 'item_groups': self.groups},
        )
        plan = result['core'] + result['picks']
        self.assertEqual(6, len(plan))
        self.assertEqual(2, sum(e['owned'] and e['item'] == 'Black Cleaver' for e in plan))
        self.assertEqual(1, sum(not e['owned'] and e['item'] == 'Black Cleaver' for e in plan))


class BundleTests(unittest.TestCase):
    def test_new_bundle_becomes_visible_without_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            bundled = root / 'base' / 'mayhem-bundle.json'
            bundled.parent.mkdir()
            bundled.write_text(
                json.dumps(
                    {'version': '16.21', 'revision': '1', 'builds': {'ahri': {'core': ['Old']}}}
                ),
                encoding='utf-8',
            )
            with (
                mock.patch.object(bundle, 'BUNDLED', bundled),
                mock.patch.object(bundle, '_cache', None),
                mock.patch.dict('os.environ', {'ARAM_DATA_DIR': str(root)}),
            ):
                self.assertEqual(['Old'], bundle.get()['builds']['ahri']['core'])
                synced = root / 'mayhem-bundle.json'
                synced.write_text(
                    json.dumps(
                        {'version': '16.21', 'revision': '2', 'builds': {'ahri': {'core': ['New']}}}
                    ),
                    encoding='utf-8',
                )
                self.assertEqual(['New'], bundle.get()['builds']['ahri']['core'])
                synced.write_text('{broken', encoding='utf-8')
                self.assertEqual(['New'], bundle.get()['builds']['ahri']['core'])
                synced.write_text(
                    json.dumps({'version': '16.21', 'revision': '3', 'builds': {'ahri': 'broken'}}),
                    encoding='utf-8',
                )
                self.assertEqual(['New'], bundle.get()['builds']['ahri']['core'])
                synced.write_text(
                    json.dumps(
                        {
                            'version': '16.21',
                            'revision': '4',
                            'builds': {'ahri': {'core': ['Bad']}},
                            'item_catalog': {'Item': {'stats': 'bad'}},
                        }
                    ),
                    encoding='utf-8',
                )
                self.assertEqual(['New'], bundle.get()['builds']['ahri']['core'])


if __name__ == '__main__':
    unittest.main()
