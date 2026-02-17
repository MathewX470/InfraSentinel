from datetime import timedelta
from fastapi import APIRouter, HTTPException, status
from ..auth import authenticate_admin, create_access_token
from ..config import get_settings
from ..schemas import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """
    Authenticate admin user and return JWT token.
    
    This is a single-admin system with hardcoded credentials.
    """
    if not authenticate_admin(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": request.username},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/verify")
async def verify_token_endpoint():
    """
    Verify if the current token is valid.
    This endpoint requires authentication (handled by dependency).
    """
    # If we reach here, the token is valid (auth dependency passed)
    return {"valid": True, "message": "Token is valid"}
