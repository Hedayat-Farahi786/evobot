# Real-Time Sync Testing Guide

## Overview
This guide explains how to test the real-time synchronization feature that keeps the dashboard updated with live MT5 data.

## Architecture
```
MT5 Terminal
    ↓ (1s polling)
Broker Client (mt5_client.py)
    ↓
Realtime Sync Service (realtime_sync.py)
    ↓ ↓
    ↓ └→ Firebase (persistent storage)
    ↓
    └→ WebSocket (instant updates)
        ↓
    Dashboard (real-time UI)
```

## Testing Methods

### Method 1: Automated Test Script

Run the comprehensive test suite:

```bash
python test_realtime_sync.py
```

This will test:
- ✅ MT5 connection
- ✅ Firebase connection
- ✅ Snapshot capture
- ✅ Firebase synchronization
- ✅ WebSocket broadcasting
- ✅ Real-time sync loop
- ✅ Change detection

**Expected Output:**
```
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
REAL-TIME SYNC TEST SUITE
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

============================================================
TEST 1: MT5 Connection
============================================================
✅ MT5 connected successfully
   Balance: 10000.00 USD
   Equity: 10000.00
   Server: YourBroker-Demo

... (more tests)

============================================================
TEST SUMMARY
============================================================
✅ PASS - MT5 Connection
✅ PASS - Firebase Connection
✅ PASS - Snapshot Capture
✅ PASS - Firebase Sync
✅ PASS - WebSocket Broadcast
✅ PASS - Real-time Loop
✅ PASS - Change Detection
============================================================
Results: 7/7 tests passed
============================================================
```

### Method 2: Visual Dashboard Test

1. **Start the dashboard:**
   ```bash
   python start_dashboard.py
   ```

2. **Open the test page:**
   ```
   http://localhost:8080/test-realtime
   ```

3. **Start the bot** from the main dashboard or test page

4. **Observe real-time updates:**
   - Connection status indicators (green = connected)
   - Account balance/equity updating every second
   - Open positions list updating in real-time
   - Trade statistics updating
   - Update log showing all WebSocket messages

**What to Look For:**
- ✅ WebSocket connects (green dot)
- ✅ MT5 status shows "Connected" (green dot)
- ✅ Update count increases every 1-2 seconds
- ✅ Account values update in real-time
- ✅ Positions list updates when trades open/close
- ✅ Log shows continuous updates

### Method 3: Manual Testing with Browser DevTools

1. **Open dashboard:**
   ```
   http://localhost:8080
   ```

2. **Open Browser DevTools** (F12)

3. **Go to Network tab** → Filter by "WS" (WebSocket)

4. **Start the bot**

5. **Monitor WebSocket messages:**
   - Click on the WebSocket connection
   - View "Messages" tab
   - You should see messages every 1-2 seconds:
     ```json
     {
       "type": "account_update",
       "data": {
         "balance": 10000.00,
         "equity": 10000.00,
         ...
       }
     }
     ```

### Method 4: Firebase Console Verification

1. **Open Firebase Console:**
   ```
   https://console.firebase.google.com/
   ```

2. **Navigate to:** Realtime Database

3. **Watch the data update in real-time:**
   - `/account` - Account information
   - `/positions` - Open positions
   - `/stats` - Trade statistics
   - `/status` - Bot status

4. **Verify data matches MT5:**
   - Balance should match MT5 terminal
   - Positions should match open trades
   - Updates should occur every 1-2 seconds

## Performance Benchmarks

### Expected Performance:
- **Update Interval:** 1 second
- **Latency:** < 100ms (MT5 → Dashboard)
- **CPU Usage:** < 5% (idle), < 10% (active trading)
- **Memory Usage:** < 100MB
- **Network:** ~1KB per update

### Monitoring Performance:

```python
# Add to test_realtime_sync.py
import time

start = time.time()
snapshot = await realtime_sync._capture_snapshot()
capture_time = time.time() - start

start = time.time()
await realtime_sync._sync_snapshot(snapshot)
sync_time = time.time() - start

print(f"Capture time: {capture_time*1000:.2f}ms")
print(f"Sync time: {sync_time*1000:.2f}ms")
```

## Troubleshooting

### Issue: No Updates Received

**Symptoms:**
- Update count stays at 0
- "Last Update" shows "Never"
- No log entries

**Solutions:**
1. Check bot is running: `bot_state.is_running = True`
2. Check MT5 connected: `bot_state.is_connected_mt5 = True`
3. Check WebSocket connection (green dot)
4. Check browser console for errors
5. Restart dashboard: `python start_dashboard.py`

### Issue: Slow Updates

**Symptoms:**
- Updates take > 2 seconds
- Dashboard feels laggy

**Solutions:**
1. Check MT5 terminal is responsive
2. Check network latency to Firebase
3. Reduce update interval (not recommended):
   ```python
   realtime_sync._update_interval = 2.0  # 2 seconds
   ```
4. Check CPU usage on server

### Issue: WebSocket Disconnects

**Symptoms:**
- Red dot on WebSocket status
- "Reconnecting..." message

**Solutions:**
1. Check firewall settings
2. Check reverse proxy configuration (if using)
3. Increase WebSocket timeout
4. Check server logs for errors

### Issue: Data Mismatch

**Symptoms:**
- Dashboard shows different values than MT5
- Positions don't match

**Solutions:**
1. Force refresh: `await realtime_sync.force_sync()`
2. Check MT5 connection
3. Verify broker_client is working:
   ```python
   account = await broker_client.get_account_info(force_refresh=True)
   print(account.balance)
   ```
4. Clear Firebase cache and restart

## Advanced Testing

### Load Testing

Test with multiple concurrent WebSocket connections:

```python
import asyncio
import websockets

async def connect_client(client_id):
    uri = "ws://localhost:8080/ws"
    async with websockets.connect(uri) as ws:
        print(f"Client {client_id} connected")
        async for message in ws:
            print(f"Client {client_id}: {message[:50]}...")

async def load_test():
    tasks = [connect_client(i) for i in range(10)]
    await asyncio.gather(*tasks)

asyncio.run(load_test())
```

### Stress Testing

Test with rapid position changes:

```python
# Open/close positions rapidly
for i in range(20):
    # Open position
    trade = Trade(...)
    await broker_client.place_market_order(trade, 0.01)
    await asyncio.sleep(0.5)
    
    # Close position
    await broker_client.close_position(ticket)
    await asyncio.sleep(0.5)
    
    # Verify dashboard updates correctly
```

## Success Criteria

✅ **All tests pass** in automated test suite
✅ **Updates occur every 1-2 seconds** consistently
✅ **WebSocket stays connected** for > 1 hour
✅ **Data matches MT5** terminal exactly
✅ **No memory leaks** after 24 hours
✅ **CPU usage < 10%** during active trading
✅ **Latency < 100ms** from MT5 to dashboard
✅ **Firebase data persists** after restart

## Continuous Monitoring

### Production Monitoring

Add to your monitoring dashboard:

```python
# Monitor sync health
metrics = {
    "updates_per_minute": update_count / uptime_minutes,
    "avg_latency_ms": sum(latencies) / len(latencies),
    "websocket_connections": len(ws_manager.active_connections),
    "last_sync_time": realtime_sync._last_snapshot.timestamp,
    "sync_errors": error_count
}
```

### Alerts

Set up alerts for:
- ⚠️ No updates for > 10 seconds
- ⚠️ Latency > 500ms
- ⚠️ WebSocket disconnects > 3 times/hour
- ⚠️ Sync errors > 5/minute

## Conclusion

The real-time sync system is critical for dashboard responsiveness. Regular testing ensures:
- Traders see accurate, up-to-date information
- Positions are monitored in real-time
- System health is visible
- Data persists across restarts

Run tests before each deployment and monitor continuously in production.
