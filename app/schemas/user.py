from datetime import date

from pydantic import BaseModel, EmailStr

from app.models.user import UserType, UserStatus

from typing import Optional
# =====================================
# CREATE USER REQUEST
# =====================================

class UserCreate(BaseModel):

    username: str

    full_name: str

    dob: date

    gender: str

    aadhar_no: str

    phone: str

    email: EmailStr

    user_type: UserType = UserType.OFFICER

    password: str


# =====================================
# CREATE USER RESPONSE
# =====================================

class UserCreateResponse(BaseModel):

    user_id: int

    username: str

    password: str

    user_type: UserType


# =====================================
# USER RESPONSE
# =====================================

class UserResponse(BaseModel):

    user_id: int

    username: str

    full_name: str

    dob: date

    gender: str

    aadhar_no: str

    phone: str

    email: str

    user_type: UserType
    status: UserStatus

    has_face_image: bool


# =====================================
# GET ALL USERS RESPONSE
# =====================================

class UsersListResponse(BaseModel):

    success: bool

    total_users: int

    users: list[UserResponse]


# =====================================
# UPLOAD FACE IMAGE REQUEST
# =====================================

class FaceImageUpload(BaseModel):

    user_id: int

    image: str


# =====================================
# UPLOAD FACE IMAGE RESPONSE
# =====================================

class FaceImageUploadResponse(BaseModel):

    success: bool

    message: str

    user: UserResponse


# =====================================
# LOGIN REQUEST
# =====================================

class UserLogin(BaseModel):
    username: str
    password: str
    system_id: int


# =====================================
# LOGIN RESPONSE
# =====================================

class UserLoginResponse(BaseModel):

    success: bool

    user_id: int

    username: str

    user_type: UserType
    system_id: int
    access_token: str

    token_type: str

class VerifyUserResponse(BaseModel):
    success: bool
    user_id: int
    system_id: int
    session_id: Optional[int] = None
    username: str
    full_name: str
    face_match_score: float
    message: str