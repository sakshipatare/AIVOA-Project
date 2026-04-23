from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crm.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class HCP(Base):
    __tablename__ = "hcps"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    specialty = Column(String)
    location = Column(String)
    email = Column(String, unique=True, index=True)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    
    interactions = relationship("Interaction", back_populates="hcp")

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"))
    date = Column(DateTime, default=datetime.utcnow)
    type = Column(String) # Meeting, Call, Email
    summary = Column(Text)
    sentiment = Column(String) # Positive, Neutral, Negative
    materials_shared = Column(JSON) # List of documents/samples
    outcomes = Column(Text)
    next_steps = Column(Text)
    raw_transcript = Column(Text, nullable=True) # For AI processing
    
    hcp = relationship("HCP", back_populates="interactions")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
