from ..infrastructure.async_io import run_blocking
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from sqlalchemy import select
from ..database import Session
from ..models import User, Event, Message
from ..domain.rules import need, emit
from ..domain.actions import validate_action
from ..domain.deliveries import REQUESTS, DAILY_LIMIT
from ..catalog import ACTIONS, ITEMS, PLACES
from .provider import ModelProvider


class AgentState(TypedDict, total=False):
    uid: str
    instruction: str
    purpose: str
    context: dict
    result: dict
    plan: list
    summary: str


class Planner:
    def __init__(self, runtime):
        self.runtime = runtime
        graph = StateGraph(AgentState)
        graph.add_node("context", self.context)
        graph.add_node("model", self.model)
        graph.add_node("validate", self.validate)
        graph.add_node("save", self.save)
        graph.add_edge(START, "context")
        graph.add_edge("context", "model")
        graph.add_edge("model", "validate")
        graph.add_edge("validate", "save")
        graph.add_edge("save", END)
        self.graph = graph.compile()

    async def context(self, state):
        uid = state["uid"]
        need(self.runtime.online(uid), "请保持在线连接后再调用AI")
        context = await run_blocking(self._context, uid)
        need(self.runtime.online(uid), "已离线，已停止读取规划上下文")
        return {"context": context}

    def _context(self, uid):
        snapshot = self.runtime.snapshot(uid)
        with Session() as db:
            u = db.get(User, uid)
            recent = db.scalars(
                select(Event).where(Event.actor_id == uid).order_by(Event.id.desc()).limit(12)
            ).all()
            inbox = db.scalars(
                select(Message)
                .where(Message.recipient_id == uid)
                .order_by(Message.id.desc())
                .limit(6)
            ).all()
            context = {
                "me": snapshot["world"]["agents"][uid],
                "goal": u.goal,
                "bio": u.bio,
                "market": snapshot["world"]["market"],
                "project": snapshot["world"]["project"],
                "neighbors": [
                    {"id": a["id"], "name": a["name"], "x": a["x"], "y": a["y"]}
                    for a in snapshot["world"]["agents"].values()
                    if a["id"] != uid
                ],
                "places": PLACES,
                "items": ITEMS,
                "allowed_actions": ACTIONS,
                "supply_requests": REQUESTS,
                "delivery_daily_limit": DAILY_LIMIT,
                "recent": [e.text for e in recent],
                "inbox": [{"from": m.sender_id, "text": m.text} for m in inbox],
            }
        return context

    async def model(self, state):
        try:
            async with asyncio.timeout(32):
                result = await self.call(
                    state["uid"], state["purpose"], state["instruction"], state["context"]
                )
            return {"result": result}
        except TimeoutError:
            raise ValueError("模型响应超时，请稍后重试；原计划保持不变") from None

    async def call(self, uid, purpose, instruction, context):
        return await ModelProvider(self.runtime).call(uid, purpose, instruction, context)

    async def validate(self, state):
        result = state["result"]
        need(isinstance(result, dict), "AI计划必须是对象")
        actions = result.get("actions")
        need(isinstance(actions, list) and len(actions) <= 8, "AI最多生成8步计划")
        need(
            isinstance(result.get("summary"), str) and len(result["summary"]) <= 1000,
            "AI需要返回简短说明",
        )
        return {"plan": [validate_action(a) for a in actions], "summary": result["summary"]}

    async def save(self, state):
        need(self.runtime.online(state["uid"]), "已离线，计划未写入")
        if state["purpose"] == "test":
            return {}

        def apply(w, events):
            need(self.runtime.online(state["uid"]), "已离线，计划未写入")
            a = w["agents"][state["uid"]]
            a["plan"] = state["plan"]
            a["last_outcome"] = state["summary"]
            # Planning is a proposal; activating rules remains an explicit player choice.
            emit(events, w, a, "plan", a["name"] + "生成了新的行动计划", steps=len(state["plan"]))

        await self.runtime.mutate(apply)
        return {}

    async def run(self, uid, instruction, purpose="plan"):
        need(uid not in self.runtime.calls, "已有模型请求正在进行")
        need(self.runtime.online(uid), "离线状态不能调用模型")

        async def invoke():
            return await self.graph.ainvoke(
                {"uid": uid, "instruction": instruction, "purpose": purpose}
            )

        task = asyncio.create_task(invoke())
        self.runtime.calls[uid] = task
        try:
            result = await task
            return {"summary": result["summary"], "actions": result["plan"]}
        finally:
            self.runtime.calls.pop(uid, None)
