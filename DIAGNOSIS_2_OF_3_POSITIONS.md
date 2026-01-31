# 🔍 DIAGNOSIS: Only 2 Positions Created Instead of 3

## Issue Summary
Signal sent with 3 TPs (TP1, TP2, TP3) but only 2 positions placed in MT5.

### Signal Details
```
EURUSD BUY
Entry Zone: 1.18660 – 1.18680
Stop Loss: 1.18620
Take Profit 1: 1.18730
Take Profit 2: 1.18780
Take Profit 3: 1.18830
```

## Investigation Steps

### 1. Check Signal Parsing
✅ Verified: Signal parser CORRECTLY extracts all 3 TPs
- TP1: 1.1873
- TP2: 1.1878
- TP3: 1.1883

### 2. Verify Trade Manager Logic
✅ Verified: Trade manager correctly loops through all 3 TP levels and attempts to create 3 orders

### 3. Identify Root Cause
❓ One of the following is happening:

**Possibility A: Broker Connection Issue**
- MetaApi connection failing for 2nd or 3rd order
- Account insufficient funds after 1st/2nd order
- Rate limiting from MetaApi

**Possibility B: Order Validation Failed**
- MT5 rejecting invalid order parameters
- Lot size validation failing
- Symbol validation failing

**Possibility C: Network/Timing Issue**
- Connection dropped after 2 orders
- Timeout on 3rd order
- Race condition

## Enhanced Logging Added

Updated `core/trade_manager.py` with detailed logging:

```python
# For each order attempt:
logger.info(f"Attempting to place TP{tp_num} order: TP={tp_price}, SL={signal.stop_loss}")

# On success:
logger.info(f"✅ TP{tp_num} order PLACED: ticket={ticket}, lots={lot_size}")

# On failure:
logger.error(f"❌ Failed to place TP{tp_num} order: {msg}")

# Summary:
logger.info(f"Total Orders Placed: {len(orders_placed)}/3")
```

## How to Debug

### 1. Check the Logs
```bash
# Watch for the signal processing
tail -f logs/evobot.log | grep -E "EURUSD|order PLACED|Failed to place|Total Orders"
```

You should see:
```
Attempting to place TP1 order: TP=1.1873, SL=1.1862
✅ TP1 order PLACED: ticket=12345, lots=0.10
Attempting to place TP2 order: TP=1.1878, SL=1.1862
✅ TP2 order PLACED: ticket=12346, lots=0.10
Attempting to place TP3 order: TP=1.1883, SL=1.1862
✅ TP3 order PLACED: ticket=12347, lots=0.10
Total Orders Placed: 3/3
```

If you see:
```
❌ Failed to place TP3 order: [ERROR MESSAGE]
Total Orders Placed: 2/3
```

Then the error message will tell us why TP3 failed.

### 2. Send Test Signal Again
```
EURUSD BUY
Entry Zone: 1.18660 – 1.18680
Stop Loss: 1.18620
Take Profit 1: 1.18730
Take Profit 2: 1.18780
Take Profit 3: 1.18830
```

### 3. Monitor MT5 Directly
Check in MT5:
- Are exactly 2 orders open for EURUSD?
- What are their details (entry, SL, TP)?
- Any warning messages about order rejection?

### 4. Check Account Status
In MT5:
- Available balance?
- Used margin after 2 orders?
- Any restrictions?

## Common Issues & Solutions

### Issue 1: Insufficient Funds
**Symptom**: TP1 and TP2 placed, TP3 fails
**Cause**: Each order locks margin. 3rd order insufficient funds
**Solution**: Reduce lot size in settings

### Issue 2: MT5 Rate Limiting
**Symptom**: Orders placed in series, last one fails
**Cause**: Too many orders too fast
**Solution**: Already added 0.5s delay between orders (just deployed)

### Issue 3: Network Timeout
**Symptom**: 2nd or 3rd order "timeout" or "connection" error
**Cause**: MetaApi connection interrupted
**Solution**: Restart bot, check internet connection

### Issue 4: Account Restrictions
**Symptom**: 2 orders succeed, 3rd fails with "account" error
**Cause**: Some accounts can only have 2 pending/orders simultaneously
**Solution**: Check account settings in MT5, may need premium account

### Issue 5: Lot Size Validation
**Symptom**: All 3 orders fail with "invalid lot" or "minimum lot" error
**Cause**: Lot size too small or not matching symbol requirements
**Solution**: Increase default lot size in settings

## Next Actions

1. **Send test signal again** - watch logs for detailed error
2. **Check logs** for exact error message from TP3 failure
3. **Compare with test** - works fine with simple "EURUSD BUY\nEntry: 1.0850" format?
4. **Verify account** - check if restrictions apply
5. **Monitor margin** - watch margin after each order placement

## Files Modified

- `core/trade_manager.py`: Added detailed logging (lines 179-211)
- Added 0.5s delay between orders to prevent rate limiting
- Added clear error messages showing which TP failed and why

## What to Report

When you send the signal again and see the issue, run:
```bash
tail -100 logs/evobot.log | grep -A 2 -B 2 "EURUSD\|Failed\|Total Orders"
```

And share the output - it will show exactly where the 3rd order failed and why.
