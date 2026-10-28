"""Aduce la pornire cele mai noi tier-uri si statistici din repo, fara exe nou.

Fisierele tier_data.json, stats_data.json si mayhem-bundle.json din repo se actualizeaza la fiecare
patch; exe-ul are o copie in el, dar aici luam una mai noua daca exista si o
punem langa exe. Incarcarea alege apoi fisierul cu patch-ul mai mare
(vezi tier_list.newest). Orice esec (fara internet, JSON stricat) lasa copia
veche: aplicatia trebuie sa porneasca si offline.
"""

import json
import logging
import os
import pathlib
import tempfile

import requests

logger = logging.getLogger(__name__)

RAW = "https://raw.githubusercontent.com/CyberKird/aram-mayhem-helper/master/"
# fisier -> (cale in repo, cheia de versiune, cheia care trebuie sa existe)
FILES = {
    "tier_data.json": ("lcu-app/", "patch", "tiers"),
    "stats_data.json": ("lcu-app/", "revision", "champions"),
    "mayhem-bundle.json": ("ingame-app/data/", "revision", "builds"),
}
TIMEOUT = 8


def _version(data, key):
    def parts(value):
        return tuple(int(p) if p.isdigit() else 0 for p in str(value or "").split("."))

    return parts(data.get("version") or data.get("patch")), parts(data.get(key))


def _write_json(path, data):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as f:
            temporary = pathlib.Path(f.name)
            json.dump(data, f, ensure_ascii=False)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def sync(dest):
    """Descarca fisierele in `dest`. Intoarce lista celor actualizate."""
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    etag_file = dest / "etags.json"
    try:
        etags = json.loads(etag_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        etags = {}
    if not isinstance(etags, dict):
        logger.warning("Ignoring non-object ETag cache")
        etags = {}
    etags = {
        name: value
        for name, value in etags.items()
        if isinstance(name, str) and isinstance(value, str)
    }
    updated = []
    for name, (folder, version_key, required) in FILES.items():
        try:
            # ETag: fisierul de Mayhem are cateva MB, nu-l re-descarcam daca n-a
            # schimbat nimeni nimic (304 e un raspuns de cativa octeti)
            headers = {}
            if etags.get(name) and (dest / name).exists():
                headers["If-None-Match"] = etags[name]
            r = requests.get(RAW + folder + name, timeout=TIMEOUT, headers=headers)
            if r.status_code != 200:
                continue
            data = r.json()
            if (
                not isinstance(data, dict)
                or not data.get(version_key)
                or not isinstance(data.get(required), dict)
                or not data[required]
            ):
                continue  # raspuns ciudat: nu stricam ce avem
            if name == "mayhem-bundle.json" and any(
                not isinstance(build, dict)
                or any(
                    not isinstance(build.get(field, []), list)
                    or any(not isinstance(n, str) for n in build.get(field, []))
                    for field in (
                        "starting",
                        "core",
                        "fourth",
                        "fifth",
                        "sixth",
                        "pool",
                        "summoners",
                    )
                )
                for build in data[required].values()
            ):
                continue
            try:
                current = json.loads((dest / name).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                current = {}
            if isinstance(current, dict) and _version(current, version_key) > _version(
                data, version_key
            ):
                continue
            _write_json(dest / name, data)
            if r.headers.get("ETag"):
                etags[name] = r.headers["ETag"]
            updated.append(name)
        except Exception:
            logger.exception('data_sync.py:sync failed; preserving fallback')
            continue
    try:
        _write_json(etag_file, etags)
    except OSError:
        pass
    return updated
