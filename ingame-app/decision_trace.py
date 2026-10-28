"""Bounded local decision evidence and offline replay; never writes to stdout in workers."""

import argparse
import hashlib
import json
import logging
import os
import pathlib
import queue
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self

import item_costs
import rules_engine

logger = logging.getLogger(__name__)
MAX_BYTES = 8 * 1024 * 1024


def evaluate(inputs: dict) -> dict:
    required = {
        'build',
        'roster',
        'champion_tags',
        'rule_set',
        'item_stats',
        'taken_augments',
        'augment_items',
        'extra',
    }
    if set(inputs) != required:
        raise ValueError('Invalid decision input fields')
    for key in required - {'taken_augments'}:
        if not isinstance(inputs[key], dict):
            raise TypeError(f'Invalid decision input: {key}')
    if not isinstance(inputs['taken_augments'], list):
        raise TypeError('Invalid taken_augments')
    return rules_engine.resolve_build(**inputs)


@dataclass(frozen=True)
class Decision:
    inputs_json: str
    output_json: str
    session: str
    game_time: float | None
    id: str

    @classmethod
    def capture(cls, inputs: dict, session: str, game_time: float | None) -> 'Decision':
        # Resolve the detached inputs, so later worker mutations cannot alter the evidence.
        # Catalog insertion order is a resolver tie-breaker; preserve it through replay.
        encoded = json.dumps(inputs, separators=(',', ':'), allow_nan=False)
        result = evaluate(json.loads(encoded))
        output = json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False)
        digest = hashlib.sha256((session + encoded + output).encode()).hexdigest()
        return cls(encoded, output, session, game_time, digest)

    @property
    def result(self) -> dict:
        return json.loads(self.output_json)

    def record(self) -> dict:
        inputs = json.loads(self.inputs_json)
        record = {
            'schema': 1,
            'session': self.session,
            'decision_id': self.id,
            'engine_version': os.environ.get('ARAM_VERSION', 'dev'),
            'game_time': self.game_time,
            'inputs': inputs,
            'result': self.result,
        }
        if isinstance(inputs.get('extra', {}).get('recipes'), dict):
            record['cost_comparison'] = item_costs.compare(inputs, self.result)
        return record


def replay(record: dict) -> bool:
    if record.get('schema') != 1:
        raise ValueError('Unsupported decision record schema')
    inputs = record.get('inputs')
    if not isinstance(inputs, dict):
        raise TypeError('Missing decision inputs')
    result = evaluate(inputs)
    if result != record.get('result'):
        return False
    return (
        'cost_comparison' not in record
        or item_costs.compare(inputs, result) == record['cost_comparison']
    )


class Journal:
    """A bounded queue keeps disk I/O away from engine and OCR threads."""

    def __init__(self, folder: pathlib.Path, max_bytes: int = MAX_BYTES, backups: int = 3):
        if max_bytes <= 0 or backups < 0:
            raise ValueError('Invalid journal retention limits')
        self.folder, self.max_bytes, self.backups = folder, max_bytes, backups
        self.error = ''
        self._queue: queue.Queue[tuple[Decision, str, str]] = queue.Queue(maxsize=32)
        self._closing = threading.Event()
        self._last: tuple[str, str, str] | None = None
        self._thread = threading.Thread(target=self._run, name='decision-journal', daemon=True)
        self._thread.start()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def submit(self, decision: Decision, ui_build: object, availability: str) -> None:
        ui = json.dumps(ui_build, sort_keys=True, separators=(',', ':'))
        key = (decision.id, ui, availability)
        if key == self._last:
            return
        try:
            self._queue.put_nowait((decision, ui, availability))
        except queue.Full:
            self._fail('Decision journal queue full; evidence dropped')
        else:
            self._last = key

    def _fail(self, message: str) -> None:
        if message != self.error:
            logger.error(message)
        self.error = message

    def _append(self, line: str) -> None:
        encoded = (line + '\n').encode('utf-8')
        if len(encoded) > self.max_bytes:
            raise ValueError('Decision journal record exceeds file limit')
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / 'decisions.jsonl'
        if path.exists() and path.stat().st_size + len(encoded) > self.max_bytes:
            if self.backups:
                for number in range(self.backups, 0, -1):
                    source = path if number == 1 else path.with_suffix(f'.jsonl.{number - 1}')
                    if source.exists():
                        source.replace(path.with_suffix(f'.jsonl.{number}'))
            else:
                path.unlink()
        with path.open('ab') as stream:
            stream.write(encoded)

    def _run(self) -> None:
        while not self._closing.is_set() or not self._queue.empty():
            try:
                entry = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                decision, ui, availability = entry
                record = decision.record()
                record.update(
                    ui_build=json.loads(ui),
                    availability=availability,
                    recorded_at=datetime.now(UTC).isoformat(),
                )
                self._append(json.dumps(record, separators=(',', ':'), allow_nan=False))
            except (OSError, ValueError) as exc:
                self._fail(f'Decision journal write failed: {exc}')
            finally:
                self._queue.task_done()

    def close(self) -> None:
        # Shutdown only: workers never wait for disk during normal operation.
        if self._thread.is_alive():
            self._closing.set()
            self._thread.join(timeout=3)
            if self._thread.is_alive():
                self._fail('Decision journal did not finish within shutdown timeout')


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Replay local decision JSONL without game/API access'
    )
    parser.add_argument('file', type=pathlib.Path)
    args = parser.parse_args()
    count, failed = 0, 0
    try:
        with args.file.open(encoding='utf-8') as stream:
            for number, line in enumerate(stream, 1):
                count += 1
                try:
                    if len(line.encode('utf-8')) > MAX_BYTES:
                        raise ValueError('Record exceeds size limit')
                    record = json.loads(line)
                    if not isinstance(record, dict) or not replay(record):
                        raise ValueError('Recommendation differs from recorded result')
                except (ValueError, TypeError, KeyError) as exc:
                    failed += 1
                    print(f'line {number}: {exc}')
    except OSError as exc:
        print(f'Cannot read journal: {exc}')
        return 1
    print(f'Replayed {count} decisions: {failed} failed')
    return 1 if failed or not count else 0


if __name__ == '__main__':
    raise SystemExit(main())
