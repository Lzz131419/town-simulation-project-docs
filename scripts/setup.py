#!/usr/bin/env python3
import os, subprocess, sys, venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
if not Path(".venv").exists():
    venv.create(".venv", with_pip=True)
env = os.environ.copy()
if sys.platform == "darwin" and Path("/etc/ssl/cert.pem").exists():
    env.setdefault("PIP_CERT", "/etc/ssl/cert.pem")
subprocess.run(
    [".venv/bin/python", "-m", "pip", "install", "-r", "backend/requirements.lock"],
    check=True,
    env=env,
)
subprocess.run(["npm", "ci", "--prefix", "frontend"], check=True)
subprocess.run(
    [".venv/bin/python", "-c", "from backend.app.main import initialize; initialize()"],
    check=True,
)
print("本地环境已就绪。运行 npm start。六名成员的初始密码与用户名相同。")
