"""Living between work and sleep, with deterministic decisions and no economy effects."""
from collections import Counter
from copy import deepcopy
import json
from random import Random

import pytest

from app.balance import balance
from app.catalog import ACTIONS, ITEMS, PLACES, initial_world
from app.database import Session
from app.domain.actions import execute, start_action, validate_action
from app.domain.homes import claim_home, home_destination
from app.domain.leisure import host_at_home
from app.domain.rules import check_invariants
from app.domain.scheduler import LEISURE_KINDS, _leisure_action, fallback_action, tick_world
from app.models import Event, World


def scene(kind='stroll'):
    world = initial_world()
    for person in world['agents'].values():
        person.update(mode='manual', x=100, y=100)
    agent = world['agents']['npc-1']
    place = PLACES[ACTIONS[kind]['place']]
    agent.update(x=place['x'], y=place['y'], energy=70, hunger=20)
    return world, agent, []


def set_hour(world, hour):
    world['tick'] = int((hour * 60 - 480) % 1440 / 10)


@pytest.mark.parametrize('kind,delta', [('stroll', -2), ('daydream', 2), ('shop_browse', -2)])
def test_solo_actions_effects_projection_and_no_money_or_goods(kind, delta):
    world, agent, events = scene(kind)
    before = deepcopy(world)
    start_action(world, agent, {'type': kind}, events)
    for _ in range(balance.leisure.stay_ticks + 1):
        tick_world(world, events)
    assert agent['energy'] == 70 + delta
    assert agent['activity'] == ACTIONS[kind]['name']
    event = next(e for e in events if e['type'] == 'leisure')
    assert event['details']['kind'] == kind
    assert agent['cash'] == before['agents'][agent['id']]['cash']
    assert agent['inventory'] == before['agents'][agent['id']]['inventory']
    assert world['market'] == before['market']
    assert world['treasury'] == before['treasury']
    assert world['activity_goal'] == before['activity_goal']
    assert agent['progress'] == before['agents'][agent['id']]['progress']
    check_invariants(world)


def test_daydream_caps_energy():
    world, agent, events = scene('daydream')
    agent['energy'] = 99
    execute(world, agent, {'type': 'daydream'}, events)
    assert agent['energy'] == 100


def test_browse_records_actual_discount_without_buying():
    world, agent, events = scene('shop_browse')
    execute(world, agent, {'type': 'shop_browse'}, events)
    d = events[-1]['details']
    assert d['price'] < d['base'] == ITEMS[d['item']]['buy']
    assert f"看到{ITEMS[d['item']]['name']}最近便宜" in agent['memories'][-1]['text']
    assert agent['memories'][-1]['topic'] == 'market_price'
    world['market'] = {item: 0 for item in ITEMS}
    count = len(agent['memories'])
    execute(world, agent, {'type': 'shop_browse'}, events)
    assert len(agent['memories']) == count
    assert 'item' not in events[-1]['details']


def home_pair():
    world, guest, events = scene('visit')
    host = world['agents']['npc-2']
    claim_home(world, host, events)
    door = home_destination(world, host)
    host.update(x=door['x'], y=door['y'])
    guest['relations'][host['id']] = 40
    return world, guest, host, events


def test_visit_routes_to_owned_door_relationships_and_both_memories():
    world, guest, host, events = home_pair()
    action = {'type': 'visit', 'target_id': host['id']}
    start_action(world, guest, action, events)
    door = home_destination(world, host)
    assert guest['path'][-1] == {'x': door['x'], 'y': door['y']}
    guest.update(x=door['x'], y=door['y'], path=[])
    tick_world(world, events)
    assert guest['task']['type'] == 'visit'  # Visible pause at the door.
    for _ in range(balance.leisure.stay_ticks):
        tick_world(world, events)
    assert guest['task'] is None
    assert guest['relations'][host['id']] == 44
    assert host['relations'][guest['id']] == 34
    assert f"去{host['name']}家里坐了坐" in guest['memories'][-1]['text']
    assert f"{guest['name']}来家里坐了坐" in host['memories'][-1]['text']
    assert events[-1]['details']['at_home'] is True


@pytest.mark.parametrize('asleep', [False, True])
def test_unavailable_host_redirects_to_plaza_without_relationship_gain(asleep):
    world, guest, host, events = home_pair()
    if asleep:
        host['sleeping'] = {'since_tick': 0, 'phase': 'light'}
    else:
        host.update(x=100, y=100)
    start_action(world, guest, {'type': 'visit', 'target_id': host['id']}, events)
    plaza = PLACES['plaza']
    assert guest['path'][-1] == {'x': plaza['x'], 'y': plaza['y']}
    guest.update(x=plaza['x'], y=plaza['y'])
    execute(world, guest, {'type': 'visit', 'target_id': host['id']}, events)
    assert guest['relations'][host['id']] == 40
    assert events[-1]['details']['at_home'] is False
    assert '改道' in events[-1]['text']


def test_host_leaving_during_travel_repaths_before_settlement():
    world, guest, host, events = home_pair()
    start_action(world, guest, {'type': 'visit', 'target_id': host['id']}, events)
    door = home_destination(world, host)
    guest.update(x=door['x'], y=door['y'], path=[])
    host.update(x=100, y=100)
    tick_world(world, events)
    assert guest['path'][-1] == {k: PLACES['plaza'][k] for k in ('x', 'y')}
    assert not any(e['type'] == 'leisure' for e in events)
    for _ in range(40):
        tick_world(world, events)
        if guest['task'] is None:
            break
    assert events[-1]['details']['at_home'] is False
    assert guest['relations'][host['id']] == 40


def test_visit_requires_relationship_and_owned_home():
    world, guest, host, events = home_pair()
    guest['relations'][host['id']] = 39
    with pytest.raises(ValueError, match='熟悉度'):
        start_action(world, guest, {'type': 'visit', 'target_id': host['id']}, events)
    with pytest.raises(ValueError, match='串门对象'):
        validate_action({'type': 'visit'})
    host['home_id'] = None
    assert not host_at_home(world, host)


def test_play_radius_all_pairs_and_hunger_with_boundary_exclusions():
    world, actor, events = scene('play')
    near, edge, outside, sleeping = [world['agents'][f'npc-{i}'] for i in (2, 3, 4, 5)]
    for person, dx, dy in ((near, 30, 40), (edge, 80, 0), (outside, 80.1, 0), (sleeping, 0, 0)):
        person.update(x=actor['x'] + dx, y=actor['y'] + dy)
    sleeping['sleeping'] = {'since_tick': 0, 'phase': 'light'}
    prior = deepcopy(world['agents'])
    execute(world, actor, {'type': 'play'}, events)
    for left in (actor, near, edge):
        assert left['hunger'] == prior[left['id']]['hunger'] + 3
        for right in (actor, near, edge):
            if left != right:
                assert left['relations'][right['id']] == 32
    assert outside == prior[outside['id']]
    assert sleeping == prior[sleeping['id']]
    assert actor['energy'] == 67
    assert set(events[-1]['details']['participants']) == {p['id'] for p in (actor, near, edge)}
    check_invariants(world)


def test_play_alone_recovers_one_after_three_cost_no_hunger_gain():
    world, actor, events = scene('play')
    execute(world, actor, {'type': 'play'}, events)
    assert actor['energy'] == 68
    assert actor['hunger'] == 20
    assert events[-1]['details']['group'] is False


@pytest.mark.parametrize('hour', [0, 5, 7, 8, 10, 12, 14, 17, 18, 21, 23])
def test_outside_windows_work_social_and_sleep_never_choose_leisure(hour):
    world, agent, _ = scene()
    set_hour(world, hour)
    assert _leisure_action(world, agent, hour, Random(1)) is None
    action = fallback_action(world, agent)
    assert action is None or action['type'] not in LEISURE_KINDS


@pytest.mark.parametrize('hour', [6, 15, 16, 19, 20])
def test_window_probability_and_personal_bedtime(monkeypatch, hour):
    world, agent, _ = scene()
    agent['personality'] = 'quiet'
    set_hour(world, hour)
    monkeypatch.setattr(balance.leisure, 'probability', 1)
    assert fallback_action(world, agent)['type'] in LEISURE_KINDS
    agent['sleeping'] = {'since_tick': world['tick'], 'phase': 'light'}
    assert fallback_action(world, agent) is None
    agent['sleeping'] = None
    agent['personality'] = 'introvert'
    if hour >= 19:
        assert fallback_action(world, agent)['type'] == 'rest'


def test_fixed_rng_personality_weights_and_diligent_half_chance():
    world, agent, host, _ = home_pair()
    set_hour(world, 15)
    results = {}
    for personality in ('introvert', 'sociable', 'generous', 'merchant', 'quiet', 'diligent', 'balanced'):
        agent['personality'] = personality
        rng = Random(1414)
        counts = Counter()
        for _ in range(3000):
            choice = _leisure_action(world, agent, 15, rng)
            counts[choice['type'] if choice else 'none'] += 1
        results[personality] = counts
    intro = results['introvert']
    assert intro['stroll'] + intro['daydream'] > 4 * (intro['visit'] + intro['play'])
    for personality in ('sociable', 'generous'):
        c = results[personality]
        assert c['visit'] + c['play'] > 4 * (c['stroll'] + c['daydream'])
    assert results['merchant']['shop_browse'] > 3 * results['merchant']['play']
    assert results['quiet']['daydream'] > 3 * results['quiet']['stroll']
    diligent = 3000 - results['diligent']['none']
    balanced = 3000 - results['balanced']['none']
    assert 0.4 < diligent / balanced < 0.6
    before = deepcopy(world)
    assert _leisure_action(world, agent, 15) == _leisure_action(world, agent, 15)
    assert world == before  # No climate RNG pollution from decision previews.


def test_diligent_can_relax_before_work_override(monkeypatch):
    world, agent, _ = scene()
    set_hour(world, 15)
    agent['personality'] = 'diligent'
    monkeypatch.setattr(balance.leisure, 'probability', 1)
    monkeypatch.setattr(balance.leisure, 'diligent_multiplier', 1)
    assert fallback_action(world, agent)['type'] in LEISURE_KINDS


def test_economy_api_ignores_leisure_even_with_amount(auth):
    with Session.begin() as db:
        world = db.get(World, 1)
        data = deepcopy(world.data)
        data['tick'] = 4
        world.data = data
        db.add(Event(tick=4, actor_id='wangjue', type='leisure', text='闲逛',
                     details={'kind': 'shop_browse', 'amount': 999, 'quantity': 4, 'unit_price': 25, 'outputs': {'grain': 99}}))
        db.add(Event(tick=4, actor_id='wangjue', type='sell', text='出售', details={'amount': 7}))
    result = auth.get('/api/report/economy').json()
    assert result['totals']['trade_amount'] == 7
    assert result['totals']['trade_count'] == 1
    assert result['totals']['production'] == {}


def test_offline_proxy_executes_life_and_return_summary(auth, monkeypatch):
    from app.services.proxy_life import depart, summarize
    monkeypatch.setattr(balance.leisure, 'probability', 1)
    world, _, events = scene()
    set_hour(world, 15)
    agent = world['agents']['wangjue']
    agent.update(x=PLACES['meadow']['x'], y=PLACES['meadow']['y'])
    # Fix only the weighted selection; real fallback, movement, hold and effects run.
    monkeypatch.setattr(Random, 'choices', lambda self, population, **kwargs: ['stroll'])
    with Session.begin() as db:
        assert depart(db, world, agent['id'])
        point = {'tick': world['tick'], 'cash': agent['cash'], 'completed': agent['completed']}
        for _ in range(5):
            tick_world(world, events)
        assert any(e['type'] == 'leisure' and e['actor_id'] == agent['id'] for e in events)
        db.add_all(Event(**e) for e in events)
        db.flush()
        result = summarize(db, world, agent['id'], point)
        assert '你去河边散了步' in result['summary']['events']
        assert result['summary']['earned'] == 0 and result['summary']['spent'] == 0
    check_invariants(world)


def test_three_days_replay_preserves_invariants_and_all_npcs_live():
    world, events = initial_world(), []
    for _ in range(144):
        tick_world(world, events)
    restored = json.loads(json.dumps(world))
    replay, rest = [], []
    for _ in range(288):
        tick_world(world, rest)
        tick_world(restored, replay)
    assert world == restored and rest == replay
    assert {e['actor_id'] for e in events + rest if e['type'] == 'leisure'} >= {f'npc-{i}' for i in range(1, 7)}
    check_invariants(world)


def test_play_solo_full_energy_keeps_one_point_recovery():
    world, actor, events = scene('play')
    actor['energy'] = 100
    execute(world, actor, {'type': 'play'}, events)
    assert actor['energy'] == 98


def test_activity_survives_world_api_and_catalog_publishes_leisure(auth):
    with Session.begin() as db:
        row = db.get(World, 1)
        world = deepcopy(row.data)
        agent = world['agents']['npc-6']
        execute(world, agent, {'type': 'daydream'}, [])
        row.data = world
    response = auth.get('/api/world').json()
    assert response['world']['agents']['npc-6']['activity'] == '看着河水发呆'
    catalog = auth.get('/api/catalog').json()
    assert all(kind in catalog['actions'] for kind in LEISURE_KINDS)
    assert catalog['rules']['leisure']['probability'] == 0.4
