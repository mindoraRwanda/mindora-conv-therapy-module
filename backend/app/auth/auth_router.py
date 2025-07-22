from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import bleach
from sqlalchemy.exc import IntegrityError
# Add this import if it's not already there
from app.auth.schemas import TokenResponse
from app.services.emotion_classifier import classify_emotion
from app.db.database import SessionLocal
from app.db.models import Conversation, Message, User
from app.auth.schemas import (
    MessageCreate, MessageOut, UserCreate, UserLogin, TokenResponse,
    ConversationOut, MessageCreate, EmotionRequest
)
from app.auth.utils import hash_password, verify_password, create_access_token, get_current_user
from app.services.llm_service import LLMService
from app.db.models import EmotionLog
from app.services.emotion_classifier import classify_emotion
router = APIRouter(prefix="/auth", tags=["Authentication"])
llm = LLMService()

# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Auth Endpoints ---

@router.post("/signup", response_model=TokenResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check for existing email
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Check for existing username
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_pw = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, password=hashed_pw)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": str(new_user.id)})
    return {"access_token": token, "token_type": "bearer", "user_id": new_user.id, "username": new_user.username}



@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username  
    }


# --- Conversation Endpoints ---

@router.post("/conversations", response_model=ConversationOut)
def create_conversation(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    new_convo = Conversation(user_id=user.id)
    db.add(new_convo)
    db.commit()
    db.refresh(new_convo)
    return new_convo



@router.get("/conversations")
def list_user_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conversations = db.query(Conversation).filter_by(user_id=user.id).order_by(Conversation.started_at.desc()).all()
    return [
        {
            "id": c.id,
            "started_at": c.started_at,
            "messages": db.query(Message).filter_by(conversation_id=c.id).order_by(Message.timestamp.asc()).limit(1).all()
        } for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation)\
        .filter_by(id=conversation_id, user_id=user.id).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message)\
        .filter_by(conversation_id=conversation_id)\
        .order_by(Message.timestamp)\
        .all()

    return messages

# --- Messaging ---
@router.post("/messages", response_model=MessageOut)
async def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    convo = db.query(Conversation).filter_by(
        id=message.conversation_id,
        user_id=user.id
    ).first()

    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    clean_content = bleach.clean(message.content.strip())

    if not clean_content:
        raise HTTPException(status_code=400, detail="Message content is empty or invalid")

    user_msg = Message(
        conversation_id=message.conversation_id,
        sender="user",
        content=clean_content
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Load full conversation history
    history = db.query(Message)\
        .filter_by(conversation_id=message.conversation_id)\
        .order_by(Message.timestamp).all()

    conversation_history = [
        {"role": msg.sender, "text": msg.content} for msg in history
    ]

    # Generate bot response (emotion-aware)
    bot_reply = await llm.generate_response(clean_content, conversation_history)
    detected_emotion = classify_emotion(clean_content)

    emotion_log = EmotionLog(
        user_id=user.id,
        conversation_id=message.conversation_id,
        input_text=clean_content,
        detected_emotion=detected_emotion
    )
    db.add(emotion_log)

    bot_msg = Message(
        conversation_id=message.conversation_id,
        sender="bot",
        content=bleach.clean(bot_reply)
    )
    db.add(bot_msg)

    convo.last_activity_at = bot_msg.timestamp
    db.commit()
    db.refresh(bot_msg)

    return bot_msg  # You could modify this to also return emotion later


# --- Context Window Endpoint ---

@router.get("/context", response_model=List[MessageOut])
def get_context_window(
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Get most recently active conversation (with messages)
    conversation = (
        db.query(Conversation)
        .filter_by(user_id=user.id)
        .order_by(Conversation.started_at.desc())
        .first()
    )

    if not conversation:
        return []

    messages = (
        db.query(Message)
        .filter_by(conversation_id=conversation.id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
        .all()
    )

    return list(reversed(messages))  # return oldest → newest


