import os
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# Import Base after other imports to avoid circular imports
from db.models import Base

# PostgreSQL database configuration
# Format: postgresql://username:password@host:port/database
SQLALCHEMY_DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# Create engine with connection pooling
engine: Engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """Get a new database session"""
    return SessionLocal()


def create_tables() -> None:
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Drop all database tables (use with caution)"""
    Base.metadata.drop_all(bind=engine)


def init_db() -> None:
    """Initialize the database"""
    create_tables()
    print("Database tables created successfully!")
