from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.face_matcher import match_faces

from app.models.system import (
    System,
    SystemStatus,
    Session as SystemSession
)
from app.models.user import User, UserStatus, UserType

from app.schemas.user import VerifyUserResponse

router = APIRouter()


@router.post(
    "/verify-user",
    response_model=VerifyUserResponse
)
async def verify_user(
    user_id: int = Form(...),
    system_id: int = Form(...),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    token_user_id = current_user.get("user_id")

    if not token_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )

    if token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID does not match authenticated user"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.user_type not in (
        UserType.OFFICER,
        UserType.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not authorized for face verification"
        )

    if user.status == UserStatus.ONLINE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already online"
        )

    system = (
        db.query(System)
        .filter(System.id == system_id)
        .first()
    )

    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System not found"
        )

    if system.status != SystemStatus.OFFLINE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="System is already in use"
        )

    if not user.face_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No reference face image found for this user"
        )

    allowed_types = {
        "image/jpeg",
        "image/jpg",
        "image/png"
    }

    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, JPEG and PNG images are allowed"
        )

    captured_image = await image.read()

    if not captured_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captured image is empty"
        )

    try:
        face_score, is_match = match_faces(
            captured_image,
            user.face_image
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Face verification failed: {str(error)}"
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face verification error: {str(error)}"
        )

    face_score = round(face_score, 4)

    if not is_match:
        return VerifyUserResponse(
            success=False,
            user_id=user.id,
            system_id=system.id,
            session_id=None,
            username=user.username,
            full_name=user.full_name,
            face_match_score=face_score,
            message="Face verification failed"
        )

    active_system_session = (
        db.query(SystemSession)
        .filter(
            SystemSession.system_id == system_id,
            SystemSession.end_time.is_(None)
        )
        .first()
    )

    if active_system_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="System already has an active session"
        )

    active_user_session = (
        db.query(SystemSession)
        .filter(
            SystemSession.officer_id == user_id,
            SystemSession.end_time.is_(None)
        )
        .first()
    )

    if active_user_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an active session"
        )

    now = datetime.utcnow()

    new_session = SystemSession(
        start_time=now,
        start_date=now.date(),
        end_time=None,
        end_date=None,
        no_of_cases=0,
        officer_id=user.id,
        system_id=system.id
    )

    db.add(new_session)

    user.status = UserStatus.ONLINE
    system.status = SystemStatus.ONLINE

    try:
        db.commit()
        db.refresh(new_session)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user session"
        )

    return VerifyUserResponse(
        success=True,
        user_id=user.id,
        system_id=system.id,
        session_id=new_session.id,
        username=user.username,
        full_name=user.full_name,
        face_match_score=face_score,
        message="User verified successfully"
    )