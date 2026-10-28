"""Conservative build-profile matching for source-backed Mayhem shop items."""


def valid_catalog(catalog):
    return isinstance(catalog, dict) and all(
        isinstance(name, str)
        and isinstance(item, dict)
        and isinstance(item.get('categories', []), list)
        and all(isinstance(category, str) for category in item.get('categories', []))
        and isinstance(item.get('stats', {}), dict)
        and all(isinstance(n, (int, float)) for n in item.get('stats', {}).values())
        for name, item in catalog.items()
    )


def profile(build, roster, champion_tags, catalog, effects, augments):
    def offense(names):
        return (
            sum((catalog.get(n, {}).get('stats') or {}).get('ap', 0) for n in names),
            sum((catalog.get(n, {}).get('stats') or {}).get('ad', 0) for n in names),
        )

    ap, ad = offense(roster.get('own_items') or [])
    if not ap and not ad:
        ap, ad = offense(build.get('core') or [])
    if ap or ad:
        damage = 'AP' if ap > ad * 1.5 else 'AD' if ad > ap * 1.5 else 'mixed'
    else:
        meta = champion_tags.get(roster.get('local_champion')) or {}
        damage = 'tank' if 'Tank' in (meta.get('tags') or []) else meta.get('damageType', 'mixed')
    for augment in augments or []:
        damage = (effects.get(augment) or {}).get('damage', damage)
    return damage


def counter_pool(build, roster, champion_tags, catalog, effects, augments, item_stats):
    damage = profile(build, roster, champion_tags, catalog, effects, augments)
    likes = {(effects.get(a) or {}).get('likes') for a in augments or []}

    def rank(name):
        stats = catalog[name].get('stats') or {}
        ap, ad = stats.get('ap', 0), stats.get('ad', 0)
        if damage == 'AP':
            fit = (2 if ap else 1, ap)
        elif damage == 'AD':
            fit = (2 if ad else 1, ad)
        elif damage == 'tank':
            fit = (
                2 if not (ap or ad) else 1,
                stats.get('hp', 0) + stats.get('armor', 0) + stats.get('mr', 0),
            )
        else:
            fit = (1, max(ap, ad))
        synergy = bool(
            likes & {k for k in ('crit', 'onhit') if (item_stats.get(name) or {}).get(k)}
        )
        return fit[0], synergy, fit[1]

    candidates = []
    for name, item in catalog.items():
        if (
            item.get('acquisition') != 'shop'
            or not item.get('purchasable')
            or not item.get('isFinal')
        ):
            continue
        if {'Boots', 'Consumable'} & set(item.get('categories') or []):
            continue
        stats = item.get('stats') or {}
        if damage == 'AP' and stats.get('ad', 0) and not stats.get('ap', 0):
            continue
        if damage == 'AD' and stats.get('ap', 0) and not stats.get('ad', 0):
            continue
        candidates.append(name)
    # Stable ties preserve source order instead of set/hash ordering.
    return sorted(candidates, key=rank, reverse=True)
