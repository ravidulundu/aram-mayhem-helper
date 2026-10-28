import importlib.util
import json
import pathlib
import sys
from collections.abc import Callable
from unittest import mock

import pytest
from PIL import Image

import app
import build_icons
import champ_ocr
import data_sync
import lcu_client
import live_client
import ocr_augments
import quality


def test_augment_gold_detection_uses_immediate_gain_not_passive_reward() -> None:
    page = app._load_page('gold_capture_regression', 'ingame-app')
    descriptions = {
        'Upgrade Collector': 'Executions grant additional 50 Gold.\nGain 250 Gold.',
        'Upgrade Sundered Sky': 'Reduce the cooldown.\nGain500 Gold.',
        'Upgrade Stormsurge': 'Gain [goldCoins] 500 Gold.',
        'Goldrend': 'Damaging a champion grants you 30 Gold.',
    }
    with mock.patch.object(
        page.Monitor,
        '_optional',
        side_effect=lambda name: descriptions if name == 'augment-desc.json' else {},
    ):
        monitor = page.Monitor({}, {}, {}, {})
    assert monitor._aug_gold == {
        'Upgrade Collector': 250,
        'Upgrade Sundered Sky': 500,
        'Upgrade Stormsurge': 500,
    }


def test_ocr_enhance_uses_supported_pillow_resampling() -> None:
    result = ocr_augments.enhance(Image.new('RGB', (20, 10)))
    assert result.size == (30, 15)


def test_icon_shrink_uses_supported_pillow_resampling() -> None:
    import io

    png = io.BytesIO()
    Image.new('RGBA', (128, 128)).save(png, format='PNG')
    with Image.open(io.BytesIO(build_icons.shrink(png.getvalue()))) as result:
        assert max(result.size) <= build_icons.MAX_ICON


def test_page_loader_rejects_missing_spec() -> None:
    with (
        mock.patch.object(importlib.util, 'spec_from_file_location', return_value=None),
        pytest.raises(ImportError, match='Cannot load'),
    ):
        app._load_page('missing_test_page', 'ingame-app')


def test_sync_recovers_from_non_object_etags(tmp_path: pathlib.Path) -> None:
    (tmp_path / 'etags.json').write_text('[]', encoding='utf-8')
    response = mock.Mock(status_code=200, headers={})
    response.json.return_value = {
        'version': '16.21',
        'revision': '1',
        'builds': {'ahri': {'core': ['Item']}},
    }
    with (
        mock.patch.object(data_sync, 'FILES', {'mayhem-bundle.json': ('', 'revision', 'builds')}),
        mock.patch.object(data_sync.requests, 'get', return_value=response),
    ):
        assert data_sync.sync(tmp_path) == ['mayhem-bundle.json']


def test_roster_uses_active_player_fallback_team() -> None:
    players = [
        {'summonerName': 'local', 'championName': 'Ahri', 'team': 'ORDER', 'items': []},
        {'summonerName': 'enemy', 'championName': 'Jinx', 'team': 'CHAOS', 'items': []},
    ]
    responses = {
        '/playerlist': players,
        '/activeplayername': None,
        '/activeplayer': {'summonerName': 'local'},
    }
    with mock.patch.object(live_client, 'get', side_effect=responses.get):
        result = live_client.get_roster()
    assert result is not None
    assert result['local_champion'] == 'Ahri'
    assert result['allies'] == ['Ahri']
    assert result['enemies'] == ['Jinx']


def test_roster_retains_anonymous_inventory_ownership_without_changing_flat_lists() -> None:
    players = [
        {
            'summonerName': 'private-local',
            'riotId': 'private-local#secret',
            'championName': 'MonkeyKing',
            'team': 'ORDER',
            'level': 9,
            'items': [{'itemID': 3115, 'slot': 0, 'count': 1}],
        },
        {
            'summonerName': 'private-enemy',
            'championName': 'Jax',
            'team': 'CHAOS',
            'level': 10,
            'items': [
                {'itemID': 1053, 'slot': 2, 'count': 2},
                {'itemID': 999999, 'displayName': 'Unknown item', 'slot': 3, 'count': 1},
            ],
        },
    ]
    endpoints = {'/playerlist': players, '/activeplayername': 'private-local'}
    with mock.patch.object(live_client, 'get', side_effect=endpoints.get):
        roster = live_client.get_roster()
    assert roster is not None
    assert roster['own_items'] == ["Nashor's Tooth"]
    assert roster['enemy_items'] == ['Vampiric Scepter', 'Unknown item']
    assert roster['players'][0]['is_local']
    assert roster['players'][1]['team'] == 'enemy'
    assert roster['players'][1]['items'][0] == {
        'item_id': 1053,
        'name': 'Vampiric Scepter',
        'slot': 2,
        'count': 2,
    }
    page = app._load_page('context_normalization', 'ingame-app')
    normalized = page.normalize_roster(roster, {'MonkeyKing': 'Wukong'})
    assert normalized['players'][0]['champion'] == 'Wukong'
    assert roster['players'][0]['champion'] == 'MonkeyKing'
    assert 'private-' not in json.dumps(normalized)


def test_live_context_rejects_invalid_numbers_and_does_not_copy_identity() -> None:
    context = live_client.decision_context(
        {
            'riotId': 'private#identity',
            'level': True,
            'currentGold': float('nan'),
            'championStats': {
                'abilityPower': 120,
                'attackSpeed': 1.5,
                'armor': float('inf'),
                'resourceMax': False,
                'riotId': 12345,
            },
        },
        None,
    )
    assert context['schema'] == 1
    assert context['level'] is None
    assert context['current_gold'] is None
    assert context['champion_stats'] == {'abilityPower': 120.0, 'attackSpeed': 1.5}
    assert context['players'] is None
    assert live_client.decision_context(None, None)['current_gold'] is None
    assert live_client.decision_context({'level': 1, 'currentGold': 0}, [])['current_gold'] == 0


def test_player_snapshot_preserves_unknown_inventory_and_missing_item_fields() -> None:
    endpoints = {
        '/playerlist': [
            {'summonerName': 'local', 'championName': 'Ahri', 'team': 'ORDER'},
            {
                'summonerName': 'other',
                'championName': 'Jax',
                'team': 'CHAOS',
                'items': [
                    {'itemID': True, 'slot': False, 'count': -1},
                ],
            },
        ],
        '/activeplayername': 'local',
    }
    with mock.patch.object(live_client, 'get', side_effect=endpoints.get) as get:
        roster = live_client.get_roster()
    assert roster is not None
    assert roster['players'][0]['items'] is None
    assert roster['players'][0]['level'] is None
    assert roster['players'][1]['items'][0] == {
        'item_id': None,
        'name': None,
        'slot': None,
        'count': None,
    }
    assert get.call_count == 2  # No extra per-player requests.


def test_unresolved_local_team_is_not_recorded_as_enemy() -> None:
    endpoints = {
        '/playerlist': [{'summonerName': 'other', 'championName': 'Jax', 'team': 'CHAOS'}],
        '/activeplayername': None,
        '/activeplayer': None,
    }
    with mock.patch.object(live_client, 'get', side_effect=endpoints.get):
        roster = live_client.get_roster()
    assert roster is not None
    assert roster['enemies'] == []
    assert roster['players'][0]['team'] == 'unknown'


def test_missing_player_team_stays_unknown_even_when_local_team_is_known() -> None:
    endpoints = {
        '/playerlist': [
            {'summonerName': 'local', 'championName': 'Ahri', 'team': 'ORDER'},
            {'summonerName': 'other', 'championName': 'Jax'},
            {'summonerName': 'third', 'championName': 'Zyra', 'team': 'OTHER'},
        ],
        '/activeplayername': 'local',
    }
    with mock.patch.object(live_client, 'get', side_effect=endpoints.get):
        roster = live_client.get_roster()
    assert roster is not None
    assert [p['team'] for p in roster['players']] == ['ally', 'unknown', 'unknown']


def test_game_window_detection_distinguishes_client() -> None:
    def enumerate_windows(visitor: Callable[[int, object], None], data: object) -> None:
        visitor(11, data)
        visitor(22, data)

    classes = {11: ocr_augments.CLIENT_CLASS, 22: ocr_augments.GAME_CLASS}
    with (
        mock.patch.object(ocr_augments.win32gui, 'EnumWindows', side_effect=enumerate_windows),
        mock.patch.object(ocr_augments.win32gui, 'IsWindowVisible', return_value=True),
        mock.patch.object(ocr_augments.win32gui, 'GetClassName', side_effect=classes.__getitem__),
        mock.patch.object(ocr_augments.win32gui, 'GetWindowText', return_value='League of Legends'),
    ):
        assert ocr_augments.find_game_window() == 22
        assert ocr_augments.find_client_window() == 11


def test_ocr_worker_logs_unexpected_error(caplog: pytest.LogCaptureFixture) -> None:
    reader = champ_ocr.ChampSelectReader(['Ahri'], lambda: True, list)

    def fail_cycle() -> None:
        reader.stop.set()
        raise ValueError('synthetic OCR failure')

    with mock.patch.object(reader, '_cycle', side_effect=fail_cycle):
        reader._loop()
    assert 'synthetic OCR failure' in caplog.text


def test_lcu_timeout_remains_non_fatal() -> None:
    client = lcu_client.LCUClient('1', 'synthetic-token')
    with mock.patch.object(client.session, 'get', side_effect=lcu_client.requests.Timeout):
        assert client.get('/lol-gameflow/v1/session') is None


def test_quality_runner_rejects_failed_check() -> None:
    with (
        mock.patch.object(
            sys, 'argv', ['quality.py', '--files', 'quality.py', '--tests', __file__]
        ),
        mock.patch.object(
            quality.subprocess,
            'run',
            side_effect=[
                mock.Mock(returncode=1),
                mock.Mock(returncode=0),
                mock.Mock(returncode=0),
                mock.Mock(returncode=0),
            ],
        ) as run,
    ):
        assert quality.main() == 1
    assert run.call_count == 4
    assert all(call.args[0][0] == sys.executable for call in run.call_args_list)
