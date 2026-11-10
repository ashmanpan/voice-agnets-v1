"""Proactive task (Type 1) endpoints: assign, list, get, update, and
dispatch a task-delivery call."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models import get_db, Contact, Call, Task
from services.livekit_service import initiate_livekit_call
from scheduler_service import schedule_one_time_call

router = APIRouter()


@router.post("/api/tasks/assign")
async def assign_task(
    contact_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    task_type: str = Form("reminder"),  # reminder/confirmation/survey/follow_up
    agent_script: str = Form(None),
    questions_to_ask: str = Form(None),  # JSON array
    scheduled_time: str = Form(None),  # ISO datetime
    priority: str = Form("medium"),
    created_by: str = Form("CTO Office"),
    db: Session = Depends(get_db)
):
    """
    Type 1: Assign a proactive task to a contact
    Agent will call the contact to explain the task and collect response
    """
    from models import Task
    try:
        # Validate contact exists
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return JSONResponse({
                "success": False,
                "error": "Contact not found"
            }, status_code=404)

        # Parse scheduled time if provided
        scheduled_datetime = None
        if scheduled_time:
            scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

        # Create task
        task = Task(
            contact_id=contact_id,
            title=title,
            description=description,
            task_type=task_type,
            agent_script=agent_script,
            questions_to_ask=questions_to_ask,
            scheduled_time=scheduled_datetime,
            priority=priority,
            created_by=created_by,
            status="pending"
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # If scheduled, create the call and schedule it
        if scheduled_datetime:
            call = Call(
                contact_id=contact_id,
                call_type="task_delivery",
                status="scheduled",
                caller_name="Krishnaji's CTO office",
                custom_greeting=agent_script or f"Hello, this is a call regarding: {title}",
                is_scheduled=True,
                scheduled_time=scheduled_datetime
            )
            db.add(call)
            db.commit()
            db.refresh(call)

            # Link task to call
            task.assigned_call_id = call.id
            task.status = "scheduled"
            db.commit()

            # Schedule the call
            schedule_one_time_call(call.id, scheduled_datetime)

        return JSONResponse({
            "success": True,
            "task_id": task.id,
            "call_id": task.assigned_call_id if task.assigned_call_id else None,
            "message": f"Task assigned to {contact.name}" +
                      (f" and scheduled for {scheduled_datetime.isoformat()}" if scheduled_datetime else "")
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/api/tasks")
async def list_tasks(
    status: Optional[str] = None,
    contact_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all proactive tasks (Type 1)
    Filter by status and/or contact
    """
    from models import Task
    try:
        query = db.query(Task).join(Contact)

        if status:
            query = query.filter(Task.status == status)
        if contact_id:
            query = query.filter(Task.contact_id == contact_id)

        tasks = query.order_by(Task.created_at.desc()).limit(limit).all()

        return JSONResponse({
            "success": True,
            "tasks": [
                {
                    "id": task.id,
                    "contact_id": task.contact_id,
                    "contact_name": task.contact.name,
                    "contact_phone": task.contact.phone_number,
                    "title": task.title,
                    "description": task.description,
                    "task_type": task.task_type,
                    "status": task.status,
                    "priority": task.priority,
                    "scheduled_time": task.scheduled_time.isoformat() if task.scheduled_time else None,
                    "created_at": task.created_at.isoformat(),
                    "created_by": task.created_by,
                    "call_attempts": task.call_attempts,
                    "max_attempts": task.max_attempts,
                    "contact_response": task.contact_response,
                    "task_completed": task.task_completed
                }
                for task in tasks
            ],
            "count": len(tasks)
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/api/tasks/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get specific task details"""
    from models import Task
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return JSONResponse({
                "success": False,
                "error": "Task not found"
            }, status_code=404)

        import json
        return JSONResponse({
            "success": True,
            "task": {
                "id": task.id,
                "contact": {
                    "id": task.contact.id,
                    "name": task.contact.name,
                    "phone": task.contact.phone_number
                },
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type,
                "agent_script": task.agent_script,
                "questions_to_ask": json.loads(task.questions_to_ask) if task.questions_to_ask else [],
                "status": task.status,
                "priority": task.priority,
                "scheduled_time": task.scheduled_time.isoformat() if task.scheduled_time else None,
                "created_at": task.created_at.isoformat(),
                "created_by": task.created_by,
                "call_attempts": task.call_attempts,
                "max_attempts": task.max_attempts,
                "contact_response": task.contact_response,
                "response_sentiment": task.response_sentiment,
                "task_completed": task.task_completed,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "notes": task.notes
            }
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: int,
    status: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update task status or notes"""
    from models import Task
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return JSONResponse({
                "success": False,
                "error": "Task not found"
            }, status_code=404)

        if status:
            task.status = status
            if status == "completed":
                task.completed_at = datetime.utcnow()

        if notes:
            task.notes = notes

        db.commit()

        return JSONResponse({
            "success": True,
            "message": "Task updated successfully"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/api/tasks/{task_id}/call")
async def initiate_task_delivery_call(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Initiate a task delivery call immediately
    This properly sets up the call with task_delivery type BEFORE dispatching the agent
    """
    from models import Task
    try:
        # Get the task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return JSONResponse({
                "success": False,
                "error": "Task not found"
            }, status_code=404)

        # Get the contact
        contact = db.query(Contact).filter(Contact.id == task.contact_id).first()
        if not contact:
            return JSONResponse({
                "success": False,
                "error": "Contact not found"
            }, status_code=404)

        # Create call record with task_delivery type FIRST
        # NEW (DROP 8): Use contact's preferred language
        preferred_lang = contact.preferred_language or "en"

        call = Call(
            contact_id=contact.id,
            call_type="task_delivery",  # CRITICAL: Set BEFORE agent starts
            direction="outbound",
            status="queued",
            caller_name="Krishnaji's CTO office",
            language=preferred_lang  # NEW (DROP 8): Set language from contact
        )
        db.add(call)
        db.commit()
        db.refresh(call)

        # Link task to call
        task.assigned_call_id = call.id
        task.status = "in_progress"
        db.commit()

        # Now initiate the call using the helper function
        try:
            room_name = await initiate_livekit_call(
                db=db,
                call_id=call.id,
                phone_number=contact.phone_number,
                contact_name=contact.name,
                custom_greeting=None,  # Agent will generate from task
                caller_name="Krishnaji's CTO office",
                language=preferred_lang  # NEW (DROP 8): Pass language to agent
            )

            return JSONResponse({
                "success": True,
                "task_id": task.id,
                "call_id": call.id,
                "room_name": room_name,
                "message": f"Task delivery call initiated to {contact.name}"
            })

        except Exception as e:
            # Rollback task status if call fails
            task.status = "pending"
            task.assigned_call_id = None
            db.commit()
            raise e

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


