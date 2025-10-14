#!/usr/bin/env python3
"""
Call Scheduler Examples
Demonstrates how to use the call scheduling API
"""
import requests
from datetime import datetime, timedelta

API_BASE = "http://localhost:8001"


def schedule_call_in_minutes(name, phone, minutes=5):
    """
    Schedule a call to happen in X minutes from now
    Useful for testing
    """
    scheduled_time = datetime.now() + timedelta(minutes=minutes)

    response = requests.post(f"{API_BASE}/api/calls/schedule", data={
        "name": name,
        "phone": phone,
        "call_type": "facility_test",
        "scheduled_time": scheduled_time.isoformat()
    })

    result = response.json()
    if result.get("success"):
        print(f"✓ Call scheduled for {name} in {minutes} minutes")
        print(f"  Call ID: {result['call_id']}")
        print(f"  Time: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"✗ Error: {result.get('error')}")

    return result


def schedule_call_at_time(name, phone, hour, minute):
    """
    Schedule a call for today at specific hour:minute
    Example: schedule_call_at_time("John", "+1234567890", 17, 0)  # 5:00 PM today
    """
    scheduled_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If time has passed today, schedule for tomorrow
    if scheduled_time < datetime.now():
        scheduled_time += timedelta(days=1)

    response = requests.post(f"{API_BASE}/api/calls/schedule", data={
        "name": name,
        "phone": phone,
        "call_type": "facility_test",
        "scheduled_time": scheduled_time.isoformat()
    })

    result = response.json()
    if result.get("success"):
        print(f"✓ Call scheduled for {name} at {hour:02d}:{minute:02d}")
        print(f"  Call ID: {result['call_id']}")
        print(f"  Date: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"✗ Error: {result.get('error')}")

    return result


def create_daily_call(name, phone, hour, minute):
    """
    Create a recurring call every day at specific time
    Example: create_daily_call("John", "+1234567890", 9, 0)  # Every day at 9:00 AM
    """
    time_str = f"{hour:02d}:{minute:02d}"

    response = requests.post(f"{API_BASE}/api/calls/recurring", data={
        "name": name,
        "phone": phone,
        "call_type": "facility_test",
        "recurrence_pattern": "daily",
        "recurrence_time": time_str
    })

    result = response.json()
    if result.get("success"):
        print(f"✓ Daily call created for {name} at {time_str}")
        print(f"  Call ID: {result['call_id']}")
    else:
        print(f"✗ Error: {result.get('error')}")

    return result


def create_weekly_call(name, phone, day, hour, minute):
    """
    Create a recurring call every week on specific day
    Example: create_weekly_call("John", "+1234567890", "sunday", 17, 0)  # Every Sunday at 5 PM
    """
    time_str = f"{hour:02d}:{minute:02d}"

    response = requests.post(f"{API_BASE}/api/calls/recurring", data={
        "name": name,
        "phone": phone,
        "call_type": "facility_test",
        "recurrence_pattern": "weekly",
        "recurrence_day": day.lower(),
        "recurrence_time": time_str
    })

    result = response.json()
    if result.get("success"):
        print(f"✓ Weekly call created for {name} every {day} at {time_str}")
        print(f"  Call ID: {result['call_id']}")
    else:
        print(f"✗ Error: {result.get('error')}")

    return result


def create_monthly_call(name, phone, hour, minute):
    """
    Create a recurring call on 1st of every month
    Example: create_monthly_call("John", "+1234567890", 10, 0)  # 1st of month at 10 AM
    """
    time_str = f"{hour:02d}:{minute:02d}"

    response = requests.post(f"{API_BASE}/api/calls/recurring", data={
        "name": name,
        "phone": phone,
        "call_type": "facility_test",
        "recurrence_pattern": "monthly",
        "recurrence_time": time_str
    })

    result = response.json()
    if result.get("success"):
        print(f"✓ Monthly call created for {name} on 1st at {time_str}")
        print(f"  Call ID: {result['call_id']}")
    else:
        print(f"✗ Error: {result.get('error')}")

    return result


def pause_call(call_id):
    """Pause a recurring call"""
    response = requests.post(f"{API_BASE}/api/calls/{call_id}/pause")
    result = response.json()

    if result.get("success"):
        print(f"✓ Call {call_id} paused")
    else:
        print(f"✗ Error: {result.get('error')}")

    return result


def resume_call(call_id):
    """Resume a paused recurring call"""
    response = requests.post(f"{API_BASE}/api/calls/{call_id}/resume")
    result = response.json()

    if result.get("success"):
        print(f"✓ Call {call_id} resumed")
    else:
        print(f"✗ Error: {result.get('error')}")

    return result


def cancel_call(call_id):
    """Cancel a scheduled or recurring call"""
    response = requests.post(f"{API_BASE}/api/calls/{call_id}/cancel")
    result = response.json()

    if result.get("success"):
        print(f"✓ Call {call_id} cancelled")
    else:
        print(f"✗ Error: {result.get('error')}")

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("Call Scheduler Examples")
    print("=" * 60)
    print()

    # Example contacts (replace with real numbers for testing)
    TEST_NAME = "Daniel Clark"
    TEST_PHONE = "+61421856756"

    print("Available functions:\n")

    print("1. schedule_call_in_minutes(name, phone, minutes=5)")
    print("   - Schedule a call in X minutes")
    print(f"   Example: schedule_call_in_minutes('{TEST_NAME}', '{TEST_PHONE}', 5)")
    print()

    print("2. schedule_call_at_time(name, phone, hour, minute)")
    print("   - Schedule a call for specific time today/tomorrow")
    print(f"   Example: schedule_call_at_time('{TEST_NAME}', '{TEST_PHONE}', 17, 0)")
    print()

    print("3. create_daily_call(name, phone, hour, minute)")
    print("   - Create daily recurring call")
    print(f"   Example: create_daily_call('{TEST_NAME}', '{TEST_PHONE}', 9, 0)")
    print()

    print("4. create_weekly_call(name, phone, day, hour, minute)")
    print("   - Create weekly recurring call")
    print(f"   Example: create_weekly_call('{TEST_NAME}', '{TEST_PHONE}', 'sunday', 17, 0)")
    print()

    print("5. create_monthly_call(name, phone, hour, minute)")
    print("   - Create monthly recurring call")
    print(f"   Example: create_monthly_call('{TEST_NAME}', '{TEST_PHONE}', 10, 0)")
    print()

    print("6. pause_call(call_id) / resume_call(call_id) / cancel_call(call_id)")
    print("   - Manage existing scheduled calls")
    print("   Example: pause_call(60)")
    print()

    print("=" * 60)
    print()
    print("Quick Test - Schedule a call in 2 minutes:")
    print("-" * 60)

    # Uncomment to actually schedule a test call
    # schedule_call_in_minutes(TEST_NAME, TEST_PHONE, 2)

    print()
    print("NOTE: Uncomment the last line in the script to run a test")
    print("      Or import this file and use the functions in your own script")
