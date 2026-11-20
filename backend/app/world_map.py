"""Authoritative geometry shared with the renderer and minimap."""

import json
from pathlib import Path

LAYOUT = json.loads((Path(__file__).resolve().parents[2] / "shared/world-map.json").read_text())
OBSTACLES = [(b["x"], b["y"], b["w"], b["h"]) for b in LAYOUT["buildings"] + LAYOUT["obstacles"]]
