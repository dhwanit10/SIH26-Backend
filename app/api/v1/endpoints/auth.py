from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.system import Session as SystemSession, System, SystemStatus
from app.models.user import User, UserStatus
from app.schemas.logout import LogoutRequest, LogoutResponse

router = APIRouter()


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db)
):
    try:
        session = (
            db.query(SystemSession)
            .filter(SystemSession.id == request.session_id)
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )

        if session.officer_id != request.user_id:
            raise HTTPException(
                status_code=403,
                detail="Session does not belong to this user"
            )

        user = (
            db.query(User)
            .filter(User.id == request.user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        system = (
            db.query(System)
            .filter(System.id == session.system_id)
            .first()
        )

        if not system:
            raise HTTPException(
                status_code=404,
                detail="System not found"
            )

        now = datetime.utcnow()

        session.end_time = now
        session.end_date = now.date()

        system.status = SystemStatus.OFFLINE
        user.status = UserStatus.OFFLINE

        db.commit()

        db.refresh(session)
        db.refresh(system)
        db.refresh(user)

        return LogoutResponse(
            success=True,
            session_id=session.id,
            user_id=user.id,
            system_id=system.id,
            end_time=session.end_time,
            system_status=system.status,
            user_status=user.status
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Logout failed: {str(e)}"
        )