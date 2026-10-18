from pathlib import Path
from typing import Literal
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env", extra="forbid", hide_input_in_errors=True
    )
    jwt_secret: SecretStr | None = None
    access_token_minutes: int = Field(default=15, ge=5, le=60)
    jwt_issuer: str = Field(default="aegislend-api", min_length=1)
    jwt_audience: str = Field(default="aegislend-client", min_length=1)

    @field_validator("jwt_secret")
    @classmethod
    def strong_signing_secret(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and len(value.get_secret_value().encode()) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 bytes; generate it randomly")
        return value

    redis_enabled: bool = False
    appointment_capacity: int = Field(default=1,ge=1,le=20)
    api_rate_limit: int = Field(default=180,ge=10,le=10000)
    auth_rate_limit: int = Field(default=20, ge=1, le=1000)
    ids_failed_threshold: int = Field(default=5, ge=2, le=100)
    ids_burst_threshold: int = Field(default=60, ge=10, le=10000)
    ids_incident_threshold: int = Field(default=30,ge=1,le=100)
    ids_stuffing_threshold: int = Field(default=5,ge=2,le=100)
    ids_anomaly_threshold: float = Field(default=0.0, ge=-1, le=1)
    ids_model_path: Path = Path(__file__).resolve().parents[1] / 'var/ids.joblib'
    chroma_enabled: bool = False
    llm_api_key: SecretStr | None = None
    llm_base_url: str = 'https://api.openai.com/v1'
    llm_model: str = ''
    crewai_enabled: bool = False

    db_host: str = "127.0.0.1"
    db_port: int = Field(default=3306, ge=1, le=65535)
    db_name: str = "aegislend"
    db_user: str = "aegislend"
    db_password: SecretStr
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    redis_url: str = "redis://127.0.0.1:6379/0"
    chroma_url: str = "http://127.0.0.1:8001"
    llm_provider: Literal["disabled", "openai-compatible"] = "disabled"

    @field_validator("db_password")
    @classmethod
    def nonempty_password(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("DB_PASSWORD must be nonempty")
        return value

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, values: list[str]) -> list[str]:
        if any(v == "*" or not v.startswith(("http://", "https://")) for v in values):
            raise ValueError("Use explicit HTTP(S) CORS origins")
        return values

    @property
    def database_url(self) -> URL:
        return URL.create("mysql+pymysql", username=self.db_user,
                          password=self.db_password.get_secret_value(),
                          host=self.db_host, port=self.db_port, database=self.db_name,
                          query={"charset": "utf8mb4"})
