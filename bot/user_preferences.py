from datetime import date
from typing import Any

from sqlalchemy import select

# from bot.buttons import DEFAULT_LANGUAGE, normalize_language
from db import database
from db.models import Student


PLACEHOLDER_DOB = date(1970, 1, 1)


def placeholder_phone(telegram_id: int) -> str:
    return f"telegram_{telegram_id}"[:30]


def placeholder_email(telegram_id: int) -> str:
    return f"telegram_{telegram_id}@marketbot.local"


def is_placeholder_phone(phone: str | None, telegram_id: int) -> bool:
    return not phone or phone == placeholder_phone(telegram_id)


def is_placeholder_email(email: str | None, telegram_id: int) -> bool:
    return not email or email == placeholder_email(telegram_id)


def is_placeholder_dob(dob: date | None) -> bool:
    return dob is None or dob == PLACEHOLDER_DOB


def get_user_by_telegram_id(telegram_id: int) -> Student | None:
    return database.execute(
        select(Student).where(Student.telegram_id == telegram_id)
    ).scalars().first()


def get_user_language(telegram_id: int | None) -> str:
    if telegram_id is None:
        return "uz"

    user = get_user_by_telegram_id(telegram_id)
    if user is None:
        return "uz"

    # return normalize_language(getattr(user, "language_code", DEFAULT_LANGUAGE))


def language_for_event_user(event_user: Any | None) -> str:
    telegram_id = getattr(event_user, "id", None)
    return get_user_language(telegram_id)


def ensure_user(telegram_user: Any, language_code: str | None = None) -> Student:
    # language_code = normalize_language(language_code)
    user = get_user_by_telegram_id(telegram_user.id)
    if user is not None:
        if not getattr(user, "language_code", None):
            user.language_code = language_code
        return user

    first_name = (telegram_user.first_name or "User")[:30]
    last_name = (telegram_user.last_name or "-")[:30]
    user = Student(
        telegram_id=telegram_user.id,
        first_name=first_name,
        last_name=last_name,
        gender="other",
        phone=placeholder_phone(telegram_user.id),
        email=placeholder_email(telegram_user.id),
        dob=PLACEHOLDER_DOB,
        language_code=language_code,
    )
    database.add(user)
    database.commit()
    return user
