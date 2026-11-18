from datetime import date, datetime

from fastapi import HTTPException


def parse_date(value: str, field: str = "date") -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail=f"'{field}' must be a valid date (YYYY-MM-DD)")


def parse_time_minutes(value: str, field: str = "time") -> int:
    try:
        t = datetime.strptime(value, "%H:%M")
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail=f"'{field}' must be a valid time (HH:MM)")
    return t.hour * 60 + t.minute


def minutes_to_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def now_local() -> datetime:
    return datetime.now()
