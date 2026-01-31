# 🔧 Troubleshooting: Signals Not Appearing

## ❌ Problem: Posted signals but nothing happened

This usually means the bot isn't started yet. Here's how to fix it:

## ✅ Solution: Start the Bot

### Step 1: Check Dashboard is Running

In terminal, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

If not, run:
```bash
python start_dashboard.py
```

### Step 2: Open Dashboard in Browser

Go to: **http://localhost:8080**

### Step 3: Click "▶ Start Bot" Button

**IMPORTANT**: The dashboard running ≠ Bot monitoring signals

You MUST click the **"▶ Start Bot"** button in the web interface!

Look for:
- Big green button that says "▶ Start Bot"
- Usually in the top-right of the dashboard
- Click it!

### Step 4: Wait for Connection

After clicking "Start Bot", wait for:
- ✅ **Telegram: Connected** (should turn green)
- ⚠️ **MT5: Disconnected** (expected on Linux)
- Status badge changes from "Stopped" to "Running"

### Step 5: Verify Bot is Listening

Check the terminal where dashboard is running. You should see:
```
Signed in successfully as Hedayat Farahi
INFO:     127.0.0.1:xxxxx - "POST /api/bot/start HTTP/1.1" 200 OK
```

### Step 6: Now Post Your Signal

Go to your Telegram channel and post:
```
XAUUSD BUY
Entry: 2050.00
SL: 2045.00
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00
```

### Step 7: Check Dashboard

You should see:
- 🔔 Notification in top-right corner
- "📡 Signal: XAUUSD BUY"
- Activity in the Logs tab

## 🔍 Common Issues

### Issue 1: "Start Bot" Button is Disabled

**Cause**: Bot is already running
**Solution**: Click "⏹ Stop Bot" first, then "▶ Start Bot"

### Issue 2: Telegram Shows "Disconnected"

**Cause**: Authentication failed or session expired
**Solution**: 
1. Stop the bot
2. Delete `evobot_session.session` file
3. Start bot again
4. Enter verification code when prompted

### Issue 3: No Notifications Appear

**Cause**: Bot not monitoring your channel
**Solution**: 
1. Verify channel ID in `.env` is correct: `-1002259448420`
2. Make sure bot is member of the channel
3. Restart the bot

### Issue 4: Wrong Channel ID

**How to get correct channel ID:**

1. Forward a message from your channel to @userinfobot
2. It will show the channel ID
3. Update `.env` file with correct ID
4. Restart dashboard

## 📋 Quick Checklist

Before posting signals, verify:

- [ ] Dashboard is running (`python start_dashboard.py`)
- [ ] Browser is open at http://localhost:8080
- [ ] **"▶ Start Bot" button was clicked**
- [ ] Status shows "Running" (not "Stopped")
- [ ] Telegram shows "Connected" (green)
- [ ] Channel ID in `.env` is correct
- [ ] You are admin/member of the test channel

## 🎯 Step-by-Step Test

**1. Open Terminal:**
```bash
cd /home/ubuntu/personal/evobot
python start_dashboard.py
```

**2. Open Browser:**
```
http://localhost:8080
```

**3. Click "▶ Start Bot"**
- Look for the green button
- Click it
- Wait for "Telegram: Connected"

**4. Open Telegram**
- Go to your test channel: -1002259448420
- Post this signal:
```
XAUUSD BUY
Entry: 2050.00
SL: 2045.00
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00
```

**5. Check Dashboard**
- Should see notification immediately
- Check "Logs" tab for details

## 🔧 Advanced Troubleshooting

### Check if Bot is Actually Running

In terminal where dashboard is running, look for:
```
INFO:     127.0.0.1:xxxxx - "POST /api/bot/start HTTP/1.1" 200 OK
```

If you see this, bot is started.

### Check Telegram Connection

After clicking "Start Bot", terminal should show:
```
Signed in successfully as Hedayat Farahi
```

If not, there's a connection issue.

### Test Signal Parser

1. Click "🧪 Test Signal" in dashboard
2. Paste your signal
3. Click "🧪 Test Parse"
4. See if it parses correctly

If parser works but channel doesn't, it's a channel monitoring issue.

### Verify Channel ID

Your `.env` should have:
```
SIGNAL_CHANNELS=-1002259448420
```

Make sure:
- No spaces
- Correct negative sign
- Correct number

### Check Bot Permissions

Make sure:
- You are admin or member of the channel
- Channel is not private (or bot has access)
- Messages are not restricted

## 💡 Most Common Solution

**90% of the time, the issue is:**

You started the dashboard but **didn't click "▶ Start Bot"** button!

The dashboard can run without the bot being active. You MUST click the button to start monitoring.

## 🎬 Visual Guide

```
1. Terminal: python start_dashboard.py
   ↓
2. Browser: http://localhost:8080
   ↓
3. Dashboard loads (shows "Stopped")
   ↓
4. Click "▶ Start Bot" button ← YOU ARE HERE
   ↓
5. Status changes to "Running"
   ↓
6. Telegram: Connected ✅
   ↓
7. Post signal in channel
   ↓
8. See notification in dashboard ✅
```

## 🚀 Quick Fix

**If nothing is working:**

1. **Stop everything:**
   - Press CTRL+C in terminal
   - Close browser

2. **Restart fresh:**
   ```bash
   python start_dashboard.py
   ```

3. **Open browser:**
   ```
   http://localhost:8080
   ```

4. **Click "▶ Start Bot"**

5. **Wait for "Telegram: Connected"**

6. **Post signal in channel**

7. **Watch for notification!**

## ✅ Success Indicators

You'll know it's working when:
- ✅ Status badge says "Running" (green)
- ✅ Telegram shows "Connected"
- ✅ Terminal shows "Signed in successfully"
- ✅ Posting signal triggers notification
- ✅ Logs tab shows activity

## 📞 Still Not Working?

If you've done all this and still no signals:

1. **Check terminal output** for errors
2. **Check browser console** (F12) for errors
3. **Verify channel ID** is correct
4. **Test with signal parser** first
5. **Try a simple signal** like:
   ```
   XAUUSD BUY 2050 SL 2045 TP 2060
   ```

---

**Remember: Dashboard running ≠ Bot monitoring signals**

**You MUST click "▶ Start Bot" button!** 🚀
