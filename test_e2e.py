#!/usr/bin/env python3
"""
End-to-End Testing Script
Tests signal capture, position creation, and TP hit processing
"""
import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from config.settings import config
from utils.logging_utils import setup_logging
from parsers.signal_parser import signal_parser
from models.trade import Trade, TradeDirection, SignalType
from core.trade_manager import trade_manager
from broker import broker_client

logger = setup_logging("e2e_test")

# Test data
TEST_SIGNALS = [
    {
        "name": "EURUSD BUY",
        "message": """
🔔 NEW SIGNAL 🔔

Symbol: EURUSD
Direction: BUY
Entry: 1.0850
SL: 1.0800
TP1: 1.0900
TP2: 1.0950
TP3: 1.1000

Strong bullish setup ✅
"""
    },
    {
        "name": "GBPUSD SELL",
        "message": """
📊 SELL SIGNAL 📊

GBPUSD
Type: SELL
Entry: 1.2500
Stop Loss: 1.2550
TP 1: 1.2450
TP 2: 1.2400
TP 3: 1.2350

Reversal expected 🔴
"""
    },
    {
        "name": "XAUUSD BUY",
        "message": """
GOLD: BUY
Entry zone: 2050
SL: 2045
Target 1: 2055
Target 2: 2060
Target 3: 2065
"""
    }
]


async def test_signal_parsing():
    """Test if signals are parsed correctly"""
    logger.info("=" * 60)
    logger.info("TEST 1: Signal Parsing")
    logger.info("=" * 60)
    
    for test_sig in TEST_SIGNALS:
        logger.info(f"\n📝 Testing: {test_sig['name']}")
        signal = signal_parser.parse(test_sig['message'])
        
        if signal:
            logger.info(f"  ✅ Signal parsed successfully")
            logger.info(f"  - Symbol: {signal.symbol}")
            logger.info(f"  - Direction: {signal.direction}")
            logger.info(f"  - Entry: {signal.entry_min} - {signal.entry_max}")
            logger.info(f"  - SL: {signal.stop_loss}")
            logger.info(f"  - TP1: {signal.take_profit_1}")
            logger.info(f"  - TP2: {signal.take_profit_2}")
            logger.info(f"  - TP3: {signal.take_profit_3}")
            logger.info(f"  - Type: {signal.signal_type}")
        else:
            logger.error(f"  ❌ Failed to parse signal")
    
    logger.info("\n✅ Signal parsing test complete\n")


async def test_trade_creation():
    """Test if trades with 3 positions are created correctly"""
    logger.info("=" * 60)
    logger.info("TEST 2: Trade Creation (3 Positions per Signal)")
    logger.info("=" * 60)
    
    await trade_manager.start()
    
    for test_sig in TEST_SIGNALS:
        logger.info(f"\n📝 Creating trade for: {test_sig['name']}")
        signal = signal_parser.parse(test_sig['message'])
        
        if signal:
            # Process signal
            trade = await trade_manager.process_signal(signal)
            
            if trade:
                logger.info(f"  ✅ Trade created: {trade.id[:8]}")
                logger.info(f"  - Symbol: {trade.symbol}")
                logger.info(f"  - Status: {trade.status}")
                logger.info(f"  - Total positions: {len(trade.position_tickets)}")
                
                # Check each position
                for i, pos in enumerate(trade.position_tickets, 1):
                    logger.info(f"    Position {i}:")
                    logger.info(f"      - Ticket: {pos.get('ticket')}")
                    logger.info(f"      - TP: {pos.get('tp')}")
                    logger.info(f"      - Lot: {pos.get('lot')}")
                    logger.info(f"      - Entry Price: {pos.get('entry_price')}")
                    logger.info(f"      - TP Price: {pos.get('tp_price')}")
                
                # Verify we have 3 positions
                if len(trade.position_tickets) == 3:
                    logger.info(f"  ✅ Correct: 3 positions created for signal")
                else:
                    logger.warning(f"  ⚠️  Expected 3 positions, got {len(trade.position_tickets)}")
            else:
                logger.error(f"  ❌ Failed to create trade")
        else:
            logger.error(f"  ❌ Failed to parse signal")
    
    await trade_manager.stop()
    logger.info("\n✅ Trade creation test complete\n")


async def test_breakeven_logic():
    """Test if breakeven is applied correctly when TP1 is hit"""
    logger.info("=" * 60)
    logger.info("TEST 3: Breakeven Logic (TP1 Hit)")
    logger.info("=" * 60)
    
    await trade_manager.start()
    
    # Create a test trade
    signal = signal_parser.parse(TEST_SIGNALS[0]['message'])
    if signal:
        trade = await trade_manager.process_signal(signal)
        
        if trade:
            logger.info(f"✅ Trade created: {trade.id[:8]}")
            logger.info(f"  - Positions: {len(trade.position_tickets)}")
            
            # Store position info before breakeven
            logger.info(f"\n📍 Before TP1 hit:")
            for i, pos in enumerate(trade.position_tickets, 1):
                logger.info(f"  Position {i}:")
                logger.info(f"    - Entry Price: {pos.get('entry_price')}")
                logger.info(f"    - TP: TP{pos.get('tp')}")
            
            # Simulate TP1 hit
            logger.info(f"\n⏱️  Simulating TP1 hit...")
            await trade_manager._process_tp_hit(trade, tp_level=1)
            
            logger.info(f"\n📍 After TP1 hit:")
            logger.info(f"  - Trade status: {trade.status}")
            logger.info(f"  - Breakeven applied: {trade.breakeven_applied}")
            logger.info(f"  - Positions:")
            for i, pos in enumerate(trade.position_tickets, 1):
                closed = pos.get('closed', False)
                entry = pos.get('entry_price')
                logger.info(f"    Position {i}: Entry={entry}, Closed={closed}")
            
            if trade.breakeven_applied:
                logger.info(f"  ✅ Breakeven correctly applied")
            else:
                logger.warning(f"  ⚠️  Breakeven not applied")
    
    await trade_manager.stop()
    logger.info("\n✅ Breakeven logic test complete\n")


async def print_summary():
    """Print test summary"""
    logger.info("\n" + "=" * 60)
    logger.info("E2E TEST SUMMARY")
    logger.info("=" * 60)
    logger.info("""
Expected behavior:
1. ✅ All signals should parse correctly
2. ✅ Each signal should create a trade with 3 positions
3. ✅ Each position has unique TP target
4. ✅ When TP1 is hit, that position closes
5. ✅ Remaining 2 positions have SL moved to their entry prices
6. ✅ Positions 2 and 3 continue with their individual TP targets

Test Checklist:
[ ] Signals parsed from all channel formats
[ ] 3 positions created per signal
[ ] Entry prices stored for each position
[ ] TP1 hit closes correct position
[ ] Remaining positions move SL to own entry
[ ] No cross-signal interference
""")
    logger.info("=" * 60)


async def main():
    """Run all tests"""
    logger.info("\n🚀 STARTING E2E TESTS\n")
    
    try:
        # Test 1: Signal parsing
        await test_signal_parsing()
        
        # Test 2: Trade creation with 3 positions
        await test_trade_creation()
        
        # Test 3: Breakeven logic
        await test_breakeven_logic()
        
        # Summary
        await print_summary()
        
        logger.info("\n✅ ALL TESTS COMPLETED\n")
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
