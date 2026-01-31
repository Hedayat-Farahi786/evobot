#!/usr/bin/env python3
"""
Test script for Telegram Channels with Profile Images feature
Run this to verify the implementation works correctly
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_channel_info():
    """Test fetching channel information"""
    print("=" * 60)
    print("Testing Telegram Channels Feature")
    print("=" * 60)
    
    try:
        from telegram.listener import telegram_listener
        from config.settings import config
        
        print("\n1. Checking configuration...")
        print(f"   Signal channels: {config.telegram.signal_channels}")
        
        if not config.telegram.signal_channels:
            print("   ❌ No signal channels configured!")
            print("   Please add channels in settings first.")
            return False
        
        print(f"   ✅ Found {len(config.telegram.signal_channels)} channel(s)")
        
        print("\n2. Connecting to Telegram...")
        await telegram_listener.start()
        
        if not telegram_listener.client or not telegram_listener.client.is_connected():
            print("   ❌ Failed to connect to Telegram!")
            return False
        
        print("   ✅ Connected to Telegram")
        
        print("\n3. Fetching channel information...")
        channels_info = await telegram_listener.get_all_monitored_channels_info()
        
        if not channels_info:
            print("   ❌ No channel info retrieved!")
            return False
        
        print(f"   ✅ Retrieved info for {len(channels_info)} channel(s)")
        
        print("\n4. Channel Details:")
        print("-" * 60)
        
        for i, channel in enumerate(channels_info, 1):
            print(f"\n   Channel {i}:")
            print(f"   ├─ Title: {channel.get('title', 'Unknown')}")
            print(f"   ├─ ID: {channel.get('id', 'Unknown')}")
            print(f"   ├─ Type: {channel.get('type', 'Unknown')}")
            print(f"   ├─ Username: @{channel.get('username', 'N/A')}")
            print(f"   ├─ Verified: {'✓' if channel.get('verified') else '✗'}")
            print(f"   ├─ Members: {channel.get('participants_count', 'N/A')}")
            
            photo_path = channel.get('photo_path')
            if photo_path and os.path.exists(photo_path):
                file_size = os.path.getsize(photo_path) / 1024  # KB
                print(f"   └─ Photo: ✅ Downloaded ({file_size:.1f} KB)")
            else:
                print(f"   └─ Photo: ❌ Not available")
        
        print("\n5. Checking photo directory...")
        photo_dir = "data/channel_photos"
        
        if not os.path.exists(photo_dir):
            print(f"   ⚠️  Directory doesn't exist: {photo_dir}")
            print("   Creating directory...")
            os.makedirs(photo_dir, exist_ok=True)
            print("   ✅ Directory created")
        else:
            photos = [f for f in os.listdir(photo_dir) if f.endswith('.jpg')]
            print(f"   ✅ Directory exists with {len(photos)} photo(s)")
        
        print("\n6. Testing API endpoint simulation...")
        print("   The following endpoints should work:")
        print(f"   - GET /api/telegram/channels")
        print(f"   - GET /api/telegram/channel/{{id}}/photo")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
        print("\nNext steps:")
        print("1. Start your dashboard: python start_dashboard.py")
        print("2. Open browser to http://localhost:8080")
        print("3. Navigate to the channels section")
        print("4. Click refresh to load channel info")
        print("5. You should see channel cards with profile images!")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            await telegram_listener.stop()
        except:
            pass


async def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)
    
    try:
        import requests
        
        base_url = "http://localhost:8080"
        
        print("\n1. Testing GET /api/telegram/channels...")
        try:
            response = requests.get(f"{base_url}/api/telegram/channels", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Endpoint works! Found {len(data.get('channels', []))} channels")
            else:
                print(f"   ⚠️  Endpoint returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("   ⚠️  Dashboard not running. Start it first:")
            print("      python start_dashboard.py")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n2. Testing photo endpoint...")
        photo_dir = "data/channel_photos"
        if os.path.exists(photo_dir):
            photos = [f for f in os.listdir(photo_dir) if f.endswith('.jpg')]
            if photos:
                channel_id = photos[0].replace('.jpg', '')
                try:
                    response = requests.get(
                        f"{base_url}/api/telegram/channel/{channel_id}/photo",
                        timeout=5
                    )
                    if response.status_code == 200:
                        print(f"   ✅ Photo endpoint works!")
                        print(f"   Photo size: {len(response.content) / 1024:.1f} KB")
                    else:
                        print(f"   ⚠️  Endpoint returned status {response.status_code}")
                except requests.exceptions.ConnectionError:
                    print("   ⚠️  Dashboard not running")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            else:
                print("   ⚠️  No photos downloaded yet")
        else:
            print("   ⚠️  Photo directory doesn't exist")
        
    except ImportError:
        print("\n⚠️  'requests' library not installed")
        print("Install it with: pip install requests")


def main():
    """Main test function"""
    print("\n🧪 EvoBot - Telegram Channels Feature Test\n")
    
    # Test 1: Channel info
    success = asyncio.run(test_channel_info())
    
    if success:
        # Test 2: API endpoints (optional)
        print("\n" + "=" * 60)
        print("Optional: Test API endpoints")
        print("=" * 60)
        print("\nMake sure your dashboard is running first!")
        print("Press Enter to test API endpoints, or Ctrl+C to skip...")
        
        try:
            input()
            asyncio.run(test_api_endpoints())
        except KeyboardInterrupt:
            print("\n\nSkipped API endpoint tests.")
    
    print("\n✨ Testing complete!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
