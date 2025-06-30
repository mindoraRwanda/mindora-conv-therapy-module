from pydantic import BaseModel, EmailStr
from datetime import datetime

class MessageOut(BaseModel):
    id: int
    sender: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True  # for Pydantic v2+ (instead of orm_mode)

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MessageCreate(BaseModel):
    conversation_id: int
    content: str  # Sender will now be set in backend

   
