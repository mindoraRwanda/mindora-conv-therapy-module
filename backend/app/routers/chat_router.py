from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Import the LLM service
from app.services.llm_service import LLMService
from nemoguardrails import LLMRails, RailsConfig


# Create a router
router = APIRouter(prefix="/api", tags=["chat"])

# Initialize the LLM service (lazy loading)
_llm_service = None

def get_llm_service():
    """Lazy initialization of the LLM service"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(model_name="llama3")  # this matches Ollama

    return _llm_service

# Define the message schema
class Message(BaseModel):
    message: str
    conversation_id: Optional[str] = None

# Define the response schema
class ChatResponse(BaseModel):
    response: str
    timestamp: str
    conversation_id: Optional[str] = None

# Simple conversation storage
conversation_store = {}
@router.post("/chat", response_model=ChatResponse)
async def chat(message: Message, llm_service: LLMService = Depends(get_llm_service)):
    conversation_id = message.conversation_id or f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conversation = conversation_store.get(conversation_id, [])
    
    conversation.append({
        "role": "user",
        "text": message.message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Await the async function
    response_text = await llm_service.generate_response(
        message.message, 
        conversation_history=conversation
    )
    
    timestamp = datetime.now().isoformat()
    
    conversation.append({
        "role": "model",
        "text": response_text,
        "timestamp": timestamp
    })
    
    conversation_store[conversation_id] = conversation
    
    return ChatResponse(
        response=response_text,
        timestamp=timestamp,
        conversation_id=conversation_id
    )
