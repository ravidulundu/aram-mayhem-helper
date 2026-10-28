import importlib.util
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
