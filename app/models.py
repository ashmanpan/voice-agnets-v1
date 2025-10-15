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
    livekit_room_name = Column(String(100))  # LiveKit room name for low-latency calls
    status = Column(String(20), default="queued")
    direction = Column(String(10), default="outbound")

    # Custom message
    custom_message = Column(Text)

    # Custom call parameters
    caller_name = Column(String(200))  # e.g., "Krishnaji's CTO office", "ABC Company"
    custom_greeting = Column(Text)  # Custom greeting text
    custom_subject = Column(String(200))  # Subject/purpose of call
    language = Column(String(10), default="en")  # Language code: 'en', 'hi' (Hindi), 'mr' (Marathi)

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


class ActionItem(Base):
    """
    Type 2: Reactive actions extracted from conversations
    These are things the user asked for / complained about / requested
    """
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))

    # Action details
    action_type = Column(String(20))  # 'question', 'request', 'complaint', 'follow_up'
    description = Column(Text, nullable=False)
    priority = Column(String(10), default='medium')  # 'high', 'medium', 'low'

    # Status tracking
    status = Column(String(20), default='pending')  # 'pending', 'in_progress', 'completed', 'cancelled'
    assigned_to = Column(String(100))  # Who should handle this (e.g., "CTO Office")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)

    # Additional context
    notes = Column(Text)  # Additional notes or updates
    urgency_score = Column(Integer, default=50)  # 0-100 score for sorting
    source_text = Column(Text)  # Original text from transcript that triggered this action

    # Relationships
    call = relationship("Call")
    contact = relationship("Contact")


class Task(Base):
    """
    Type 1: Proactive tasks assigned TO contacts
    Agent will call the contact to explain task and collect response
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    assigned_call_id = Column(Integer, ForeignKey("calls.id"))  # The call that will deliver this task

    # Task details
    title = Column(String(200), nullable=False)  # Short title
    description = Column(Text, nullable=False)  # Full task description
    task_type = Column(String(50), default='reminder')  # 'reminder', 'confirmation', 'survey', 'follow_up'

    # What agent should say/ask
    agent_script = Column(Text)  # What agent says to contact
    questions_to_ask = Column(Text)  # JSON array of questions agent should ask
    collect_response = Column(Boolean, default=True)  # Should agent collect and record response?

    # Status tracking
    status = Column(String(20), default='pending')  # 'pending', 'scheduled', 'in_progress', 'completed', 'failed'
    priority = Column(String(10), default='medium')

    # Response collection
    contact_response = Column(Text)  # What contact said in response
    response_sentiment = Column(String(20))  # Sentiment of their response
    task_completed = Column(Boolean, default=False)  # Did contact confirm/complete task?

    # Scheduling
    scheduled_time = Column(DateTime)  # When to make the call
    call_attempts = Column(Integer, default=0)  # How many times we tried
    max_attempts = Column(Integer, default=3)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))  # Who assigned this task
    completed_at = Column(DateTime)
    last_attempt_at = Column(DateTime)

    # Additional notes
    notes = Column(Text)

    # Relationships
    contact = relationship("Contact")
    assigned_call = relationship("Call", foreign_keys=[assigned_call_id])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
