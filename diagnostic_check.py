"""
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
    print("\n1. Checking trades...")
    trade_manager._load_trades_sync()
    trades = trade_manager.get_all_trades()
    print(f"   Total trades: {len(trades)}")
    
    active = trade_manager.get_active_trades()
    print(f"   Active trades: {len(active)}")
    
    for trade in active[:3]:  # Show first 3
        print(f"\n   Trade {trade.id[:8]}:")
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
    print("\n2. Checking signals...")
    signals = signal_storage.get_messages(10)
    print(f"   Total signals: {len(signals)}")
    
    for sig in signals[:3]:
        print(f"\n   Signal {sig.id[:8]}:")
        print(f"     Symbol: {sig.symbol}")
        print(f"     Executed: {sig.executed}")
        print(f"     Trade ID: {sig.trade_id or 'None'}")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if not any(t.position_tickets for t in active):
        print("❌ CRITICAL: No position_tickets found in active trades!")
        print("   Solution: Restart bot to reload trades with fix")
    
    if len(signals) == 0:
        print("⚠️ No signals stored")
        print("   Check: Is Firebase connected?")
        print("   Check: Are signals being parsed?")
    
    print("\n✅ Diagnostic complete")

if __name__ == "__main__":
    asyncio.run(main())
