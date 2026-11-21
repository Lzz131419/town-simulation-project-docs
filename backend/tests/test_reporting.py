from copy import deepcopy

from app.balance import balance
from app.catalog import initial_world
from app.database import Session
from app.models import Event, World, WorldSample
from app.services.history import sample_world


def test_economy_report_aggregates_structured_events(auth):
    with Session.begin() as db:
        world = db.get(World, 1)
        data = deepcopy(world.data)
        data["tick"] = 300
        world.data = data
        db.add_all(
            [
                Event(
                    tick=10,
                    actor_id="wangjue",
                    type="buy",
                    text="buy",
                    details={"amount": 12, "item": "bread", "quantity": 3, "unit_price": 4},
                ),
                Event(
                    tick=20,
                    actor_id="wangjue",
                    type="farm",
                    text="farm",
                    details={"outputs": {"grain": 3}},
                ),
                Event(
                    tick=150,
                    actor_id="zhangguo",
                    type="order",
                    text="filled",
                    details={
                        "transaction_type": "filled",
                        "amount": 9,
                        "item": "wood",
                        "quantity": 2,
                        "unit_price": 4.5,
                    },
                ),
                Event(
                    tick=160,
                    actor_id="zhangguo",
                    type="levy",
                    text="levy",
                    details={"amount": 5},
                ),
                Event(
                    tick=170,
                    actor_id="zhangguo",
                    type="fiscal",
                    text="fiscal summary",
                    details={"amount": 5},
                ),
                Event(
                    tick=180,
                    actor_id="zhangguo",
                    type="spoilage",
                    text="spoilage",
                    details={"quantity": 2, "items": {"bread": 2}},
                ),
            ]
        )

    response = auth.get("/api/report/economy?days=7")
    assert response.status_code == 200
    payload = response.json()
    assert payload["start_tick"] == 0 and payload["end_tick"] == 300
    day_zero = next(day for day in payload["daily"] if day["day"] == 0)
    assert day_zero == {
        "day": 0,
        "trade_amount": 12,
        "trade_count": 1,
        "production": {"grain": 3},
        "levy_total": 0,
        "spoilage_loss": 0,
    }
    day_one = next(day for day in payload["daily"] if day["day"] == 1)
    assert day_one["trade_amount"] == 9
    assert day_one["trade_count"] == 1
    assert day_one["levy_total"] == 5
    assert day_one["spoilage_loss"] == 2
    assert payload["totals"] == {
        "trade_amount": 21,
        "trade_count": 2,
        "production": {"grain": 3},
        "levy_total": 5,
        "spoilage_loss": 2,
    }


def test_economy_report_auth_and_empty_data(client, auth):
    auth.post("/api/auth/logout")
    assert client.get("/api/report/economy").status_code == 401
    assert (
        client.post(
            "/api/auth/login", json={"username": "wangjue", "password": "wangjue"}
        ).status_code
        == 200
    )
    payload = auth.get("/api/report/economy").json()
    assert all(
        day["trade_amount"] == day["trade_count"] == day["levy_total"] == day["spoilage_loss"] == 0
        and day["production"] == {}
        for day in payload["daily"]
    )
    assert payload["totals"] == {
        "trade_amount": 0,
        "trade_count": 0,
        "production": {},
        "levy_total": 0,
        "spoilage_loss": 0,
    }


def test_sample_world_contains_dashboard_dimensions(client):
    world = initial_world()
    world["tick"] = balance.simulation.sample_interval_ticks
    with Session.begin() as db:
        sample_world(db, world)
        sample = db.get(WorldSample, world["tick"])
        assert sample is not None
        assert {
            "tick",
            "treasury",
            "resident_cash",
            "completed",
            "reputation",
            "market",
            "prices",
            "weather",
            "season",
        } <= sample.data.keys()
        assert sample.data["tick"] == world["tick"]
        assert sample.data["market"] == world["market"]
