import requests
from datetime import date, timedelta

from config import BASE_URL, COLLEGE_ID, GROUP_ID

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]


def _get(path, **params):
    params["college_id"] = COLLEGE_ID
    resp = requests.get(f"{BASE_URL}/{path}", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_groups():
    """Список всех групп колледжа."""
    return _get("public-schedule/groups")


def _current_week_start(weeks):
    """Выбирает неделю, в которую попадает сегодняшняя дата."""
    today = date.today().isoformat()
    for i, w in enumerate(weeks):
        nxt = weeks[i + 1] if i + 1 < len(weeks) else "9999"
        if w <= today < nxt:
            return w
    future = [w for w in weeks if w > today]
    return future[0] if future else (weeks[-1] if weeks else None)


def _build_bell_index(bell_schedule):
    """
    dict[(day_of_week | None, pair_number)] -> (starts_at, ends_at)
    Ключ None — общий график, конкретное число — переопределение для дня.
    """
    idx = {}
    for b in bell_schedule or []:
        if b.get("kind") != "pair" or b.get("pair_number") is None:
            continue
        idx[(b.get("day_of_week"), b["pair_number"])] = (
            b.get("starts_at") or "",
            b.get("ends_at") or "",
        )
    return idx


def _pair_time(bell_idx, day_of_week, pair_number):
    if day_of_week is not None and (day_of_week, pair_number) in bell_idx:
        return bell_idx[(day_of_week, pair_number)]
    if (None, pair_number) in bell_idx:
        return bell_idx[(None, pair_number)]
    return ("", "")


def update_schedule(group_id=GROUP_ID):
    """
    Возвращает (rows, week_start).
    rows — список словарей:
      day, date, lesson_number, time, subject, teacher, subgroup, room, building
    """
    weeks = _get("public-schedule/weeks", group_id=group_id)
    if not weeks:
        return [], None

    week_start = _current_week_start(weeks)
    data = _get(
        "public-schedule/week",
        group_id=group_id,
        week_start_date=week_start,
    )

    bell_idx = _build_bell_index(data.get("bell_schedule"))

    by_date = {}
    for les in data.get("lessons", []):
        by_date.setdefault(les["date"], []).append(les)

    start = date.fromisoformat(week_start)
    rows = []
    for offset, day_name in enumerate(DAYS):
        d = (start + timedelta(days=offset)).isoformat()
        day_of_week = offset + 1  # 1=Пн … 6=Сб
        for les in sorted(by_date.get(d, []), key=lambda x: x.get("pair_number") or 0):
            starts, ends = _pair_time(bell_idx, day_of_week, les.get("pair_number"))
            time_str = f"{starts[:5]}-{ends[:5]}" if starts and ends else ""
            rows.append({
                "day": day_name,
                "date": d,
                "lesson_number": les.get("pair_number"),
                "time": time_str,
                "subject": les.get("discipline") or "",
                "teacher": les.get("teacher") or "",
                "subgroup": les.get("subgroup") or "",
                "room": les.get("room") or "",
                "building": les.get("building") or "",
            })
    return rows, week_start