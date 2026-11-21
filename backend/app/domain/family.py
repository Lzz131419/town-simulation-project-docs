"""Household life and invitations, persisted entirely in the world snapshot."""
from math import hypot

from ..balance import balance
from .memories import remember
from .rules import emit
from .weather import next_random


def same_family(a, b):
    group = (a.get('family') or {}).get('group')
    return bool(group and a['id'] != b['id'] and group == (b.get('family') or {}).get('group'))


def members(w, a):
    return [a] + [b for b in w['agents'].values() if same_family(a, b)]


def day_number(w):
    return (w['tick'] + balance.weather.dawn_offset_ticks) // balance.weather.ticks_per_day


def state(w):
    return w.setdefault('family_state', {'groups': {}, 'invitations': {}})


def group_state(w, a):
    return state(w)['groups'].setdefault(a['family']['group'], {})


def change_relation(a, b, amount):
    floor = balance.family.relation_floor if same_family(a, b) else 0
    a['relations'][b['id']] = max(floor, min(100, a['relations'].get(b['id'], 30) + amount))


def social_blocked(w, a, b):
    return same_family(a, b) and group_state(w, a).get('quarrel_day') == day_number(w)


def reconcile(w, a, b, events):
    if not same_family(a, b):
        return False
    household = group_state(w, a)
    since = household.get('quarrel_tick')
    if since is None or not 0 <= w['tick'] - since <= balance.family.reconciliation_ticks:
        return False
    household.pop('quarrel_tick')
    for left, right in ((a, b), (b, a)):
        change_relation(left, right, balance.family.reconciliation_gain)
        remember(w, left, f"与{right['name']}又和好了")
    emit(events, w, a, 'family', f"{a['name']}和{b['name']}两人又和好了",
         kind='reconcile', participants=[a['id'], b['id']], relationship_change=balance.family.reconciliation_gain)
    return True


def family_dawn(w, events):
    seen = set()
    for a in w['agents'].values():
        group = (a.get('family') or {}).get('group')
        if not group or group in seen:
            continue
        seen.add(group)
        household = group_state(w, a)
        if household.get('dawn_day') == day_number(w):
            continue
        household['dawn_day'] = day_number(w)
        relatives = [b for b in members(w, a) if b['id'] != a['id']]
        for b in relatives:
            if min(a['relations'].get(b['id'], 80), b['relations'].get(a['id'], 80)) >= balance.family.quarrel_threshold:
                continue
            if next_random(w) >= balance.family.quarrel_probability:
                continue
            household.update(quarrel_tick=w['tick'], quarrel_day=day_number(w))
            text = f"{a['name']}和{b['name']}拌了嘴"
            for person in (a, b):
                person['hunger'] = min(100, person['hunger'] + balance.family.quarrel_hunger)
                remember(w, person, text, topic='dispute')
            emit(events, w, a, 'family', text, kind='quarrel', participants=[a['id'], b['id']])


def maybe_family_meal(w, events):
    from .homes import owned_home, home_destination
    hour = ((w['tick'] * 10 + 480) % 1440) / 60
    if not balance.events.feast_start_hour <= hour < balance.events.feast_end_hour:
        return
    day = day_number(w)
    seen = set()
    for a in w['agents'].values():
        group = (a.get('family') or {}).get('group')
        if not group or group in seen:
            continue
        seen.add(group)
        family = members(w, a)
        household = group_state(w, a)
        meals = [d for d in household.get('meal_days', []) if d // 7 == day // 7]
        home = owned_home(w, a)
        if len(family) < 2 or not home or day in meals or len(meals) >= balance.family.meals_per_week:
            continue
        door = home_destination(w, a)
        if any(b.get('home_id') != home['id'] or b.get('shared_meal_day') == day
               or b.get('sleeping') or hypot(b['x'] - door['x'], b['y'] - door['y']) > balance.family.meal_radius
               for b in family):
            continue
        household['meal_days'] = meals + [day]
        for b in family:
            b['shared_meal_day'] = day
            b['hunger'] = max(0, b['hunger'] - balance.family.meal_hunger_relief)
            remember(w, b, '和家人一起吃了晚饭')
            for other in family:
                if other['id'] != b['id']:
                    change_relation(b, other, balance.family.meal_relation_gain)
        emit(events, w, a, 'family', '、'.join(b['name'] for b in family) + '和家人一起吃了晚饭',
             kind='meal', home_id=home['id'], participants=[b['id'] for b in family])
        for b in family[1:]:
            reconcile(w, a, b, events)


def maybe_invite(w, a, b, events):
    from .homes import owned_home
    host, guest = (a, b) if a['npc'] else (b, a)
    if not host['npc'] or guest['npc'] or not (host.get('family') or {}).get('group'):
        return
    home = owned_home(w, host)
    if not home or guest['relations'].get(host['id'], 30) < balance.family.invite_threshold:
        return
    key = host['family']['group'] + ':' + guest['id']
    previous = state(w)['invitations'].get(key)
    if previous and w['tick'] < previous['issued_tick'] + balance.family.invite_cooldown_ticks:
        return
    if next_random(w) >= balance.family.invite_probability:
        return
    invite = dict(group=host['family']['group'], host_id=host['id'], guest_id=guest['id'],
                  home_id=home['id'], issued_tick=w['tick'],
                  expires_tick=w['tick'] + balance.family.invite_duration_ticks, status='pending')
    state(w)['invitations'][key] = invite
    text = f"{host['name']}邀请{guest['name']}到家里做客（{balance.family.invite_duration_ticks} tick 内）"
    remember(w, guest, text)
    remember(w, host, f"邀请{guest['name']}到家里做客")
    emit(events, w, host, 'invite', text, kind='issued', **invite)


def pending_invite(w, guest, host):
    if guest['npc'] or same_family(guest, host):
        return None
    for invite in state(w)['invitations'].values():
        if (invite['status'] == 'pending' and invite['guest_id'] == guest['id']
                and invite['group'] == (host.get('family') or {}).get('group')
                and invite['home_id'] == host.get('home_id') and w['tick'] <= invite['expires_tick']):
            return invite
    return None


def accept_invite(w, guest, host, events):
    from .homes import home_destination
    invite = pending_invite(w, guest, host)
    if not invite:
        return False
    door = home_destination(w, host)
    if hypot(guest['x'] - door['x'], guest['y'] - door['y']) > 4:
        return False
    invite['status'] = 'accepted'
    family = members(w, host)
    for person in family:
        change_relation(person, guest, balance.family.invite_relation_gain)
        change_relation(guest, person, balance.family.invite_relation_gain)
        remember(w, person, f"招待{guest['name']}到家里吃饭")
    guest['hunger'] = max(0, guest['hunger'] - balance.family.invite_hunger_relief)
    text = f"{guest['name']}应邀到{host['name']}家做客，被招待了一顿饭"
    remember(w, guest, text)
    emit(events, w, guest, 'invite', text, kind='accepted', participants=[guest['id']] + [a['id'] for a in family], **invite)
    return True


def expire_invites(w, events):
    for invite in state(w)['invitations'].values():
        if invite['status'] != 'pending' or w['tick'] <= invite['expires_tick']:
            continue
        invite['status'] = 'expired'
        host, guest = w['agents'].get(invite['host_id']), w['agents'].get(invite['guest_id'])
        if not host or not guest:
            continue
        change_relation(host, guest, -balance.family.invite_expiry_loss)
        change_relation(guest, host, -balance.family.invite_expiry_loss)
        text = f"{guest['name']}错过了{host['name']}家的邀请，有些失礼"
        remember(w, host, text)
        remember(w, guest, text)
        emit(events, w, host, 'invite', text, kind='expired', **invite)
