from dataclasses import dataclass
import os


@dataclass
class Config:
    telegram_token: str
    db_path: str = "weather.db"
    tz_offset: int = 0

    @classmethod
    def from_env(cls) -> "Config":
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            raise RuntimeError("TELEGRAM_TOKEN is required")
        db_path = os.environ.get("DB_PATH", "weather.db")
        tz_offset = int(os.environ.get("TZ_OFFSET", "0"))
        return cls(token, db_path, tz_offset)
