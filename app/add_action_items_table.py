"""
Add action_items table to database
Run this to create the new action items tracking table
"""
from models import Base, engine, ActionItem

def create_action_items_table():
    """Create action_items table in database"""
    print("Creating action_items table...")

    # Create the table
    ActionItem.__table__.create(engine, checkfirst=True)

    print("✅ action_items table created successfully!")
    print("\nTable schema:")
    print("- id: Primary key")
    print("- call_id: Link to calls table")
    print("- contact_id: Link to contacts table")
    print("- action_type: question/request/complaint/follow_up/task")
    print("- description: What needs to be done")
    print("- priority: high/medium/low")
    print("- status: pending/in_progress/completed/cancelled")
    print("- urgency_score: 0-100 for sorting")
    print("- created_at, due_date, completed_at: Timestamps")
    print("- notes: Additional context")

if __name__ == "__main__":
    create_action_items_table()
