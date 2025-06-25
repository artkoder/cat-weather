from dataclasses import dataclass
import os


@dataclass
class Config:
    telegram_token: str
    webhook_url: str
    db_path: str = "weather.db"
    tz_offset: int = 0

    @classmethod
    def from_env(cls) -> "Config":

        token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required")


        webhook_url = os.environ.get("WEBHOOK_URL")
        if not webhook_url:
            raise RuntimeError("WEBHOOK_URL is required")


        # Validate URL to avoid Telegram errors
        from urllib.parse import urlparse

        parsed = urlparse(webhook_url)
        if not parsed.scheme or not parsed.netloc:
            raise RuntimeError("WEBHOOK_URL must include scheme and host")


        db_path = os.environ.get("DB_PATH", "weather.db")
        tz_offset = int(os.environ.get("TZ_OFFSET", "0"))
        return cls(token, webhook_url, db_path, tz_offset)
