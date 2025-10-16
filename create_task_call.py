#!/usr/bin/env python3
"""
Quick script to create a task and call immediately
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
sys.path.append('app')
from models import Contact, Task, Call

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://voiceagent:voiceagent123@localhost:5432/voiceagent")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Contact details
contact_name = "Rishikesh Sawant"
contact_phone = "+919833105490"

# Check if contact exists
contact = db.query(Contact).filter(Contact.phone_number == contact_phone).first()
if not contact:
    # Create new contact
    contact = Contact(
        name=contact_name,
        phone_number=contact_phone,
        contact_type="friend"
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    print(f"✅ Created contact: {contact.name} (ID: {contact.id})")
else:
    print(f"✅ Found existing contact: {contact.name} (ID: {contact.id})")

# Create task
task = Task(
    contact_id=contact.id,
    title="Effort Estimation Required",
    description="Need to complete effort estimation tomorrow for Parental Control project",
    task_type="reminder",
    agent_script="Hi Rishikesh, this is a reminder that you need to complete the effort estimation for the Parental Control project tomorrow. Can you confirm you will be able to do this?",
    questions_to_ask='["Will you be able to complete the effort estimation tomorrow?", "Do you need any information or support for the estimation?"]',
    priority="high",
    status="pending",
    created_by="CTO Office",
    collect_response=True
)
db.add(task)
db.commit()
db.refresh(task)
print(f"✅ Created task: {task.title} (ID: {task.id})")

# Create call linked to task
call = Call(
    contact_id=contact.id,
    call_type="task_delivery",
    direction="outbound",
    status="scheduled",
    livekit_room_name=f"task-{task.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
)
db.add(call)
db.commit()
db.refresh(call)

# Link task to call
task.assigned_call_id = call.id
db.commit()

print(f"✅ Created call: {call.livekit_room_name} (ID: {call.id})")
print(f"✅ Linked task to call")

# Now trigger the call via API
import requests
try:
    response = requests.post(
        "http://localhost:8001/api/call-now",
        data={
            "contact_id": contact.id,
            "contact_name": contact.name,
            "greeting": f"Hi {contact.name}, I have an important reminder for you regarding the effort estimation task."
        }
    )
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Call initiated successfully!")
        print(f"   Room: {result.get('room_name')}")
        print(f"   Call ID: {result.get('call_id')}")
    else:
        print(f"❌ Call initiation failed: {response.text}")
except Exception as e:
    print(f"❌ Error initiating call: {e}")

db.close()
print("\n✅ Task assignment complete!")
print(f"\nTask Details:")
print(f"  Contact: {contact.name} ({contact.phone_number})")
print(f"  Task: {task.title}")
print(f"  Priority: {task.priority}")
print(f"  Call Type: task_delivery")
print(f"  Call ID: {call.id}")
