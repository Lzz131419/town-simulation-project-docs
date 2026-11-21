"""Family integration: actions, migration, deterministic ticks and replay."""
from copy import deepcopy
import json
from unittest.mock import patch
import pytest
from app.catalog import initial_world, PLACES
from app.domain.actions import execute, start_action
from app.domain.family import (family_dawn, maybe_family_meal, maybe_invite,
                               expire_invites, social_blocked)
from app.domain.homes import claim_home, home_destination, owned_home, sleep_multiplier
from app.domain.initiatives import maybe_feast
from app.domain.leisure import visit_candidates, visit_destination
from app.domain.migration import upgrade_world
from app.domain.scheduler import tick_world, social_neighbor
from app.domain.sleep import begin_sleep, disturb
from app.domain.fortune import draw_daily_event


def scene():
    w, events = initial_world(), []
    for a in w['agents'].values():
        a.update(mode='manual', x=0, y=0)
        a['policy']['auto_eat'] = False
    return w, w['agents']['npc-2'], w['agents']['npc-5'], w['agents']['wangjue'], events


def home_family(w, a, b, events):
    claim_home(w, a, events)
    door = home_destination(w, a)
    for person in (a, b):
        person.update(x=door['x'], y=door['y'], hunger=60)
    return door


def invite_scene():
    w, a, b, guest, events = scene()
    door = home_family(w, a, b, events)
    guest.update(x=door['x'], y=door['y'], hunger=60)
    guest['relations'][a['id']] = a['relations'][guest['id']] = 60
    w['tick'] = 10
    with patch('app.domain.family.next_random', return_value=0):
        execute(w, guest, {'type': 'social', 'target_id': a['id']}, events)
    return w, a, b, guest, events


def quarrel_scene():
    w, a, b, guest, events = scene()
    home_family(w, a, b, events)
    a['relations'][b['id']] = b['relations'][a['id']] = 30
    w['tick'] = 96
    with patch('app.domain.family.next_random', return_value=0):
        family_dawn(w, events)
    return w, a, b, guest, events


def test_initial_families_and_players_unhoused():
    w, a, b, guest, _ = scene()
    assert a['family'] == b['family'] == {'group': 'a', 'kin': 'spouse'}
    assert a['relations'][b['id']] == b['relations'][a['id']] == 80
    assert all(a['home_id'] is None for a in w['agents'].values())
    assert guest['family'] == {'group': None, 'kin': None}


@pytest.mark.parametrize('first,second', [('npc-2', 'npc-5'), ('npc-5', 'npc-2'), ('npc-6', 'npc-4')])
def test_claim_shares_home_and_sleep_bonus(first, second):
    w, _, _, _, events = scene()
    a, b = w['agents'][first], w['agents'][second]
    claim_home(w, a, events)
    claim_home(w, b, events)
    assert a['home_id'] == b['home_id']
    assert sum(h['owner_id'] is not None for h in w['homes']) == 1
    assert len(events) == 1
    owned_home(w, a)['level'] = 2
    assert owned_home(w, a) == owned_home(w, b)
    assert home_destination(w, a) == dict(home_destination(w, b), name=a['name'] + '的家')
    assert sleep_multiplier(w, b) == 1.3


def test_shared_home_works_without_free_houses():
    w, a, b, _, events = scene()
    claim_home(w, a, events)
    for person in w['agents'].values():
        claim_home(w, person, events)
    assert all(h['owner_id'] for h in w['homes'])
    b['home_id'] = None
    claim_home(w, b, events)
    assert a['home_id'] == b['home_id']


def test_meal_window_distance_offline_and_once_daily():
    w, a, b, _, events = scene()
    home_family(w, a, b, events)
    b['online'] = False
    w['tick'] = 59
    maybe_family_meal(w, events)
    assert not any(e['type'] == 'family' for e in events)
    w['tick'] = 60
    b['x'] += 100
    maybe_family_meal(w, events)
    assert a['hunger'] == 60
    b['x'] -= 100
    maybe_family_meal(w, events)
    maybe_family_meal(w, events)
    assert a['hunger'] == b['hunger'] == 45
    assert a['relations'][b['id']] == 82
    assert a['memories'][-1]['text'].endswith('和家人一起吃了晚饭')
    assert len([e for e in events if e['type'] == 'family']) == 1


def test_meals_five_per_calendar_week_then_reset():
    w, a, b, _, events = scene()
    home_family(w, a, b, events)
    for day in range(7):
        w['tick'] = day * 144 + 60
        maybe_family_meal(w, events)
    assert len([e for e in events if e['type'] == 'family']) == 5
    w['tick'] = 7 * 144 + 60
    maybe_family_meal(w, events)
    assert len([e for e in events if e['type'] == 'family']) == 6


@pytest.mark.parametrize('first', ['feast', 'family'])
def test_feast_and_family_meals_never_stack(first):
    w, a, b, guest, events = scene()
    door = home_family(w, a, b, events)
    w['tick'] = 60
    if first == 'family':
        maybe_family_meal(w, events)
    for p in (a, b, guest):
        p.update(x=PLACES['plaza']['x'], y=PLACES['plaza']['y'])
    maybe_feast(w, events)
    if first == 'feast':
        for p in (a, b):
            p.update(x=door['x'], y=door['y'])
        maybe_family_meal(w, events)
    assert a['hunger'] == b['hunger'] == (40 if first == 'feast' else 45)
    assert not ({'family', 'feast'} <= {e['type'] for e in events})


@pytest.mark.parametrize('roll,relation,quarrel', [(0.149, 39, True), (0.15, 39, False), (0, 40, False)])
def test_dawn_probability_threshold_and_idempotence(roll, relation, quarrel):
    w, a, b, _, events = scene()
    a['relations'][b['id']] = b['relations'][a['id']] = relation
    w['tick'] = 96
    with patch('app.domain.family.next_random', return_value=roll):
        family_dawn(w, events)
        family_dawn(w, events)
    assert len(events) == int(quarrel)
    assert a['hunger'] == b['hunger'] == 20 + int(quarrel) * 5
    if quarrel:
        assert a['memories'][-1]['topic'] == 'dispute'
        assert social_blocked(w, a, b)
        a.update(x=500, y=500)
        b.update(x=500, y=500)
        assert social_neighbor(w, a) is None
        with pytest.raises(ValueError, match='拌了嘴'):
            execute(w, a, {'type': 'social', 'target_id': b['id']}, events)


@pytest.mark.parametrize('method', ['social', 'meal'])
def test_reconcile_once_within_two_days(method):
    w, a, b, _, events = quarrel_scene()
    w['tick'] = 240 if method == 'social' else 204
    if method == 'social':
        execute(w, a, {'type': 'social', 'target_id': b['id']}, events)
        assert a['relations'][b['id']] == 45
        execute(w, a, {'type': 'social', 'target_id': b['id']}, events)
        assert a['relations'][b['id']] == 50
    else:
        maybe_family_meal(w, events)
        assert a['relations'][b['id']] == 42
    assert [e['details']['kind'] for e in events if e['type'] == 'family'] == ['quarrel'] + (['meal'] if method == 'meal' else []) + ['reconcile']


def test_expired_reconcile_and_gossip():
    w, a, b, guest, events = quarrel_scene()
    guest.update(x=a['x'], y=a['y'])
    execute(w, guest, {'type': 'social', 'target_id': a['id']}, events)
    assert '拌了嘴' in events[-1]['details']['gossip']
    w['tick'] += 289
    execute(w, a, {'type': 'social', 'target_id': b['id']}, events)
    assert a['relations'][b['id']] == 35
    assert not any(e['details'].get('kind') == 'reconcile' for e in events)


def test_family_floor_in_daily_dispute_and_sleep_disturbance():
    w, a, b, _, events = scene()
    home_family(w, a, b, events)
    a['relations'][b['id']] = b['relations'][a['id']] = 20
    from itertools import combinations
    pairs = list(combinations(sorted(x['id'] for x in w['agents'].values() if x['npc']), 2))
    fraction = (pairs.index((a['id'], b['id'])) + .5) / len(pairs)
    draw_daily_event(w, events, roll=(60 + fraction * 20) / 100)
    assert events[-1]['details']['participants'] == [a['id'], b['id']]
    assert a['relations'][b['id']] == b['relations'][a['id']] == 20
    a['energy'] = 10
    begin_sleep(w, a, events)
    disturb(w, a, b, events)
    assert a['relations'][b['id']] == b['relations'][a['id']] == 20


def test_invite_social_arrival_rewards_all_once():
    w, a, b, guest, events = invite_scene()
    invite = next(iter(w['family_state']['invitations'].values()))
    assert invite['expires_tick'] == 58 and invite['home_id'] == a['home_id']
    before = deepcopy(guest['relations'])
    w['tick'] = 58
    execute(w, guest, {'type': 'visit', 'target_id': b['id']}, events)
    assert invite['status'] == 'accepted'
    assert guest['relations'][a['id']] == before[a['id']] + 8
    assert guest['relations'][b['id']] == before.get(b['id'], 30) + 8
    assert b['relations'][guest['id']] == 38 and guest['hunger'] == 50
    execute(w, guest, {'type': 'visit', 'target_id': a['id']}, events)
    assert guest['hunger'] == 50
    assert len([e for e in events if e['details'].get('kind') == 'accepted']) == 1


def test_invite_routes_home_when_host_away():
    w, a, b, guest, events = invite_scene()
    door = home_destination(w, a)
    a.update(x=0, y=0)
    b.update(x=0, y=0)
    assert visit_destination(w, guest, a['id']) == door
    start_action(w, guest, {'type': 'visit', 'target_id': a['id']}, events)
    execute(w, guest, {'type': 'visit', 'target_id': a['id']}, events)
    assert next(iter(w['family_state']['invitations'].values()))['status'] == 'accepted'


def test_expiry_household_cooldown_and_json_replay():
    w, a, b, guest, events = invite_scene()
    invite = next(iter(w['family_state']['invitations'].values()))
    old = guest['relations'][a['id']]
    w['tick'] = 58
    expire_invites(w, events)
    assert invite['status'] == 'pending'
    w['tick'] = 59
    expire_invites(w, events)
    expire_invites(w, events)
    assert invite['status'] == 'expired' and guest['relations'][a['id']] == old - 2
    assert len([e for e in events if e['details'].get('kind') == 'expired']) == 1
    guest['relations'][b['id']] = 80
    with patch('app.domain.family.next_random', return_value=0):
        w['tick'] = 441
        maybe_invite(w, b, guest, events)
        assert len([e for e in events if e['details'].get('kind') == 'issued']) == 1
        w['tick'] = 442
        maybe_invite(w, b, guest, events)
        assert len([e for e in events if e['details'].get('kind') == 'issued']) == 2
    restored = json.loads(json.dumps(w))
    for _ in range(50):
        left, right = [], []
        tick_world(w, left)
        tick_world(restored, right)
        assert left == right
    assert w == restored


@pytest.mark.parametrize('reason', ['poor_relation', 'no_home', 'roll'])
def test_invitation_prerequisites(reason):
    w, a, b, guest, events = scene()
    guest['relations'][a['id']] = 60
    if reason != 'no_home':
        home_family(w, a, b, events)
    if reason == 'poor_relation':
        guest['relations'][a['id']] = 59
    with patch('app.domain.family.next_random', return_value=.25 if reason == 'roll' else 0):
        maybe_invite(w, a, guest, events)
    assert not w['family_state']['invitations']


def test_visit_filters_family_and_preserves_invitation():
    w, a, b, guest, events = invite_scene()
    assert b not in visit_candidates(w, a)
    with pytest.raises(ValueError):
        start_action(w, a, {'type': 'visit', 'target_id': b['id']}, events)
    claim_home(w, b, events)
    assert next(iter(w['family_state']['invitations'].values()))['status'] == 'pending'


def test_migration_merges_legacy_homes_preserves_assets_idempotently():
    w, a, b, guest, events = scene()
    for person in w['agents'].values():
        person.pop('family')
    w.pop('family_state')
    a['relations'].pop(b['id'])
    b['relations'][a['id']] = 12
    claim_home(w, a, events)
    claim_home(w, b, events)
    owned_home(w, b)['level'] = 3
    old = deepcopy(w)
    assert upgrade_world(w)
    assert a['home_id'] == b['home_id'] and owned_home(w, a)['level'] == 3
    assert sum(h['owner_id'] is not None for h in w['homes']) == 1
    assert a['relations'][b['id']] == 80 and b['relations'][a['id']] == 20
    for uid, person in w['agents'].items():
        for key in ('cash', 'inventory', 'plan', 'task'):
            assert person[key] == old['agents'][uid][key]
    snapshot = deepcopy(w)
    assert upgrade_world(w) is False and w == snapshot


def test_scheduler_runs_meal_and_invite_expiry():
    w, a, b, guest, events = quarrel_scene()
    w['tick'] = 203
    tick_world(w, events)
    assert any(e['type'] == 'family' and e['details']['kind'] == 'meal' for e in events)
    w, a, b, guest, events = invite_scene()
    w['tick'] = 58
    tick_world(w, events)
    assert next(iter(w['family_state']['invitations'].values()))['status'] == 'expired'


def test_invite_deadline_is_arrival_not_end_of_leisure_pause():
    w, a, b, guest, events = invite_scene()
    start_action(w, guest, {'type': 'visit', 'target_id': a['id']}, events)
    w['tick'] = 57
    tick_world(w, events)
    assert next(iter(w['family_state']['invitations'].values()))['status'] == 'accepted'
    assert guest['task'] is None


def test_one_family_member_at_feast_prevents_whole_family_meal():
    w, a, b, guest, events = scene()
    door = home_family(w, a, b, events)
    w['tick'] = 60
    other = w['agents']['npc-1']
    for p in (a, guest, other):
        p.update(x=PLACES['plaza']['x'], y=PLACES['plaza']['y'])
    maybe_feast(w, events)
    a.update(x=door['x'], y=door['y'])
    maybe_family_meal(w, events)
    assert b['hunger'] == 60
    assert not any(e['type'] == 'family' for e in events)


def test_scheduler_quarrel_at_dawn_uses_persisted_random():
    w, a, b, _, events = scene()
    a['relations'][b['id']] = b['relations'][a['id']] = 30
    w['tick'] = 95
    with patch('app.domain.family.next_random', return_value=0):
        tick_world(w, events)
    assert any(e['type'] == 'family' and e['details']['kind'] == 'quarrel' and e['tick'] == 96 for e in events)


def test_partial_family_fields_are_filled_without_resetting_life_state():
    w, a, b, guest, events = invite_scene()
    a['family'].pop('kin')
    w['family_state'].pop('groups')
    invite = deepcopy(w['family_state']['invitations'])
    assert upgrade_world(w)
    assert a['family']['kin'] == 'spouse'
    assert w['family_state']['invitations'] == invite
    assert upgrade_world(w) is False
