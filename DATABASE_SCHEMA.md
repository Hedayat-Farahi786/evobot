# Signal Tracking Database Schema

## Firebase Structure

```
signal_messages/
  ├── {signal_id}/
  │   ├── id: string
  │   ├── channel_id: string
  │   ├── channel_name: string
  │   ├── message_id: int
  │   ├── text: string
  │   ├── timestamp: ISO datetime
  │   ├── sender_name: string | null
  │   │
  │   ├── # Signal Details
  │   ├── symbol: string (XAUUSD, EURUSD, etc.)
  │   ├── direction: string (BUY/SELL)
  │   ├── signal_type: string (new_trade, update, etc.)
  │   ├── entry_min: float
  │   ├── entry_max: float
  │   ├── stop_loss: float
  │   ├── take_profit_1: float
  │   ├── take_profit_2: float
  │   ├── take_profit_3: float
  │   │
  │   ├── # Execution Tracking
  │   ├── trade_id: string | null
  │   ├── executed: boolean
  │   ├── execution_time: ISO datetime | null
  │   ├── actual_entry_price: float | null
  │   ├── lot_size: float | null
  │   │
  │   ├── # Outcome Tracking
  │   ├── status: string (pending/active/tp1_hit/tp2_hit/tp3_hit/sl_hit/closed)
  │   ├── tp1_hit: boolean
  │   ├── tp1_hit_time: ISO datetime | null
  │   ├── tp1_profit: float | null
  │   ├── tp2_hit: boolean
  │   ├── tp2_hit_time: ISO datetime | null
  │   ├── tp2_profit: float | null
  │   ├── tp3_hit: boolean
  │   ├── tp3_hit_time: ISO datetime | null
  │   ├── tp3_profit: float | null
  │   ├── sl_hit: boolean
  │   ├── sl_hit_time: ISO datetime | null
  │   ├── sl_loss: float | null
  │   │
  │   ├── # Final Results
  │   ├── closed_time: ISO datetime | null
  │   ├── total_profit: float | null
  │   ├── total_pips: float | null
  │   ├── duration_minutes: int | null
  │   ├── win: boolean | null
  │   └── risk_reward_ratio: float | null

channel_analytics/
  ├── {channel_id}/
  │   ├── channel_name: string
  │   ├── total_signals: int
  │   ├── executed_signals: int
  │   ├── closed_signals: int
  │   ├── win_rate: float
  │   ├── total_profit: float
  │   ├── avg_profit: float
  │   ├── tp1_hit_count: int
  │   ├── tp2_hit_count: int
  │   ├── tp3_hit_count: int
  │   ├── sl_hit_count: int
  │   ├── tp1_rate: float
  │   ├── tp2_rate: float
  │   ├── tp3_rate: float
  │   └── last_updated: ISO datetime
```

## Data Flow

1. **Signal Received** → Create SignalMessage with status="pending"
2. **Trade Executed** → Update with trade_id, executed=true, status="active"
3. **TP/SL Hit** → Update with hit times and profits
4. **Trade Closed** → Update with final results and analytics
5. **Analytics Updated** → Aggregate channel statistics

## Indexes for Performance

- channel_id (for filtering by channel)
- timestamp (for time-based queries)
- status (for filtering active/closed signals)
- symbol (for symbol-specific analytics)
