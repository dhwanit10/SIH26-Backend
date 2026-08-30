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

from passlib.context import CryptContext

from app.core.security import create_access_token
from app.core.database import get_db

from app.models.user import User

from app.schemas.user import (
    UserCreate,
    UserCreateResponse,
    UserResponse,
    UsersListResponse,
    UserLogin,
    UserLoginResponse
)


router = APIRouter()


# =====================================
# PASSWORD CONFIGURATION
# =====================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# =====================================
# HASH PASSWORD
# =====================================

def hash_password(password: str):

    return pwd_context.hash(password)


# =====================================
# VERIFY PASSWORD
# =====================================

def verify_password(
    plain_password: str,
    hashed_password: str
):

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# =====================================
# CONVERT USER TO RESPONSE
# =====================================

def user_to_response(user: User):

    return UserResponse(

        user_id=user.id,

        username=user.username,

        full_name=user.full_name,

        dob=user.dob,

        gender=user.gender,

        aadhar_no=user.aadhar_no,

        phone=user.phone,

        email=user.email,

        user_type=user.user_type,
        status=user.status,

        has_face_image=user.face_image is not None

    )


# =================================================
# API 1: CREATE USER
# JSON FORMAT
# =================================================

@router.post(
    "/create",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(

    user_data: UserCreate,

    db: Session = Depends(get_db)

):

    # -----------------------------------
    # CHECK USERNAME
    # -----------------------------------

    existing_username = db.query(User).filter(

        User.username == user_data.username

    ).first()


    if existing_username:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Username already exists"

        )


    # -----------------------------------
    # CHECK AADHAAR NUMBER
    # -----------------------------------

    existing_aadhar = db.query(User).filter(

        User.aadhar_no == user_data.aadhar_no

    ).first()


    if existing_aadhar:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Aadhaar number already exists"

        )


    # -----------------------------------
    # CHECK EMAIL
    # -----------------------------------

    existing_email = db.query(User).filter(

        User.email == user_data.email

    ).first()


    if existing_email:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Email already exists"

        )


    # -----------------------------------
    # HASH PASSWORD
    # -----------------------------------

    hashed_password = hash_password(

        user_data.password

    )


    # -----------------------------------
    # CREATE USER
    # -----------------------------------

    new_user = User(

        username=user_data.username,

        password=hashed_password,

        full_name=user_data.full_name,

        dob=user_data.dob,

        gender=user_data.gender,

        aadhar_no=user_data.aadhar_no,

        phone=user_data.phone,

        email=user_data.email,

        user_type=user_data.user_type,

        face_image=None

    )


    # -----------------------------------
    # SAVE USER
    # -----------------------------------

    db.add(new_user)

    db.commit()

    db.refresh(new_user)


    # -----------------------------------
    # RETURN RESPONSE
    # -----------------------------------

    return UserCreateResponse(

        user_id=new_user.id,

        username=new_user.username,

        password=user_data.password,

        user_type=new_user.user_type

    )


# =================================================
# API 2: GET ALL USERS
# =================================================

@router.get(
    "/",
    response_model=UsersListResponse
)
def get_all_users(

    db: Session = Depends(get_db)

):

    users = db.query(User).all()


    return UsersListResponse(

        success=True,

        total_users=len(users),

        users=[

            user_to_response(user)

            for user in users

        ]

    )


# =================================================
# API 3: UPLOAD FACE IMAGE
# BOX FORMAT
# =================================================

@router.post(
    "/upload-face"
)
async def upload_face_image(

    user_id: int = Form(...),

    image: UploadFile = File(...),

    db: Session = Depends(get_db)

):

    # -----------------------------------
    # FIND USER
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
    # READ IMAGE
    # -----------------------------------

    image_bytes = await image.read()


    if not image_bytes:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Image is empty"

        )


    # -----------------------------------
    # STORE IMAGE
    # -----------------------------------

    user.face_image = image_bytes


    db.commit()

    db.refresh(user)


    # -----------------------------------
    # RETURN RESPONSE
    # -----------------------------------

    return {

        "success": True,

        "user_id": user.id,

        "username": user.username,

        "full_name": user.full_name,

        "user_type": user.user_type.value,

        "has_face_image": True,

        "message": "Face image uploaded successfully"

    }


# =================================================
# API 4: USER LOGIN
# JSON FORMAT
# =================================================

@router.post(
    "/login",
    response_model=UserLoginResponse
)
def login_user(

    login_data: UserLogin,

    db: Session = Depends(get_db)

):

    # -----------------------------------
    # FIND USER
    # -----------------------------------

    user = db.query(User).filter(

        User.id == login_data.user_id

    ).first()


    if not user:

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Invalid user ID or password"

        )


    # -----------------------------------
    # VERIFY PASSWORD
    # -----------------------------------

    password_valid = verify_password(

        login_data.password,

        user.password

    )


    if not password_valid:

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Invalid user ID or password"

        )


    # -----------------------------------
    # CREATE JWT TOKEN
    # -----------------------------------

    access_token = create_access_token(

        data={

            "user_id": user.id,

            "username": user.username,

            "user_type": user.user_type.value

        }

    )


    # -----------------------------------
    # RETURN RESPONSE
    # -----------------------------------

    return UserLoginResponse(

        success=True,

        user_id=user.id,

        username=user.username,

        user_type=user.user_type,

        access_token=access_token,

        token_type="bearer"

    )