import os
from pathlib import Path
import uvicorn

os.chdir(Path(__file__).resolve().parents[1])

uvicorn.run(
    "app.main:app", app_dir=str(Path(__file__).parent), host="127.0.0.1", port=8000, workers=1
)
