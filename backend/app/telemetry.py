"""Small bounded Prometheus exposition; no user IDs, keys or message contents."""

import json
import logging
import threading
import time
from contextlib import contextmanager


class Metrics:
    def __init__(self):
        self.values = {}
        self.lock = threading.Lock()

    def add(self, name, value=1):
        with self.lock:
            self.values[name] = self.values.get(name, 0) + value

    def set(self, name, value):
        with self.lock:
            self.values[name] = value

    @contextmanager
    def duration(self, name):
        start = time.perf_counter()
        try:
            yield
        finally:
            seconds = time.perf_counter() - start
            self.add(name + "_seconds_sum", seconds)
            self.add(name + "_seconds_count")
            self.set(name + "_seconds_last", seconds)

    def render(self):
        with self.lock:
            return "\n".join(f"town_{k} {v}" for k, v in sorted(self.values.items())) + "\n"


metrics = Metrics()
logger = logging.getLogger("town")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.propagate = False


def log(event, **fields):
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False))
