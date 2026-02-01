#!/usr/bin/env python3
"""
Reset and reload signal channels from .env file
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.firebase_service import firebase_service
from core.firebase_settings import firebase_settings

def reset_channels():
    """Reset channels from .env file"""
    print("=" * 60)
    print("Resetting Signal Channels from .env")
    print("=" * 60)
    
    # Get channels from .env
    channels_str = os.getenv("SIGNAL_CHANNELS", "")
    if not channels_str:
        print("No SIGNAL_CHANNELS found in .env file")
        return
    
    # Parse channels (strip whitespace)
    channels = [c.strip() for c in channels_str.split(",") if c.strip()]
    
    print(f"\nFound {len(channels)} channels in .env:")
    for i, ch in enumerate(channels, 1):
        print(f"   {i}. {ch}")
    
    # Initialize Firebase
    print("\nInitializing Firebase...")
    firebase_service.initialize()
    
    if not firebase_service.initialized:
        print("Firebase not initialized - updating local cache only")
        # Update local cache
        cache_file = "data/settings_cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                settings = json.load(f)
            
            settings['telegram']['signal_channels'] = channels
            
            with open(cache_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            print(f"Updated local cache: {cache_file}")
        return
    
    # Initialize Firebase settings
    firebase_settings.initialize(firebase_service.db_ref)
    
    # Update channels
    print("\nUpdating channels in Firebase...")
    firebase_settings.set("telegram", "signal_channels", channels)
    
    # Verify
    loaded_channels = firebase_settings.signal_channels
    print(f"\nSuccessfully updated! Loaded {len(loaded_channels)} channels:")
    for i, ch in enumerate(loaded_channels, 1):
        print(f"   {i}. {ch}")
    
    print("\n" + "=" * 60)
    print("Channels reset complete!")
    print("=" * 60)
    print("\nRestart the dashboard to see the changes:")
    print("  python start_dashboard.py")

if __name__ == "__main__":
    reset_channels()
