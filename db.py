from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use SQLite for now; later you can switch to Postgres via an env var
DATABASE_URL = "sqlite:///./prices.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # only for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()