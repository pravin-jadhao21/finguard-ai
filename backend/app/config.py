import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FinGuard AI Security Gateway"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    POLICY_FILE_PATH: str = "policies/v1_baseline_policy.yaml"

    FAIL_CLOSED: bool = True
    MAX_PAYLOAD_SIZE_BYTES: int = 65536
    LATENCY_BUDGET_MS: float = 10.0
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
