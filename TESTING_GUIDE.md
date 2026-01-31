# 🧪 EvoBot Testing Guide

## ✅ Your Current Setup

You've already configured your test channel:
- **Signal Channel**: -1002259448420
- **Notification Channel**: -1002259448420 (same channel)

This is perfect for testing! The bot will:
1. Monitor this channel for trading signals
2. Send notifications back to the same channel

## 🚀 How to Test

### Step 1: Start the Dashboard

```bash
python start_dashboard.py
```

Open browser: http://localhost:8080

### Step 2: Start the Bot

1. Click the **"▶ Start Bot"** button in the dashboard
2. Wait for status to show:
   - ✅ Telegram: Connected
   - ⚠️ MT5: Disconnected (expected on Linux)

### Step 3: Post Test Signals

Go to your Telegram test channel and post trading signals!

## 📝 Signal Formats That Work

### Format 1: Basic Signal
```
XAUUSD BUY
Entry: 2050.00
SL: 2045.00
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00
```

### Format 2: With Emojis
```
🟢 GOLD BUY
Entry: 2050.00
Stop Loss: 2045.00
🎯 TP1: 2055.00
🎯 TP2: 2060.00
🎯 TP3: 2065.00
```

### Format 3: Entry Zone
```
GBPUSD SELL
Entry Zone: 1.2500 - 1.2520
SL: 1.2550
TP1: 1.2450
TP2: 1.2400
TP3: 1.2350
```

### Format 4: With Lot Size
```
📈 EURUSD LONG
@ 1.0850
SL: 1.0800
TP1: 1.0900
TP2: 1.0950
TP3: 1.1000
Lot: 0.02
```

### Format 5: Short Format
```
USDJPY SELL @ 150.50
SL 151.00
TP 149.50
```

## 🎯 Supported Symbols

The bot recognizes these symbols and their aliases:

### Forex Pairs
- **EURUSD** (EUR/USD, FIBER)
- **GBPUSD** (GBP/USD, CABLE)
- **USDJPY** (USD/JPY, NINJA)
- **USDCAD** (USD/CAD, LOONIE)
- **AUDUSD** (AUD/USD, AUSSIE)
- **NZDUSD** (NZD/USD, KIWI)
- **USDCHF** (USD/CHF, SWISSY)
- **EURJPY** (EUR/JPY)
- **GBPJPY** (GBP/JPY)

### Metals
- **XAUUSD** (XAU/USD, GOLD)
- **XAGUSD** (XAG/USD, SILVER)

## 🧪 Testing Workflow

### Test 1: Basic Signal Parsing

1. **Post this in your channel:**
```
XAUUSD BUY
Entry: 2050.00
SL: 2045.00
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00
```

2. **Check the dashboard:**
   - You should see a notification: "📡 Signal: XAUUSD BUY"
   - Check the logs tab for parsing details

3. **Expected behavior:**
   - Signal parsed successfully
   - Bot will try to execute (but MT5 is disconnected on Linux)
   - You'll see the signal in the dashboard

### Test 2: Signal Parser Tester

1. **In the dashboard, click "🧪 Test Signal"**

2. **Paste a signal:**
```
GBPUSD SELL
Entry: 1.2500
SL: 1.2550
TP1: 1.2450
TP2: 1.2400
TP3: 1.2350
```

3. **Click "🧪 Test Parse"**

4. **You'll see:**
   - ✅ Parsed Successfully (if valid)
   - Symbol: GBPUSD
   - Direction: SELL
   - Entry: 1.2500
   - SL: 1.2550
   - TPs: 1.2450, 1.2400, 1.2350

### Test 3: Multiple Signals

Post multiple signals in your channel:

```
EURUSD BUY @ 1.0850
SL: 1.0800
TP1: 1.0900
TP2: 1.0950

---

GBPUSD SELL @ 1.2500
SL: 1.2550
TP1: 1.2450

---

XAUUSD BUY
Entry Zone: 2050-2052
SL: 2045
TP1: 2060
TP2: 2070
TP3: 2080
```

Watch the dashboard for real-time notifications!

### Test 4: Signal Updates

Post an update signal:

```
✅ XAUUSD TP1 HIT
🔒 Move SL to Breakeven
```

Or:

```
❌ GBPUSD SL HIT
```

The bot will parse these as signal updates.

## 📊 What to Watch in Dashboard

### Real-Time Updates
- **Notifications** appear in top-right corner
- **Logs tab** shows all parsing activity
- **WebSocket** provides instant updates

### Signal Flow
1. You post signal in Telegram
2. Bot receives message instantly
3. Signal parser extracts data
4. Dashboard shows notification
5. Risk checks performed
6. Trade would execute (if MT5 connected)

## 🔍 Monitoring Your Tests

### Dashboard Tabs

**1. Active Trades Tab**
- Shows trades that would be opened
- On Linux (no MT5), this will be empty
- On Windows with MT5, you'd see live trades

**2. Logs Tab**
- Click "📋 Logs" tab
- See all signal parsing activity
- Check for any errors

**3. Settings**
- Click "⚙ Settings"
- Adjust lot size, spread limits, etc.
- Changes apply immediately

## 🎮 Interactive Testing

### Test Different Formats

Try posting these variations:

**Minimal Format:**
```
GOLD BUY 2050 SL 2045 TP 2060
```

**Detailed Format:**
```
📊 TRADING SIGNAL 📊

Symbol: XAUUSD
Direction: BUY
Entry Price: 2050.00
Stop Loss: 2045.00

Take Profit Levels:
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00

Risk: 1%
```

**With Emojis:**
```
🚀 EURUSD LONG SETUP 🚀

💰 Entry: 1.0850
🛑 Stop Loss: 1.0800
🎯 Target 1: 1.0900
🎯 Target 2: 1.0950
🎯 Target 3: 1.1000
```

## ✅ Expected Results

### On Linux (Your Current Setup)

✅ **What Works:**
- Signal parsing from Telegram
- Real-time dashboard updates
- WebSocket notifications
- Signal testing
- Configuration changes
- Log viewing

❌ **What Doesn't Work:**
- Actual MT5 trading (Windows only)
- Position monitoring
- Trade execution

### On Windows (Production)

✅ **Everything Works:**
- All of the above PLUS
- Actual trade execution
- Position monitoring
- Partial closes at TP levels
- Breakeven management
- Real P/L tracking

## 🧪 Advanced Testing

### Test Risk Filters

**1. Test Spread Filter:**
- Post a signal
- Bot checks if spread is acceptable
- Rejects if spread > MAX_SPREAD_PIPS (5.0)

**2. Test Trading Hours:**
- Signals outside trading hours are rejected
- Default: 24/7 trading

**3. Test Max Trades:**
- After MAX_OPEN_TRADES (10), new signals rejected

### Test Signal Variations

**Different Symbols:**
```
EURUSD BUY @ 1.0850 SL 1.0800 TP 1.0900
GBPUSD SELL @ 1.2500 SL 1.2550 TP 1.2450
USDJPY BUY @ 150.00 SL 149.50 TP 150.50
XAUUSD BUY @ 2050 SL 2045 TP 2060
```

**Different Formats:**
```
BUY GOLD 2050 / 2045 / 2060
SELL CABLE 1.2500 SL 1.2550 TP 1.2450
LONG FIBER @ 1.0850 STOP 1.0800 TARGET 1.0900
```

## 📱 Mobile Testing

Access dashboard from your phone:
```
http://YOUR_SERVER_IP:8080
```

Post signals from Telegram mobile app and watch them appear in the dashboard!

## 🔔 Notification Testing

The bot will send notifications back to your channel:

**Signal Received:**
```
📡 Signal Received
Symbol: XAUUSD
Direction: BUY
Entry: 2050.00
```

**Trade Opened (Windows only):**
```
✅ Trade Opened
XAUUSD BUY
Entry: 2050.00
Lot: 0.01
```

**Risk Alert:**
```
⚠️ Trade Skipped
Reason: Spread too high (6.5 pips)
```

## 💡 Pro Testing Tips

1. **Start Simple**: Test basic signals first
2. **Check Logs**: Always review logs tab
3. **Use Test Parser**: Test signals before posting
4. **Try Variations**: Test different formats
5. **Monitor Dashboard**: Watch real-time updates
6. **Test Updates**: Post TP hit, SL hit messages
7. **Check Notifications**: Verify bot responds in channel

## 🎯 Quick Test Checklist

- [ ] Dashboard started
- [ ] Bot started (green status)
- [ ] Telegram connected
- [ ] Posted test signal in channel
- [ ] Saw notification in dashboard
- [ ] Checked logs tab
- [ ] Tested signal parser
- [ ] Tried different formats
- [ ] Tested signal updates
- [ ] Verified notifications in channel

## 🚀 Ready to Test!

Your setup is perfect for testing:
1. **Start dashboard**: `python start_dashboard.py`
2. **Click "Start Bot"** in dashboard
3. **Post signals** in your Telegram channel: -1002259448420
4. **Watch the magic happen** in real-time!

The bot will:
- ✅ Parse your signals instantly
- ✅ Show notifications in dashboard
- ✅ Send updates to your channel
- ✅ Log everything for review

**Start testing now!** 🎉

---

**Need help?** Check the logs tab or review the signal format examples above.
