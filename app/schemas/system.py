from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.system import SystemStatus


class SystemSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    no_of_cases: Optional[int] = None
    officer_id: int


class SystemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    system_name: str
    status: SystemStatus
    primary_owner_id: int
    sessions: list[SystemSessionResponse] = []


class SystemsResponse(BaseModel):
    total: int
    systems: list[SystemResponse]