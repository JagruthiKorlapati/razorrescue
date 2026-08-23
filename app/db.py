from datetime import datetime

from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class PaymentFailure(Base):
    __tablename__ = "payment_failures"

    id = Column(String, primary_key=True)  # payment_id
    error_code = Column(String)
    error_source = Column(String)
    amount = Column(Integer)
    classification = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class RetryJob(Base):
    __tablename__ = "retry_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(String)
    attempt_no = Column(Integer)
    outcome = Column(String)  # 'recovered', 'failed', 'exhausted'
    created_at = Column(DateTime, default=datetime.utcnow)


class RailSwitchEvent(Base):
    __tablename__ = "rail_switch_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(String)
    fallback_txn_ref = Column(String)
    upi_intent_link = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(String)
    direction = Column(String)  # 'outbound' or 'inbound'
    message_text = Column(Text)
    extracted_intent = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RecoveryLedger(Base):
    __tablename__ = "recovery_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(String)
    recovered = Column(Boolean, default=False)
    recovery_channel = Column(String, nullable=True)  # 'same_rail_retry', 'cross_rail', 'promise_to_pay'
    action = Column(String)  # 'rescheduled', 'cancelled', 'immediate_retry_triggered', etc
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()