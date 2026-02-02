"""
Test concurrent trades logic - Ensure multiple signals are tracked independently
"""
import asyncio
from models.trade import Trade, TradeDirection, TradeStatus
from core.trade_manager import TradeManager, trade_manager
from config.settings import config

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

async def test_concurrent_trades():
    print_section("TEST: Concurrent Trades Independence")
    
    # 1. Setup two distinct trades
    trade1 = Trade()
    trade1.id = "trade_A"
    trade1.symbol = "EURUSD"
    trade1.direction = TradeDirection.BUY
    trade1.status = TradeStatus.ACTIVE
    trade1.position_tickets = [
        {"tp": 1, "ticket": "A1", "closed": False, "tp_price": 1.1020, "entry_price": 1.1000},
        {"tp": 2, "ticket": "A2", "closed": False, "tp_price": 1.1040, "entry_price": 1.1000}
    ]
    
    trade2 = Trade()
    trade2.id = "trade_B" 
    trade2.symbol = "GBPUSD"
    trade2.direction = TradeDirection.SELL
    trade2.status = TradeStatus.ACTIVE
    trade2.position_tickets = [
        {"tp": 1, "ticket": "B1", "closed": False, "tp_price": 1.2980, "entry_price": 1.3000},
        {"tp": 2, "ticket": "B2", "closed": False, "tp_price": 1.2960, "entry_price": 1.3000}
    ]
    
    # Mock the trade manager's trades
    trade_manager.trades = {
        trade1.id: trade1,
        trade2.id: trade2
    }
    
    print("Initialized 2 active trades:")
    print(f"  Trade A (EURUSD): Status={trade1.status}, Breakeven={trade1.breakeven_applied}")
    print(f"  Trade B (GBPUSD): Status={trade2.status}, Breakeven={trade2.breakeven_applied}")
    
    # 2. Simulate TP1 hit for Trade A ONLY
    print("\n[Simulating] TP1 Hit for Trade A (Ticket A1 closed)")
    
    # We need to mock broker_client.get_positions to return everything EXCEPT A1
    # This simulates A1 being closed by the broker
    open_positions = [
        {"ticket": "A2", "id": "A2"}, # A2 still open
        {"ticket": "B1", "id": "B1"}, # B1 still open
        {"ticket": "B2", "id": "B2"}, # B2 still open
    ]
    
    # Run ONE check cycle with mocked broker
    print("Running check cycle...")
    
    from unittest.mock import patch, AsyncMock
    
    with patch('core.trade_manager.broker_client') as mock_broker:
        mock_broker.get_positions = AsyncMock(return_value=open_positions)
        mock_broker.get_current_price = AsyncMock(return_value=(1.1030, 1.1035))
        mock_broker.modify_position = AsyncMock(return_value=(True, "Modified"))
        
        await trade_manager._check_tp_levels()
    
    # 3. Verify Results
    print("\nResults after Cycle 1:")
    
    # Check Trade A
    a1_closed = trade1.position_tickets[0]["closed"]
    a_breakeven = trade1.breakeven_applied
    print(f"  Trade A (Expected: TP1 Hit, Breakeven Applied)")
    print(f"    - Ticket A1 Closed: {a1_closed} [{'PASS' if a1_closed else 'FAIL'}]")
    print(f"    - Breakeven Applied: {a_breakeven} [{'PASS' if a_breakeven else 'FAIL'}]")
    
    # Check Trade B
    b1_closed = trade2.position_tickets[0]["closed"]
    b_breakeven = trade2.breakeven_applied
    print(f"  Trade B (Expected: No Change)")
    print(f"    - Ticket B1 Closed: {b1_closed} [{'PASS' if not b1_closed else 'FAIL'}]")
    print(f"    - Breakeven Applied: {b_breakeven} [{'PASS' if not b_breakeven else 'FAIL'}]")
    
    if a1_closed and a_breakeven and not b1_closed and not b_breakeven:
        print("\n[SUCCESS] Trade A updated independently of Trade B")
        return True
    else:
        print("\n[FAIL] Cross-contamination or failure to update")
        return False

if __name__ == "__main__":
    asyncio.run(test_concurrent_trades())
