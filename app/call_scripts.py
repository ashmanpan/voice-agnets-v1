"""
Call script templates for different use cases
"""

PERSONAL_MESSAGE_SCRIPT = {
    "call_type": "personal_message",
    "voice": "en-US-Neural2-F",
    "language": "en",
    "steps": [
        {
            "id": "greeting",
            "agent_says": "Hi, may I speak with {contact_name}?",
            "wait_for_response": True,
            "max_wait_seconds": 10,
            "record_response": True
        },
        {
            "id": "deliver_message",
            "agent_says": "Hi! My name is SOS and I want to give you an update: {custom_message}",
            "wait_for_response": False
        },
        {
            "id": "ask_for_response",
            "agent_says": "Do you have any questions or comments?",
            "wait_for_response": True,
            "max_wait_seconds": 30,
            "record_response": True
        },
        {
            "id": "closing",
            "agent_says": "Thank you! I've recorded your response. Have a great day!",
            "wait_for_response": False
        },
        {
            "id": "end_call",
            "action": "hangup"
        }
    ]
}

FACILITY_TEST_SCRIPT = {
    "call_type": "facility_test",
    "voice": "en-US-Neural2-F",
    "language": "en",
    "use_ai_conversation": True,  # Enable dynamic AI conversation
    "conversation_system_prompt": "You are a friendly AI assistant making a test call. Have a natural conversation with the person. Ask them how they are, discuss the purpose of the call (testing the phone system), and engage in friendly small talk. Keep responses concise (1-2 sentences). After 4-5 exchanges, politely end the conversation.",
    "max_conversation_turns": 8,  # Maximum back-and-forth exchanges
    "steps": [
        {
            "id": "greeting",
            "agent_says": "Hello! This is an AI assistant calling from {caller_name}. May I speak with {contact_name}?",
            "wait_for_response": True,
            "max_wait_seconds": 10,
            "record_response": True,
            "use_ai": True,  # Use AI to respond to greeting response
            "next_step": "ai_conversation"
        },
        {
            "id": "ai_conversation",
            "use_ai": True,  # This step uses dynamic AI responses
            "wait_for_response": True,
            "max_wait_seconds": 20,
            "record_response": True,
            "repeat_until_turns": 8,  # Keep conversing for up to 8 turns
            "next_step": "closing"
        },
        {
            "id": "closing",
            "agent_says": "Thank you so much for chatting with me! This test call was successful. Have a wonderful day!",
            "wait_for_response": False,
            "action": "hangup"
        }
    ]
}


def get_script(call_type: str):
    """Get call script by type"""
    if call_type == "personal_message":
        return PERSONAL_MESSAGE_SCRIPT
    elif call_type == "facility_test":
        return FACILITY_TEST_SCRIPT
    else:
        raise ValueError(f"Unknown call type: {call_type}")


def format_script_text(text: str, **kwargs):
    """Format script text with provided variables"""
    return text.format(**kwargs)
