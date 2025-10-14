"""
Add tasks table for proactive task assignments
Run this to create the tasks table for Type 1 actions
"""
from models import Base, engine, Task

def create_tasks_table():
    """Create tasks table in database"""
    print("Creating tasks table...")

    # Create the table
    Task.__table__.create(engine, checkfirst=True)

    print("✅ tasks table created successfully!")
    print("\nTable schema:")
    print("Type 1: PROACTIVE TASKS (YOU assign → Agent calls → Collects response)")
    print("=" * 70)
    print("Fields:")
    print("- title: Short task name")
    print("- description: Full task details")
    print("- task_type: reminder/confirmation/survey/follow_up")
    print("- agent_script: What agent says to contact")
    print("- questions_to_ask: Questions agent should ask (JSON)")
    print("- collect_response: Should agent record response?")
    print("- contact_response: What contact said")
    print("- response_sentiment: Sentiment of response")
    print("- task_completed: Did contact confirm?")
    print("- scheduled_time: When to make call")
    print("- call_attempts / max_attempts: Retry logic")
    print("\nStatus: pending → scheduled → in_progress → completed/failed")

if __name__ == "__main__":
    create_tasks_table()
