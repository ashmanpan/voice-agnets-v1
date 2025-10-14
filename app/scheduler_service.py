"""
Call Scheduler Service
Handles scheduled and recurring calls using APScheduler
NOW USES LIVEKIT FOR ALL CALLS (1-3s latency!)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Call, Contact, get_db
import logging
import asyncio
import json
import os
from livekit import api as livekit_api

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()


def initiate_livekit_call_sync(
    db: Session,
    call_id: int,
    phone_number: str,
    contact_name: str,
    custom_greeting: str = None,
    caller_name: str = None,
    system_prompt: str = None,
    max_turns: int = 8
):
    """
    Synchronous wrapper for LiveKit call initiation (for scheduler)
    """
    async def _async_initiate():
        try:
            lk_api = livekit_api.LiveKitAPI(
                url=os.getenv("LIVEKIT_URL"),
                api_key=os.getenv("LIVEKIT_API_KEY"),
                api_secret=os.getenv("LIVEKIT_API_SECRET"),
            )

            room_name = f"call-{call_id}"

            # Prepare metadata
            metadata = {
                "phone_number": phone_number,
                "contact_name": contact_name,
                "greeting": custom_greeting,
                "call_id": call_id,
                "caller_name": caller_name or "Krishnaji's CTO office",
                "sip_trunk_id": os.getenv("LIVEKIT_SIP_TRUNK_ID"),
                "system_prompt": system_prompt,
                "max_turns": max_turns
            }

            # Dispatch agent
            dispatch_response = await lk_api.agent_dispatch.create_dispatch(
                livekit_api.CreateAgentDispatchRequest(
                    room=room_name,
                    agent_name="voice-assistant",
                    metadata=json.dumps(metadata)
                )
            )

            logger.info(f"✅ LiveKit scheduled call initiated: Room={room_name}, Phone={phone_number}")

            # Update call record
            call = db.query(Call).filter(Call.id == call_id).first()
            if call:
                call.livekit_room_name = room_name
                call.status = "in-progress"
                db.commit()

            return room_name

        except Exception as e:
            logger.error(f"❌ LiveKit scheduled call failed: {e}")
            call = db.query(Call).filter(Call.id == call_id).first()
            if call:
                call.status = "failed"
                db.commit()
            raise

    # Run async function in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_async_initiate())
    finally:
        loop.close()


def execute_scheduled_call(call_id: int):
    """
    Execute a scheduled call using LiveKit (1-3s latency!)

    Args:
        call_id: ID of the call to execute
    """
    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            logger.error(f"Call {call_id} not found for scheduled execution")
            return

        # Check if call is still active (for recurring)
        if call.is_recurring and not call.is_active:
            logger.info(f"Skipping call {call_id} - recurring schedule is paused")
            return

        contact = db.query(Contact).filter(Contact.id == call.contact_id).first()
        if not contact:
            logger.error(f"Contact not found for call {call_id}")
            return

        logger.info(f"Executing scheduled LiveKit call {call_id} to {contact.name} ({contact.phone_number})")

        # Update status
        call.status = "queued"
        db.commit()

        # Initiate the call with LiveKit
        initiate_livekit_call_sync(
            db=db,
            call_id=call_id,
            phone_number=contact.phone_number,
            contact_name=contact.name,
            custom_greeting=call.custom_greeting,
            caller_name=call.caller_name
        )

        logger.info(f"✅ Successfully initiated scheduled LiveKit call {call_id}")

    except Exception as e:
        logger.error(f"❌ Error executing scheduled call {call_id}: {str(e)}")
    finally:
        db.close()


def schedule_one_time_call(call_id: int, scheduled_time: datetime):
    """
    Schedule a one-time call

    Args:
        call_id: ID of the call
        scheduled_time: When to make the call
    """
    job_id = f"call_{call_id}"

    # Remove existing job if any
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # Schedule the call
    scheduler.add_job(
        execute_scheduled_call,
        trigger=DateTrigger(run_date=scheduled_time),
        args=[call_id],
        id=job_id,
        replace_existing=True
    )

    logger.info(f"Scheduled one-time call {call_id} for {scheduled_time}")


def schedule_recurring_call(call_id: int, pattern: str, recurrence_time: str, day: str = None):
    """
    Schedule a recurring call

    Args:
        call_id: ID of the call
        pattern: 'daily', 'weekly', 'monthly'
        recurrence_time: Time in HH:MM format (e.g., "17:00")
        day: Day of week for weekly pattern (e.g., "monday")
    """
    job_id = f"recurring_call_{call_id}"

    # Remove existing job if any
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # Parse time
    hour, minute = map(int, recurrence_time.split(':'))

    # Create cron trigger based on pattern
    if pattern == 'daily':
        trigger = CronTrigger(hour=hour, minute=minute)
        logger.info(f"Scheduling daily call {call_id} at {recurrence_time}")

    elif pattern == 'weekly':
        # Map day names to cron format
        day_map = {
            'monday': 'mon',
            'tuesday': 'tue',
            'wednesday': 'wed',
            'thursday': 'thu',
            'friday': 'fri',
            'saturday': 'sat',
            'sunday': 'sun'
        }
        cron_day = day_map.get(day.lower(), 'mon')
        trigger = CronTrigger(day_of_week=cron_day, hour=hour, minute=minute)
        logger.info(f"Scheduling weekly call {call_id} every {day} at {recurrence_time}")

    elif pattern == 'monthly':
        # Run on the 1st of every month
        trigger = CronTrigger(day=1, hour=hour, minute=minute)
        logger.info(f"Scheduling monthly call {call_id} on day 1 at {recurrence_time}")

    else:
        logger.error(f"Unknown recurrence pattern: {pattern}")
        return

    # Schedule the call
    scheduler.add_job(
        execute_scheduled_call,
        trigger=trigger,
        args=[call_id],
        id=job_id,
        replace_existing=True
    )


def cancel_scheduled_call(call_id: int):
    """
    Cancel a scheduled call

    Args:
        call_id: ID of the call
    """
    job_id = f"call_{call_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Cancelled scheduled call {call_id}")


def pause_recurring_call(call_id: int):
    """
    Pause a recurring call

    Args:
        call_id: ID of the call
    """
    job_id = f"recurring_call_{call_id}"
    if scheduler.get_job(job_id):
        scheduler.pause_job(job_id)
        logger.info(f"Paused recurring call {call_id}")


def resume_recurring_call(call_id: int):
    """
    Resume a paused recurring call

    Args:
        call_id: ID of the call
    """
    job_id = f"recurring_call_{call_id}"
    if scheduler.get_job(job_id):
        scheduler.resume_job(job_id)
        logger.info(f"Resumed recurring call {call_id}")


def cancel_recurring_call(call_id: int):
    """
    Cancel a recurring call

    Args:
        call_id: ID of the call
    """
    job_id = f"recurring_call_{call_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Cancelled recurring call {call_id}")


def load_scheduled_calls():
    """
    Load all scheduled calls from database and add them to scheduler
    This should be called on application startup
    """
    from models import SessionLocal
    db = SessionLocal()

    try:
        # Load one-time scheduled calls
        scheduled_calls = db.query(Call).filter(
            Call.is_scheduled == True,
            Call.scheduled_time > datetime.utcnow(),
            Call.status == 'scheduled'
        ).all()

        for call in scheduled_calls:
            schedule_one_time_call(call.id, call.scheduled_time)
            logger.info(f"Loaded scheduled call {call.id} for {call.scheduled_time}")

        # Load recurring calls
        recurring_calls = db.query(Call).filter(
            Call.is_recurring == True,
            Call.is_active == True
        ).all()

        for call in recurring_calls:
            schedule_recurring_call(
                call.id,
                call.recurrence_pattern,
                call.recurrence_time,
                call.recurrence_day
            )
            logger.info(f"Loaded recurring call {call.id} - {call.recurrence_pattern} at {call.recurrence_time}")

        logger.info(f"Loaded {len(scheduled_calls)} scheduled calls and {len(recurring_calls)} recurring calls")

    except Exception as e:
        logger.error(f"Error loading scheduled calls: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """Start the scheduler"""
    if not scheduler.running:
        scheduler.start()
        logger.info("Call scheduler started")

        # Load existing scheduled calls
        load_scheduled_calls()


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Call scheduler stopped")


# Import SessionLocal after models are defined
from models import SessionLocal
