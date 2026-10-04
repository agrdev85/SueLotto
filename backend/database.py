import os
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("suenalotto.database")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./suelotto.db")
IS_SQLITE = "sqlite" in DATABASE_URL

if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    _needs_ssl = "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"sslmode": "require", "connect_timeout": 10} if _needs_ssl else {"connect_timeout": 10},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _add_missing_columns():
    from backend.models import User

    with engine.connect() as conn:
        for table, model_columns in (
            (
                "users",
                {
                    "email_verified": "BOOLEAN DEFAULT FALSE" if not IS_SQLITE else "BOOLEAN DEFAULT 0",
                    "email_verification_token": "VARCHAR(200)",
                    "password_reset_token": "VARCHAR(200)",
                    "password_reset_expires": "TIMESTAMP" if not IS_SQLITE else "DATETIME",
                    "tier": "VARCHAR(20) DEFAULT 'free'",
                    "tier_expires": "DATE",
                    "is_active": "BOOLEAN DEFAULT TRUE" if not IS_SQLITE else "BOOLEAN DEFAULT 1",
                },
            ),
            (
                "manual_payments",
                {
                    "receipt_extension": "VARCHAR(10)",
                    "receipt_data": "BYTEA" if not IS_SQLITE else "BLOB",
                },
            ),
        ):
            if not engine.dialect.has_table(conn, table):
                continue
            existing_columns = {c["name"] for c in inspect(conn).get_columns(table)}
            for col_name, col_type in model_columns.items():
                if col_name not in existing_columns:
                    logger.info("Adding missing column: %s.%s", table, col_name)
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
        conn.commit()


def _seed_default_admin():
    from backend.auth import hash_password, verify_password
    from backend.models import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "AGR").first()
        if user is None:
            try:
                db.add(
                    User(
                        username="AGR",
                        email="admin@suenalotto.com",
                        password_hash=hash_password("agr*282"),
                        tier="admin",
                        email_verified=True,
                        is_active=True,
                    )
                )
                db.commit()
                logger.info("Default admin user 'AGR' created")
            except Exception as e:
                db.rollback()
                logger.warning("Seed AGR falló (posible secuencia desalineada): %s — reintentando", e)
                from backend.db_manager import _reset_sequences
                _reset_sequences(db)
                db.add(
                    User(
                        username="AGR",
                        email="admin@suenalotto.com",
                        password_hash=hash_password("agr*282"),
                        tier="admin",
                        email_verified=True,
                        is_active=True,
                    )
                )
                db.commit()
                logger.info("Default admin user 'AGR' created tras re-sincronizar secuencias")
        else:
            user.tier = "admin"
            if not user.password_hash or not verify_password("agr*282", user.password_hash):
                user.password_hash = hash_password("agr*282")
                logger.info("Default admin 'AGR' password restaurada al valor por defecto")
            db.commit()
            logger.info("Default admin user 'AGR' ensured (tier=admin)")
    except Exception as e:
        db.rollback()
        logger.warning("Could not seed default admin (non-fatal): %s", e)
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        _add_missing_columns()
    except Exception as e:
        logger.warning("Could not add missing columns (non-fatal): %s", e)
    _seed_default_admin()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine_info() -> dict:
    return {
        "driver": "sqlite" if IS_SQLITE else "postgresql",
        "url": DATABASE_URL if IS_SQLITE else DATABASE_URL.split("@")[-1].split("?")[0],
    }
