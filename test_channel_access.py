#!/usr/bin/env python3
"""
Test if bot can access the channel and read messages
"""
import asyncio
import sys
sys.path.insert(0, '/home/ubuntu/personal/evobot')

from telethon import TelegramClient
from config.settings import config

async def test_channel():
    client = TelegramClient(
        config.telegram.session_name,
        config.telegram.api_id,
        config.telegram.api_hash
    )
    
    await client.start(phone=config.telegram.phone_number)
    
    print("✅ Connected to Telegram")
    print(f"Testing channel: {config.telegram.signal_channels[0]}")
    
    try:
        # Try to get the channel entity
        channel_id = int(config.telegram.signal_channels[0])
        entity = await client.get_entity(channel_id)
        print(f"✅ Channel found: {getattr(entity, 'title', 'Unknown')}")
        
        # Try to get recent messages
        messages = await client.get_messages(channel_id, limit=5)
        print(f"✅ Can read messages: {len(messages)} messages found")
        
        if messages:
            print("\n📨 Recent messages:")
            for msg in messages[:3]:
                text = msg.text or msg.raw_text or "(no text)"
                print(f"  - {text[:50]}...")
        else:
            print("⚠️  No messages found in channel")
        
        print("\n✅ Bot can access the channel!")
        print("If you don't see your test message above, the bot might not be receiving new messages.")
        
    except Exception as e:
        print(f"❌ Error accessing channel: {e}")
        print("\nPossible issues:")
        print("1. Bot is not a member of the channel")
        print("2. Channel ID is incorrect")
        print("3. Channel is private and bot doesn't have access")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_channel())
