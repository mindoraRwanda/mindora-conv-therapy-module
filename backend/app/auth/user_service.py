from app.db.models import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

def get_or_create_user(user_id: str, db: Session) -> User:
    user_id = str(user_id)  # Ensure always string
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user

    new_user = User(
        id=user_id,
        username=f"user_{user_id[:8]}",
        email=f"unknown_{user_id}@placeholder.local",
        password="external_auth"
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.query(User).filter(User.id == user_id).first()

    db.refresh(new_user)
    return new_user
