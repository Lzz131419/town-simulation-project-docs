"""Short synchronous model-call transactions; network never holds a database session."""

import time
from ..config import encryption
from ..database import Session
from ..models import ModelConfig, ModelCall
from ..domain.rules import need


def prepare_call(uid, purpose):
    with Session.begin() as db:
        cfg = db.get(ModelConfig, uid)
        need(cfg is not None, "请先配置模型服务")
        need(time.time() - cfg.last_call >= 10, "两次模型调用至少间隔10秒")
        key = encryption().decrypt(cfg.encrypted_key.encode()).decode()
        cfg.last_call = time.time()
        record = ModelCall(user_id=uid, purpose=purpose, status="running")
        db.add(record)
        db.flush()
        return cfg.base_url, cfg.model, key, record.id


def finish_call(record_id, status, counts=None, reported=False):
    with Session.begin() as db:
        record = db.get(ModelCall, record_id)
        record.status = status
        if counts is not None:
            record.input_tokens, record.output_tokens = counts
            record.usage_reported = reported
