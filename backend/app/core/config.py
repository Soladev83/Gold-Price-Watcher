"""
Central configuration — reads from environment variables.
"""

import os


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./gold_watcher.db")
    secret_key: str = os.getenv("SECRET_KEY", "change-this-in-production")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_bot_username: str = os.getenv("TELEGRAM_BOT_USERNAME", "YourGoldWatcherBot")
    telegram_webhook_secret: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    fetch_interval_hours: int = int(os.getenv("FETCH_INTERVAL_HOURS", "12"))

    @property
    def cors_origins(self) -> list[str]:
        raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
        return [o.strip() for o in raw.split(",")]


settings = Settings()
