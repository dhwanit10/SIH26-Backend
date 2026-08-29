from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.system import SystemStatus


class SessionSystemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    system_name: str
    status: SystemStatus


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    start_date: date
    end_date: Optional[date] = None
    no_of_cases: Optional[int] = None
    officer_id: int
    system: SessionSystemResponse


class SessionsResponse(BaseModel):
    total: int
    sessions: list[SessionResponse]