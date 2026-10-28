import io
import json
import pathlib
import threading
from unittest import mock

import pytest

import app
import decision_trace
import live_client
import rules_engine


@pytest.fixture
def monitor():
    page = app._load_page('evidence_ingame', 'ingame-app')
    return page.Monitor({}, {}, {'rules': [], 'categories': {}}, {})


def test_outage_preserves_augments_and_blocks_new_decisions(monitor):
    monitor.phase = 'in_game'
    monitor._last_live_at = 100.0
    monitor.taken_augments = ['Snowday']
    monitor.resolved_build = {'core': []}
    with (
        mock.patch.object(app.time, 'monotonic', return_value=105.0),
        mock.patch('live_client.get_roster', return_value=None),
    ):
        monitor._roster_cycle()
        monitor._recompute_build()
        assert not monitor.data_stale
    assert monitor.phase == 'in_game'
    assert monitor.taken_augments == ['Snowday']
    assert monitor.resolved_build == {'core': []}
    assert not monitor.live_available


def test_expired_data_does_not_reset_while_game_window_exists(monitor):
    monitor.phase = 'in_game'
    monitor._last_live_at = 100.0
    monitor.taken_augments = ['Snowday']
    with (
        mock.patch.object(app.time, 'monotonic', return_value=140.0),
        mock.patch('live_client.get_roster', return_value=None),
        mock.patch('ocr_augments.find_game_window', return_value=7),
    ):
        monitor._roster_cycle()
        assert monitor.data_stale
    assert monitor.taken_augments == ['Snowday']


def test_missing_game_window_after_grace_resets_session(monitor):
    monitor.phase = 'in_game'
    monitor._last_live_at = 100.0
    monitor.taken_augments = ['Snowday']
    with (
        mock.patch.object(app.time, 'monotonic', return_value=140.0),
        mock.patch('live_client.get_roster', return_value=None),
        mock.patch('ocr_augments.find_game_window', return_value=None),
    ):
        monitor._roster_cycle()
    assert monitor.phase == 'waiting_for_game'
    assert monitor.taken_augments == []


def inputs():
    return {
        'build': {'core': ['Hubris'], 'pool': ['Hubris', "Death's Dance"]},
        'roster': {'local_champion': 'Zaahen', 'own_items': [], 'enemies': ['Jax']},
        'champion_tags': {},
        'rule_set': {'rules': [], 'categories': {}},
        'item_stats': {},
        'taken_augments': [],
        'augment_items': {},
        'extra': {},
    }


def test_decision_detaches_inputs_and_replays_purchase_and_augment():
    data = inputs()
    first = decision_trace.Decision.capture(data, 'session', 10.0)
    data['roster']['own_items'].append('Hubris')
    data['taken_augments'].append('Test quest')
    data['augment_items']['Test quest'] = "Death's Dance"
    second = decision_trace.Decision.capture(data, 'session', 20.0)
    assert not first.result['core'][0]['owned']
    assert second.result['core'][0]['owned'] or second.result['core'][1]['owned']
    assert first.id != second.id
    assert decision_trace.replay(first.record())
    assert decision_trace.replay(second.record())
    damaged = second.record()
    damaged['result'] = {}
    assert not decision_trace.replay(damaged)


def test_journal_deduplicates_and_bounds_files(tmp_path: pathlib.Path):
    decision = decision_trace.Decision.capture(inputs(), 'session', 10.0)
    with decision_trace.Journal(tmp_path, max_bytes=2400, backups=2) as journal:
        for i in range(8):
            journal.submit(decision, {'next': [str(i)]}, 'fresh')
            journal.submit(decision, {'next': [str(i)]}, 'fresh')
    files = list(tmp_path.glob('decisions.jsonl*'))
    assert 1 <= len(files) <= 3
    records = [json.loads(line) for file in files for line in file.read_text().splitlines()]
    assert all(decision_trace.replay(record) for record in records)
    assert len({json.dumps(record['ui_build']) for record in records}) == len(records)


def test_journal_io_failure_is_observable_and_non_fatal(tmp_path, caplog):
    blocked = tmp_path / 'file'
    blocked.write_text('occupied')
    with decision_trace.Journal(blocked) as journal:
        journal.submit(decision_trace.Decision.capture(inputs(), 'session', 10), {}, 'fresh')
    assert 'journal' in caplog.text.lower()


def test_replay_rejects_unknown_record_schema():
    with pytest.raises(ValueError, match='schema'):
        decision_trace.replay({'schema': 999})


def test_ui_expires_advice_but_keeps_detected_augments(monitor):
    page = app._load_page('ui_evidence_ingame', 'ingame-app')
    lcu = app._load_page('ui_evidence_lcu', 'lcu-app')
    engine = app.Engine(lcu, mock.Mock(phase='idle'), page, monitor)
    monitor.phase = 'in_game'
    monitor.roster = {'local_champion': 'Zaahen', 'enemies': ['Jax'], 'own_items': []}
    monitor._last_live_at = 100.0
    monitor.live_available = False
    monitor.taken_augments = ['Snowday']
    monitor.decision = decision_trace.Decision.capture(inputs(), 'session', 10)
    monitor.resolved_build = monitor.decision.result
    with mock.patch.object(app.time, 'monotonic', return_value=120.0):
        view = engine.in_game()
    assert view['build'] is None
    assert view['availability'] == 'stale'
    assert view['taken'][0]['name'] == 'Snowday'
    assert view['decision_id'] == monitor.decision.id


def test_same_game_recovery_preserves_selection_and_new_game_clears_it(monitor, tmp_path):
    page = __import__(monitor.__module__)
    monitor.phase = 'in_game'
    monitor.game_time = 300.0
    monitor._last_live_at = 100.0
    monitor.taken_augments = ['Snowday']
    roster = {'local_champion': 'Zaahen', 'allies': ['Zaahen'], 'enemies': ['Jax']}
    endpoints = {'/gamestats': {'gameTime': 310.0}, '/activeplayer': {}}
    with (
        mock.patch('live_client.get_roster', return_value=roster),
        mock.patch('live_client.get', side_effect=endpoints.get),
        mock.patch.object(page, 'TAKEN_FILE', tmp_path / 'taken.json'),
        mock.patch.object(monitor, '_compute_build'),
    ):
        monitor.live_available = False
        monitor._roster_cycle()
        assert monitor.live_available
        assert monitor.taken_augments == ['Snowday']
        old_session = monitor.session
        endpoints['/gamestats'] = None
        monitor._roster_cycle()
        assert monitor.taken_augments == ['Snowday']
        # Same champions, but a new game's clock and a stale saved selection.
        page.TAKEN_FILE.write_text(json.dumps({'game': monitor._game, 'taken': ['Snowday']}))
        endpoints['/gamestats'] = {'gameTime': 5.0}
        monitor._roster_cycle()
        assert monitor.session != old_session
        assert monitor.taken_augments == []


def test_journal_queue_overflow_is_observable_without_waiting(tmp_path, caplog):
    entered, release = threading.Event(), threading.Event()

    def blocked_write(_line):
        entered.set()
        release.wait(3)

    with (
        mock.patch.object(decision_trace.Journal, '_append', side_effect=blocked_write),
        decision_trace.Journal(tmp_path) as journal,
    ):
        decision = decision_trace.Decision.capture(inputs(), 'session', 10)
        try:
            journal.submit(decision, {'next': 0}, 'fresh')
            assert entered.wait(1)
            for i in range(1, 35):
                journal.submit(decision, {'next': i}, 'fresh')
            assert 'queue full' in journal.error
        finally:
            release.set()
    assert 'evidence dropped' in caplog.text


def test_replay_cli_reports_truncated_record_and_continues(tmp_path, capsys):
    path = tmp_path / 'decisions.jsonl'
    record = decision_trace.Decision.capture(inputs(), 'session', 10).record()
    path.write_text('{broken\n' + json.dumps(record) + '\n')
    with mock.patch('sys.argv', ['decision_trace.py', str(path)]):
        assert decision_trace.main() == 1
    assert 'Replayed 2 decisions: 1 failed' in capsys.readouterr().out


def test_late_ocr_result_is_discarded_after_session_reset(monitor):
    monitor.phase = 'in_game'

    def old_offer(_names):
        monitor._reset()
        return ['Snowday', 'Scopiest Weapons'], 'old OCR result'

    with mock.patch('ocr_augments.detect_offered_augments', side_effect=old_offer):
        monitor._ocr_cycle()
    assert monitor.ocr_status == ''
    assert monitor.augments == []


def test_capture_does_not_record_player_identity_from_monitor(monitor):
    monitor._game = 'private-riot-id|Zaahen'
    monitor.roster = inputs()['roster']
    monitor.build = inputs()['build']
    monitor._recompute_build()
    assert monitor.decision is not None
    assert 'private-riot-id' not in json.dumps(monitor.decision.record())


def test_engine_journals_the_decision_it_delivers_to_stdout(monitor, tmp_path):
    page = app._load_page('delivery_ingame', 'ingame-app')
    lcu = app._load_page('delivery_lcu', 'lcu-app')
    engine = app.Engine(lcu, mock.Mock(phase='idle'), page, monitor)
    monitor.phase = 'in_game'
    monitor.roster = inputs()['roster']
    monitor.decision = decision_trace.Decision.capture(inputs(), 'session', 10)
    stop = threading.Event()

    def state_once():
        stop.set()
        data = engine.in_game()
        # Simulate a newer worker result before the old state finishes sending.
        monitor.decision = decision_trace.Decision.capture(inputs(), 'new-session', 20)
        return {'t': 'state', 'view': 'in_game', 'data': data, 'geo': {}}

    output = io.StringIO()
    with (
        decision_trace.Journal(tmp_path) as journal,
        mock.patch.object(engine, 'state', side_effect=state_once),
        mock.patch('sys.stdout', output),
    ):
        engine.journal = journal
        engine.loop(stop)
    sent = json.loads(output.getvalue())['data']
    record = json.loads((tmp_path / 'decisions.jsonl').read_text())
    assert record['decision_id'] == sent['decision_id']
    assert record['decision_id'] != monitor.decision.id
    assert record['ui_build'] == sent['build']
    assert decision_trace.replay(record)


def test_ocr_state_application_is_atomic_with_session_reset(monitor):
    monitor.phase = 'in_game'
    entered, release, reset_done = threading.Event(), threading.Event(), threading.Event()

    def blocked_choice():
        entered.set()
        release.wait(2)

    def reset():
        monitor._reset()
        reset_done.set()

    with (
        mock.patch('ocr_augments.detect_offered_augments', return_value=([], 'old session')),
        mock.patch.object(monitor, '_track_choice', side_effect=blocked_choice),
    ):
        worker = threading.Thread(target=monitor._ocr_cycle)
        resetter = threading.Thread(target=reset)
        worker.start()
        try:
            assert entered.wait(1)
            resetter.start()
            assert not reset_done.wait(0.05), 'reset interleaved with applying old OCR state'
        finally:
            release.set()
            worker.join(2)
            if resetter.ident is not None:
                resetter.join(2)
    assert reset_done.is_set()
    assert monitor.ocr_status == ''


def test_capture_preserves_source_order_for_equally_ranked_counters():
    data = inputs()
    data['roster']['own_items'] = ['Hubris']
    data['champion_tags'] = {'Jax': {'damageType': 'AD'}}
    data['rule_set'] = {
        'rules': [
            {
                'id': 'ad',
                'condition': {'team': 'enemies', 'damageType': 'AD', 'countGte': 1},
                'suggestCategory': 'defense',
                'reason': 'AD enemies',
            }
        ],
        'categories': {'defense': ['Zulu Counter', 'Alpha Counter']},
    }
    data['extra']['item_catalog'] = {
        name: {'acquisition': 'shop', 'purchasable': True, 'isFinal': True, 'stats': {'ad': 40}}
        for name in ['Zulu Counter', 'Alpha Counter']
    }
    expected = rules_engine.resolve_build(**data)
    assert expected['core'][0]['item'] == 'Zulu Counter'
    assert decision_trace.Decision.capture(data, 'session', 10).result == expected


def test_monitor_records_fresh_context_and_journal_replays_without_ranking_change(
    monitor, tmp_path
):
    page = __import__(monitor.__module__)
    raw = {
        'local_champion': 'Zaahen',
        'allies': ['Zaahen'],
        'enemies': ['Jax'],
        'own_items': ['Hubris'],
        'enemy_items': [],
        'ally_items': [],
        'players': [
            {
                'index': 0,
                'champion': 'Zaahen',
                'team': 'ally',
                'is_local': True,
                'level': 11,
                'items': [{'item_id': 6697, 'name': 'Hubris', 'slot': 0, 'count': 1}],
            }
        ],
    }
    active = {
        'riotId': 'private#identity',
        'level': 11,
        'currentGold': 75.0,
        'championStats': {'armor': 88, 'attackRange': 175, 'abilityPower': 0},
    }
    with (
        mock.patch.object(page, 'load_cached', return_value=inputs()['build']),
        mock.patch.object(page, 'TAKEN_FILE', tmp_path / 'taken.json'),
    ):
        monitor._accept_roster(raw, active, 100.0)
        decision = monitor.decision
        captured = json.loads(decision.inputs_json)
        context = captured['extra']['live_context']
        assert context['level'] == 11
        assert context['current_gold'] == 75
        assert context['champion_stats']['armor'] == 88
        assert context['players'][0]['items'][0]['name'] == 'Hubris'
        baseline = json.loads(decision.inputs_json)
        baseline['extra'].pop('live_context')
        baseline['roster'].pop('players')
        assert rules_engine.resolve_build(**baseline) == decision.result
        assert 'private' not in json.dumps(decision.record())
        with decision_trace.Journal(tmp_path / 'logs') as journal:
            journal.submit(decision, decision.result, 'fresh')
        record = json.loads((tmp_path / 'logs/decisions.jsonl').read_text())
        assert record['inputs']['extra']['live_context'] == context
        assert decision_trace.replay(record)

        monitor._accept_roster(raw, None, 104.0)
        assert monitor._last_gold == 75  # Existing activity tracking retains its value.
        assert monitor.live_context['current_gold'] is None
        assert monitor.live_context['level'] is None
        assert monitor.live_context['champion_stats'] == {}
        monitor._reset()
        assert monitor.live_context is None


def test_extra_live_context_is_optional_and_does_not_change_legacy_replay():
    data = inputs()
    old = decision_trace.Decision.capture(data, 'session', 10)
    data['extra']['live_context'] = live_client.decision_context(
        {'level': 18, 'currentGold': 5000, 'championStats': {'abilityPower': 900}}, None
    )
    new = decision_trace.Decision.capture(data, 'session', 10)
    assert new.result == old.result
    assert decision_trace.replay(old.record())
    assert decision_trace.replay(new.record())
