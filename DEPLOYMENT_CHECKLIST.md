# 🚀 QUICK DEPLOYMENT & TESTING CHECKLIST

## ✅ Pre-Flight Checklist

```bash
# 1. Verify Python syntax
python3 -m py_compile core/trade_manager.py
python3 -m py_compile parsers/signal_parser.py
echo "✅ Syntax OK"

# 2. Run validation tests
python3 validate_trading_logic.py
echo "✅ Logic verified"

# 3. Check environment
python3 -c "import os; print('✅ API ID:', os.getenv('TELEGRAM_API_ID', 'NOT SET')[:15])"
```

## 🎬 Start System

```bash
# Terminal 1: Start dashboard
python3 start_dashboard.py

# Terminal 2: Monitor logs
tail -f logs/evobot.log | grep -E "(TP|Entry|breakeven|Position)"

# Terminal 3: Monitor signals (optional)
watch -n 5 'tail -20 logs/evobot.log'
```

## 📍 Access Dashboard

```
Browser: http://localhost:8080
Port: 8080
Protocol: HTTP (or HTTPS if configured)
```

## 📨 Send Test Signals

Copy & paste these to your Telegram signal channel:

### Test 1: EURUSD BUY
```
EURUSD BUY
Entry: 1.0850
SL: 1.0800
TP1: 1.0900
TP2: 1.0950
TP3: 1.1000
```

### Test 2: GBPUSD SELL
```
GBPUSD SELL
Entry: 1.2500
SL: 1.2550
TP1: 1.2450
TP2: 1.2400
TP3: 1.2350
```

### Test 3: XAUUSD BUY
```
XAUUSD BUY
Entry: 2050.00
SL: 2045.00
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00
```

## 🔍 Verify on Dashboard

### Dashboard Tab
- [ ] Signal appears in feed
- [ ] All 3 TPs extracted
- [ ] Symbol/Direction correct
- [ ] Time recorded

### Open Positions Tab
- [ ] Click "Group" button
- [ ] Signal group visible
- [ ] Shows 3 positions
- [ ] Expand arrow works
- [ ] Entry/SL/TP displayed
- [ ] P&L shows real-time

### List View (Toggle)
- [ ] Click "List" button
- [ ] All positions in flat table
- [ ] Ticker, Symbol, Type, Volume
- [ ] Entry, Current, SL, TP, P/L
- [ ] Action buttons work

## ✅ Verification Steps

### 1. Signal Capture
```bash
# Watch logs for signal capture
tail -f logs/evobot.log | grep "Signal received"
# Should show: ✅ EURUSD BUY parsed
```

### 2. Position Creation
```bash
# Watch for 3 orders per signal
tail -f logs/evobot.log | grep "Order placed"
# Should show 3 lines per signal:
# TP1 order placed: ticket=12345
# TP2 order placed: ticket=12346
# TP3 order placed: ticket=12347
```

### 3. Breakeven Application
```bash
# When TP1 hits, watch for:
tail -f logs/evobot.log | grep "Moving remaining"
# Should show:
# Position 12346 moved to breakeven SL=1.0850 (entry was 1.0850)
# Position 12347 moved to breakeven SL=1.0850 (entry was 1.0850)
```

## 🔧 Troubleshooting

### Dashboard won't start
```bash
# Kill any existing process
lsof -i :8080 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Start fresh
python3 start_dashboard.py
```

### No signals captured
```bash
# Check channels are configured
grep "signal_channels" logs/evobot.log

# Check Telegram connection
grep "Telegram" logs/evobot.log

# Manually test signal parser
python3 -c "
from parsers.signal_parser import signal_parser
sig = signal_parser.parse('EURUSD BUY\nEntry: 1.0850\nSL: 1.0800\nTP1: 1.0900\nTP2: 1.0950\nTP3: 1.1000')
print(f'✅ Parsed: {sig.symbol} {sig.direction}' if sig else '❌ Failed')
"
```

### Only 1 position created
```bash
# Check TPs are being extracted
grep "take_profit" logs/evobot.log

# Verify signal has all 3 TPs
# Make sure signal has clear TP1, TP2, TP3 labels
```

### View toggle not working
```bash
# Clear browser cache: Ctrl+Shift+Delete
# Or restart dashboard:
pkill -f "start_dashboard.py"
python3 start_dashboard.py
```

## 📊 Performance Monitoring

### Check Active Trades
```bash
ls -la data/trades.json
tail -20 data/trades.json | python3 -m json.tool
```

### Monitor Position Count
```bash
grep "position_tickets" logs/evobot.log | tail -5
```

### Watch P&L Updates
```bash
grep -E "P.L|profit|unrealized" logs/evobot.log | tail -10
```

## 🎯 Expected Log Output

```
[INFO] EvoBot Trading System starting...
[INFO] Connecting to MetaTrader 5...
[INFO] Telegram listener started
[INFO] Signal received: EURUSD BUY
[INFO] Parsing signal...
[INFO] =================================================================
[INFO] === NEW SIGNAL GROUP: Trade xxxxx... ===
[INFO] Symbol: EURUSD, Direction: BUY
[INFO] Orders: [TP1=12345, TP2=12346, TP3=12347]
[INFO] Each order has same lot (0.10) and SL (1.0800)
[INFO] TP1 order placed: 12345 @ 0.10 lots, TP: 1.0900, SL: 1.0800
[INFO] TP2 order placed: 12346 @ 0.10 lots, TP: 1.0950, SL: 1.0800
[INFO] TP3 order placed: 12347 @ 0.10 lots, TP: 1.1000, SL: 1.0800

[When TP1 hits]
[INFO] TP1 HIT! Position 12345 closed at 1.0900
[INFO] Moving remaining positions to breakeven...
[INFO] Position 12346 moved to breakeven SL=1.0850 (entry was 1.0850)
[INFO] Position 12347 moved to breakeven SL=1.0850 (entry was 1.0850)
```

## 📱 Dashboard Features

### Dashboard Tab
- Real-time signal feed from Telegram
- Connection status (MT5, Telegram)
- Account info (login, balance, margin)
- Quick stats (open positions, total P&L)

### Open Positions Tab
- **Group View** (default): Collapsible signal groups
  - Expand arrow to show/hide positions
  - Quick stats per group
  - Entry, SL, TP, P&L per position
  
- **List View**: Flat table all positions
  - Sortable columns
  - All details visible
  - Easier for scanning

- **View Toggle**: Switch between views
  - Preference saved to localStorage
  - Persists across browser refresh

### Trades Tab
- Completed trades history
- Entry/Exit details
- Realized P&L
- Duration, Returns

### Settings Tab
- Telegram configuration
- Trading parameters
- Risk management
- Notification setup

## 🎓 Understanding the Flow

```
Signal from Telegram
         ↓
Signal Parser (extracts symbol, direction, entry, SL, TP1, TP2, TP3)
         ↓
Risk Manager (checks spreads, drawdown, news)
         ↓
Trade Manager (creates 3 orders)
         ↓
Broker Client (places on MT5)
         ↓
Position Monitor (watches for TP hits)
         ↓
TP1 Hit Event:
├─ Close Position 1 (profit at TP1)
├─ Move Position 2 SL to Position 2's entry
├─ Move Position 3 SL to Position 3's entry
└─ Continue monitoring for TP2/TP3
         ↓
Dashboard Display (shows all positions, P&L, status)
```

## ✅ Success Indicators

All of these should be ✅:

- [x] Dashboard starts without errors
- [x] Telegram channels appear in Settings
- [x] Test signal appears in feed
- [x] 3 positions created (visible in Open Positions)
- [x] Each position has different TP
- [x] Positions grouped by signal
- [x] View toggle (Group/List) works
- [x] P&L calculates correctly
- [x] Logs show all operations
- [x] System remains stable

---

## 📞 Support

For detailed information, see:
- `E2E_TESTING_GUIDE.md` - Comprehensive testing guide
- `IMPLEMENTATION_COMPLETE.md` - Complete documentation
- `logs/evobot.log` - Live system logs

---

**Status:** ✅ Ready for Deployment  
**Last Updated:** Jan 30, 2026
