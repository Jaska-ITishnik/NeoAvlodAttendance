import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def _parse_admin_ids(value: str | None) -> tuple[int, ...]:
    if not value:
        return ()

    admin_ids = []
    normalized_value = value.replace(";", ",").replace(" ", ",")
    for raw_item in normalized_value.split(","):
        item = raw_item.strip()
        if item.startswith("-"):
            is_integer = item[1:].isdigit()
        else:
            is_integer = item.isdigit()
        if is_integer:
            admin_ids.append(int(item))
    return tuple(admin_ids)


class Settings:
    USERNAME = os.getenv('ADMIN_USERNAME')
    SECRET_KEY = os.getenv('SECRET_KEY')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')

    def __init__(self, database, user, password, host, port, admin_ids):
        self.database = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.admin_ids = _parse_admin_ids(admin_ids)
        self.public_base_url = (os.getenv("PUBLIC_BASE_URL") or os.getenv("WEB_BASE_URL") or "").rstrip("/")
        self.session_https_only = (os.getenv("SESSION_HTTPS_ONLY") or "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    def postgresql_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


settings = Settings(
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    admin_ids=os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID") or os.getenv("ADMINS"),
)
