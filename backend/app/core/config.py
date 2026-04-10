import secrets
from functools import cached_property
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    tz: str = "Asia/Shanghai"

    @field_validator("tz")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)  # 尝试验证时区字符串是否合法
            return v
        except ZoneInfoNotFoundError:
            raise ValueError(f"无效的时区标识符: {v}")

    @computed_field
    @cached_property
    def tz_info(self) -> ZoneInfo:
        return ZoneInfo(self.tz)

    project_root: Path = Path(__file__).resolve().parent.parent.parent
    db_file: str = "db.sqlite3"

    config_dir: str = Field(
        default=str(project_root / "config"),
        alias="CONFIG_DIR",
        title="配置目录",
    )
    download_dir: str = Field(
        default=str(project_root / "downloads"),
        alias="DOWNLOAD_DIR",
        title="下载目录",
    )

    auth: bool = Field(default=True, alias="AUTH", title="启用认证")
    username: str = Field(default="admin", alias="USERNAME", title="用户名")
    password: str = Field(default="123456", alias="PASSWORD", title="密码")
    # JWT 相关
    secret_key: str = Field(
        default=secrets.token_urlsafe(32), alias="SECRET_KEY", title="密钥"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM", title="算法")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES", title="访问令牌过期时间"
    )
    refresh_token_expire_minutes: int = Field(
        default=60 * 24 * 7,
        alias="REFRESH_TOKEN_EXPIRE_MINUTES",
        title="刷新令牌过期时间",
    )
    refresh_token_replace_minutes: int = Field(
        default=60 * 24 * 1,
        alias="REFRESH_TOKEN_REPLACE_MINUTES",
        title="刷新令牌替换时间",
    )

    @computed_field
    @cached_property
    def config_path(self) -> Path:
        return Path(self.config_dir)

    @computed_field
    @cached_property
    def download_path(self) -> Path:
        return Path(self.download_dir)

    @computed_field
    @cached_property
    def db_url(self) -> str:
        return f"sqlite:///{self.config_path / self.db_file}"

    @computed_field
    @cached_property
    def tortoise_orm(self) -> dict[str, Any]:
        return {
            "connections": {"default": self.db_url},
            "apps": {
                "models": {
                    # 包含所有模型的路径
                    "models": ["app.models"],
                    # 迁移文件所在模块（用于 tortoise CLI / migrate 加载迁移）
                    "migrations": "app.migrations",
                    "default_connection": "default",
                }
            },
            "use_tz": True,
            "timezone": self.tz,
        }


settings = Settings()

# Tortoise CLI（tortoise init / makemigrations 等）通过模块路径引用，需为模块级变量
TORTOISE_ORM: dict[str, Any] = settings.tortoise_orm
