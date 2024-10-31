from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

DATABASE_PAPER = "sqlite:///./data/papers.db"

# Set up SQLAlchemy
engine = create_engine(DATABASE_PAPER, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Paper model representing the papers table
class Paper(Base):
    __tablename__ = "papers"

    doi = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    authors = Column(String)  # Store as comma-separated string
    abstract = Column(String)
    journal = Column(String)
    volume = Column(String)
    published = Column(DateTime)
    added_by = Column(String)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    votes = Column(Integer, default=0)

# Create tables
Base.metadata.create_all(bind=engine)
