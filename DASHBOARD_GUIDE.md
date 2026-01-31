# 🚀 EvoBot Web Dashboard - Quick Start Guide

## ✅ Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.8+ installed
- ✅ MetaTrader 5 installed (if trading)
- ✅ Telegram API credentials
- ✅ `.env` file configured

## 📦 Installation Steps

### 1. Install Dependencies

```bash
# Navigate to project directory
cd /home/ubuntu/personal/evobot

# Install/upgrade dependencies
pip install -r requirements.txt
```

### 2. Verify Configuration

Check your `.env` file has these settings:

```env
# Telegram
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
SIGNAL_CHANNELS=channel1,channel2

# MT5
MT5_SERVER=YourBroker-Server
MT5_LOGIN=12345678
MT5_PASSWORD=your_password

# Trading
DEFAULT_LOT_SIZE=0.01
MAX_SPREAD_PIPS=5.0
MAX_DAILY_DRAWDOWN=5.0
MAX_OPEN_TRADES=10
```

## 🎯 Starting the Dashboard

### Option 1: Simple Start (Recommended)

```bash
python start_dashboard.py
```

### Option 2: Direct Start

```bash
python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8080
```

### Option 3: Development Mode (Auto-reload)

```bash
uvicorn dashboard.app:app --host 0.0.0.0 --port 8080 --reload
```

## 🌐 Accessing the Dashboard

Once started, open your browser and go to:

- **Dashboard**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Alternative API Docs**: http://localhost:8080/redoc

### Remote Access (VPS/Server)

If running on a VPS, replace `localhost` with your server IP:
- http://YOUR_SERVER_IP:8080

## 🎮 Using the Dashboard

### 1. Start the Bot

1. Click the **"▶ Start Bot"** button
2. Wait for connections (Telegram + MT5)
3. Status badges will turn green when connected

### 2. Monitor Trades

- **Active Trades Tab**: See all open positions in real-time
- **Trade History Tab**: Review closed trades
- **Logs Tab**: View system logs

### 3. Configure Settings

1. Click **"⚙ Settings"** button
2. Adjust:
   - Default lot size
   - Max spread
   - Max daily drawdown
   - Max open trades
3. Click **"💾 Save Configuration"**

### 4. Test Signal Parser

1. Click **"🧪 Test Signal"** button
2. Paste a signal message
3. Click **"🧪 Test Parse"**
4. See if it parses correctly

### 5. Manual Trade Control

- Click **"Close"** button on any active trade to close it manually
- Real-time P/L updates every 5 seconds

## 📊 Dashboard Features

### Real-Time Updates
- ✅ WebSocket connection for instant updates
- ✅ Auto-refresh every 5 seconds
- ✅ Live P/L tracking
- ✅ Connection status monitoring

### Account Overview
- 💰 Balance, Equity, Margin
- 📈 Current profit/loss
- 📊 Today's statistics
- 🎯 Win rate tracking

### Trade Management
- 📈 View all active trades
- ❌ Close trades manually
- 📜 Trade history
- 💹 Real-time P/L updates

### Configuration
- ⚙️ Change settings on-the-fly
- 🧪 Test signal parsing
- 📋 View system logs
- 🔔 Real-time notifications

## 🔧 Troubleshooting

### Dashboard Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Can't Connect to MT5

**Error**: MT5 status shows "Disconnected"

**Solutions**:
1. Ensure MT5 terminal is running
2. Check `.env` file has correct MT5 credentials
3. Verify MT5_PATH points to terminal64.exe
4. Enable "Allow DLL imports" in MT5 settings

### Telegram Not Connecting

**Error**: Telegram status shows "Disconnected"

**Solutions**:
1. Verify TELEGRAM_API_ID and TELEGRAM_API_HASH
2. Check phone number format (+1234567890)
3. Delete `evobot_session.session` and re-authenticate
4. Check internet connection

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn dashboard.app:app --host 0.0.0.0 --port 8081
```

### WebSocket Not Connecting

**Error**: WebSocket connection fails

**Solutions**:
1. Check browser console for errors
2. Ensure no firewall blocking WebSocket
3. Try refreshing the page
4. Check if dashboard is running

## 🔒 Security Notes

### Production Deployment

If deploying to production:

1. **Use HTTPS**: Set up SSL/TLS certificate
2. **Add Authentication**: Implement login system
3. **Firewall**: Restrict access to dashboard port
4. **Environment Variables**: Never commit `.env` file
5. **Strong Passwords**: Use strong MT5 and API credentials

### Recommended: Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 📱 Mobile Access

The dashboard is responsive and works on mobile devices:
- Access via mobile browser
- Same URL: http://YOUR_SERVER_IP:8080
- Touch-friendly interface

## 🚀 Advanced Usage

### Run as Background Service (Linux)

Create systemd service:

```bash
sudo nano /etc/systemd/system/evobot-dashboard.service
```

Add:

```ini
[Unit]
Description=EvoBot Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/personal/evobot
ExecStart=/usr/bin/python3 /home/ubuntu/personal/evobot/start_dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable evobot-dashboard
sudo systemctl start evobot-dashboard
sudo systemctl status evobot-dashboard
```

### Run with Screen (Simple Background)

```bash
# Start screen session
screen -S evobot-dashboard

# Run dashboard
python start_dashboard.py

# Detach: Press Ctrl+A then D

# Reattach later
screen -r evobot-dashboard
```

## 📊 API Endpoints

The dashboard provides REST API endpoints:

- `GET /api/status` - Bot status and stats
- `POST /api/bot/start` - Start the bot
- `POST /api/bot/stop` - Stop the bot
- `GET /api/trades` - Get all trades
- `POST /api/trades/{id}/close` - Close a trade
- `POST /api/signal/test` - Test signal parsing
- `POST /api/config/update` - Update configuration
- `GET /api/logs` - Get system logs

Full API documentation: http://localhost:8080/docs

## 🎯 Next Steps

1. ✅ Start the dashboard
2. ✅ Test signal parsing
3. ✅ Configure settings
4. ✅ Start the bot
5. ✅ Monitor trades
6. ✅ Review logs

## 💡 Tips

- **Test First**: Use demo account before live trading
- **Monitor Regularly**: Check dashboard daily
- **Review Logs**: Check logs tab for errors
- **Backup Config**: Save your `.env` file
- **Start Small**: Begin with small lot sizes
- **Stay Updated**: Keep dependencies updated

## 📞 Support

If you encounter issues:

1. Check logs in the dashboard
2. Review system logs: `logs/system.log`
3. Check error logs: `logs/errors.log`
4. Verify all dependencies installed
5. Ensure MT5 and Telegram are connected

## ⚠️ Important Reminders

- 🔴 **Never share your `.env` file**
- 🔴 **Test on demo account first**
- 🔴 **Monitor the bot regularly**
- 🔴 **Start with small lot sizes**
- 🔴 **Understand the risks of automated trading**

---

**Ready to trade? Start the dashboard and click "▶ Start Bot"!** 🚀
