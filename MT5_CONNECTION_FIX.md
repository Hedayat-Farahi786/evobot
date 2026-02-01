# MT5 Connection Fix Guide

## Error: "Terminal: Authorization failed"

This error means your MT5 credentials are incorrect or the MT5 terminal is not properly configured.

## Quick Fix Steps:

### 1. Check Your .env File

Open `.env` file and verify these settings:

```env
# MT5 BROKER CONFIGURATION
MT5_SERVER=YourBroker-Demo
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

### 2. Get Correct MT5 Credentials

1. Open MetaTrader 5 terminal
2. Go to **Tools → Options → Server** tab
3. Copy the exact server name (e.g., "ICMarkets-Demo02")
4. Your login number is shown at the top of MT5
5. Use the password you set when creating the account

### 3. Enable Automated Trading in MT5

1. Open MT5
2. Go to **Tools → Options**
3. Click **Expert Advisors** tab
4. Check these boxes:
   - ✅ Allow automated trading
   - ✅ Allow DLL imports
   - ✅ Allow WebRequest for listed URL
5. Click **OK**

### 4. Update Your .env File

Replace the values in `.env` with your actual credentials:

```env
MT5_SERVER=ICMarkets-Demo02
MT5_LOGIN=12345678
MT5_PASSWORD=YourActualPassword
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

### 5. Restart the Dashboard

```bash
# Stop the current dashboard (Ctrl+C)
# Then restart:
python .\start_dashboard.py
```

## Common Issues:

### Issue 1: Wrong Server Name
- ❌ Wrong: `ICMarkets`
- ✅ Correct: `ICMarkets-Demo02` (exact name from MT5)

### Issue 2: Wrong Password
- Make sure you're using the **trading password**, not the investor password
- Password is case-sensitive

### Issue 3: MT5 Not Running
- MT5 terminal must be running for the bot to connect
- Keep MT5 open while the bot is running

### Issue 4: Wrong Path
- Default path: `C:\Program Files\MetaTrader 5\terminal64.exe`
- If you installed MT5 elsewhere, update MT5_PATH

## Test Your Connection:

After updating `.env`, test the connection:

1. Start the dashboard: `python .\start_dashboard.py`
2. Click "Start Bot" in the web interface
3. Watch the terminal for connection status
4. If successful, you'll see: "MT5 connected successfully"

## Still Having Issues?

Check the terminal output for specific error messages. The improved error messages will tell you exactly what's wrong:

- "Invalid login credentials" → Check server, login, password
- "MT5 terminal not running" → Open MT5 terminal
- "Connection timeout" → Ensure MT5 is open and responding

## Example Working Configuration:

```env
# Example for ICMarkets Demo
MT5_SERVER=ICMarkets-Demo02
MT5_LOGIN=12345678
MT5_PASSWORD=MySecurePass123
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

---

**Note**: The bot connects directly to your local MT5 terminal, not to MetaAPI cloud. Make sure MT5 is installed and running on your computer.
