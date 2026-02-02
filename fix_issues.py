"""
Fix script to ensure breakeven and signal storage work properly
"""
import json
import os

def fix_trade_manager():
    """Add position_tickets loading to trade_manager.py"""
    file_path = "core/trade_manager.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Add position_tickets loading in both _load_trades methods
    old_pattern = 'trade.position_ticket = tdata.get("position_ticket")\n                trade.status = TradeStatus'
    new_pattern = 'trade.position_ticket = tdata.get("position_ticket")\n                trade.position_tickets = tdata.get("position_tickets", [])  # Load position_tickets\n                trade.status = TradeStatus'
    
    if old_pattern in content and 'trade.position_tickets = tdata.get("position_tickets"' not in content:
        content = content.replace(old_pattern, new_pattern)
        print("[OK] Added position_tickets loading")
    else:
        print("[WARN] position_tickets loading already present or pattern not found")
    
    # Fix 2: Ensure monitoring interval is reasonable
    if 'await asyncio.sleep(10)  # Check every 10 seconds' in content:
        print("[OK] Monitoring interval is 10 seconds (good)")
    else:
        print("[WARN] Check monitoring interval")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] Fixed {file_path}")

def check_signal_storage():
    """Verify signal storage is being used"""
    print("\n" + "="*60)
    print("Checking signal storage integration...")
    print("="*60)
    
    # Check if signals are being stored in telegram listener
    listener_path = "telegram/listener.py"
    with open(listener_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'signal_storage.add_message' in content:
        print("[OK] Signals are being stored in telegram listener")
    else:
        print("[FAIL] Signals NOT being stored!")
    
    if 'signal_storage.link_trade' in content:
        print("[OK] Signals are being linked to trades")
    else:
        print("[WARN] Signal-trade linking may be missing")

def create_diagnostic_script():
    """Create a script to diagnose issues"""
    script = '''"""
Diagnostic script to check breakeven and signal storage
"""
import asyncio
import json
from core.trade_manager import trade_manager
from core.signal_storage import signal_storage

async def main():
    print("="*60)
    print("DIAGNOSTIC CHECK")
    print("="*60)
    
    # Check trades
    print("\\n1. Checking trades...")
    trade_manager._load_trades_sync()
    trades = trade_manager.get_all_trades()
    print(f"   Total trades: {len(trades)}")
    
    active = trade_manager.get_active_trades()
    print(f"   Active trades: {len(active)}")
    
    for trade in active[:3]:  # Show first 3
        print(f"\\n   Trade {trade.id[:8]}:")
        print(f"     Symbol: {trade.symbol}")
        print(f"     Status: {trade.status.name}")
        print(f"     Breakeven applied: {trade.breakeven_applied}")
        if trade.position_tickets:
            print(f"     Positions: {len(trade.position_tickets)}")
            for pos in trade.position_tickets:
                status = "CLOSED" if pos.get("closed") else "OPEN"
                print(f"       - TP{pos.get('tp')}: {pos.get('ticket')} [{status}]")
        else:
            print(f"     ⚠️ NO position_tickets found!")
    
    # Check signals
    print("\\n2. Checking signals...")
    signals = signal_storage.get_messages(10)
    print(f"   Total signals: {len(signals)}")
    
    for sig in signals[:3]:
        print(f"\\n   Signal {sig.id[:8]}:")
        print(f"     Symbol: {sig.symbol}")
        print(f"     Executed: {sig.executed}")
        print(f"     Trade ID: {sig.trade_id or 'None'}")
    
    print("\\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if not any(t.position_tickets for t in active):
        print("❌ CRITICAL: No position_tickets found in active trades!")
        print("   Solution: Restart bot to reload trades with fix")
    
    if len(signals) == 0:
        print("⚠️ No signals stored")
        print("   Check: Is Firebase connected?")
        print("   Check: Are signals being parsed?")
    
    print("\\n✅ Diagnostic complete")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open('diagnostic_check.py', 'w', encoding='utf-8') as f:
        f.write(script)
    
    print("\n[OK] Created diagnostic_check.py")
    print("   Run: python diagnostic_check.py")

if __name__ == "__main__":
    print("="*60)
    print("FIXING BREAKEVEN AND SIGNAL STORAGE ISSUES")
    print("="*60)
    
    fix_trade_manager()
    check_signal_storage()
    create_diagnostic_script()
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Restart the bot to apply fixes")
    print("2. Run: python diagnostic_check.py")
    print("3. Check logs for breakeven events")
    print("4. Verify signals appear in dashboard")
    print("="*60)
