import threading
import time
from datetime import datetime

from flask import Flask, render_template, jsonify

from config import PORT, UPDATE_INTERVAL_MINUTES, GROUP_ID
from parser import update_schedule
from storage import save_schedule, load_schedule

app = Flask(__name__)


def refresh_job():
    while True:
        try:
            rows, week_start = update_schedule(GROUP_ID)
            save_schedule(rows, week_start=week_start)
            print(f"[{datetime.now():%H:%M:%S}] Обновлено, строк: {len(rows)}")
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] Ошибка: {e}")
        time.sleep(UPDATE_INTERVAL_MINUTES * 60)


@app.route("/")
def index():
    data = load_schedule()
    return render_template(
        "index.html",
        rows=data["rows"],
        updated_at=data["updated_at"],
        week_start=data.get("week_start"),
        interval=UPDATE_INTERVAL_MINUTES,
    )


@app.route("/api/schedule")
def api_schedule():
    return jsonify(load_schedule())


if __name__ == "__main__":
    try:
        rows, week_start = update_schedule(GROUP_ID)
        save_schedule(rows, week_start=week_start)
        print(f"Первичный парсинг: {len(rows)} строк, неделя с {week_start}")
    except Exception as e:
        print(f"Первичный парсинг не удался: {e}")

    threading.Thread(target=refresh_job, daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False)