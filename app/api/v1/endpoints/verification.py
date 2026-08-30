from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.face_matcher import match_faces
from app.core.dependencies import get_current_user

from app.models.user import User, UserType

from app.schemas.verification import (
    FaceVerificationResponse
)


router = APIRouter()


@router.post(
    "/scan",
    response_model=FaceVerificationResponse
)
async def scan_face(

    image: UploadFile = File(...),

    current_user: dict = Depends(get_current_user),

    db: Session = Depends(get_db)

):

    # -----------------------------------
    # GET USER ID FROM JWT TOKEN
    # -----------------------------------

    user_id = current_user.get("user_id")


    if not user_id:

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Invalid access token"

        )


    # -----------------------------------
    # FIND LOGGED-IN USER
    # -----------------------------------

    user = db.query(User).filter(

        User.id == user_id

    ).first()


    if not user:

        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,

            detail="User not found"

        )


    # -----------------------------------
    # CHECK USER ROLE
    # -----------------------------------

    if user.user_type not in [

        UserType.OFFICER,

        UserType.ADMIN

    ]:

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail=(
                "Only officers or admins "
                "can perform face verification"
            )

        )


    # -----------------------------------
    # CHECK REFERENCE FACE IMAGE
    # -----------------------------------

    if not user.face_image:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail=(
                "No reference face image "
                "found for this user"
            )

        )


    # -----------------------------------
    # VALIDATE IMAGE TYPE
    # -----------------------------------

    allowed_types = [

        "image/jpeg",

        "image/jpg",

        "image/png"

    ]


    if image.content_type not in allowed_types:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail=(
                "Only JPG, JPEG and PNG "
                "images are allowed"
            )

        )


    # -----------------------------------
    # READ CAPTURED IMAGE
    # -----------------------------------

    captured_image = await image.read()


    if not captured_image:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Captured image is empty"

        )


    # -----------------------------------
    # VERIFY FACE
    # -----------------------------------

    try:

        similarity_score, verified = match_faces(

            user.face_image,

            captured_image

        )


    except ValueError as error:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail=str(error)

        )


    except Exception as error:

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=f"Face verification error: {str(error)}"

        )


    # -----------------------------------
    # VERIFICATION SUCCESS
    # -----------------------------------

    if verified:

        return FaceVerificationResponse(

            success=True,

            user_id=user.id,

            username=user.username,

            user_type=user.user_type.value,

            verification_status="verified",

            similarity_score=round(
                similarity_score,
                4
            ),

            message="Face verification successful"

        )


    # -----------------------------------
    # VERIFICATION FAILED
    # -----------------------------------

    return FaceVerificationResponse(

        success=False,

        user_id=user.id,

        username=user.username,

        user_type=user.user_type.value,

        verification_status="failed",

        similarity_score=round(
            similarity_score,
            4
        ),

        message="Face verification failed"

    )