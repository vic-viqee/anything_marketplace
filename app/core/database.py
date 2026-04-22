from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import Settings
import logging

settings = Settings()
logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=settings.DEBUG)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def run_startup_migrations():
    """Run migrations for missing columns on startup."""
    migrations = [
        ("users", "is_identity_verified", "BOOLEAN DEFAULT FALSE"),
        ("users", "pending_tier", "VARCHAR(20)"),
        ("users", "pending_payment_checkout_id", "VARCHAR(100)"),
        ("users", "payment_pending_at", "TIMESTAMP WITH TIME ZONE"),
        ("products", "is_featured", "BOOLEAN DEFAULT FALSE"),
        ("products", "featured_until", "TIMESTAMP WITH TIME ZONE"),
        ("products", "featured_by_admin", "BOOLEAN DEFAULT FALSE"),
    ]

    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                result = conn.execute(
                    text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{column}'
                """)
                )
                if result.fetchone() is None:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                    )
                    logger.info(f"Migration: Added {column} to {table}")
                else:
                    logger.debug(f"Migration: {column} already exists in {table}")
            except Exception as e:
                logger.error(f"Migration error for {column}: {e}")
        conn.commit()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
