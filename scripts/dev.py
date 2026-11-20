#!/usr/bin/env python3
"""Start only this project's backend and frontend; never kill existing listeners."""

import os, signal, socket, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for port in [8000, 5173]:
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            sys.exit(f"端口{port}已被使用。请关闭本项目的旧进程，或使用已运行的页面。")
python = ROOT / ".venv/bin/python"
if not python.exists() or not (ROOT / "frontend/node_modules").exists():
    sys.exit("请先运行 python3 scripts/setup.py")
children = []


def stop(*_):
    for p in children:
        if p.poll() is None:
            p.terminate()
    for p in children:
        try:
            p.wait(timeout=8)
        except subprocess.TimeoutExpired:
            p.kill()
    raise SystemExit(0)


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)
try:
    children.append(subprocess.Popen([str(python), "backend/run.py"], cwd=ROOT))
    children.append(subprocess.Popen(["npm", "run", "dev"], cwd=ROOT / "frontend"))
    print(
        "\n雾河镇：http://127.0.0.1:5173\nAPI 文档：http://127.0.0.1:8000/docs\n按 Ctrl+C 关闭这两个进程。",
        flush=True,
    )
    while all(p.poll() is None for p in children):
        time.sleep(0.5)
finally:
    stop()
