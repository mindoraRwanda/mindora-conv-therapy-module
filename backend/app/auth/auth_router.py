from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Conversation, Message, User
from app.auth.schemas import MessageCreate, MessageOut, UserCreate, UserLogin, TokenResponse
from app.auth.utils import hash_password, verify_password, create_access_token
from app.auth.utils import get_current_user
from typing import List
from app.services.llm_service import LLMService

router = APIRouter(prefix="/auth", tags=["Authentication"])
llm = LLMService()


# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup", response_model=TokenResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    print(User.__table__.columns.keys())

    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@router.post("/messages", response_model=MessageOut)
async def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # 1. Validate the conversation belongs to the user
    convo = db.query(Conversation).filter_by(id=message.conversation_id, user_id=user.id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Save user message
    user_msg = Message(
        conversation_id=message.conversation_id,
        sender="user",
        content=message.content
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 3. Fetch full conversation history to pass to LLM
    history = db.query(Message).filter_by(conversation_id=message.conversation_id).order_by(Message.timestamp).all()
    conversation_history = [
        { "role": msg.sender, "text": msg.content } for msg in history
    ]

    # 4. Generate LLM response using LangChain + Ollama + RAG
    bot_reply = await llm.generate_response(message.content, conversation_history)

    # 5. Save bot response
    bot_msg = Message(
        conversation_id=message.conversation_id,
        sender="bot",
        content=bot_reply
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    # 6. Return the latest bot message to frontend
    return bot_msg
#Starting a new conversation 
@router.post("/conversations")
def create_conversation(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    new_convo = Conversation(user_id=user.id)
    db.add(new_convo)
    db.commit()
    db.refresh(new_convo)
    return {"conversation_id": new_convo.id, "started_at": new_convo.started_at}

 # make sure this is defined

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter_by(id=conversation_id, user_id=user.id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
    return messages

@router.get("/conversations")
def list_user_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(Conversation).filter_by(user_id=user.id).order_by(Conversation.started_at.desc()).all()
