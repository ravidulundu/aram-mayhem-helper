import json
import pathlib
import unittest

import bundle
import live_client
import rules_engine

DATA = pathlib.Path(__file__).with_name('data')


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


class AdaptiveItemsTests(unittest.TestCase):
    def test_bundle_rejects_non_string_catalog_categories(self):
        data = {
            'builds': {'ahri': {'core': ['Item']}},
            'item_catalog': {'Item': dict(self.item(), categories=[{}])},
        }
        self.assertFalse(bundle._valid(data))

    def setUp(self):
        self.rules = load('item-rules.json')
        self.stats = load('item-stats.json')
        self.tags = load('champion-tags.json')
        self.catalog = {
            "Banshee's Veil": self.item(ap=105, mr=40),
            'Maw of Malmortius': self.item(ad=60, mr=40),
            'Force of Nature': self.item(hp=400, mr=55),
            'Morellonomicon': self.item(ap=75, hp=350),
            'Mortal Reminder': self.item(ad=35, crit=25),
            'Thornmail': self.item(armor=75, hp=150),
            'Void Staff': self.item(ap=95),
            'Cryptbloom': self.item(ap=75),
            "Liandry's Torment": self.item(ap=60, hp=300),
            "Rod of Ages": self.item(ap=50, mana=400, hp=350),
            'Infinity Edge': self.item(ad=70, crit=25),
            'Heartsteel': self.item(hp=800),
        }
        self.extra = {'item_catalog': self.catalog, 'item_groups': load('item-groups.json')}

    @staticmethod
    def item(**stats):
        return {
            'purchasable': True,
            'acquisition': 'shop',
            'isFinal': True,
            'categories': [],
            'stats': stats,
        }

    def resolve(self, champion, *, enemies=None, enemy_items=None, own=None, allies=None, **extra):
        roster = {
            'local_champion': champion,
            'own_items': own or [],
            'ally_items': allies or [],
            'enemy_items': enemy_items or [],
            'allies': [champion],
            'enemies': enemies or [],
        }
        return rules_engine.resolve_build(
            load('builds/' + champion.lower() + '.json'),
            roster,
            self.tags,
            self.rules,
            self.stats,
            extra=dict(self.extra, **extra),
        )

    @staticmethod
    def planned(result):
        return result['core'] + result['picks']

    def test_ap_caster_finds_antiheal_outside_original_pool(self):
        result = self.resolve('Kassadin', enemies=['Soraka', 'Sona'])
        self.assertIn('Morellonomicon', [e['item'] for e in self.planned(result)])
        self.assertNotIn('Mortal Reminder', [e['item'] for e in self.planned(result)])

    def test_counter_is_actionable_before_remaining_generic_core(self):
        result = self.resolve('Kassadin', enemies=['Soraka', 'Sona'], own=['Rod of Ages'])
        self.assertEqual(
            'Morellonomicon', next(e['item'] for e in self.planned(result) if e['next'])
        )

    def test_damage_profiles_select_appropriate_mr_items(self):
        for champion, expected in [
            ('Kassadin', "Banshee's Veil"),
            ('Garen', 'Maw of Malmortius'),
            ('Leona', 'Force of Nature'),
        ]:
            with self.subTest(champion=champion):
                result = self.resolve(champion, enemies=['Ahri', 'Lux', 'Veigar'])
                self.assertIn(expected, [e['item'] for e in self.planned(result)])

    def test_owned_alternate_build_overrides_default_champion_damage(self):
        result = self.resolve('Kassadin', enemies=['Soraka', 'Sona'], own=['Infinity Edge'])
        self.assertIn('Mortal Reminder', [e['item'] for e in self.planned(result)])
        self.assertNotIn('Morellonomicon', [e['item'] for e in self.planned(result)])
        self.assertTrue(
            any(e['item'] == 'Infinity Edge' and e['owned'] for e in self.planned(result))
        )

    def test_augment_requirement_stays_ahead_of_reactive_items(self):
        result = rules_engine.resolve_build(
            load('builds/kassadin.json'),
            {
                'local_champion': 'Kassadin',
                'own_items': ['Rod of Ages'],
                'enemies': ['Soraka', 'Sona'],
            },
            self.tags,
            self.rules,
            self.stats,
            ["Upgrade Zhonya's"],
            {"Upgrade Zhonya's": "Zhonya's Hourglass"},
            self.extra,
        )
        self.assertEqual(
            "Zhonya's Hourglass", next(e['item'] for e in self.planned(result) if e['next'])
        )

    def test_original_candidates_must_still_be_buyable(self):
        self.catalog['Morellonomicon']['purchasable'] = False
        result = rules_engine.resolve_build(
            {'core': ['Morellonomicon'], 'pool': ['Morellonomicon']},
            {'local_champion': 'Kassadin'},
            self.tags,
            self.rules,
            self.stats,
            extra=self.extra,
        )
        self.assertNotIn('Morellonomicon', [e['item'] for e in self.planned(result)])

    def test_starting_core_is_preserved_before_optional_counters(self):
        result = self.resolve('Kassadin', enemies=['Soraka', 'Sona'])
        self.assertEqual('Rod of Ages', next(e['item'] for e in self.planned(result) if e['next']))

    def test_owned_situational_items_are_not_duplicated(self):
        self.extra['item_catalog'] = load('item-catalog.json')['items']
        result = self.resolve('Ahri', own=['Stormsurge', "Banshee's Veil"])
        names = [e['item'] for e in self.planned(result)]
        self.assertEqual(1, names.count('Stormsurge'))
        self.assertEqual(1, names.count("Banshee's Veil"))
        self.assertEqual(6, len(names))

    def test_owned_counter_prevents_a_second_counter_for_same_need(self):
        result = self.resolve('Kassadin', enemies=['Soraka', 'Sona'], own=['Morellonomicon'])
        unowned = [e['item'] for e in self.planned(result) if not e['owned']]
        self.assertFalse(set(unowned) & set(self.rules['categories']['grievous_wounds']))

    def test_shop_and_item_group_constraints_apply_to_new_candidates(self):
        self.catalog['Morellonomicon']['purchasable'] = False
        result = self.resolve('Kassadin', enemies=['Soraka', 'Sona'])
        self.assertNotIn('Morellonomicon', [e['item'] for e in self.planned(result)])

    def test_health_stacking_uses_health_damage_not_unrelated_penetration(self):
        result = self.resolve(
            'Kassadin', enemy_items=['Heartsteel', "Warmog's Armor", 'Unending Despair']
        )
        counters = [
            e['item']
            for e in self.planned(result)
            if e.get('reason') == 'enemies are stacking health'
        ]
        self.assertEqual(["Liandry's Torment"], counters)

    def test_full_build_sale_uses_legal_external_counter(self):
        self.extra['item_catalog'] = load('item-catalog.json')['items']
        own = [
            'Rod of Ages',
            "Sorcerer's Shoes",
            'Malignance',
            "Archangel's Staff",
            'Riftmaker',
            "Zhonya's Hourglass",
        ]
        result = self.resolve('Kassadin', enemies=['Soraka', 'Sona'], own=own)
        self.assertIsNotNone(result['sell'])
        self.assertEqual('Morellonomicon', result['sell']['buy'])

    def test_full_build_without_boots_can_replace_a_situational_item(self):
        self.extra['item_catalog'] = load('item-catalog.json')['items']
        own = [
            'Rod of Ages',
            'Malignance',
            "Archangel's Staff",
            'Riftmaker',
            "Rabadon's Deathcap",
            'Frozen Heart',
        ]
        result = self.resolve('Kassadin', enemies=['Soraka', 'Sona'], own=own)
        self.assertIsNotNone(result['sell'])
        self.assertEqual('Morellonomicon', result['sell']['buy'])
        self.assertNotIn(result['sell']['sell'], ['Rod of Ages', 'Malignance', "Archangel's Staff"])

    def test_required_quest_precedes_optional_stack_copy(self):
        result = rules_engine.resolve_build(
            load('builds/ahri.json'),
            {'local_champion': 'Ahri', 'own_items': ['Rod of Ages']},
            self.tags,
            self.rules,
            self.stats,
            ['True Eternity', "Upgrade Zhonya's"],
            {"Upgrade Zhonya's": "Zhonya's Hourglass"},
            dict(self.extra, effects=load('augment-effects.json')),
        )
        self.assertEqual(
            "Zhonya's Hourglass", next(e['item'] for e in self.planned(result) if e['next'])
        )

    def test_owned_augment_requirement_is_not_sold_for_counter(self):
        self.extra['item_catalog'] = load('item-catalog.json')['items']
        own = [
            'Rod of Ages',
            'Malignance',
            "Archangel's Staff",
            'Riftmaker',
            "Rabadon's Deathcap",
            "Zhonya's Hourglass",
        ]
        result = rules_engine.resolve_build(
            load('builds/kassadin.json'),
            {'local_champion': 'Kassadin', 'own_items': own, 'enemies': ['Soraka', 'Sona']},
            self.tags,
            self.rules,
            self.stats,
            ["Upgrade Zhonya's"],
            load('augment-items.json'),
            self.extra,
        )
        self.assertIsNotNone(result['sell'])
        self.assertNotEqual("Zhonya's Hourglass", result['sell']['sell'])

    def test_counter_boots_remain_protected_in_adaptive_sales(self):
        self.extra['item_catalog'] = load('item-catalog.json')['items']
        own = [
            'Heartsteel',
            "Mercury's Treads",
            'Unending Despair',
            "Warmog's Armor",
            'Thornmail',
            "Randuin's Omen",
        ]
        result = self.resolve('Leona', enemies=['Ahri', 'Lux', 'Veigar'], own=own)
        if result['sell']:
            self.assertNotEqual("Mercury's Treads", result['sell']['sell'])

    def test_damage_conversion_augments_change_counter_family(self):
        for champion, augment, expected in [
            ('Garen', 'ADAPt', 'Morellonomicon'),
            ('Kassadin', 'escAPADe', 'Mortal Reminder'),
        ]:
            with self.subTest(champion=champion):
                result = rules_engine.resolve_build(
                    load('builds/' + champion.lower() + '.json'),
                    {'local_champion': champion, 'enemies': ['Soraka', 'Sona']},
                    self.tags,
                    self.rules,
                    self.stats,
                    [augment],
                    {},
                    dict(self.extra, effects=load('augment-effects.json')),
                )
                self.assertIn(expected, [e['item'] for e in self.planned(result)])

    def test_multiple_augment_explanation_names_all_contributors(self):
        extra = dict(
            self.extra,
            item_names={'1': 'Riftmaker'},
            aug_table={'Weapon of Destiny': [[1, 580, 59]], 'Clown College': [[1, 551, 36]]},
        )
        result = rules_engine.resolve_build(
            {'core': [], 'pool': ['Riftmaker'], 'fourth': ['Riftmaker']},
            {'local_champion': 'Kassadin'},
            self.tags,
            {'rules': []},
            self.stats,
            ['Weapon of Destiny', 'Clown College'],
            extra=extra,
        )
        reason = self.planned(result)[0]['reason']
        self.assertIn('Weapon of Destiny', reason)
        self.assertIn('Clown College', reason)
        self.assertIn('average', reason.lower())

    def test_champion_situation_inventory_matrix(self):
        catalog = load('item-catalog.json')['items']
        groups = self.extra['item_groups']
        scenarios = [
            (['Soraka', 'Sona'], []),
            (['Ahri', 'Lux', 'Veigar'], []),
            ([], ['Force of Nature', 'Spirit Visage']),
        ]
        failures = []
        for path in (DATA / 'builds').glob('*.json'):
            build = json.loads(path.read_text(encoding='utf-8'))
            for enemies, enemy_items in scenarios:
                for own in [build['core'][:2], (build.get('fourth') or [])[:1]]:
                    roster = {
                        'local_champion': build['champion'],
                        'own_items': own,
                        'enemies': enemies,
                        'enemy_items': enemy_items,
                    }
                    result = rules_engine.resolve_build(
                        build,
                        roster,
                        self.tags,
                        self.rules,
                        self.stats,
                        extra=dict(self.extra, item_catalog=catalog),
                    )
                    context = live_client.decision_context(
                        {'level': 18, 'currentGold': 5000, 'championStats': {'abilityPower': 900}},
                        None,
                    )
                    observed = rules_engine.resolve_build(
                        build,
                        roster,
                        self.tags,
                        self.rules,
                        self.stats,
                        extra=dict(self.extra, item_catalog=catalog, live_context=context),
                    )
                    if observed != result:
                        failures.append((build['champion'], 'context changed ranking'))
                    plan = self.planned(result)
                    names = [e['item'] for e in plan]
                    valid = len(plan) == 6 and len(set(names)) == len(names)
                    valid = valid and sum(bool(e['next']) for e in plan) <= 1
                    held = rules_engine.owned_keys(
                        [e['item'] for e in plan if e['owned']], self.stats
                    )
                    valid = valid and all(rules_engine.item_key(n) in held for n in own)
                    valid = valid and all(
                        not set(groups.get(n, [])) & set(groups.get(m, []))
                        for i, n in enumerate(names)
                        for m in names[i + 1 :]
                    )
                    if not valid:
                        failures.append((build['champion'], enemies, own, names))
        self.assertEqual([], failures[:10])


if __name__ == '__main__':
    unittest.main()
