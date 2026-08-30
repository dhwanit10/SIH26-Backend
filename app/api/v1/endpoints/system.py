from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.system import System, SystemStatus
from app.schemas.system import SystemsResponse

router = APIRouter()


@router.get("/get", response_model=SystemsResponse)
async def get_systems(
    db: Session = Depends(get_db)
):
    systems = (
        db.query(System)
        .options(
            joinedload(System.sessions)
        )
        .order_by(System.id)
        .all()
    )

    return SystemsResponse(
        total=len(systems),
        systems=systems
    )

@router.get("/get-offline", response_model=SystemsResponse)
async def get_systems(
    db: Session = Depends(get_db)
):
    systems = (
        db.query(System)
        .options(
            joinedload(System.sessions)
        )
        .filter(System.status == SystemStatus.OFFLINE)
        .order_by(System.id)
        .all()
    )

    return SystemsResponse(
        total=len(systems),
        systems=systems
    )