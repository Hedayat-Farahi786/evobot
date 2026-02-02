# Signal Tracking & Analytics Feature

## Overview
Enhanced signal storage to track complete trade execution and outcomes for channel analytics.

## What's Tracked

### Signal Execution
- ✅ **Executed**: Whether signal was executed as a trade
- ✅ **Execution Time**: When trade was opened
- ✅ **Entry Price**: Actual entry price achieved
- ✅ **Lot Size**: Volume traded

### Take Profit Tracking
- ✅ **TP1 Hit**: Time, profit amount
- ✅ **TP2 Hit**: Time, profit amount  
- ✅ **TP3 Hit**: Time, profit amount

### Stop Loss Tracking
- ✅ **SL Hit**: Time, loss amount

### Final Results
- ✅ **Total Profit/Loss**: Final P&L in currency
- ✅ **Total Pips**: Pip movement
- ✅ **Duration**: Trade duration in minutes
- ✅ **Win/Loss**: Boolean outcome
- ✅ **Risk/Reward Ratio**: Calculated RR

## Database Schema

```python
SignalMessage:
    # Basic Info
    - id, channel_id, channel_name, message_id, text, timestamp
    - symbol, direction, signal_type
    - entry_min, entry_max, stop_loss
    - take_profit_1, take_profit_2, take_profit_3
    
    # Execution
    - trade_id, executed, execution_time
    - actual_entry_price, lot_size
    
    # Outcomes
    - status (pending/active/tp1_hit/tp2_hit/tp3_hit/sl_hit/closed)
    - tp1_hit, tp1_hit_time, tp1_profit
    - tp2_hit, tp2_hit_time, tp2_profit
    - tp3_hit, tp3_hit_time, tp3_profit
    - sl_hit, sl_hit_time, sl_loss
    
    # Results
    - closed_time, total_profit, total_pips
    - duration_minutes, win, risk_reward_ratio
```

## Analytics API

### Get Channel Analytics
```
GET /api/signals/analytics/{channel_id}
```

Returns:
```json
{
  "success": true,
  "channel_id": "123456",
  "analytics": {
    "total_signals": 50,
    "executed_signals": 48,
    "closed_signals": 45,
    "win_rate": 75.5,
    "total_profit": 1250.50,
    "avg_profit": 27.79,
    "tp1_hit_count": 40,
    "tp2_hit_count": 30,
    "tp3_hit_count": 20,
    "sl_hit_count": 10,
    "tp1_rate": 83.3,
    "tp2_rate": 62.5,
    "tp3_rate": 41.7
  }
}
```

### Get All Channels Analytics
```
GET /api/signals/analytics
```

## How It Works

1. **Signal Received** → Stored with `status: "pending"`

2. **Trade Executed** → Updated:
   - `executed: true`
   - `trade_id: "xyz"`
   - `execution_time: timestamp`
   - `actual_entry_price: 2050.00`
   - `status: "active"`

3. **TP1 Hit** → Updated:
   - `tp1_hit: true`
   - `tp1_hit_time: timestamp`
   - `tp1_profit: 50.00`
   - `status: "tp1_hit"`

4. **TP2 Hit** → Updated:
   - `tp2_hit: true`
   - `tp2_hit_time: timestamp`
   - `tp2_profit: 30.00`
   - `status: "tp2_hit"`

5. **Trade Closed** → Updated:
   - `closed_time: timestamp`
   - `total_profit: 120.00`
   - `total_pips: 50`
   - `duration_minutes: 45`
   - `win: true`
   - `risk_reward_ratio: 2.5`
   - `status: "closed"`

## Storage

- **Memory**: Last 500 signals
- **Firebase**: All signals persisted
- **Updates**: Real-time via trade event listeners

## Usage for Analytics

```python
# Get channel performance
analytics = signal_storage.get_channel_analytics("channel_123")

print(f"Win Rate: {analytics['win_rate']}%")
print(f"TP3 Rate: {analytics['tp3_rate']}%")
print(f"Avg Profit: ${analytics['avg_profit']}")
```

## Future Enhancements

- Channel comparison dashboard
- Signal quality scoring
- Best performing channels
- Time-based analytics (daily/weekly/monthly)
- Symbol-specific performance
- Entry accuracy tracking
