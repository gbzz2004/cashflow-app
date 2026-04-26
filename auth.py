import bcrypt
import streamlit as st
from sqlalchemy.orm import Session
from database import User, SessionLocal


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def get_db():
    return SessionLocal()


def register_user(username: str, password: str, business_name: str) -> tuple[bool, str]:
    db = get_db()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False, "Username already taken."
        user = User(
            username=username,
            hashed_password=hash_password(password),
            business_name=business_name
        )
        db.add(user)
        db.commit()
        return True, "Account created!"
    except Exception as e:
        return False, str(e)
    finally:
        db.close()


def login_user(username: str, password: str):
    db = get_db()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return {"id": user.id, "username": user.username, "business_name": user.business_name}
    finally:
        db.close()


def require_login():
    """Returns current user dict or None. Call at top of every page."""
    return st.session_state.get("user", None)
