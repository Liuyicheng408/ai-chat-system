"""应用配置：全部从 .env 读取，禁止硬编码密钥。"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # 数据库：默认 MySQL，测试可切 sqlite
    database_url: str = "sqlite:///./data/app.db"

    # 认证
    jwt_secret: str = "dev-secret-please-change"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    # 模型
    models_dir: str = str(BASE_DIR.parent.parent / "models")
    context_rounds: int = 10
    max_new_tokens: int = 1024
    temperature: float = 0.7
    local_base_model: str = ""

    # 远端模型（OpenAI 兼容）
    remote_base_url: str = "https://api.deepseek.com/v1"
    remote_api_key: str = ""
    remote_model: str = "deepseek-chat"
    remote_display_name: str = "DeepSeek 远端"

    # 跨域
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
