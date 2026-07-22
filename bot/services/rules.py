from datetime import time


ODD_WEEKDAYS = (0, 2, 4)
EVEN_WEEKDAYS = (1, 3, 5)


def period_weekdays(period: str) -> tuple[int, ...]:
    return ODD_WEEKDAYS if period == "odd" else EVEN_WEEKDAYS


def time_in_lesson(current: time, start: time, end: time) -> bool:
    return start <= current <= end


def attendance_percent(present: int, absent: int) -> float:
    total = present + absent
    return round(present * 100 / total, 1) if total else 0.0
