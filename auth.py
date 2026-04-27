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


# ── Admin Auth ────────────────────────────────────────────────────────────────

def register_user(username: str, password: str, business_name: str) -> tuple[bool, str]:
    db = get_db()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False, "Username already taken."
        user = User(
            username=username,
            hashed_password=hash_password(password),
            business_name=business_name,
            role="admin"  # ← explicitly set role
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
        user = db.query(User).filter(
            User.username == username,
            User.role == "admin"  # ← only admins can login here
        ).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return {
            "id": user.id,
            "username": user.username,
            "business_name": user.business_name,
            "role": user.role
        }
    finally:
        db.close()


def require_login():
    """Returns current user dict or None. Call at top of every admin page."""
    return st.session_state.get("user", None)


# ── Customer Auth ─────────────────────────────────────────────────────────────

def register_customer(username: str, password: str, full_name: str) -> tuple[bool, str]:
    db = get_db()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False, "Username already taken."
        user = User(
            username=username,
            hashed_password=hash_password(password),
            business_name=full_name,  # store full name in business_name field
            role="customer"  # ← customer role
        )
        db.add(user)
        db.commit()
        return True, "Account created successfully!"
    except Exception as e:
        return False, str(e)
    finally:
        db.close()


def login_customer(username: str, password: str):
    db = get_db()
    try:
        user = db.query(User).filter(
            User.username == username,
            User.role == "customer"  # ← only customers can login here
        ).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.business_name,
            "role": user.role
        }
    finally:
        db.close()


def require_customer_login():
    """Returns current customer dict or None. Call at top of customer pages."""
    return st.session_state.get("customer", None)