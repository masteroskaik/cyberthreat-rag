from fastapi import APIRouter, HTTPException, status

from api.schemas import LoginRequest, TokenResponse
from api.auth import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
        )
    token = create_access_token(request.username)
    return TokenResponse(access_token=token)
