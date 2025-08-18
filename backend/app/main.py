
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.chat_router import router as chat_router
from app.auth.auth_router import router as auth_router
from app.auth.emotion_router import router as emotion_router
from app.auth.emotion_router import router as mental_health_router  #  Correct source

from app.db.database import engine
from app.db import models
from dotenv import load_dotenv
load_dotenv()  # Loads variables from .env into environment

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Therapy Chatbot API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(emotion_router)
app.include_router(mental_health_router, prefix="/insights")  # 

@app.get("/")
async def root():
    return {"message": "Therapy Chatbot API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
