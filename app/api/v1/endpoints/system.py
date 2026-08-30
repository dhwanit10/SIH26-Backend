from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.system import System, SystemStatus
from app.models.user import User, UserType
from app.schemas.system import SystemsResponse, SystemCreateRequest, SystemCreateResponse

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


@router.post("/create", response_model=SystemCreateResponse)
async def create_system(
    request: SystemCreateRequest,
    db: Session = Depends(get_db)
):
    owner = (
        db.query(User)
        .filter(User.id == request.primary_owner_id)
        .first()
    )

    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Primary owner not found"
        )

    if owner.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=400,
            detail="Primary owner must be an admin"
        )

    existing_system = (
        db.query(System)
        .filter(System.system_name == request.system_name)
        .first()
    )

    if existing_system:
        raise HTTPException(
            status_code=409,
            detail="System with this name already exists"
        )

    system = System(
        system_name=request.system_name,
        primary_owner_id=request.primary_owner_id,
        status=SystemStatus.OFFLINE
    )

    db.add(system)
    db.commit()
    db.refresh(system)

    return SystemCreateResponse(
        id=system.id,
        system_name=system.system_name,
        status=system.status,
        primary_owner_id=system.primary_owner_id
    )