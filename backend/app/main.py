# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn

# # Import the chat router
# from app.routers.chat_router import router as chat_router
# # from routers.chat_router import router as chat_router

# app = FastAPI(title="Therapy Chatbot API")

# # Configure CORS for local development
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include the chat router
# app.include_router(chat_router)

# @app.get("/")
# async def root():
#     return {"message": "Therapy Chatbot API is running"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.chat_router import router as chat_router

# Import your database engine and models
from app.db.database import engine
from app.db import models
from app.db.database import Base
from app.auth.auth_router import router as auth_router


# TEMPORARY: Drop everything before recreating
models.Base.metadata.drop_all(bind=engine)  # ❗️ This wipes all tables
models.Base.metadata.create_all(bind=engine)  # ❗️ This rebuilds all tables

from app.auth.auth_router import router as auth_router
app = FastAPI(title="Therapy Chatbot API")

# Include both routers
app.include_router(auth_router)


# Create database tables on startup
models.Base.metadata.create_all(bind=engine)

# CORS for frontend (adjust domains as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register chat router
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"message": "Therapy Chatbot API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
