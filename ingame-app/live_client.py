"""Acces la Live Client Data API al jocului (127.0.0.1:2999).

Spre deosebire de LCU (champ select), API-ul asta ruleaza doar cat timp e un
meci efectiv pornit (nu in champ select). Expune tot rosterul (ambele echipe),
nu doar echipa proprie -- exact ce ne trebuie pentru build adaptat la comp.
"""

import json
import math
import pathlib
import re
from typing import Literal, TypedDict

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://127.0.0.1:2999/liveclientdata"


class PlayerItem(TypedDict):
    item_id: int | None
    name: str | None
    slot: int | None
    count: int | None


class PlayerSnapshot(TypedDict):
    index: int
    champion: str
    team: Literal['ally', 'enemy', 'unknown']
    is_local: bool
    level: int | None
    items: list[PlayerItem] | None


class LiveContext(TypedDict):
    schema: int
    level: int | None
    current_gold: float | None
    champion_stats: dict[str, float]
    players: list[PlayerSnapshot] | None


# Only documented numeric local-player fields cross the recording boundary.
CHAMPION_STAT_FIELDS = (
    'abilityHaste',
    'abilityPower',
    'armor',
    'armorPenetrationFlat',
    'armorPenetrationPercent',
    'attackDamage',
    'attackRange',
    'attackSpeed',
    'bonusArmorPenetrationPercent',
    'bonusMagicPenetrationPercent',
    'cooldownReduction',
    'critChance',
    'critDamage',
    'currentHealth',
    'healthRegenRate',
    'lifeSteal',
    'magicLethality',
    'magicPenetrationFlat',
    'magicPenetrationPercent',
    'magicResist',
    'maxHealth',
    'moveSpeed',
    'physicalLethality',
    'resourceMax',
    'resourceRegenRate',
    'resourceValue',
    'spellVamp',
    'tenacity',
)


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


def _inventory(items: object) -> list[PlayerItem] | None:
    if not isinstance(items, list):
        return None
    result: list[PlayerItem] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item_label(item)
        result.append(
            {
                'item_id': _integer(item.get('itemID')),
                'name': name if isinstance(name, str) else None,
                'slot': _integer(item.get('slot')),
                'count': _integer(item.get('count')),
            }
        )
    return result


def decision_context(active: object, players: list[PlayerSnapshot] | None) -> LiveContext:
    """Capture current response fields, without carrying forward stale values or identities."""
    active = active if isinstance(active, dict) else {}
    raw_stats = active.get('championStats')
    stats: dict[str, float] = {}
    if isinstance(raw_stats, dict):
        for key in CHAMPION_STAT_FIELDS:
            value = _number(raw_stats.get(key))
            if value is not None:
                stats[key] = value
    gold = _number(active.get('currentGold'))
    return {
        'schema': 1,
        'level': _integer(active.get('level')),
        'current_gold': gold if gold is not None and gold >= 0 else None,
        'champion_stats': stats,
        'players': players,
    }


_ids = None


def item_names_by_id():
    """{itemID: nume} din itemele de Mayhem (data/item-ids.json).

    Cheia e id-ul, nu textul: displayName vine in limba clientului si cateva
    iteme au nume diferit in joc fata de datele noastre, iar un nume care nu
    se potriveste inseamna "itemul asta nu l-am detectat". Id-ul nu greseste.
    """
    global _ids
    if _ids is None:
        try:
            path = pathlib.Path(__file__).with_name("data") / "item-ids.json"
            _ids = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _ids = {}
    return _ids


def item_label(item):
    """Numele cu care recunoastem itemul: dupa id daca il stim, altfel cel din joc."""
    return item_names_by_id().get(str(item.get("itemID"))) or item.get("displayName")


def get(path):
    """JSON-ul de la endpoint, sau None daca jocul nu e pornit / nu raspunde."""
    try:
        r = requests.get(BASE + path, timeout=2, verify=False)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except ValueError:
        return None


def get_roster():
    """{allies, enemies, local_champion} sau None daca jocul nu ruleaza.

    'allies'/'enemies' sunt liste de nume de campioni (numele Riot intern,
    ex. 'MonkeyKing' pentru Wukong -- normalizat separat la afisare).
    """
    players = get("/playerlist")
    active = get("/activeplayername")
    if not players:
        return None

    local_name = active if isinstance(active, str) and active else None

    def team_for(name):
        return next(
            (
                p.get("team")
                for p in players
                if name and name in (p.get("summonerName"), p.get("riotIdGameName"))
            ),
            None,
        )

    local_team = team_for(local_name)

    if local_team is None:
        # activeplayername poate lipsi in unele moduri; fallback simplu:
        # jucatorul local e cel al carui items/abilities sunt disponibile
        active_full = get("/activeplayer")
        if isinstance(active_full, dict):
            local_name = (
                active_full.get("summonerName") or active_full.get("riotIdGameName") or local_name
            )
            local_team = team_for(local_name)

    allies, enemies, local_champ = [], [], None
    enemy_items, ally_items, own_items, spell_augments = [], [], [], []
    snapshots: list[PlayerSnapshot] = []
    for index, p in enumerate(players):
        champ = p.get("championName")
        if not champ:
            continue
        is_local = bool(local_name) and local_name in (
            p.get("summonerName"),
            p.get("riotIdGameName"),
        )
        if is_local:
            local_champ = champ
        snapshots.append(
            {
                'index': index,
                'champion': champ,
                'team': 'unknown'
                if local_team not in ('ORDER', 'CHAOS') or p.get('team') not in ('ORDER', 'CHAOS')
                else ('ally' if p.get('team') == local_team else 'enemy'),
                'is_local': is_local,
                'level': _integer(p.get('level')),
                'items': _inventory(p.get('items')),
            }
        )
        if local_team is None:
            continue

        names = [label for label in (item_label(i) for i in (p.get("items") or [])) if label]
        if p.get("team") == local_team:
            allies.append(champ)
            if is_local:
                own_items.extend(names)  # ce ai deja cumparat
                # augmentele care dau un summoner spell (Clown College, Brass Blast...) se vad in numele lui
                spell_augments = [
                    m.group(1)
                    for sp in (p.get("summonerSpells") or {}).values()
                    for m in [
                        re.search(
                            r"Augment_ARAM_([A-Za-z0-9]+?)_", str(sp.get("rawDisplayName") or "")
                        )
                    ]
                    if m
                ]
            else:
                # itemii coechipierilor conteaza pentru golurile de echipa:
                # daca nimeni n-a luat anti-heal, trebuie sa-l iei tu
                ally_items.extend(names)
        else:
            enemies.append(champ)
            # itemii chiar cumparati de inamici: semnal mult mai bun
            # decat tipul campionului cand alegem contra-itemi
            enemy_items.extend(names)

    if local_team is None:
        # nu am putut determina echipa: mai bine gol decat gresit
        return {
            "allies": [],
            "enemies": [],
            "enemy_items": [],
            "ally_items": [],
            "own_items": own_items,
            "spell_augments": spell_augments,
            "local_champion": local_champ,
            'players': snapshots,
        }

    return {
        "allies": allies,
        "enemies": enemies,
        "enemy_items": enemy_items,
        "ally_items": ally_items,
        "own_items": own_items,
        "spell_augments": spell_augments,
        "local_champion": local_champ,
        'players': snapshots,
    }
