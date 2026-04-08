from app.core.config import settings


def ensure_sqlite_parent_dir() -> None:
    settings.config_path.mkdir(parents=True, exist_ok=True)
