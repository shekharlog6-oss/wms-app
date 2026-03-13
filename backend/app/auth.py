from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta

# TODO(PROD): Replace dev JWT with Azure AD (MSAL) validation.
SECRET = "dev-secret-change-me"
ALG = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_token(user_id: int, username: str, role: str, minutes: int = 240) -> str:
    payload = {
        "id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, SECRET, algorithm=ALG)

def current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required: str):
    def checker(user=Depends(current_user)):
        role = user.get("role")
        if role != required and role != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker