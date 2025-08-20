from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get DB session.
    Provides a database session for each request and ensures it's closed properly.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session directly (for use in background tasks).
    Remember to close the session manually when done.
    """
    return SessionLocal()


def close_db_session(db: Session) -> None:
    """
    Close a database session manually.
    """
    if db:
        db.close()


def create_tables():
    """
    Create all database tables.
    This should be used during initial setup or migrations.
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Drop all database tables.
    WARNING: This will delete all data!
    """
    Base.metadata.drop_all(bind=engine)


def check_database_connection() -> bool:
    """
    Check if the database connection is working.
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception:
        return False


def get_engine():
    """
    Get the database engine.
    """
    return engine
