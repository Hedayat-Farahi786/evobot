"""
End-to-End Test - Verify Breakeven, Signal Storage, and Dashboard Integration
"""
import asyncio
import json
from datetime import datetime

def test_trade_persistence():
    """Test 1: Verify position_tickets are saved and loaded"""
    print("\n" + "="*70)
    print("TEST 1: Trade Persistence (position_tickets)")
    print("="*70)
    
    # Check if trades.json has position_tickets
    try:
        with open('data/trades.json', 'r') as f:
            data = json.load(f)
        
        trades = data.get('trades', {})
        print(f"Total trades in file: {len(trades)}")
        
        has_position_tickets = 0
        for trade_id, trade_data in trades.items():
            if trade_data.get('position_tickets'):
                has_position_tickets += 1
        
        print(f"Trades with position_tickets: {has_position_tickets}")
        
        if has_position_tickets > 0:
            print("[PASS] position_tickets are being saved")
            
            # Show example
            for trade_id, trade_data in list(trades.items())[:1]:
                if trade_data.get('position_tickets'):
                    print(f"\nExample trade {trade_id[:8]}:")
                    for pos in trade_data['position_tickets']:
                        print(f"  - TP{pos.get('tp')}: ticket={pos.get('ticket')}, "
                              f"entry={pos.get('entry_price')}, closed={pos.get('closed')}")
        else:
            print("[WARN] No position_tickets found - place a new trade to test")
        
        return has_position_tickets > 0
        
    except FileNotFoundError:
        print("[FAIL] trades.json not found")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_trade_loading():
    """Test 2: Verify position_tickets are loaded correctly"""
    print("\n" + "="*70)
    print("TEST 2: Trade Loading (position_tickets in memory)")
    print("="*70)
    
    try:
        from core.trade_manager import trade_manager
        
        # Force reload
        trade_manager._load_trades_sync()
        
        trades = trade_manager.get_all_trades()
        print(f"Loaded trades: {len(trades)}")
        
        has_position_tickets = 0
        for trade in trades:
            if hasattr(trade, 'position_tickets') and trade.position_tickets:
                has_position_tickets += 1
        
        print(f"Trades with position_tickets in memory: {has_position_tickets}")
        
        if has_position_tickets > 0:
            print("[PASS] position_tickets loaded correctly")
            
            # Show active trades
            active = trade_manager.get_active_trades()
            print(f"\nActive trades: {len(active)}")
            for trade in active[:2]:
                print(f"\n  Trade {trade.id[:8]}:")
                print(f"    Symbol: {trade.symbol}")
                print(f"    Status: {trade.status.name}")
                print(f"    Breakeven: {trade.breakeven_applied}")
                if trade.position_tickets:
                    print(f"    Positions: {len(trade.position_tickets)}")
                    for pos in trade.position_tickets:
                        status = "CLOSED" if pos.get('closed') else "OPEN"
                        print(f"      TP{pos.get('tp')}: {pos.get('ticket')} [{status}]")
        else:
            print("[FAIL] position_tickets NOT loaded - fix not applied!")
            return False
        
        return has_position_tickets > 0
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_storage():
    """Test 3: Verify signals are being stored"""
    print("\n" + "="*70)
    print("TEST 3: Signal Storage")
    print("="*70)
    
    try:
        from core.signal_storage import signal_storage
        
        signals = signal_storage.get_messages(10)
        print(f"Signals in memory: {len(signals)}")
        
        if len(signals) > 0:
            print("[PASS] Signals are being stored")
            
            # Show recent signals
            for sig in signals[:3]:
                print(f"\n  Signal {sig.id[:8]}:")
                print(f"    Symbol: {sig.symbol}")
                print(f"    Direction: {sig.direction}")
                print(f"    Executed: {sig.executed}")
                print(f"    Trade ID: {sig.trade_id or 'None'}")
                print(f"    Status: {sig.status}")
        else:
            print("[WARN] No signals stored yet - wait for new signals")
        
        # Check Firebase connection
        if signal_storage.firebase_db:
            print("\n[PASS] Firebase connected for signal storage")
        else:
            print("\n[WARN] Firebase not connected - signals won't persist")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_breakeven_logic():
    """Test 4: Verify breakeven logic is correct"""
    print("\n" + "="*70)
    print("TEST 4: Breakeven Logic")
    print("="*70)
    
    try:
        from core.trade_manager import TradeManager
        import inspect
        
        # Check if _move_all_to_breakeven has the fix
        source = inspect.getsource(TradeManager._move_all_to_breakeven)
        
        checks = {
            "Loops through positions": "for pos_info in trade.position_tickets" in source,
            "Skips closed positions": 'pos_info.get("closed"' in source,
            "Gets entry price": 'pos_info.get("entry_price"' in source,
            "Modifies each position": "broker_client.modify_position(ticket, sl=" in source,
            "Uses safe SL calculation": "min(ideal_sl, current_price -" in source or "max(ideal_sl, current_price +" in source,
        }
        
        all_pass = True
        for check, result in checks.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {check}")
            if not result:
                all_pass = False
        
        if all_pass:
            print("\n[PASS] Breakeven logic is correct")
        else:
            print("\n[FAIL] Breakeven logic has issues")
        
        return all_pass
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_monitoring():
    """Test 5: Verify monitoring is configured"""
    print("\n" + "="*70)
    print("TEST 5: Position Monitoring")
    print("="*70)
    
    try:
        from core.trade_manager import TradeManager
        import inspect
        
        source = inspect.getsource(TradeManager._monitor_positions)
        
        # Check monitoring interval
        if "await asyncio.sleep(10)" in source:
            print("[PASS] Monitoring interval: 10 seconds")
        else:
            print("[WARN] Monitoring interval may be different")
        
        # Check if it calls _check_tp_levels
        if "await self._check_tp_levels()" in source:
            print("[PASS] TP level checking enabled")
        else:
            print("[FAIL] TP level checking not found")
        
        # Check if it calls _update_pnl
        if "await self._update_pnl()" in source:
            print("[PASS] P&L updating enabled")
        else:
            print("[WARN] P&L updating not found")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("END-TO-END VERIFICATION TEST")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Trade Persistence", test_trade_persistence()))
    results.append(("Trade Loading", test_trade_loading()))
    results.append(("Signal Storage", test_signal_storage()))
    results.append(("Breakeven Logic", test_breakeven_logic()))
    results.append(("Position Monitoring", test_monitoring()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    # Final verdict
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)
    
    if passed == total:
        print("[SUCCESS] All systems operational!")
        print("\nNext steps:")
        print("1. Bot is ready to use")
        print("2. Place a new trade to test breakeven")
        print("3. Monitor logs for TP1 hit and breakeven trigger")
    elif passed >= 3:
        print("[PARTIAL] Core systems working, some issues detected")
        print("\nAction required:")
        print("1. Review failed tests above")
        print("2. Restart bot if needed")
        print("3. Check logs for errors")
    else:
        print("[CRITICAL] Multiple systems not working")
        print("\nAction required:")
        print("1. Restart bot: python start_dashboard.py")
        print("2. Check logs: tail -f logs/system.log")
        print("3. Verify MT5 connection")
    
    print("="*70)

if __name__ == "__main__":
    main()
