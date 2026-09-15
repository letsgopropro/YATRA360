from typing import List, Union
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "YATRA360 API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/yatra360_db"

    # Security Placeholders
    SECRET_KEY: str = "yatra360-dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                decoded = json.loads(v)
                if isinstance(decoded, list):
                    return [str(origin) for origin in decoded]
            except Exception:
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(origin) for origin in v]
        return ["http://localhost:5173", "http://localhost:3000"]

    # External APIs
    OPENWEATHER_API_KEY: str = "mock-weather-key"
    MAPBOX_ACCESS_TOKEN: str = "mock-mapbox-token"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
