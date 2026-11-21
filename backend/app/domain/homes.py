"""Stable homes derived from shared artwork; doors remain outside collision walls."""
from ..balance import balance
from ..world_map import LAYOUT
from ..pathfinding import nearest_walkable
from .perishables import inv_qty, inv_take


def new_homes():
    return [dict(id=b['id'].replace('house-', 'home-'), x=b['x'] + b['w'] / 2,
                 y=b['y'] + b['h'] / 2, level=1, owner_id=None)
            for b in LAYOUT['buildings'] if b['kind'] == 'home']


def owned_home(w, a):
    from .family import same_family
    return next((h for h in w.get('homes', [])
                 if h['id'] == a.get('home_id') and (h.get('owner_id') == a['id']
                 or (h.get('owner_id') in w['agents'] and same_family(a, w['agents'][h['owner_id']])))), None)


def available_home(w, a):
    from .family import same_family
    shared = next((owned_home(w, b) for b in w['agents'].values()
                   if same_family(a, b) and owned_home(w, b)), None)
    return shared or owned_home(w, a) or min(
        (h for h in w.get('homes', []) if h.get('owner_id') is None),
        key=lambda h: ((h['x'] - a['x']) ** 2 + (h['y'] - a['y']) ** 2, h['id']),
        default=None)


def home_destination(w, a):
    home = available_home(w, a)
    if home:
        building = next(b for b in LAYOUT['buildings'] if b['id'] == home['id'].replace('home-', 'house-'))
        x, y = nearest_walkable(home['x'], building['y'] + building['h'] + 16)
        return {'x': x, 'y': y, 'name': a['name'] + '的家'}
    x, y = nearest_walkable(423, 450)  # south-west plaza bench, below the seat
    return {'x': x, 'y': y, 'name': '广场长椅'}


def claim_home(w, a, events):
    from .rules import emit
    from .memories import remember
    home = available_home(w, a)
    if home and not owned_home(w, a):
        from .family import members
        if home['owner_id'] is None:
            home['owner_id'] = a['id']
        for member in members(w, a):
            member['home_id'] = home['id']
        text = f"{a['name']} 在南岸安了家"
        emit(events, w, a, 'home_claimed', text, home_id=home['id'], level=home['level'])
        remember(w, a, text)
    return home


def sleep_multiplier(w, a):
    home = owned_home(w, a)
    return balance.homes.sleep_multipliers[home['level'] - 1] if home else balance.homes.bench_sleep_multiplier


def upgrade_cost(home):
    return balance.homes.upgrades.get(home['level']) if home else None


def wants_upgrade(w, a):
    cost = upgrade_cost(owned_home(w, a))
    return (a.get('personality') in {'diligent', 'generous'} and cost is not None
            and a['cash'] > a['policy']['reserve'] * 3
            and a['cash'] - cost.cash >= a['policy']['reserve']
            and inv_qty(a['inventory'], 'wood') >= cost.wood)


def upgrade_home(w, a, events, automatic=False):
    from .rules import need
    from .memories import remember
    home = owned_home(w, a)
    need(home is not None, '请先回家睡一次，认领住宅')
    cost = upgrade_cost(home)
    need(cost is not None, '住宅已经达到3级')
    target = home_destination(w, a)
    need(abs(a['x'] - target['x']) + abs(a['y'] - target['y']) < 1, '请先回到自己家中')
    need(inv_qty(a['inventory'], 'wood') >= cost.wood, '升级所需木材不足')
    need(a['cash'] >= cost.cash, '升级所需镇币不足')
    if automatic:
        need(a['cash'] - cost.cash >= a['policy']['reserve'], '升级超出保留余额')
    inv_take(a['inventory'], 'wood', cost.wood)
    a['cash'] -= cost.cash
    w['treasury'] += cost.cash  # preserve existing money conservation invariant
    a['spent_today'] += cost.cash
    home['level'] += 1
    text = f"{a['name']} 的家升到了 {home['level']} 级"
    remember(w, a, text)
    return text, dict(home_id=home['id'], level=home['level'], wood=cost.wood, amount=cost.cash)


def dawn_meal(w, a):
    home = owned_home(w, a)
    if home and home['level'] == 3:
        a['hunger'] = max(0, a['hunger'] - balance.homes.dawn_hunger_relief)
