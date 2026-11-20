"""External response parsing has no access to game state or tools."""

import json


def parse_response(raw):
    try:
        payload = json.loads(raw)
        content = payload["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError
        if content.strip().startswith("```"):
            content = content.strip().split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(content)
        if not isinstance(result, dict):
            raise TypeError
        usage = payload.get("usage") or {}
        if not isinstance(usage, dict):
            raise TypeError
        counts = [usage.get(k, 0) for k in ("prompt_tokens", "completion_tokens")]
        if any(type(n) is not int or n < 0 for n in counts):
            raise TypeError
        return result, counts, bool(usage)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        raise ValueError("模型返回格式不正确，请重试；原计划保持不变") from None
