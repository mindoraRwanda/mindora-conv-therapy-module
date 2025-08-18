# from passlib.context import CryptContext
# from jose import JWTError, jwt
# from datetime import datetime, timedelta
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.orm import Session
# from app.db.models import User
# from app.db.database import get_db
# import os

# # Auth scheme for FastAPI
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# # Security settings
# SECRET_KEY = os.getenv("SECRET_KEY", "dev_default_secret_key")
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 360

# # Password hashing config
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

# def create_access_token(data: dict) -> str:
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire, "token_type": "access"})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ) -> User:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub")
#         if user_id is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception

#     user = db.query(User).filter(User.id == int(user_id)).first()
#     if user is None:
#         raise credentials_exception
#     return user
# backend/app/auth/utils.py

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os, logging
from app.db.models import User
from app.db.database import get_db
from app.auth.user_service import get_or_create_user

# Load .env for secrets
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET not set. Refusing to start.")

ALGORITHM = os.getenv("JWT_ALG", "HS256")
JWT_LEEWAY = int(os.getenv("JWT_LEEWAY", "60"))
ACCESS_TOKEN_EXPIRE_MINUTES = 360

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True, "leeway": JWT_LEEWAY}
        )
        user_id = payload.get("sub") or payload.get("id")
        if not user_id:
            logging.error("JWT missing 'sub' or 'id'")
            raise credentials_exception

        return get_or_create_user(str(user_id), db)

    except JWTError as e:
        logging.error(f"JWT decode failed: {e}")
        import os
        print(repr(os.getenv("JWT_SECRET")))

        raise credentials_exception
