from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import (
    security_scheme,
    verify_access_token
)


# ==========================================
# GET CURRENT AUTHENTICATED USER
# ==========================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security_scheme
    )
):

    payload = verify_access_token(credentials)

    return payload