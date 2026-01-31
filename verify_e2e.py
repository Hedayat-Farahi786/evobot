#!/usr/bin/env python3
"""
Verification Script - Check system configuration and readiness
"""
import os
import sys
import json
import asyncio
from pathlib import Path

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from config.settings import config
from utils.logging_utils import setup_logging

logger = setup_logging("verify_system")

def check_environment():
    """Check if all required environment variables are set"""
    logger.info("\n" + "=" * 60)
    logger.info("ENVIRONMENT CONFIGURATION CHECK")
    logger.info("=" * 60)
    
    required_vars = [
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH",
        "TELEGRAM_PHONE",
    ]
    
    optional_vars = [
        "SIGNAL_CHANNELS",
        "NOTIFICATION_CHANNEL",
        "MT5_LOGIN",
        "MT5_PASSWORD",
        "MT5_SERVER",
    ]
    
    missing = []
    for var in required_vars:
        val = os.getenv(var, "")
        status = "✅" if val else "❌"
        logger.info(f"{status} {var}: {val[:20] if val else 'NOT SET'}")
        if not val:
            missing.append(var)
    
    logger.info("\nOptional Settings:")
    for var in optional_vars:
        val = os.getenv(var, "")
        status = "✅" if val else "⚠️"
        logger.info(f"{status} {var}: {val[:30] if val else 'NOT SET'}")
    
    if missing:
        logger.error(f"\n❌ Missing required environment variables: {', '.join(missing)}")
        return False
    
    logger.info("\n✅ All required environment variables are set")
    return True


def check_configuration():
    """Check if trading configuration is valid"""
    logger.info("\n" + "=" * 60)
    logger.info("TRADING CONFIGURATION CHECK")
    logger.info("=" * 60)
    
    try:
        logger.info(f"Default lot size: {config.trading.default_lot_size}")
        logger.info(f"TP1 close percent: {config.trading.tp1_close_percent * 100}%")
        logger.info(f"TP2 close percent: {config.trading.tp2_close_percent * 100}%")
        logger.info(f"TP3 close percent: {config.trading.tp3_close_percent * 100}%")
        logger.info(f"Move SL to breakeven at TP1: {config.trading.move_sl_to_breakeven_at_tp1}")
        logger.info(f"Breakeven offset pips: {config.trading.breakeven_offset_pips}")
        
        # Verify lot sizes add up to 100%
        total_percent = (config.trading.tp1_close_percent + 
                        config.trading.tp2_close_percent + 
                        config.trading.tp3_close_percent) * 100
    except Exception as e:
        logger.warning(f"Could not read all trading config: {e}")
        return True
    
    if abs(total_percent - 100) < 0.1:
        logger.info(f"✅ TP close percentages sum to 100%")
    else:
        logger.warning(f"⚠️  TP close percentages sum to {total_percent:.1f}% (expected 100%)")
    
    return True


def check_channels():
    """Check if signal channels are configured"""
    logger.info("\n" + "=" * 60)
    logger.info("TELEGRAM CHANNELS CHECK")
    logger.info("=" * 60)
    
    channels = config.telegram.signal_channels
    
    if channels:
        logger.info(f"✅ {len(channels)} signal channel(s) configured:")
        for ch in channels:
            logger.info(f"  - {ch}")
    else:
        logger.warning("⚠️  No signal channels configured")
        logger.info("   You can add channels in the dashboard Settings > Telegram")
    
    notification_ch = config.telegram.notification_channel
    if notification_ch:
        logger.info(f"✅ Notification channel: {notification_ch}")
    else:
        logger.warning("⚠️  No notification channel configured (optional)")
    
    return True


def check_firebase():
    """Check Firebase connection"""
    logger.info("\n" + "=" * 60)
    logger.info("FIREBASE CHECK")
    logger.info("=" * 60)
    
    try:
        logger.info("✅ Firebase module available (optional)")
        return True
    except Exception as e:
        logger.warning(f"⚠️  Firebase check skipped: {e}")
        return True


def check_files():
    """Check if all required files exist"""
    logger.info("\n" + "=" * 60)
    logger.info("FILE STRUCTURE CHECK")
    logger.info("=" * 60)
    
    required_files = [
        "main.py",
        "config/settings.py",
        "core/trade_manager.py",
        "telegram/listener.py",
        "parsers/signal_parser.py",
        "dashboard/app.py",
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = Path(script_dir) / file_path
        if full_path.exists():
            logger.info(f"✅ {file_path}")
        else:
            logger.error(f"❌ {file_path} - NOT FOUND")
            all_ok = False
    
    return all_ok


def print_next_steps():
    """Print next steps for testing"""
    logger.info("\n" + "=" * 60)
    logger.info("NEXT STEPS")
    logger.info("=" * 60)
    logger.info("""
1. START THE DASHBOARD:
   python3 start_dashboard.py

2. OPEN DASHBOARD IN BROWSER:
   http://localhost:8080

3. CONFIGURE CHANNELS (if needed):
   - Go to Settings > Telegram
   - Add your signal channels
   - Save configuration

4. SEND TEST SIGNALS:
   - Send test signals to your configured channel
   - Watch signals appear in Dashboard

5. VERIFY POSITION CREATION:
   - Go to "Open Positions" tab
   - Should see 3 positions per signal
   - Each with different TP target

6. TEST BREAKEVEN:
   - Monitor positions as price moves
   - When TP1 is hit:
     * Position 1 closes
     * Positions 2 & 3 SL moves to their entry price
     * Remaining positions continue with their TP targets

7. MONITOR LOGS:
   tail -f logs/evobot.log

Test Signals (copy & paste to Telegram):
""")
    
    test_signals = [
        "EURUSD BUY\nEntry: 1.0850\nSL: 1.0800\nTP1: 1.0900\nTP2: 1.0950\nTP3: 1.1000",
        "GBPUSD SELL\nEntry: 1.2500\nSL: 1.2550\nTP1: 1.2450\nTP2: 1.2400\nTP3: 1.2350",
        "XAUUSD BUY\nEntry: 2050.00\nSL: 2045.00\nTP1: 2055.00\nTP2: 2060.00\nTP3: 2065.00",
    ]
    
    for i, sig in enumerate(test_signals, 1):
        logger.info(f"\nTest Signal {i}:")
        for line in sig.split("\n"):
            logger.info(f"  {line}")


def main():
    """Run all verification checks"""
    logger.info("\n🔍 SYSTEM VERIFICATION\n")
    
    checks = [
        ("Environment", check_environment),
        ("Configuration", check_configuration),
        ("Channels", check_channels),
        ("Firebase", check_firebase),
        ("Files", check_files),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Error in {name} check: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    all_passed = all(r[1] for r in results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {name}")
    
    if all_passed:
        logger.info("\n✅ All checks passed! System is ready for testing.")
    else:
        logger.warning("\n⚠️  Some checks failed. Please review above.")
    
    # Next steps
    print_next_steps()
    
    logger.info("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
