"""Reactive action-item (Type 2) endpoints."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models import get_db, Contact, ActionItem

router = APIRouter()


@router.get("/api/actions")
async def list_actions(
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    contact_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all reactive action items (Type 2)
    These are extracted from call conversations
    """
    try:
        query = db.query(ActionItem).join(Contact)

        if status:
            query = query.filter(ActionItem.status == status)
        if action_type:
            query = query.filter(ActionItem.action_type == action_type)
        if contact_id:
            query = query.filter(ActionItem.contact_id == contact_id)

        actions = query.order_by(
            ActionItem.urgency_score.desc(),
            ActionItem.created_at.desc()
        ).limit(limit).all()

        return JSONResponse({
            "success": True,
            "actions": [
                {
                    "id": action.id,
                    "call_id": action.call_id,
                    "contact_id": action.contact_id,
                    "contact_name": action.contact.name,
                    "contact_phone": action.contact.phone_number,
                    "action_type": action.action_type,
                    "description": action.description,
                    "priority": action.priority,
                    "status": action.status,
                    "urgency_score": action.urgency_score,
                    "assigned_to": action.assigned_to,
                    "created_at": action.created_at.isoformat(),
                    "due_date": action.due_date.isoformat() if action.due_date else None,
                    "source_text": action.source_text
                }
                for action in actions
            ],
            "count": len(actions)
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/api/actions/{action_id}")
async def get_action(action_id: int, db: Session = Depends(get_db)):
    """Get specific action item details"""
    try:
        action = db.query(ActionItem).filter(ActionItem.id == action_id).first()
        if not action:
            return JSONResponse({
                "success": False,
                "error": "Action not found"
            }, status_code=404)

        return JSONResponse({
            "success": True,
            "action": {
                "id": action.id,
                "call_id": action.call_id,
                "contact": {
                    "id": action.contact.id,
                    "name": action.contact.name,
                    "phone": action.contact.phone_number
                },
                "action_type": action.action_type,
                "description": action.description,
                "priority": action.priority,
                "status": action.status,
                "urgency_score": action.urgency_score,
                "assigned_to": action.assigned_to,
                "created_at": action.created_at.isoformat(),
                "due_date": action.due_date.isoformat() if action.due_date else None,
                "completed_at": action.completed_at.isoformat() if action.completed_at else None,
                "notes": action.notes,
                "source_text": action.source_text
            }
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.patch("/api/actions/{action_id}")
async def update_action(
    action_id: int,
    status: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    assigned_to: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update action item status, notes, or assignment"""
    try:
        action = db.query(ActionItem).filter(ActionItem.id == action_id).first()
        if not action:
            return JSONResponse({
                "success": False,
                "error": "Action not found"
            }, status_code=404)

        if status:
            action.status = status
            if status == "completed":
                action.completed_at = datetime.utcnow()

        if notes:
            action.notes = notes

        if assigned_to:
            action.assigned_to = assigned_to

        db.commit()

        return JSONResponse({
            "success": True,
            "message": "Action updated successfully"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
