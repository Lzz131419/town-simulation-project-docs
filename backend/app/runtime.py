from .infrastructure.async_io import settled_thread, run_blocking
import asyncio
import json
import time
from copy import deepcopy
from sqlalchemy import select
from .database import Session
from .models import World, Event, LoginSession, Departure
from .engine import tick_world, check_invariants
from .security import digest
from .realtime.protocol import personalize, delta
from .telemetry import metrics, log
from .services.history import sample_world


class TownRuntime:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.clients = {}
        self.calls = {}
        self.send_timeout = 1
        self.last_tick_at = None
        self.last_cycle_failed = False

    def online(self, uid):
        return any(
            v["uid"] == uid and time.monotonic() - v["seen"] < 20
            for v in tuple(self.clients.values())
        )

    def user_ids(self):
        return {v["uid"] for v in tuple(self.clients.values()) if self.online(v["uid"])}

    def valid_connection(self, ws):
        v = self.clients.get(ws)
        if not v:
            return False
        with Session() as db:
            s = db.get(LoginSession, v["session"])
            return bool(s and s.expires > time.time())

    def connect(self, ws, uid, token, protocol=1):
        self.clients[ws] = {
            "uid": uid,
            "seen": time.monotonic(),
            "session": digest(token),
            "protocol": protocol,
            "queue": asyncio.Queue(maxsize=1),
            "sender": None,
            "send_lock": asyncio.Lock(),
            "baseline": None,
            "generation": 0,
        }
        metrics.set("online_players", len(self.user_ids()))

    def disconnect(self, ws):
        v = self.clients.pop(ws, None)
        if v:
            sender = v.get("sender")
            if sender and sender is not asyncio.current_task():
                sender.cancel()
            if not self.online(v["uid"]):
                self.cancel_calls(v["uid"])
        metrics.set("online_players", len(self.user_ids()))

    def cancel_calls(self, uid):
        task = self.calls.get(uid)
        if task and task is not asyncio.current_task():
            task.cancel()

    def record_departure(self, uid):
        if self.online(uid):
            return
        with Session.begin() as db:
            w = db.get(World, 1)
            if not w:
                return
            a = w.data["agents"][uid]
            point = {"tick": w.data["tick"], "cash": a["cash"], "completed": a["completed"]}
            row = db.get(Departure, uid)
            if row:
                row.checkpoint = point
            else:
                db.add(Departure(user_id=uid, checkpoint=point))

    async def disconnect_session(self, sid):
        for ws, v in list(self.clients.items()):
            if v["session"] == sid:
                self.disconnect(ws)
                try:
                    await asyncio.wait_for(ws.close(code=4001), self.send_timeout)
                except Exception:
                    pass

    @staticmethod
    def _read(db, row):
        events = db.scalars(select(Event).order_by(Event.id.desc()).limit(60)).all()
        return {
            "type": "world",
            "revision": row.revision,
            "world": deepcopy(row.data),
            "events": [
                {
                    "id": e.id,
                    "tick": e.tick,
                    "actor_id": e.actor_id,
                    "type": e.type,
                    "text": e.text,
                    "details": e.details,
                }
                for e in events
            ],
        }

    def _snapshot(self):
        with Session() as db:
            return self._read(db, db.get(World, 1))

    def snapshot(self, uid):
        return personalize(self._snapshot(), uid, self.user_ids())

    def _commit(self, fn):
        with metrics.duration("transaction"):
            with Session.begin() as db:
                row = db.get(World, 1)
                w = deepcopy(row.data)
                events = []
                result = fn(w, events)
                check_invariants(w)
                row.data = w
                row.revision += 1
                for e in events:
                    db.add(Event(**e))
                sample_world(db, w)
                db.flush()
                # One read per transaction, rather than one read per socket.
                packet = self._read(db, row)
            return result, packet

    async def mutate(self, fn):
        async with self.lock:
            # Keep the authoritative transaction serialized, off the event loop.
            # Cancellation must not release the lock while the worker still commits.
            (result, packet), cancelled = await settled_thread(self._commit, fn)
            self._publish(packet)
            if cancelled:
                raise asyncio.CancelledError
            return result

    def _publish(self, snapshot):
        online = self.user_ids()
        packets = {}
        for ws, v in list(self.clients.items()):
            if v["uid"] not in packets:
                packets[v["uid"]] = personalize(snapshot, v["uid"], online)
            q = v["queue"]
            if q.full():
                q.get_nowait()  # Replace stale pending state, never build an unbounded backlog.
                metrics.add("ws_coalesced_total")
            q.put_nowait(packets[v["uid"]])
            if v["sender"] is None or v["sender"].done():
                v["sender"] = asyncio.create_task(self._sender(ws, v))

    async def send(self, ws, packet):
        v = self.clients.get(ws)
        if v:
            async with v["send_lock"]:
                await asyncio.wait_for(ws.send_json(packet), self.send_timeout)

    async def _sender(self, ws, client):
        try:
            while self.clients.get(ws) is client:
                current = await client["queue"].get()
                baseline = client["baseline"]
                generation = client["generation"]
                if baseline and current["revision"] < baseline["revision"]:
                    continue
                packet = (
                    delta(baseline, current) if baseline and client["protocol"] == 2 else current
                )
                await self.send(ws, packet)
                if generation == client["generation"]:
                    client["baseline"] = current
                metrics.add("ws_packets_total")
                metrics.add("ws_bytes_total", len(json.dumps(packet, ensure_ascii=False).encode()))
        except asyncio.CancelledError:
            raise
        except Exception:
            metrics.add("ws_send_failures_total")
            self.disconnect(ws)
            await asyncio.to_thread(self.record_departure, client["uid"])
            try:
                await asyncio.wait_for(ws.close(code=4002), self.send_timeout)
            except Exception:
                pass

    async def broadcast(self):
        async with self.lock:
            packet = await run_blocking(self._snapshot)
            self._publish(packet)

    async def resync(self, ws):
        v = self.clients.get(ws)
        if v:
            v["generation"] += 1
            v["baseline"] = None
            await self.broadcast()

    async def shutdown(self):
        tasks = [v["sender"] for v in self.clients.values() if v.get("sender")]
        for ws in list(self.clients):
            self.disconnect(ws)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def run(self, seconds):
        while True:
            await asyncio.sleep(seconds)
            try:
                for ws, v in list(self.clients.items()):
                    if time.monotonic() - v["seen"] >= 20 or not await run_blocking(
                        self.valid_connection, ws
                    ):
                        self.disconnect(ws)
                        await run_blocking(self.record_departure, v["uid"])
                        try:
                            await asyncio.wait_for(ws.close(code=4001), self.send_timeout)
                        except Exception:
                            pass
                with metrics.duration("tick"):
                    await self.mutate(tick_world)
                self.last_tick_at = time.monotonic()
                self.last_cycle_failed = False
                metrics.add("ticks_total")
                metrics.set("last_tick_timestamp", time.time())
            except asyncio.CancelledError:
                raise
            except Exception:
                self.last_cycle_failed = True
                metrics.add("tick_failures_total")
                log("tick_failed", reason="transaction_rolled_back")
                import logging

                logging.getLogger(__name__).exception("World tick failed; transaction rolled back")
