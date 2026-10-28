import json
import pathlib
import tempfile
import unittest
from unittest import mock

import data_sync


class SyncTests(unittest.TestCase):
    def test_older_download_does_not_replace_newer_local_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'mayhem-bundle.json'
            old = {'version': '16.22', 'revision': '3', 'builds': {'ahri': {'core': ['New']}}}
            path.write_text(json.dumps(old), encoding='utf-8')
            response = mock.Mock(status_code=200, headers={})
            response.json.return_value = {
                'version': '16.21',
                'revision': '9',
                'builds': {'ahri': {'core': ['Old']}},
            }
            with (
                mock.patch.object(
                    data_sync, 'FILES', {'mayhem-bundle.json': ('', 'revision', 'builds')}
                ),
                mock.patch.object(data_sync.requests, 'get', return_value=response),
            ):
                self.assertEqual([], data_sync.sync(folder))
            self.assertEqual(old, json.loads(path.read_text(encoding='utf-8')))

    def test_failed_replace_preserves_previous_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'mayhem-bundle.json'
            old = {'revision': '1', 'builds': {'ahri': {'core': ['Old']}}}
            path.write_text(json.dumps(old), encoding='utf-8')
            response = mock.Mock(status_code=200, headers={'ETag': 'new'})
            response.json.return_value = {'revision': '2', 'builds': {'ahri': {'core': ['New']}}}
            with (
                mock.patch.object(
                    data_sync, 'FILES', {'mayhem-bundle.json': ('', 'revision', 'builds')}
                ),
                mock.patch.object(data_sync.requests, 'get', return_value=response),
                mock.patch('os.replace', side_effect=OSError('disk error')),
            ):
                self.assertEqual([], data_sync.sync(folder))
            self.assertEqual(old, json.loads(path.read_text(encoding='utf-8')))

    def test_invalid_build_payload_does_not_replace_valid_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'mayhem-bundle.json'
            old = {'revision': '1', 'builds': {'ahri': {}}}
            path.write_text(json.dumps(old), encoding='utf-8')
            response = mock.Mock(status_code=200, headers={})
            with (
                mock.patch.object(
                    data_sync, 'FILES', {'mayhem-bundle.json': ('', 'revision', 'builds')}
                ),
                mock.patch.object(data_sync.requests, 'get', return_value=response),
            ):
                for malformed in ['broken', {'ahri': 'broken'}, {'ahri': {'core': 'broken'}}]:
                    response.json.return_value = {'revision': '2', 'builds': malformed}
                    self.assertEqual([], data_sync.sync(folder))
            self.assertEqual(old, json.loads(path.read_text(encoding='utf-8')))


if __name__ == '__main__':
    unittest.main()
