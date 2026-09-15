from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.core.config import settings

# Engine configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    """Dependency that yields a database session and safely closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> Tuple[bool, str]:
    """
    Safely probes database connectivity without throwing unhandled exceptions.
    Returns (status_boolean, message).
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connected successfully"
    except OperationalError as e:
        return False, f"Database operational error: {e.orig if hasattr(e, 'orig') else str(e)}"
    except SQLAlchemyError as e:
        return False, f"Database error: {str(e)}"
    except Exception as e:
        return False, f"Database connection unavailable: {str(e)}"
