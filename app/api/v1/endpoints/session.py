from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.system import Session as SystemSession
from app.schemas.session import SessionsResponse

router = APIRouter()


@router.get("/get", response_model=SessionsResponse)
async def get_sessions(
    db: Session = Depends(get_db)
):
    sessions = (
        db.query(SystemSession)
        .options(
            joinedload(SystemSession.system)
        )
        .order_by(SystemSession.id.desc())
        .all()
    )

    return SessionsResponse(
        total=len(sessions),
        sessions=sessions
    )