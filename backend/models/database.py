from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Створюємо абсолютний шлях до бази даних
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "media_scanner.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Створюємо директорію для бази даних, якщо вона не існує
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class KnownSource(Base):
    __tablename__ = "known_sources"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True)
    name = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class NewSource(Base):
    __tablename__ = "new_sources"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True)
    name = Column(String)
    url = Column(String)
    found_at = Column(DateTime, default=datetime.utcnow)

class SourceAnalysis(Base):
    __tablename__ = "source_analysis"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, index=True)
    is_active = Column(Boolean, default=True)
    last_post_date = Column(DateTime, nullable=True)
    category = Column(String, nullable=True)
    llm_comment = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

# Створюємо таблиці
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 