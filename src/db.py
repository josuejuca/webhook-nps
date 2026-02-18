import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_URL_MYSQL = os.getenv("DATABASE_URL_MYSQL", "").strip()


def _normalize_mysql_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return url

    
    
    if url.startswith("mysql://"):
        return "mysql+pymysql://" + url[len("mysql://") :]
    return url


def _create_engine(database_url: str):
    database_url = (database_url or "").strip()
    if database_url.startswith("sqlite:"):
        engine_kwargs = {
            "connect_args": {"check_same_thread": False},
            "pool_pre_ping": True,
        }

        
        
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool

        return create_engine(database_url, **engine_kwargs)

    connect_args = {}
    if database_url.startswith("postgresql"):
        connect_args["connect_timeout"] = 3
    elif database_url.startswith("mysql"):
        connect_args["connect_timeout"] = 3

    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    }
    if connect_args:
        engine_kwargs["connect_args"] = connect_args

    return create_engine(database_url, **engine_kwargs)


def _engine_is_available(candidate_engine) -> bool:
    try:
        with candidate_engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


def _select_engine():
    mysql_url = _normalize_mysql_url(DATABASE_URL_MYSQL)

    
    if DATABASE_URL:
        candidate = _create_engine(DATABASE_URL)
        if _engine_is_available(candidate):
            return candidate

    
    if mysql_url:
        candidate = _create_engine(mysql_url)
        if _engine_is_available(candidate):
            return candidate

    
    return _create_engine("sqlite:///:memory:")


engine = _select_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
