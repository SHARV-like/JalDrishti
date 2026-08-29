from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.production.config import get_settings


def _engine_url() -> str:
    database_url = get_settings().database_url
    # SQLite does not create parent directories itself. Keeping this small
    # local fallback under tmp/ avoids accidentally tracking development data.
    if database_url.startswith("sqlite:///./"):
        database_path = Path(database_url.removeprefix("sqlite:///"))
        database_path.parent.mkdir(parents=True, exist_ok=True)
    return database_url


engine = create_engine(_engine_url(), future=True, connect_args={"check_same_thread": False} if _engine_url().startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
