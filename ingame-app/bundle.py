"""Pachetul de date Mayhem (build-uri, augmente per campion, tier global).

Doua copii: cea din pachet (data/mayhem-bundle.json, scrisa de
update_aramkit.py) si cea adusa de data_sync.py in ARAM_DATA_DIR. O folosim pe
cea cu patch-ul mai mare. Fara niciuna, get() intoarce {} si apelantii cad pe
fisierele per campion din data/builds si data/augments.
"""

import json
import os
import pathlib

BUNDLED = pathlib.Path(__file__).with_name("data") / "mayhem-bundle.json"

_cache = None
_stamp = None


def _read(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _vkey(version):
    return tuple(int(x) if x.isdigit() else 0 for x in str(version or "").split("."))


def _valid(data):
    if not isinstance(data, dict) or not isinstance(data.get("builds"), dict) or not data["builds"]:
        return False
    if "item_catalog" in data:
        from item_candidates import valid_catalog

        if not valid_catalog(data["item_catalog"]):
            return False
    return all(
        isinstance(build, dict)
        and all(
            isinstance(build.get(field, []), list)
            and all(isinstance(n, str) for n in build.get(field, []))
            for field in ("starting", "core", "fourth", "fifth", "sixth", "pool", "summoners")
        )
        for build in data["builds"].values()
    )


def get():
    global _cache, _stamp
    folder = os.environ.get("ARAM_DATA_DIR")
    synced_path = pathlib.Path(folder) / BUNDLED.name if folder else None
    stamp = []
    for path in (BUNDLED, synced_path):
        try:
            stat = path.stat() if path else None
            stamp.append((str(path), stat.st_mtime_ns, stat.st_size) if stat else None)
        except OSError:
            stamp.append((str(path), None))
    if _cache is None or stamp != _stamp:
        best = _read(BUNDLED)
        candidates = [best, _cache or {}]
        if synced_path:
            candidates.append(_read(synced_path))
        valid = [d for d in candidates if _valid(d)]
        _cache = max(
            valid, key=lambda d: (_vkey(d.get("version")), _vkey(d.get("revision"))), default={}
        )
        _stamp = stamp
    return _cache
