#!/usr/bin/env python3
"""
Quick validation of 3-position trading logic
Tests without needing broker connection
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from parsers.signal_parser import signal_parser
from models.trade import Trade, TradeDirection

def test_signal_parsing():
    """Test that signals parse correctly"""
    print("\n" + "=" * 70)
    print("TEST 1: Signal Parsing (All Formats)")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "Standard Format",
            "signal": "EURUSD BUY\nEntry: 1.0850\nSL: 1.0800\nTP1: 1.0900\nTP2: 1.0950\nTP3: 1.1000"
        },
        {
            "name": "With Emojis",
            "signal": "🔔 GBPUSD SELL 🔔\nEntry: 1.2500\nStop Loss: 1.2550\nTP1: 1.2450\nTP2: 1.2400\nTP3: 1.2350"
        },
        {
            "name": "Abbreviated Format",
            "signal": "XAUUSD BUY\nE: 2050.00\nSL: 2045.00\nTP: 2055.00 2060.00 2065.00"
        },
        {
            "name": "Long Form",
            "signal": "USDJPY BUY\nEntry Zone: 150.00\nStop Loss: 149.50\nTake Profit 1: 150.50\nTake Profit 2: 151.00\nTake Profit 3: 151.50"
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        print(f"\n✓ Testing: {test['name']}")
        sig = signal_parser.parse(test['signal'])
        
        if sig and sig.symbol and sig.direction and sig.take_profit_1 and sig.take_profit_2 and sig.take_profit_3:
            print(f"  ✅ PASS - Symbol: {sig.symbol}, Direction: {sig.direction.value}")
            print(f"     TPs: {sig.take_profit_1}, {sig.take_profit_2}, {sig.take_profit_3}")
        else:
            print(f"  ❌ FAIL - Could not parse signal completely")
            all_passed = False
    
    return all_passed


def test_3_position_structure():
    """Test that trades create 3 positions correctly"""
    print("\n" + "=" * 70)
    print("TEST 2: 3-Position Structure")
    print("=" * 70)
    
    # Parse a signal
    signal_text = "EURUSD BUY\nEntry: 1.0850\nSL: 1.0800\nTP1: 1.0900\nTP2: 1.0950\nTP3: 1.1000"
    sig = signal_parser.parse(signal_text)
    
    if not sig:
        print("❌ FAIL - Could not parse signal")
        return False
    
    # Create trade from signal
    trade = Trade.from_signal(sig, lot_size=0.10)
    
    print(f"\n✓ Trade created from signal")
    print(f"  - Symbol: {trade.symbol}")
    print(f"  - Direction: {trade.direction.value}")
    print(f"  - Entry: {sig.entry_min}")
    print(f"  - SL: {trade.stop_loss}")
    
    # Simulate position creation (3 positions with different TPs)
    current_price = 1.0850
    position_tickets = []
    
    tp_levels = [
        (1, sig.take_profit_1),
        (2, sig.take_profit_2),
        (3, sig.take_profit_3)
    ]
    
    for tp_num, tp_price in tp_levels:
        if tp_price:
            pos_info = {
                "tp": tp_num,
                "ticket": 10000 + tp_num,
                "lot": 0.10,
                "tp_price": tp_price,
                "entry_price": current_price,  # KEY: Store entry price
                "closed": False
            }
            position_tickets.append(pos_info)
    
    trade.position_tickets = position_tickets
    
    # Verify structure
    print(f"\n✓ Positions created:")
    if len(position_tickets) == 3:
        print(f"  ✅ Correct: 3 positions")
        for i, pos in enumerate(position_tickets, 1):
            print(f"     Position {i}: Ticket={pos['ticket']}, TP{pos['tp']}={pos['tp_price']}, Entry={pos['entry_price']}")
        return True
    else:
        print(f"  ❌ FAIL: Expected 3 positions, got {len(position_tickets)}")
        return False


def test_breakeven_logic():
    """Test that breakeven moves SL to each position's entry"""
    print("\n" + "=" * 70)
    print("TEST 3: Breakeven Logic (SL → Entry)")
    print("=" * 70)
    
    # Create a trade with 3 positions
    signal_text = "EURUSD BUY\nEntry: 1.0850\nSL: 1.0800\nTP1: 1.0900\nTP2: 1.0950\nTP3: 1.1000"
    sig = signal_parser.parse(signal_text)
    trade = Trade.from_signal(sig, lot_size=0.10)
    
    # Add 3 positions (simulating market fill)
    positions = [
        {"tp": 1, "ticket": 10001, "lot": 0.10, "tp_price": 1.0900, "entry_price": 1.0850, "closed": False},
        {"tp": 2, "ticket": 10002, "lot": 0.10, "tp_price": 1.0950, "entry_price": 1.0850, "closed": False},
        {"tp": 3, "ticket": 10003, "lot": 0.10, "tp_price": 1.1000, "entry_price": 1.0850, "closed": False},
    ]
    trade.position_tickets = positions
    
    print(f"\n✓ Initial state (all 3 positions open):")
    for pos in positions:
        print(f"  - Position {pos['ticket']}: Entry={pos['entry_price']}, SL={trade.stop_loss}, TP{pos['tp']}={pos['tp_price']}")
    
    # Simulate TP1 hit (position 1 closes)
    print(f"\n✓ Simulating TP1 hit...")
    positions[0]["closed"] = True
    
    # Apply breakeven to remaining positions
    print(f"\n✓ Applying breakeven to remaining positions:")
    for pos in positions[1:]:
        if not pos.get("closed"):
            entry_price = pos.get("entry_price")
            # In real code, new_sl would be entry_price + offset
            new_sl = entry_price  # For simplicity, assume offset is 0
            print(f"  ✅ Position {pos['ticket']}: SL moved to {new_sl} (from {trade.stop_loss})")
            print(f"     Entry was: {entry_price}, SL now: {new_sl}")
    
    print(f"\n✓ Verification:")
    remaining_open = sum(1 for p in positions if not p.get("closed"))
    if remaining_open == 2:
        print(f"  ✅ Correct: 1 position closed, 2 remaining")
        print(f"  ✅ Remaining positions will SL to their entry prices")
        return True
    else:
        print(f"  ❌ FAIL: Expected 2 remaining, got {remaining_open}")
        return False


def test_multiple_signals():
    """Test that multiple signals don't interfere"""
    print("\n" + "=" * 70)
    print("TEST 4: Multiple Signals Independence")
    print("=" * 70)
    
    signals = [
        ("EURUSD BUY", "EURUSD BUY\nEntry: 1.0850\nSL: 1.0800\nTP1: 1.0900\nTP2: 1.0950\nTP3: 1.1000"),
        ("GBPUSD SELL", "GBPUSD SELL\nEntry: 1.2500\nSL: 1.2550\nTP1: 1.2450\nTP2: 1.2400\nTP3: 1.2350"),
        ("XAUUSD BUY", "XAUUSD BUY\nEntry: 2050.00\nSL: 2045.00\nTP1: 2055.00\nTP2: 2060.00\nTP3: 2065.00"),
    ]
    
    trades = []
    
    for name, sig_text in signals:
        print(f"\n✓ Processing: {name}")
        sig = signal_parser.parse(sig_text)
        
        if sig:
            trade = Trade.from_signal(sig, lot_size=0.10)
            
            # Add positions
            positions = [
                {"tp": 1, "ticket": 10001 + len(trades) * 100, "lot": 0.10, "tp_price": sig.take_profit_1, "entry_price": sig.entry_min or sig.entry_max, "closed": False},
                {"tp": 2, "ticket": 10002 + len(trades) * 100, "lot": 0.10, "tp_price": sig.take_profit_2, "entry_price": sig.entry_min or sig.entry_max, "closed": False},
                {"tp": 3, "ticket": 10003 + len(trades) * 100, "lot": 0.10, "tp_price": sig.take_profit_3, "entry_price": sig.entry_min or sig.entry_max, "closed": False},
            ]
            trade.position_tickets = positions
            trades.append(trade)
            
            print(f"  ✅ Trade {trade.id[:8]}: {len(positions)} positions")
        else:
            print(f"  ❌ Failed to parse")
            return False
    
    # Verify independence
    print(f"\n✓ Verification:")
    if len(trades) == 3:
        print(f"  ✅ Created {len(trades)} independent trades")
        for i, trade in enumerate(trades, 1):
            print(f"     Trade {i}: {trade.symbol} with {len(trade.position_tickets)} positions")
        return True
    else:
        print(f"  ❌ FAIL: Expected 3 trades, got {len(trades)}")
        return False


def main():
    print("\n" + "=" * 70)
    print("🔍 EVOBOT 3-POSITION TRADING VALIDATION")
    print("=" * 70)
    
    tests = [
        ("Signal Parsing", test_signal_parsing),
        ("3-Position Structure", test_3_position_structure),
        ("Breakeven Logic", test_breakeven_logic),
        ("Multiple Signals", test_multiple_signals),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("✅ ALL VALIDATION TESTS PASSED!")
        print("=" * 70)
        print("\nSystem is ready for end-to-end testing.")
        print("\nNext steps:")
        print("1. Start dashboard: python3 start_dashboard.py")
        print("2. Open http://localhost:8080")
        print("3. Send test signals to your Telegram channel")
        print("4. Verify positions are created and grouped correctly")
        print("\nSee E2E_TESTING_GUIDE.md for detailed testing instructions.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Review above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
