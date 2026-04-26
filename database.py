import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload
from datetime import datetime

# Uses DATABASE_URL env var on Render, falls back to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cashflow.db")

# Render gives postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    business_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="owner")
    products = relationship("Product", back_populates="owner")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    price = Column(Float)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="products")
    bookings = relationship("Booking", back_populates="product")


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    customer_name = Column(String)
    amount = Column(Float)
    status = Column(String, default="completed")  # completed, pending, cancelled
    booking_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    owner = relationship("User", back_populates="bookings")
    product = relationship("Product", back_populates="bookings")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_bookings(owner_id: int):
    """Fetch all bookings with product eagerly loaded — avoids DetachedInstanceError."""
    db = SessionLocal()
    try:
        return (
            db.query(Booking)
            .options(joinedload(Booking.product))
            .filter(Booking.owner_id == owner_id)
            .all()
        )
    finally:
        db.close()
