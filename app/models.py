from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://voiceagent:voiceagent@db:5432/voiceagent")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    phone_number = Column(String(20), nullable=False)
    contact_type = Column(String(20))  # 'friend' or 'facility'
    created_at = Column(DateTime, default=datetime.utcnow)

    calls = relationship("Call", back_populates="contact")


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    call_type = Column(String(20), nullable=False)  # 'personal_message' or 'facility_test'

    # Call details
    twilio_call_sid = Column(String(100), unique=True)
    status = Column(String(20), default="queued")
    direction = Column(String(10), default="outbound")

    # Custom message
    custom_message = Column(Text)

    # Custom call parameters
    caller_name = Column(String(200))  # e.g., "Krishnaji's CTO office", "ABC Company"
    custom_greeting = Column(Text)  # Custom greeting text
    custom_subject = Column(String(200))  # Subject/purpose of call

    # Timing
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    duration = Column(Integer)  # seconds

    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    scheduled_time = Column(DateTime)  # When to make the call

    # Recurring schedules
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(20))  # 'daily', 'weekly', 'monthly'
    recurrence_day = Column(String(20))  # 'monday', 'tuesday', etc. for weekly
    recurrence_time = Column(String(10))  # Time in HH:MM format (e.g., "17:00" for 5pm)
    is_active = Column(Boolean, default=True)  # For recurring calls, can pause/resume

    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    retry_on_no_answer = Column(Boolean, default=True)

    # Results
    recording_url = Column(Text)
    recording_file_path = Column(Text)
    transcript = Column(Text)
    test_result = Column(String(10))  # 'PASS'/'FAIL' for facility_test

    created_at = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="calls")
    transcript_segments = relationship("TranscriptSegment", back_populates="call", cascade="all, delete-orphan")
    analysis = relationship("CallAnalysis", back_populates="call", uselist=False, cascade="all, delete-orphan")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"))
    speaker = Column(String(10), nullable=False)  # 'agent' or 'user'
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sequence_number = Column(Integer, nullable=False)

    call = relationship("Call", back_populates="transcript_segments")


class CallAnalysis(Base):
    __tablename__ = "call_analysis"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"), unique=True)

    # AI-generated analysis
    summary = Column(Text)  # Brief summary of the conversation
    action_items = Column(Text)  # JSON array of action items
    requests = Column(Text)  # JSON array of requests made by user
    complaints = Column(Text)  # JSON array of complaints
    sentiment = Column(String(20))  # 'positive', 'neutral', 'negative'
    call_outcome = Column(String(50))  # 'answered', 'voicemail', 'no_answer', 'busy'

    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    call = relationship("Call", back_populates="analysis")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
