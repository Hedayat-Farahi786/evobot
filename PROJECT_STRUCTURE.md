# 📁 EvoBot Project Structure

## 🎯 New Files Created for Web Dashboard

```
evobot/
│
├── 🌐 dashboard/                    # Web Dashboard (NEW)
│   ├── app.py                       # FastAPI application
│   └── templates/
│       └── dashboard.html           # Modern web interface
│
├── 🚀 start_dashboard.py            # Dashboard launcher (NEW)
├── 🚀 run_dashboard.sh              # One-click startup script (NEW)
│
├── 📚 START_HERE.md                 # Quick start guide (NEW)
├── 📚 DASHBOARD_GUIDE.md            # Complete dashboard guide (NEW)
├── 📚 DASHBOARD_COMPLETE.md         # Setup summary (NEW)
│
├── 📦 requirements.txt              # Updated with web dependencies
│
├── 🤖 Core Bot Files (Existing)
│   ├── broker/                      # MT5 integration
│   ├── config/                      # Configuration
│   ├── core/                        # Trade & risk management
│   ├── models/                      # Data models
│   ├── parsers/                     # Signal parsing
│   ├── telegram/                    # Telegram listener
│   ├── utils/                       # Utilities
│   └── main.py                      # Original CLI bot
│
└── ⚙️ Configuration
    ├── .env                         # Your credentials
    └── .env.example                 # Template
```

## 🎯 Two Ways to Run EvoBot

### 1️⃣ Web Dashboard (NEW - Recommended)
```bash
./run_dashboard.sh
# or
python start_dashboard.py
```
- ✅ Web interface at http://localhost:8080
- ✅ Control everything from browser
- ✅ Real-time monitoring
- ✅ Easy configuration
- ✅ Mobile friendly

### 2️⃣ Command Line (Original)
```bash
python main.py
```
- ✅ Runs in terminal
- ✅ No web interface
- ✅ Lightweight
- ✅ Good for background service

## 🌐 Dashboard URLs

Once started:
- **Main Dashboard**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Alternative API Docs**: http://localhost:8080/redoc

## 📊 Dashboard Pages

### Main Dashboard (/)
- Control panel (Start/Stop bot)
- Account overview
- Today's statistics
- Configuration display
- Active trades table
- Trade history
- System logs

### API Docs (/docs)
- Interactive API documentation
- Test endpoints directly
- See request/response formats

## 🔌 API Endpoints

```
GET  /api/status              # Bot status and stats
POST /api/bot/start           # Start the bot
POST /api/bot/stop            # Stop the bot
GET  /api/trades              # Get all trades
GET  /api/trades/{id}         # Get specific trade
POST /api/trades/{id}/close   # Close a trade
POST /api/signal/test         # Test signal parsing
POST /api/config/update       # Update configuration
GET  /api/logs                # Get system logs
WS   /ws                      # WebSocket for real-time updates
```

## 🎮 Dashboard Features

### Control Panel
- ▶️ Start Bot button
- ⏹️ Stop Bot button
- ⚙️ Settings modal
- 🧪 Test Signal modal

### Real-Time Monitoring
- 💰 Account balance, equity, margin
- 📊 Today's trades, win rate, P/L
- 📈 Active trades with live P/L
- 🔔 WebSocket notifications

### Trade Management
- View all active trades
- Close trades manually
- See real-time profit/loss
- Review trade history

### Configuration
- Change lot size
- Adjust max spread
- Set max drawdown
- Limit open trades

### Signal Testing
- Paste signal message
- Test parsing
- See extracted data
- Verify before trading

### System Logs
- View recent logs
- Filter by level
- Real-time updates

## 🚀 Quick Start Commands

### First Time Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure credentials
nano .env

# 3. Start dashboard
./run_dashboard.sh
```

### Daily Use
```bash
# Start dashboard
./run_dashboard.sh

# Open browser
# http://localhost:8080

# Click "Start Bot"
```

### Background Service
```bash
# Using screen
screen -S evobot
./run_dashboard.sh
# Press Ctrl+A then D to detach

# Using systemd (see DASHBOARD_GUIDE.md)
sudo systemctl start evobot-dashboard
```

## 📱 Access Methods

### Local Access
```
http://localhost:8080
```

### Remote Access (VPS)
```
http://YOUR_SERVER_IP:8080
```

### Mobile Access
```
http://YOUR_SERVER_IP:8080
(Same URL, responsive design)
```

## 🔧 Configuration Files

### .env (Your Credentials)
```env
# Telegram
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abc123...
TELEGRAM_PHONE=+1234567890
SIGNAL_CHANNELS=channel1,channel2

# MT5
MT5_SERVER=Broker-Server
MT5_LOGIN=12345678
MT5_PASSWORD=yourpassword

# Trading
DEFAULT_LOT_SIZE=0.01
MAX_SPREAD_PIPS=5.0
MAX_DAILY_DRAWDOWN=5.0
MAX_OPEN_TRADES=10
```

### config/settings.py (Code Configuration)
- Telegram settings
- Broker settings
- Trading parameters
- Risk management
- Logging configuration

## 📊 Data Storage

### Runtime Data
```
data/
└── trades.json              # Persisted trade state
```

### Logs
```
logs/
├── system.log               # General logs
├── trades.log               # Trade events
└── errors.log               # Error logs
```

### Session
```
evobot_session.session       # Telegram session
```

## 🎯 Workflow

### 1. Start Dashboard
```bash
./run_dashboard.sh
```

### 2. Open Browser
```
http://localhost:8080
```

### 3. Start Bot
- Click "▶ Start Bot"
- Wait for connections
- Status badges turn green

### 4. Monitor
- Watch active trades
- Check P/L updates
- Review logs

### 5. Manage
- Close trades manually
- Adjust settings
- Test signals

### 6. Stop Bot
- Click "⏹ Stop Bot"
- Or press Ctrl+C in terminal

## 💡 Tips

### Development
- Use `--reload` flag for auto-reload
- Check `/docs` for API testing
- Monitor logs tab for errors

### Production
- Run as systemd service
- Use reverse proxy (nginx)
- Enable HTTPS
- Add authentication
- Configure firewall

### Monitoring
- Check dashboard daily
- Review logs regularly
- Monitor drawdown
- Track win rate

### Testing
- Test on demo account first
- Use signal tester
- Start with small lots
- Monitor closely

## 🔒 Security

### Local Development
- Dashboard accessible only on localhost
- No authentication required

### Production Deployment
- Add authentication system
- Use HTTPS/SSL
- Configure firewall rules
- Restrict IP access
- Use strong passwords

## 📞 Support Files

- `START_HERE.md` - Quick 3-step guide
- `DASHBOARD_GUIDE.md` - Complete guide
- `DASHBOARD_COMPLETE.md` - Setup summary
- `README.md` - Full project documentation

## ✅ Checklist

Before starting:
- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured
- [ ] MT5 terminal running (if trading)
- [ ] Telegram credentials obtained

To start:
- [ ] Run `./run_dashboard.sh`
- [ ] Open http://localhost:8080
- [ ] Click "▶ Start Bot"
- [ ] Verify connections (green badges)
- [ ] Monitor trades

## 🎉 You're All Set!

Everything is ready. Just run:

```bash
./run_dashboard.sh
```

Then open your browser to http://localhost:8080 and start trading! 🚀
