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
