"""Non-economic moments: no stock, cash, XP or trade counters are changed."""
import math

from ..catalog import ITEMS, PLACES
from ..balance import balance
from .economy import price
from .homes import owned_home, home_destination
from .memories import remember
from .rules import need
from .family import same_family, pending_invite, accept_invite


def visit_candidates(w, a):
    return [other for other in w['agents'].values()
            if other['id'] != a['id'] and not same_family(a, other)
            and (a['relations'].get(other['id'], 30) >= 40 or pending_invite(w, a, other))
            and owned_home(w, other)]


def host_at_home(w, other):
    if not other or not owned_home(w, other) or other.get('sleeping'):
        return False
    door = home_destination(w, other)
    return math.hypot(other['x'] - door['x'], other['y'] - door['y']) <= 2


def visit_destination(w, a, target_id):
    other = w['agents'].get(target_id)
    if other and (host_at_home(w, other) or pending_invite(w, a, other)):
        return home_destination(w, other)
    return PLACES['plaza']


def settle_leisure(w, a, action, events=None):
    events = events if events is not None else []
    kind = action['type']
    details = {'kind': kind}
    if kind == 'stroll':
        text = f"{a['name']}在河边散步"
    elif kind == 'daydream':
        details['energy_gain'] = 2
        text = f"{a['name']}看着河水发呆"
    elif kind == 'visit':
        other = w['agents'].get(action.get('target_id'))
        need(other is not None and other['id'] != a['id'], '请选择另一位小镇居民')
        need(other in visit_candidates(w, a), '只能去熟悉度至少40且已有住宅的邻居家串门')
        target = visit_destination(w, a, other['id'])
        need(math.hypot(a['x'] - target['x'], a['y'] - target['y']) <= 4, '请先到达串门地点')
        invited = accept_invite(w, a, other, events)
        at_home = invited or host_at_home(w, other)
        details.update(target_id=other['id'], at_home=at_home)
        if invited:
            details.update(invited=True, home_id=other['home_id'], relationship_change=balance.family.invite_relation_gain)
            text = f"{a['name']}应邀去{other['name']}家吃了饭"
        elif at_home:
            for left, right in ((a, other), (other, a)):
                left['relations'][right['id']] = min(100, left['relations'].get(right['id'], 30) + 4)
            remember(w, a, f"去{other['name']}家里坐了坐")
            remember(w, other, f"{a['name']}来家里坐了坐")
            text = f"{a['name']}去{other['name']}家里坐了坐"
            details['relationship_change'] = 4
        else:
            text = f"{a['name']}改道邻里广场坐了坐"
    elif kind == 'play':
        plaza = PLACES['plaza']
        need(math.hypot(a['x'] - plaza['x'], a['y'] - plaza['y']) <= 80, '请先到达广场')
        nearby = [person for person in w['agents'].values()
                  if not person.get('sleeping')
                  and math.hypot(person['x'] - plaza['x'], person['y'] - plaza['y']) <= 80]
        group = len(nearby) >= 2
        details.update(participants=[person['id'] for person in nearby], group=group)
        if group:
            for left in nearby:
                left['hunger'] = min(100, left['hunger'] + 3)
                for right in nearby:
                    if left['id'] != right['id']:
                        left['relations'][right['id']] = min(100, left['relations'].get(right['id'], 30) + 2)
            text = f"{a['name']}和邻居们在广场玩耍"
        else:
            details['energy_gain'] = 1
            text = f"{a['name']}在广场自娱自乐"
    else:  # shop_browse: remember an actual quote, never buy it.
        cheap = [item for item in sorted(ITEMS)
                 if w['market'].get(item, 0) > 0 and price(w, item, 'buy') < ITEMS[item]['buy']]
        text = f"{a['name']}在集市闲逛"
        if cheap:
            item = cheap[(w['tick'] // 4) % len(cheap)]
            remember(w, a, f"看到{ITEMS[item]['name']}最近便宜", topic='market_price')
            details.update(item=item, price=price(w, item, 'buy'), base=ITEMS[item]['buy'])
    return text, details
