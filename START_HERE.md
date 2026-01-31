# 🚀 EvoBot - How to Start

## ⚡ Quick Start (3 Steps)

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Configure Your Settings

Edit the `.env` file with your credentials:

```bash
nano .env
```

**Required settings:**
- `TELEGRAM_API_ID` - Get from https://my.telegram.org/apps
- `TELEGRAM_API_HASH` - Get from https://my.telegram.org/apps
- `TELEGRAM_PHONE` - Your phone number (+1234567890)
- `SIGNAL_CHANNELS` - Telegram channels to monitor
- `MT5_SERVER` - Your broker's server name
- `MT5_LOGIN` - Your MT5 account number
- `MT5_PASSWORD` - Your MT5 password

### 3️⃣ Start the Dashboard

```bash
./run_dashboard.sh
```

Or:

```bash
python start_dashboard.py
```

## 🌐 Access the Dashboard

Open your browser and go to:

**http://localhost:8080**

## 🎮 Using the Dashboard

1. **Click "▶ Start Bot"** - Starts the trading bot
2. **Monitor trades** - See active trades in real-time
3. **Adjust settings** - Click "⚙ Settings" to change configuration
4. **Test signals** - Click "🧪 Test Signal" to test parsing
5. **View logs** - Click "Logs" tab to see system logs

## 📊 Dashboard Features

- ✅ **Real-time monitoring** - Live updates every 5 seconds
- ✅ **Account overview** - Balance, equity, profit/loss
- ✅ **Trade management** - View and close trades
- ✅ **Configuration** - Change settings on-the-fly
- ✅ **Signal testing** - Test if signals parse correctly
- ✅ **System logs** - View recent log entries
- ✅ **WebSocket updates** - Instant notifications

## 🔧 Troubleshooting

### Dashboard won't start?

```bash
# Install dependencies again
pip install -r requirements.txt

# Try starting directly
python start_dashboard.py
```

### Can't connect to MT5?

1. Make sure MT5 terminal is running
2. Check your `.env` file has correct credentials
3. Verify MT5_PATH points to terminal64.exe
4. Enable "Allow DLL imports" in MT5 Tools → Options → Expert Advisors

### Telegram not connecting?

1. Verify API_ID and API_HASH are correct
2. Check phone number format (+1234567890)
3. Delete `evobot_session.session` file and restart
4. Make sure you have internet connection

## 📱 Remote Access

If running on a VPS/server, access from anywhere:

**http://YOUR_SERVER_IP:8080**

## 🛑 Stopping the Bot

- **In Dashboard**: Click "⏹ Stop Bot"
- **In Terminal**: Press `CTRL+C`

## 📚 More Information

- **Full Guide**: See `DASHBOARD_GUIDE.md`
- **API Docs**: http://localhost:8080/docs
- **Project README**: See `README.md`

## ⚠️ Important

- 🔴 **Test on demo account first**
- 🔴 **Start with small lot sizes**
- 🔴 **Monitor regularly**
- 🔴 **Never share your .env file**

---

**Need help?** Check the logs in the dashboard or review `logs/system.log`
