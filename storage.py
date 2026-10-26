import json
import os
from datetime import datetime

from config import DATA_FILE


def save_schedule(rows, week_start=None):
    data = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "week_start": week_start,
        "rows": rows,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_schedule():
    if not os.path.exists(DATA_FILE):
        return {"updated_at": None, "week_start": None, "rows": []}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)