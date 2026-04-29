import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/cashflow.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

is_sqlite = "sqlite" in DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {"sslmode": "require"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    business_name   = Column(String)
    role            = Column(String, default="admin")
    created_at      = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="owner", foreign_keys="Booking.owner_id")
    products = relationship("Product", back_populates="owner")


class Product(Base):
    __tablename__ = "products"
    id          = Column(Integer, primary_key=True, index=True)
    owner_id    = Column(Integer, ForeignKey("users.id"))
    name        = Column(String)
    price       = Column(Float)
    description = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    owner    = relationship("User", back_populates="products")
    bookings = relationship("Booking", back_populates="product")


class Team(Base):
    __tablename__ = "teams"
    id          = Column(Integer, primary_key=True, index=True)
    owner_id    = Column(Integer, ForeignKey("users.id"))
    name        = Column(String)
    description = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    owner    = relationship("User", foreign_keys=[owner_id])
    bookings = relationship("Booking", back_populates="team")


class Booking(Base):
    __tablename__ = "bookings"
    id                = Column(Integer, primary_key=True, index=True)
    owner_id          = Column(Integer, ForeignKey("users.id"))
    product_id        = Column(Integer, ForeignKey("products.id"))
    customer_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id           = Column(Integer, ForeignKey("teams.id"), nullable=True)
    customer_name     = Column(String)
    amount            = Column(Float)
    downpayment       = Column(Float, nullable=True)
    remaining_balance = Column(Float, nullable=True)
    downpayment_paid  = Column(Boolean, default=False)
    status            = Column(String, default="pending")
    booking_date      = Column(DateTime, default=datetime.utcnow)
    notes             = Column(Text, nullable=True)

    owner    = relationship("User", back_populates="bookings", foreign_keys=[owner_id])
    product  = relationship("Product", back_populates="bookings")
    customer = relationship("User", foreign_keys=[customer_id])
    team     = relationship("Team", back_populates="bookings")


def init_db():
    # Creates all tables — works for both SQLite and PostgreSQL
    Base.metadata.create_all(bind=engine)

    # SQLite-only migrations for existing databases
    if is_sqlite:
        with engine.connect() as conn:
            for stmt in [
                "ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'admin'",
                "UPDATE users SET role = 'admin' WHERE role IS NULL",
                "ALTER TABLE bookings ADD COLUMN customer_id INTEGER",
                "ALTER TABLE bookings ADD COLUMN team_id INTEGER",
                "ALTER TABLE bookings ADD COLUMN downpayment REAL",
                "ALTER TABLE bookings ADD COLUMN remaining_balance REAL",
                "ALTER TABLE bookings ADD COLUMN downpayment_paid BOOLEAN DEFAULT 0",
            ]:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception:
                    pass

    # ── Create static admin account if it doesn't exist ──────────────────────
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "GAB_EDITOR").first()
        if not existing:
            import bcrypt
            hashed = bcrypt.hashpw("bgboy123".encode(), bcrypt.gensalt()).decode()
            admin  = User(
                username="GAB_EDITOR",
                hashed_password=hashed,
                business_name="StoryWeave Films",
                role="admin"
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_bookings(owner_id: int):
    """Fetch all bookings with product eagerly loaded."""
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