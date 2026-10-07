"""
SQLAlchemy engine and session management.

Every query in this application goes through the SQLAlchemy ORM/Core
query builder (never raw string-formatted SQL), which parameterizes
values automatically and is the primary defense against SQL injection.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
