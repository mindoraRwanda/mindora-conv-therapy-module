# from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, String
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from .database import Base

# class User(Base):
#     __tablename__ = 'users'
#     id = Column(Integer, primary_key=True)
#     username = Column(Text, nullable=False) 
#     email = Column(Text, nullable=False, unique=True)  # Email remains unique
#     password = Column(Text, nullable=False) 
#     created_at = Column(TIMESTAMP, default=datetime.utcnow)
#     conversations = relationship("Conversation", back_populates="user")

# class Conversation(Base):
#     __tablename__ = 'conversations'
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
#     started_at = Column(TIMESTAMP, default=datetime.utcnow)
#     last_activity_at = Column(TIMESTAMP, default=datetime.utcnow)  # added for tracking
    
#     user = relationship("User", back_populates="conversations")
#     messages = relationship(
#         "Message",
#         back_populates="conversation",
#         cascade="all, delete-orphan"
#     )

# class Message(Base):
#     __tablename__ = 'messages'
#     id = Column(Integer, primary_key=True)
#     conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
#     sender = Column(String(10), nullable=False)  # "user" or "bot"
#     content = Column(Text, nullable=False)
#     timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    
#     conversation = relationship("Conversation", back_populates="messages")

# class EmotionLog(Base):
#     __tablename__ = "emotion_logs"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     conversation_id = Column(Integer, ForeignKey("conversations.id"))
#     input_text = Column(Text)
#     detected_emotion = Column(String(50))
#     timestamp = Column(TIMESTAMP, default=datetime.utcnow)    
### FILE: app/db/models.py

# from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, String
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from .database import Base

# class User(Base):
#     __tablename__ = 'users'
#     id = Column(String, primary_key=True, index=True)
#     username = Column(Text, nullable=False)
#     email = Column(Text, nullable=False, unique=True)
#     password = Column(Text, nullable=False)
#     created_at = Column(TIMESTAMP, default=datetime.utcnow)
#     conversations = relationship("Conversation", back_populates="user")

# class Conversation(Base):
#     __tablename__ = 'conversations'
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
#     started_at = Column(TIMESTAMP, default=datetime.utcnow)
#     last_activity_at = Column(TIMESTAMP, default=datetime.utcnow)

#     user = relationship("User", back_populates="conversations")
#     messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

# class Message(Base):
#     __tablename__ = 'messages'
#     id = Column(Integer, primary_key=True)
#     conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
#     sender = Column(String(10), nullable=False)
#     content = Column(Text, nullable=False)
#     timestamp = Column(TIMESTAMP, default=datetime.utcnow)

#     conversation = relationship("Conversation", back_populates="messages")

# class EmotionLog(Base):
#     __tablename__ = "emotion_logs"

#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     conversation_id = Column(Integer, ForeignKey("conversations.id"))
#     input_text = Column(Text)
#     detected_emotion = Column(String(50))
#     timestamp = Column(TIMESTAMP, default=datetime.utcnow)

import uuid
from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, String
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True, index=True)  # UUID from mobile or generated locally
    username = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password = Column(Text, nullable=False)  # 'external_auth' for bridged users
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    started_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_activity_at = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    emotion_logs = relationship(
        "EmotionLog",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True
    )



class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey('conversations.id', ondelete="CASCADE"),
        nullable=False
    )
    sender = Column(String(10), nullable=False)  # 'user' or 'bot'
    content = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class EmotionLog(Base):
    __tablename__ = "emotion_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    input_text = Column(Text)
    detected_emotion = Column(String(50))
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="emotion_logs")

