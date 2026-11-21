"""Short, deterministic resident memories shared by actions and orders."""


def remember(w, agent, text, *, topic=None):
    memories = agent.setdefault("memories", [])
    memories.append({"tick": w["tick"], "text": f"第{w['tick'] // 144 + 1}天，{text}"})
    if topic is not None:
        memories[-1]["topic"] = topic
    del memories[:-10]
