#!/usr/bin/env python3
"""
Interactive script to authenticate Telegram session.
Run this once to set up the session, then the bot can run non-interactively.
"""
import asyncio
from telethon import TelegramClient
from config.settings import config

async def authenticate():
    print("=" * 50)
    print("Telegram Authentication Setup")
    print("=" * 50)
    print(f"\nSession name: {config.telegram.session_name}")
    print(f"Phone number: {config.telegram.phone_number}")
    print("\nThis will send a verification code to your Telegram app.")
    print("You'll need to enter the code when prompted.\n")
    
    client = TelegramClient(
        config.telegram.session_name,
        config.telegram.api_id,
        config.telegram.api_hash
    )
    
    await client.start(phone=config.telegram.phone_number)
    
    me = await client.get_me()
    print(f"\n✅ Successfully authenticated as: {me.first_name} (@{me.username})")
    print(f"Session saved to: {config.telegram.session_name}.session")
    print("\nYou can now run the bot with: python3 main.py")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(authenticate())
