import os
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("suenalotto.database")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./suelotto.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _add_missing_columns():
    """Add columns that exist in models but not in the database."""
    from backend.models import User

    inspector = inspect(engine)
    existing_columns = {c["name"] for c in inspector.get_columns("users")}

    model_columns = {
        "email_verified": "BOOLEAN DEFAULT 0",
        "email_verification_token": "VARCHAR(200)",
        "password_reset_token": "VARCHAR(200)",
        "password_reset_expires": "DATETIME",
    }

    with engine.connect() as conn:
        for col_name, col_type in model_columns.items():
            if col_name not in existing_columns:
                logger.info("Adding missing column: users.%s", col_name)
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
        conn.commit()


def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        _add_missing_columns()
    except Exception as e:
        logger.warning("Could not add missing columns (non-fatal): %s", e)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
