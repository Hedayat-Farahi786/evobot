import requests
import os
from dotenv import load_dotenv

load_dotenv()

# We need a token. We can't easily get one from the browser here, 
# but we can try to look into how tokens are generated.
# Actually, the dashboard uses Telegram auth.
# Let's try to see if we can bypass auth for testing or if there's a stored token.

# Alternative: Test the backend logic directly by importing the router function.
import sys
sys.path.append(os.getcwd())

from dashboard.routers.channels import get_signal_channels_details
from fastapi import Request
import asyncio

async def test():
    # Mock request
    class MockRequest:
        def __init__(self):
            self.headers = {"Authorization": "Bearer test_token"}
            
    # We need a valid token though.
    # Let's just check the database directly via firebase_service.
    from core.firebase_service import firebase_service
    from core.firebase_settings import firebase_settings
    
    print(f"Signal Channels: {firebase_settings.signal_channels}")
    
    # Check Firebase path
    # users/{user_id}/channels_meta
    # But we don't know the user_id for the current session easily.
    
    # Let's just try to list all users and their metadata if we have access.
    if firebase_service.db_ref:
        users = firebase_service.db_ref.child('users').get()
        if users:
            for uid, data in users.items():
                print(f"User: {uid}")
                if 'channels_meta' in data:
                    print(f"  Metadata: {list(data['channels_meta'].keys())}")
                else:
                    print("  No metadata found.")
        else:
            print("No users found in Firebase.")
    else:
        print("Firebase not connected.")

if __name__ == "__main__":
    asyncio.run(test())
