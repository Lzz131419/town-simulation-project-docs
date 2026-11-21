"""Weekly fair lifecycle, transfers, progression and replay safety."""
from copy import deepcopy
import math
import pytest
from app.balance import balance
from app.catalog import ITEMS, PLACES, initial_world
from app.domain.actions import execute
from app.domain.deliveries import settle_delivery
from app.domain.economy import price
from app.domain.fortune import draw_daily_event
from app.domain.market_day import is_market_day
from app.domain.migration import upgrade_world
from app.domain.orders import fill_order, post_order
from app.domain.perishables import inv_add
from app.domain.progression import record_progress
from app.domain.rules import check_invariants
from app.domain.scheduler import tick_world


def world(fair=True):
    w = initial_world()
    for a in w['agents'].values():
        a['mode'] = 'manual'
    w['tick'] = 1104
    w['market_day'] = {'until_tick': 1248} if fair else {}
    return w


def test_eight_dawns_preview_open_expiry_and_weekly_repeat():
    w, events = world(False), []
    # Explicit zero-based days 1..8 (tick//144).
    w['tick'] = 239
    for day in range(1, 9):
        while w['tick'] < day * 144 + 96:
            tick_world(w, events)
        assert is_market_day(w) == (day == 7)
        record_progress(w, w['agents']['wangjue'], 'work', [])
        assert w['agents']['wangjue']['progress']['xp'] == 5 * (day + (day >= 7))
        check_invariants(w)
    notice = [e for e in events if e['details'].get('card', '').startswith('market_day')]
    assert [(e['tick'] // 144, e['details']['card']) for e in notice] == [
        (6, 'market_day_preview'), (7, 'market_day')]
    assert notice[0]['text'] == balance.market_day.preview_text
    assert notice[1]['details']['until_tick'] - notice[1]['tick'] == 144
    assert notice[1]['details']['market_day'] is True
    assert w['market_day'] == {}
    for day in (14, 21):
        w['tick'] = day * 144 + 95
        tick_world(w, events)
        assert is_market_day(w)


def test_no_day_zero_fair_and_expiry_without_cleanup():
    w = world(False)
    w['tick'] = 95
    tick_world(w, [])
    assert not is_market_day(w)
    w.update(tick=1248, market_day={'until_tick': 1248})
    assert not is_market_day(w)
    a = w['agents']['wangjue']
    record_progress(w, a, 'work', [])
    assert a['progress']['xp'] == 5


def test_sell_bonus_quote_pure_transfer_and_actual_event_quote():
    w, events = world(False), []
    w['market']['furniture'] = 8
    normal, buy = price(w, 'furniture', 'sell'), price(w, 'furniture', 'buy')
    w['market_day'] = {'until_tick': 1248}
    before = deepcopy(w)
    quote = price(w, 'furniture', 'sell')
    assert quote == math.floor(normal * 1.1 + .5) > normal
    assert price(w, 'furniture', 'buy') == buy and w == before
    a = w['agents']['wangjue']
    inv_add(a['inventory'], 'furniture', 2)
    cash, treasury = a['cash'], w['treasury']
    execute(w, a, {'type': 'sell', 'item': 'furniture', 'quantity': 2}, events)
    assert (a['cash'] - cash, treasury - w['treasury']) == (quote * 2, quote * 2)
    assert events[-1]['details']['unit_price'] == quote
    assert events[-1]['details']['market_day'] is True
    check_invariants(w)
    w['tick'], w['market']['furniture'] = 1248, 8
    assert price(w, 'furniture', 'sell') == normal


def test_fair_prices_keep_positive_spread():
    w = world()
    for item in ITEMS:
        if item != 'spoiled':
            for stock in (0, 8, 20, 1000):
                w['market'][item] = stock
                assert 1 <= price(w, item, 'sell') < price(w, item, 'buy')


def test_public_delivery_double_reward_event_and_progress():
    w, events = world(), []
    a = w['agents']['wangjue']
    inv_add(a['inventory'], 'bread', 3)
    cash, treasury = a['cash'], w['treasury']
    execute(w, a, {'type': 'delivery', 'item': 'bread'}, events)
    assert a['cash'] - cash == treasury - w['treasury'] == 24
    assert a['progress']['xp'] == 20 and a['progress']['metrics']['supply'] == 2
    assert {k: events[-1]['details'][k] for k in ('amount', 'item', 'quantity', 'unit_price', 'market_day')} == {'amount': 24, 'item': 'bread', 'quantity': 3,
                                    'unit_price': 8, 'market_day': True}
    assert '24镇币' in events[-1]['text']
    check_invariants(w)


def test_delivery_double_budget_is_checked_before_consumption():
    w = world()
    a = w['agents']['wangjue']
    inv_add(a['inventory'], 'bread', 3)
    a['cash'] += w['treasury'] - 12
    w['treasury'] = 12
    before = deepcopy(w)
    with pytest.raises(ValueError, match='预算不足'):
        settle_delivery(w, a, 'bread', [])
    assert w == before
    check_invariants(w)


def test_progress_metrics_xp_and_milestone_bonus_double_once():
    w, events = world(), []
    a = w['agents']['wangjue']
    record_progress(w, a, 'farm', events)
    assert a['progress'] == {'xp': 52, 'metrics': {'harvested': 6}, 'badges': ['grower']}
    assert events[-1]['details']['xp'] == 40
    record_progress(w, a, 'farm', events)
    assert a['progress']['xp'] == 64 and len(events) == 1


@pytest.mark.parametrize('distance,bonus', [(0, 2), (80, 2), (81, 0)])
def test_social_plaza_radius_and_both_relation_directions(distance, bonus):
    w, events = world(), []
    a, b = w['agents']['wangjue'], w['agents']['zhangguo']
    for person in (a, b):
        person.update(x=PLACES['plaza']['x'] + distance, y=PLACES['plaza']['y'])
    execute(w, a, {'type': 'social', 'target_id': b['id']}, events)
    assert a['relations'][b['id']] == b['relations'][a['id']] == 35 + bonus
    assert events[-1]['details']['relationship_change'] == 5 + bonus
    check_invariants(w)


def test_social_bonus_expires_and_relation_caps_at_100():
    w = world()
    a, b = w['agents']['wangjue'], w['agents']['zhangguo']
    for person in (a, b):
        person.update(x=PLACES['plaza']['x'], y=PLACES['plaza']['y'])
    a['relations'][b['id']] = 99
    execute(w, a, {'type': 'social', 'target_id': b['id']}, [])
    assert a['relations'][b['id']] == 100
    w['tick'] = 1248
    b['relations'][a['id']] = 30
    execute(w, a, {'type': 'social', 'target_id': b['id']}, [])
    assert b['relations'][a['id']] == 35


def test_card_pool_excludes_caravan_and_renormalizes_weights():
    w = world()
    cards = [draw_daily_event(w, [], (i + .5) / 75) for i in range(75)]
    assert {card: cards.count(card) for card in set(cards)} == {
        'bees': 20, 'flood': 15, 'dispute': 20, 'peaceful': 20}
    w['tick'] = 1248
    assert draw_daily_event(w, [], 0) == 'caravan'


@pytest.mark.parametrize('private', [True, False])
def test_escrow_orders_never_double_money(private):
    w, events = world(), []
    buyer, seller = w['agents']['npc-2'], w['agents']['wangjue']
    inv_add(seller['inventory'], 'fish', 2)
    options = {'private_to': seller['id'], 'total_reward': 7} if private else {}
    order = post_order(w, buyer, 'fish', 2, 3, events, **options)
    paid, cash = order['escrow'], seller['cash']
    fill_order(w, seller, order['id'], events)
    assert seller['cash'] == cash + paid and order['escrow'] == 0
    assert events[-1]['details']['amount'] == paid
    assert events[-1]['details']['market_day'] is True
    assert seller['progress']['metrics']['deliveries'] == 2
    check_invariants(w)


def test_legacy_upgrade_additive_idempotent_and_live_state_preserved():
    w = world()
    del w['market_day']
    assert upgrade_world(w) and w['market_day'] == {}
    w['market_day'] = {'until_tick': 1248}
    before = deepcopy(w)
    assert not upgrade_world(w) and w == before
    check_invariants(w)
