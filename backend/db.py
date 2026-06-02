import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Fallback to local SQLite if no database URL is configured in environment
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    db_dir = os.environ.get("DATABASE_DIR")
    if db_dir:
        DATABASE_URL = f"sqlite:///{Path(db_dir) / 'events.db'}"
    else:
        DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'events.db'}"

# SQLite requires special connect arguments for threading
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

