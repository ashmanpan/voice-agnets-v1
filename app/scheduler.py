"""
Call Scheduler Service - Manages scheduled and recurring calls
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Call, Contact, SessionLocal
from twilio.rest import Client
import os
from call_analyzer import CallAnalyzer


class CallScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.analyzer = CallAnalyzer()

    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        print("📅 Call scheduler started")

        # Load existing scheduled calls from database
        self._load_scheduled_calls()

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("📅 Call scheduler stopped")

    def _load_scheduled_calls(self):
        """Load all scheduled calls from database and add them to scheduler"""
        db = SessionLocal()
        try:
            # Load one-time scheduled calls
            scheduled_calls = db.query(Call).filter(
                Call.is_scheduled == True,
                Call.scheduled_time > datetime.utcnow(),
                Call.status == 'queued'
            ).all()

            for call in scheduled_calls:
                self.schedule_call(call.id, call.scheduled_time)
                print(f"  Loaded scheduled call {call.id} for {call.scheduled_time}")

            # Load recurring calls
            recurring_calls = db.query(Call).filter(
                Call.is_recurring == True,
                Call.is_active == True
            ).all()

            for call in recurring_calls:
                self.schedule_recurring_call(
                    call.id,
                    call.recurrence_pattern,
                    call.recurrence_time,
                    call.recurrence_day
                )
                print(f"  Loaded recurring call {call.id} ({call.recurrence_pattern})")

        finally:
            db.close()

    def schedule_call(self, call_id: int, scheduled_time: datetime):
        """Schedule a one-time call"""
        job_id = f"call_{call_id}"

        # Remove existing job if present
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Add new job
        self.scheduler.add_job(
            self._execute_call,
            trigger=DateTrigger(run_date=scheduled_time),
            args=[call_id],
            id=job_id,
            replace_existing=True
        )
        print(f"📅 Scheduled call {call_id} for {scheduled_time}")

    def schedule_recurring_call(self, call_id: int, pattern: str, time_str: str, day: str = None):
        """Schedule a recurring call"""
        job_id = f"recurring_call_{call_id}"

        # Parse time (HH:MM format)
        hour, minute = map(int, time_str.split(':'))

        # Remove existing job if present
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Create trigger based on pattern
        if pattern == 'daily':
            trigger = CronTrigger(hour=hour, minute=minute)
        elif pattern == 'weekly':
            # Map day names to cron day_of_week
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2,
                'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
            }
            dow = day_map.get(day.lower(), 0)
            trigger = CronTrigger(day_of_week=dow, hour=hour, minute=minute)
        elif pattern == 'monthly':
            # First day of month
            trigger = CronTrigger(day=1, hour=hour, minute=minute)
        else:
            print(f"Unknown recurrence pattern: {pattern}")
            return

        # Add job
        self.scheduler.add_job(
            self._execute_recurring_call,
            trigger=trigger,
            args=[call_id],
            id=job_id,
            replace_existing=True
        )
        print(f"📅 Scheduled recurring call {call_id} ({pattern}, {time_str})")

    def _execute_call(self, call_id: int):
        """Execute a scheduled call"""
        db = SessionLocal()
        try:
            call = db.query(Call).filter(Call.id == call_id).first()
            if not call:
                print(f"Call {call_id} not found")
                return

            contact = call.contact
            if not contact:
                print(f"Contact not found for call {call_id}")
                return

            print(f"📞 Executing scheduled call {call_id} to {contact.name}")

            # Make the Twilio call
            self._make_twilio_call(call, contact, db)

        except Exception as e:
            print(f"Error executing call {call_id}: {e}")
        finally:
            db.close()

    def _execute_recurring_call(self, call_id: int):
        """Execute a recurring call - creates a new call record each time"""
        db = SessionLocal()
        try:
            # Get the template call
            template_call = db.query(Call).filter(Call.id == call_id).first()
            if not template_call or not template_call.is_active:
                print(f"Recurring call {call_id} not active or not found")
                return

            contact = template_call.contact

            # Create a new call record based on the template
            new_call = Call(
                contact_id=template_call.contact_id,
                call_type=template_call.call_type,
                custom_message=template_call.custom_message,
                caller_name=template_call.caller_name,
                custom_greeting=template_call.custom_greeting,
                custom_subject=template_call.custom_subject,
                status='queued',
                retry_on_no_answer=template_call.retry_on_no_answer,
                max_retries=template_call.max_retries
            )
            db.add(new_call)
            db.commit()
            db.refresh(new_call)

            print(f"📞 Executing recurring call (template: {call_id}, new: {new_call.id}) to {contact.name}")

            # Make the Twilio call
            self._make_twilio_call(new_call, contact, db)

        except Exception as e:
            print(f"Error executing recurring call {call_id}: {e}")
        finally:
            db.close()

    def _make_twilio_call(self, call: Call, contact: Contact, db: Session):
        """Make the actual Twilio call"""
        try:
            twilio_call = self.twilio_client.calls.create(
                to=contact.phone_number,
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                url=f"{os.getenv('BASE_URL')}/api/twilio/voice/{call.id}",
                status_callback=f"{os.getenv('BASE_URL')}/api/twilio/status/{call.id}",
                status_callback_event=['completed'],
                record=True
            )

            call.twilio_call_sid = twilio_call.sid
            call.status = 'in-progress'
            db.commit()

            print(f"✅ Call initiated: {twilio_call.sid}")

        except Exception as e:
            call.status = 'failed'
            db.commit()
            print(f"❌ Failed to initiate call: {e}")

            # Schedule retry if applicable
            if call.retry_on_no_answer and call.retry_count < call.max_retries:
                self._schedule_retry(call, db)

    def _schedule_retry(self, call: Call, db: Session):
        """Schedule a retry for a failed call"""
        call.retry_count += 1
        db.commit()

        # Retry after 30 minutes
        retry_time = datetime.utcnow() + timedelta(minutes=30)

        print(f"🔄 Scheduling retry {call.retry_count}/{call.max_retries} for call {call.id} at {retry_time}")

        self.schedule_call(call.id, retry_time)

    def cancel_scheduled_call(self, call_id: int):
        """Cancel a scheduled call"""
        job_id = f"call_{call_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            print(f"❌ Cancelled scheduled call {call_id}")

    def pause_recurring_call(self, call_id: int, db: Session):
        """Pause a recurring call"""
        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.is_active = False
            db.commit()

            job_id = f"recurring_call_{call_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

            print(f"⏸️  Paused recurring call {call_id}")

    def resume_recurring_call(self, call_id: int, db: Session):
        """Resume a paused recurring call"""
        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.is_active = True
            db.commit()

            self.schedule_recurring_call(
                call.id,
                call.recurrence_pattern,
                call.recurrence_time,
                call.recurrence_day
            )

            print(f"▶️  Resumed recurring call {call_id}")


# Global scheduler instance
scheduler_instance = None


def get_scheduler():
    """Get or create the global scheduler instance"""
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = CallScheduler()
        scheduler_instance.start()
    return scheduler_instance
