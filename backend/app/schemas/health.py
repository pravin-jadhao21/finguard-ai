from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Gateway health status")
    service: str = Field(...)
    version: str = Field(...)
    environment: str = Field(...)
    timestamp: datetime = Field(...)
    active_policy_version: str = Field(...)
    engine_mode: str = Field(...)
