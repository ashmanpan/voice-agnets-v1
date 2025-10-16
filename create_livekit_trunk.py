#!/usr/bin/env python3
"""
Create LiveKit SIP Trunk for Twilio Integration
"""
import asyncio
import os
from dotenv import load_dotenv
from livekit.api import LiveKitAPI
from livekit.protocol import sip as proto_sip

# Load environment variables
load_dotenv()

async def create_outbound_trunk():
    """Create an outbound SIP trunk in LiveKit for Twilio"""

    # Initialize LiveKit API
    lk_api = LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    try:
        # Create outbound SIP trunk for Twilio
        trunk_info = proto_sip.SIPOutboundTrunkInfo(
            name="Twilio Outbound Trunk",
            address="sip.twilio.com",
            numbers=["+61340537198", "+17407933007"],
            # Twilio doesn't require auth credentials for outbound
        )

        trunk = await lk_api.sip.create_sip_outbound_trunk(
            proto_sip.CreateSIPOutboundTrunkRequest(trunk=trunk_info)
        )

        print("✅ Outbound SIP Trunk Created Successfully!")
        print(f"   Trunk ID: {trunk.sip_trunk_id}")
        print(f"   Name: {trunk.name}")
        print(f"   Address: {trunk.address}")
        print(f"   Numbers: {trunk.numbers}")
        print()
        print("📝 Next steps:")
        print("   1. Update Twilio SIP trunk origination to: sip:voice-agents-aw8yrvjs.sip.livekit.cloud")
        print(f"   2. Update .env with: LIVEKIT_SIP_TRUNK_ID={trunk.sip_trunk_id}")
        print("   3. Test the call!")

        return trunk.sip_trunk_id

    except Exception as e:
        print(f"❌ Error creating trunk: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   - Check that your LiveKit API key has SIP permissions")
        print("   - Verify your LiveKit Cloud account has telephony enabled")
        print("   - Try creating the trunk via LiveKit Cloud dashboard instead")
        return None

async def create_inbound_trunk():
    """Create an inbound SIP trunk in LiveKit for Twilio"""

    # Initialize LiveKit API
    lk_api = LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    try:
        # Create inbound SIP trunk
        trunk_info = proto_sip.SIPInboundTrunkInfo(
            name="Twilio Inbound Trunk",
            numbers=["+61340537198", "+17407933007"],
        )

        trunk = await lk_api.sip.create_sip_inbound_trunk(
            proto_sip.CreateSIPInboundTrunkRequest(trunk=trunk_info)
        )

        print("✅ Inbound SIP Trunk Created Successfully!")
        print(f"   Trunk ID: {trunk.sip_trunk_id}")
        print(f"   Name: {trunk.name}")
        print(f"   Numbers: {trunk.numbers}")

        return trunk.sip_trunk_id

    except Exception as e:
        print(f"❌ Error creating inbound trunk: {e}")
        return None

async def create_dispatch_rule(trunk_id):
    """Create a dispatch rule to route incoming calls to agent"""

    lk_api = LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    try:
        # Create dispatch rule
        rule_info = proto_sip.SIPDispatchRuleIndividual(
            room_prefix="call-"
        )

        rule = await lk_api.sip.create_sip_dispatch_rule(
            proto_sip.CreateSIPDispatchRuleRequest(
                name="Voice Agent Dispatch",
                trunk_ids=[trunk_id],
                rule=rule_info
            )
        )

        print("✅ Dispatch Rule Created!")
        print(f"   Rule ID: {rule.sip_dispatch_rule_id}")
        print(f"   Agent: voice-assistant")

        return rule.sip_dispatch_rule_id

    except Exception as e:
        print(f"❌ Error creating dispatch rule: {e}")
        return None

async def list_trunks():
    """List all existing SIP trunks"""

    lk_api = LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    try:
        # List outbound trunks
        outbound = await lk_api.sip.list_sip_outbound_trunk(proto_sip.ListSIPOutboundTrunkRequest())
        print("📋 Existing Outbound Trunks:")
        if outbound.items:
            for trunk in outbound.items:
                print(f"   - {trunk.name} (ID: {trunk.sip_trunk_id})")
        else:
            print("   (none)")

        # List inbound trunks
        inbound = await lk_api.sip.list_sip_inbound_trunk(proto_sip.ListSIPInboundTrunkRequest())
        print("\n📋 Existing Inbound Trunks:")
        if inbound.items:
            for trunk in inbound.items:
                print(f"   - {trunk.name} (ID: {trunk.sip_trunk_id})")
        else:
            print("   (none)")

    except Exception as e:
        print(f"❌ Error listing trunks: {e}")

if __name__ == "__main__":
    import sys

    print("=" * 80)
    print("LiveKit SIP Trunk Setup")
    print("=" * 80)
    print()

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_trunks())
    elif len(sys.argv) > 1 and sys.argv[1] == "inbound":
        asyncio.run(create_inbound_trunk())
    else:
        # Create outbound trunk by default
        trunk_id = asyncio.run(create_outbound_trunk())
        if trunk_id:
            print()
            print("=" * 80)
