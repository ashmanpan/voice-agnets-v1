#!/usr/bin/env python3
"""
Test script for task delivery system
Creates a task and initiates a task-delivery call
"""
import os
from datetime import datetime
from sqlalchemy.orm import Session
from models import Contact, Task, Call
from database import SessionLocal
import requests

def test_task_delivery():
    db = SessionLocal()

    # Use US test number
    test_phone = "+12025551234"
    contact_name = "Test User"

    # Check if contact exists
    contact = db.query(Contact).filter(Contact.phone_number == test_phone).first()
    if not contact:
        contact = Contact(
            name=contact_name,
            phone_number=test_phone,
            contact_type="friend"
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        print(f"✅ Created test contact: {contact.name} (ID: {contact.id})")
    else:
        print(f"✅ Using existing contact: {contact.name} (ID: {contact.id})")

    # Create task
    task = Task(
        contact_id=contact.id,
        title="Effort Estimation Reminder",
        description="Need to complete effort estimation for Parental Control project tomorrow",
        task_type="reminder",
        agent_script="Hi, I'm calling to remind you about completing the effort estimation for the Parental Control project tomorrow. This is important for project planning.",
        questions_to_ask='["Will you be able to complete the effort estimation tomorrow?", "Do you need any additional information or resources?"]',
        priority="high",
        status="pending",
        created_by="CTO Office",
        collect_response=True
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    print(f"✅ Created task: {task.title} (ID: {task.id})")

    # Create call with task_delivery type
    room_name = f"task-{task.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    call = Call(
        contact_id=contact.id,
        call_type="task_delivery",  # IMPORTANT: This triggers task loading in agent
        direction="outbound",
        status="initiated",
        livekit_room_name=room_name
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    print(f"✅ Created call: {room_name} (ID: {call.id})")

    # Link task to call
    task.assigned_call_id = call.id
    task.status = "in_progress"
    db.commit()
    print(f"✅ Linked task to call and set status to in_progress")

    db.close()

    # Now initiate the call via LiveKit API
    try:
        # Use the call initiation endpoint
        response = requests.post(
            "http://app:8000/api/calls/livekit-call",
            data={
                "contact_id": contact.id,
                "name": contact.name,
                "phone": test_phone,
                "greeting": "Hi, I have an important reminder for you."
            }
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ CALL INITIATED SUCCESSFULLY!")
            print(f"   Room: {result.get('room_name')}")
            print(f"   Call ID: {result.get('call_id')}")
            print(f"   This call should use task-aware prompts!")
        else:
            print(f"\n❌ Call initiation failed: {response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   You can manually initiate the call from outside the container")

    print(f"\n📋 Task Delivery Test Summary:")
    print(f"   Contact: {contact.name} ({test_phone})")
    print(f"   Task ID: {task.id}")
    print(f"   Call ID: {call.id}")
    print(f"   Call Type: task_delivery")
    print(f"   Room: {room_name}")
    print(f"\nThe agent should:")
    print(f"  1. Load task from database")
    print(f"  2. Generate task-aware system prompt")
    print(f"  3. Deliver task message")
    print(f"  4. Ask the questions")
    print(f"  5. Collect responses")
    print(f"  6. Update task status on completion")

if __name__ == "__main__":
    test_task_delivery()
