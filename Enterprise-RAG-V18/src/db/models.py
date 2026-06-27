# src/db/models.py
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    sessions = relationship("Session", back_populates="user")
    token_budgets = relationship("TokenBudget", back_populates="user")
    query_logs = relationship("QueryLog", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    user = relationship("User", back_populates="sessions")
    query_logs = relationship("QueryLog", back_populates="session")

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    query = Column(String, nullable=False)
    intent = Column(String)
    response = Column(String)
    latency_ms = Column(Integer)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    session = relationship("Session", back_populates="query_logs")
    user = relationship("User", back_populates="query_logs")


class TokenBudget(Base):
    __tablename__ = "token_budgets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    tokens_used = Column(Integer, default=0)
    
    user = relationship("User", back_populates="token_budgets")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )

class SQLApproval(Base):
    __tablename__ = "sql_approvals"
    id = Column(String, primary_key=True, index=True) # Usually mapping to session or query id
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    sql_query = Column(String, nullable=False)
    status = Column(String, default="pending") # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class EvalResult(Base):
    __tablename__ = "eval_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_config = Column(String, nullable=False)
    metrics = Column(JSON, nullable=False) # e.g. {"faithfulness": 0.9, ...}
    confidence = Column(JSON, nullable=True) # Confidence intervals
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_hash = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, nullable=False)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
