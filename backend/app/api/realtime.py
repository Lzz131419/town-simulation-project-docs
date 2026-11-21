import asyncio
from anyio import CancelScope
import time
from urllib.parse import urlsplit
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..security import COOKIE, find_user
from ..services.container import runtime

router = APIRouter()


def valid_origin(origin, host):
    if not origin:
        return True  # Native clients may omit Origin; authentication is still required.
    try:
        value = urlsplit(origin)
        return (
            value.scheme in ("http", "https")
            and value.netloc == host
            and not value.username
            and not value.password
            and value.path in ("", "/")
            and not value.query
            and not value.fragment
        )
    except ValueError:
        return False


@router.websocket("/api/ws")
async def socket(ws: WebSocket):
    if not valid_origin(ws.headers.get("origin"), ws.headers.get("host")):
        await ws.close(code=4403)
        return
    token = ws.cookies.get(COOKIE)
    u = await asyncio.to_thread(find_user, token)
    if not u:
        await ws.close(code=4401)
        return
    await ws.accept()
    protocol = 2 if ws.query_params.get("protocol") == "2" else 1
    runtime.connect(ws, u.id, token, protocol)
    try:
        summary = await runtime.return_summary(u.id, only_active=True)
        if summary:
            await runtime.send(ws, {"type": "return_summary", "summary": summary})
        if protocol == 1:
            await runtime.send(ws, await asyncio.to_thread(runtime.snapshot, u.id))
        await runtime.broadcast()
        while True:
            msg = await ws.receive_text()
            if ws not in runtime.clients or not await asyncio.to_thread(
                runtime.valid_connection, ws
            ):
                break
            if msg == "ping":
                runtime.clients[ws]["seen"] = time.monotonic()
                await runtime.send(ws, {"type": "pong"})
            elif msg == "resync":
                await runtime.resync(ws)
    except (WebSocketDisconnect, RuntimeError, TimeoutError):
        pass
    finally:
        runtime.disconnect(ws)
        # Socket teardown must finish the durable checkpoint even if cancelled.
        with CancelScope(shield=True):
            await runtime.record_departure(u.id)
        try:
            await ws.close()
        except (RuntimeError, WebSocketDisconnect):
            pass
