#!/usr/bin/env python3
"""
Example script showing how to make calls with custom parameters:
- Custom caller name
- Custom greeting
- Custom subject
"""
import requests

API_URL = "http://localhost:8001/api/calls/facility-test"

# Example 1: Default call (uses "Krishnaji's CTO office")
def call_default(name, phone):
    response = requests.post(API_URL, data={
        "name": name,
        "phone": phone
    })
    return response.json()

# Example 2: Call with custom caller name
def call_custom_caller(name, phone, caller_name):
    response = requests.post(API_URL, data={
        "name": name,
        "phone": phone,
        "caller_name": caller_name  # e.g., "ABC Company", "TechCorp Support Team"
    })
    return response.json()

# Example 3: Call with completely custom greeting
def call_custom_greeting(name, phone, custom_greeting):
    response = requests.post(API_URL, data={
        "name": name,
        "phone": phone,
        "custom_greeting": custom_greeting  # Completely override the greeting
    })
    return response.json()

# Example 4: Full customization
def call_full_custom(name, phone, caller_name, custom_subject):
    response = requests.post(API_URL, data={
        "name": name,
        "phone": phone,
        "caller_name": caller_name,
        "custom_subject": custom_subject
    })
    return response.json()


if __name__ == "__main__":
    print("Example Calls:\n")

    # Example 1: Default
    print("1. Default call:")
    print("   Greeting: 'Hello! This is an AI assistant calling from Krishnaji's CTO office. May I speak with {name}?'")
    print()

    # Example 2: Custom caller name
    print("2. Custom caller name:")
    print("   Call: call_custom_caller('John', '+1234567890', 'ABC Company Support Team')")
    print("   Greeting: 'Hello! This is an AI assistant calling from ABC Company Support Team. May I speak with John?'")
    print()

    # Example 3: Completely custom greeting
    print("3. Completely custom greeting:")
    print("   Call: call_custom_greeting('Jane', '+1234567890', 'Hi Jane! This is Sarah from XYZ Corp. Do you have a moment?')")
    print("   Greeting: 'Hi Jane! This is Sarah from XYZ Corp. Do you have a moment?'")
    print()

    # Example 4: Full customization
    print("4. Full customization:")
    print("   Call: call_full_custom('Mike', '+1234567890', 'Digital Marketing Agency', 'website feedback')")
    print("   Greeting: 'Hello! This is an AI assistant calling from Digital Marketing Agency. May I speak with Mike?'")
    print("   (Subject used in conversation context)")
    print()

    print("\nUsage:")
    print("  # Default call")
    print("  result = call_default('Senthil', '+61411314178')")
    print()
    print("  # Custom caller")
    print("  result = call_custom_caller('Senthil', '+61411314178', 'TechStartup Solutions')")
    print()
    print("  # Or use curl:")
    print("  curl -X POST http://localhost:8001/api/calls/facility-test \\")
    print("    -F 'name=Senthil' \\")
    print("    -F 'phone=+61411314178' \\")
    print("    -F 'caller_name=ABC Company'")
