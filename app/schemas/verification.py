from pydantic import BaseModel


class FaceVerificationResponse(BaseModel):

    success: bool

    user_id: int

    username: str

    user_type: str

    verification_status: str

    similarity_score: float

    message: str