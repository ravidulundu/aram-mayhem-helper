"""Run local checks with this interpreter; no CI or service is required."""

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--files', nargs='+', default=['.'], help='Changed Python paths to check')
    parser.add_argument('--tests', nargs='+', default=[], help='Relevant pytest paths or node IDs')
    args = parser.parse_args()
    commands = [
        ('Ruff lint', ['ruff', 'check', *args.files]),
        ('Ruff format', ['ruff', 'format', '--check', *args.files]),
        ('Pyright', ['pyright', '--pythonpath', sys.executable, *args.files]),
        ('Pytest', ['pytest', '-q', *args.tests]),
    ]
    failed = []
    for name, command in commands:
        print(f'\n{name}:', flush=True)
        result = subprocess.run([sys.executable, '-m', *command], cwd=ROOT, check=False)
        if result.returncode:
            failed.append(name)
    if failed:
        print('\nFAILED: ' + ', '.join(failed), file=sys.stderr)
        return 1
    print('\nAll local quality checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
