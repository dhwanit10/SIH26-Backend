from datetime import datetime

from pydantic import BaseModel

from app.models.system import SystemStatus
from app.models.user import UserStatus


class LogoutRequest(BaseModel):
    session_id: int
    user_id: int


class LogoutResponse(BaseModel):
    success: bool
    session_id: int
    user_id: int
    system_id: int
    end_time: datetime
    system_status: SystemStatus
    user_status: UserStatus