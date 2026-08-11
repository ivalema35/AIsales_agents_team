import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from config import Config

Base = declarative_base()
engine = create_engine(
    f"sqlite:///{Config.DB_PATH}",
    connect_args={"check_same_thread": False},   # sessions opened per worker thread
    future=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")     # persistent; harmless to repeat
        cur.execute("PRAGMA foreign_keys=ON;")      # MUST be per-connection
        cur.execute("PRAGMA synchronous=NORMAL;")   # safe + fast under WAL
        cur.execute("PRAGMA busy_timeout=10000;")   # 10s lock wait
        cur.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
