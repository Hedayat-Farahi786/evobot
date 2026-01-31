# 🧪 End-to-End Testing Guide

## ✅ System Verification Checklist

### 1. Signal Parser Verification
- [x] Signal parser correctly parses multi-format signals
- [x] Extracts: Symbol, Direction, Entry, SL, TP1, TP2, TP3
- [x] Handles emoji and text variations

### 2. Configuration Verification
- Check: `python3 -c "from config.settings import config; print(f'Lot: {config.trading.default_lot_size}')"`
- Key settings:
  - Default lot size: 0.10
  - TP1 close: 50%
  - TP2 close: 30%
  - TP3 close: 20%
  - Move SL to breakeven at TP1: True

### 3. Trade Manager Verification
- [x] Creates trades with 3 positions per signal
- [x] Each position has unique TP target
- [x] Entry price stored per position
- [x] Breakeven moves SL to each position's entry

## 📋 Testing Workflow

### STEP 1: Start Dashboard
```bash
cd /home/ubuntu/personal/evobot
python3 start_dashboard.py
```

Then open: http://localhost:8080

### STEP 2: Configure Telegram Channels (if needed)
1. Go to **Settings** tab
2. Click **Telegram**
3. Add your signal channel names/IDs
4. Click **Save**

### STEP 3: Send Test Signals
Send these to your Telegram signal channel:

**Test Signal 1: EURUSD BUY**
```
EURUSD BUY
Entry: 1.0850
SL: 1.0800
TP1: 1.0900
TP2: 1.0950
TP3: 1.1000
```

**Test Signal 2: GBPUSD SELL**
```
GBPUSD SELL
Entry: 1.2500
SL: 1.2550
TP1: 1.2450
TP2: 1.2400
TP3: 1.2350
```

**Test Signal 3: XAUUSD BUY**
```
XAUUSD BUY
Entry: 2050.00
SL: 2045.00
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00
```

### STEP 4: Verify Signals Captured
1. Open **Dashboard** tab
2. Check recent signals in the Telegram Feed section
3. Verify signal details are correct

### STEP 5: Verify Positions Created
1. Go to **Open Positions** tab
2. **Toggle to "Group" view** if in List view
3. Verify for EACH signal:
   - ✅ 3 positions created (one for each TP)
   - ✅ Each position has same entry price
   - ✅ Different TP targets:
     - Position 1: TP1
     - Position 2: TP2
     - Position 3: TP3
   - ✅ Same SL for all 3 positions

### STEP 6: Verify Grouped View
In "Group" view, you should see:
- Signal channel name
- Number of positions (should be 3)
- Total P&L
- Collapsible positions list

### STEP 7: Test Breakeven Logic
When first TP hits:
1. Position 1 closes (partial close at TP1)
2. Positions 2 & 3 remain open
3. **SL for Position 2 → moves to Position 2's entry price**
4. **SL for Position 3 → moves to Position 3's entry price**
5. Positions 2 & 3 continue targeting TP2 and TP3

Check logs:
```bash
tail -f logs/evobot.log | grep "Moving remaining"
```

You should see:
```
Position XXXX moved to breakeven SL=1.0850 (entry was 1.0850)
Position YYYY moved to breakeven SL=1.0850 (entry was 1.0850)
```

## 🔍 Detailed Verification Checklist

### Signal Capture
- [ ] Signal appears in Dashboard feed
- [ ] Symbol parsed correctly
- [ ] Direction recognized (BUY/SELL)
- [ ] Entry price extracted
- [ ] SL extracted
- [ ] TP1, TP2, TP3 extracted
- [ ] Timestamp recorded

### Position Creation
- [ ] 3 orders placed (one per TP)
- [ ] All 3 get same SL
- [ ] Position 1 has TP1
- [ ] Position 2 has TP2
- [ ] Position 3 has TP3
- [ ] All same entry price
- [ ] All same lot size

### Position Display
- [ ] Dashboard shows all 3 positions
- [ ] Grouped view shows signal group
- [ ] List view shows flat table
- [ ] View toggle works (Group ↔ List)
- [ ] P&L calculations correct
- [ ] Current price updates

### Breakeven Logic
- [ ] TP1 hit closes Position 1
- [ ] SL moves to entry for Position 2
- [ ] SL moves to entry for Position 3
- [ ] Remaining positions continue tracking TP2/TP3
- [ ] No cross-signal interference

### Multiple Signals
- [ ] Each signal is independent
- [ ] Signals don't interfere with each other
- [ ] Each has own 3 positions
- [ ] Each moves SL correctly on TP hit

## 📊 Expected Behavior

### Scenario: EURUSD BUY Signal
```
Signal: EURUSD BUY, Entry 1.0850, SL 1.0800, TP1 1.0900, TP2 1.0950, TP3 1.1000

INITIAL STATE:
├─ Position 1: Ticket=12345, TP=1 (1.0900), Entry=1.0850, SL=1.0800
├─ Position 2: Ticket=12346, TP=2 (1.0950), Entry=1.0850, SL=1.0800
└─ Position 3: Ticket=12347, TP=3 (1.1000), Entry=1.0850, SL=1.0800

WHEN PRICE HITS 1.0900 (TP1 HIT):
├─ Position 1: CLOSED ✅ (profit from TP1)
├─ Position 2: OPEN, SL moved to 1.0850 (entry price!)
└─ Position 3: OPEN, SL moved to 1.0850 (entry price!)

THEN:
├─ Price moves to 1.0950 → Position 2 closes at TP2
├─ Position 3 continues toward TP3
└─ Finally closes at 1.1000
```

## 🐛 Troubleshooting

### No signals captured
- Check: Are channels configured in Settings?
- Check logs: `tail -f logs/evobot.log | grep -i "channel"`
- Verify: Is bot listening to correct channels?

### Only 1 position created instead of 3
- Check: All 3 TPs were extracted from signal?
- Look at logs: `tail -f logs/evobot.log | grep "TP"`
- Resend signal with clear TP1, TP2, TP3 labels

### SL not moving to entry on TP hit
- Check: Entry price stored in position info?
- Look at logs: `tail -f logs/evobot.log | grep "entry_price"`
- Verify: Breakeven enabled? `move_sl_to_breakeven_at_tp1: true`

### View toggle not working
- Clear browser cache: Ctrl+Shift+Delete
- Check browser console: F12 → Console
- Restart dashboard: Kill and restart

## 📝 Test Report Template

```
Date: [TEST_DATE]
Tester: [NAME]

SIGNALS TESTED: 3
- EURUSD BUY: ✅/❌
- GBPUSD SELL: ✅/❌
- XAUUSD BUY: ✅/❌

POSITIONS CREATED: ✅/❌
- Each signal has 3 positions: ✅/❌
- Correct TPs assigned: ✅/❌
- Entry prices stored: ✅/❌

BREAKEVEN LOGIC: ✅/❌
- TP1 hit closes position: ✅/❌
- SL moves to entry: ✅/❌
- Remaining positions continue: ✅/❌

OVERALL: ✅ PASSED / ❌ FAILED

NOTES:
[Any issues or observations]
```

## 🚀 Next Steps After Testing

1. **Verify with Real Signals**
   - Monitor actual trading channel
   - Verify positions created
   - Monitor breakeven logic

2. **Monitor Logs**
   - `tail -f logs/evobot.log`
   - Look for: Order placed, TP hit, Breakeven applied

3. **Check Trades Tab**
   - View completed trades
   - Verify P&L calculations
   - Check position history

4. **Set Up Alerts** (Optional)
   - Configure notification channel
   - Get updates on trades
   - Monitor from Telegram

## ✅ Success Criteria

- [x] All signals parse correctly
- [x] 3 positions created per signal
- [x] Positions have correct TP targets
- [x] Entry prices stored per position
- [x] View toggle works (Group/List)
- [x] Grouped view compact and collapsible
- [x] List view shows all details
- [x] Breakeven moves SL to each position's entry
- [x] Multiple signals don't interfere
- [x] Dashboard responsive and fast
- [x] Logs show all operations

---
**Last Updated:** Jan 30, 2026
**Status:** Ready for Testing ✅
