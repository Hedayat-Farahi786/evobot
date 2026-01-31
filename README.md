# EvoBot - Advanced Telegram-to-Broker Copy Trading Bot

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Firebase](https://img.shields.io/badge/Firebase-Realtime%20DB-orange.svg)](https://firebase.google.com/)

EvoBot is a professional-grade, high-frequency copy trading bot that listens to Telegram trading signals and automatically executes them on MetaTrader 5 (MT5). Built for scalping and high-frequency trading with support for partial closes, breakeven management, and comprehensive risk controls.

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
  - [Environment Variables](#environment-variables)
  - [Telegram Setup](#telegram-setup)
  - [MT5 Setup](#mt5-setup)
  - [Firebase Setup](#firebase-setup)
  - [Dashboard Setup](#dashboard-setup)
- [Usage](#-usage)
- [Web Dashboard](#-web-dashboard)
- [Signal Formats](#-signal-formats)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Production Deployment](#-production-deployment)
- [License](#-license)

---

## 🚀 Features

### Real-Time Signal Processing
- **Telethon-based** real-time Telegram message listener
- **Auto-reconnect** with exponential backoff
- **Multi-channel monitoring** with configurable sources
- **Instant signal parsing** with regex + structured parsing + fallback checks
- Handles **emojis, formatting variations**, and multiple signal formats

### Advanced Signal Parser
- Supports **multiple symbols**: XAUUSD, GBPUSD, EURUSD, USDJPY, and more
- Recognizes **symbol aliases** (GOLD, CABLE, FIBER, etc.)
- Parses **entry zones** (single price or range)
- Extracts **multiple TP levels** (TP1, TP2, TP3)
- Detects **signal updates**: TP hit, SL hit, Breakeven, Close
- **Robust error handling** with detailed parse error reporting

### Smart Trade Management
- **Partial closing** at multiple TP levels (configurable percentages)
- **Auto-breakeven** when TP1 is hit
- **Dynamic lot sizing** with risk-based calculations
- **Trade state persistence** (survives restarts)
- **Position monitoring** at 1-second intervals (scalping-ready)
- Tracks **P&L, swap, commission** in real-time

### MT5 Integration
- **Direct MT5 API** integration via MetaTrader5 Python package
- **Market orders** with slippage control
- **Pending orders** (Buy/Sell Limit/Stop)
- **Position modification** (SL/TP updates)
- **Partial closes** for TP management
- **Retry logic** with exponential backoff
- **Symbol info caching** for performance

### Web Dashboard
- **Real-time monitoring** with Firebase Realtime Database
- **Live trade tracking** with instant updates
- **Account statistics** (balance, equity, margin, P&L)
- **Signal channel management** with photo support
- **Responsive design** for desktop and mobile
- **Dark/Light theme** support

### Risk Management
- **Spread filtering** (skip trades if spread too high)
- **Daily drawdown limits** (auto-stop trading)
- **Max open trades** limit
- **Trading hours** restrictions
- **News calendar integration** (avoid high-impact events)
- **Weekend close protection**
- **Risk-based lot sizing**

### Notifications
- **Telegram notifications** for all trade events
- Trade opened/closed alerts
- TP hit notifications
- Breakeven alerts
- Risk alerts
- Daily summary reports

### Reliability & Performance
- **24/7 operation** ready (designed for VPS)
- **Auto-reconnect** for Telegram and MT5
- **Trade persistence** (JSON-based state storage)
- **Comprehensive logging** (structured JSON logs)
- **Error recovery** mechanisms
- **High-frequency ready** (20-50+ trades per hour)

---

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Hedayat-Farahi786/evobot.git
cd evobot

# 2. Run setup script
./setup.sh

# 3. Configure environment
cp .env.example .env
nano .env  # Edit with your credentials

# 4. Start the dashboard
python start_dashboard.py

# 5. Open browser
# Navigate to http://localhost:8080
```

---

## 📋 Requirements

- **Python 3.8+**
- **MetaTrader 5** terminal (Windows or Wine on Linux)
- **Telegram API** credentials
- **MT5 broker** account
- **Firebase project** (for real-time features)

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Hedayat-Farahi786/evobot.git
cd evobot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements_firebase.txt  # For Firebase support
```

### 4. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
cp .env.firebase.example .env.firebase  # Optional: Firebase config
cp .env.security.example .env.security  # Optional: Security config
```

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` with your configuration:

```env
# ============================================
# TELEGRAM CONFIGURATION
# ============================================
# Get these from https://my.telegram.org/apps
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
TELEGRAM_SESSION=evobot_session

# Comma-separated list of channel usernames or IDs to monitor
SIGNAL_CHANNELS=channel1,channel2,-1001234567890

# Channel to send trade notifications (optional)
NOTIFICATION_CHANNEL=your_notification_channel

# ============================================
# MT5 BROKER CONFIGURATION
# ============================================
BROKER_TYPE=mt5
MT5_SERVER=YourBroker-Server
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# ============================================
# TRADING CONFIGURATION
# ============================================
DEFAULT_LOT_SIZE=0.01
MAX_SPREAD_PIPS=5.0
MAX_DAILY_DRAWDOWN=5.0
MAX_OPEN_TRADES=10

# ============================================
# DASHBOARD CONFIGURATION
# ============================================
DASHBOARD_ENABLED=true
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DASHBOARD_SECRET=change-this-secret-key-in-production

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
LOG_DIR=logs
```

### Telegram Setup

1. Visit https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application (any name/description)
4. Copy `api_id` and `api_hash`
5. Add them to your `.env` file:

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+1234567890
```

**First Run Authentication:**
On first run, you'll be prompted to enter the verification code sent to your Telegram app.

### MT5 Setup

1. **Install MetaTrader 5** from your broker
2. **Get server name**: Tools → Options → Server
3. **Enable automation**:
   - Tools → Options → Expert Advisors
   - ✅ Allow automated trading
   - ✅ Allow DLL imports
4. **Add to `.env`**:

```env
MT5_SERVER=YourBroker-Demo
MT5_LOGIN=12345678
MT5_PASSWORD=your_secure_password
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

### Firebase Setup

Firebase enables real-time data synchronization across all dashboard instances.

#### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add Project"
3. Name it (e.g., `evobot-trading`)
4. Enable/disable Google Analytics (optional)

#### 2. Enable Realtime Database

1. Navigate to **Build > Realtime Database**
2. Click **Create Database**
3. Choose location closest to your server
4. Start in **Test Mode** for development

#### 3. Get Service Account Credentials

1. Go to **Project Settings** (gear icon)
2. Navigate to **Service Accounts** tab
3. Click **Generate New Private Key**
4. Download the JSON file

#### 4. Configure Environment

Extract values from the downloaded JSON and add to `.env`:

```env
# Firebase Configuration
FIREBASE_PRIVATE_KEY_ID=abc123def456...
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBg...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=123456789012345678901
```

⚠️ **Important**: Keep the `\n` characters in the private key!

#### 5. Database Rules (Production)

```json
{
  "rules": {
    ".read": "auth != null",
    ".write": "auth != null"
  }
}
```

### Dashboard Setup

The dashboard is pre-configured with Firebase integration. The Firebase config in the dashboard HTML uses:

```javascript
const firebaseConfig = {
    apiKey: "AIzaSyClrXVHM5xP4FqZKsjaqN7VEXAsGwNeax4",
    authDomain: "evobot-8.firebaseapp.com",
    databaseURL: "https://evobot-8-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "evobot-8",
    storageBucket: "evobot-8.firebasestorage.app",
    messagingSenderId: "349123654411",
    appId: "1:349123654411:web:afc01b90aa06984c74e80e",
    measurementId: "G-Q1BRXP7KRE"
};
```

### Security Configuration (Optional)

For production deployments, configure `.env.security`:

```env
# JWT & Authentication
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
TOKEN_EXPIRE_MINUTES=1440
ADMIN_PASSWORD=Admin@123!

# CORS & Network Security
CORS_ORIGINS=https://yourdomain.com
TRUSTED_HOSTS=yourdomain.com,*.yourdomain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Account Security
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
```

Generate a secure JWT secret:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🚀 Usage

### Start the Bot with Dashboard

```bash
# Activate virtual environment
source venv/bin/activate

# Start dashboard (includes bot controls)
python start_dashboard.py
```

### Start Bot Only (No Dashboard)

```bash
python main.py
```

### Using the Dashboard

1. Open http://localhost:8080 in your browser
2. Click **"▶ Start Bot"** to begin
3. Wait for Telegram and MT5 connections (status badges turn green)
4. Monitor trades in real-time

---

## 🖥️ Web Dashboard

### Features

- **Real-time Trade Monitoring**: See all open positions with live P&L updates
- **Account Overview**: Balance, equity, margin, and daily profit/loss
- **Signal Channel Management**: Add/remove Telegram channels with photos
- **Activity Feed**: Recent trade events and system notifications
- **Settings Panel**: Configure trading parameters on-the-fly
- **Responsive Design**: Works on desktop, tablet, and mobile

### Access Points

| URL | Description |
|-----|-------------|
| `http://localhost:8080` | Main Dashboard |
| `http://localhost:8080/docs` | API Documentation (Swagger) |
| `http://localhost:8080/redoc` | API Documentation (ReDoc) |

### Remote Access

For VPS/server deployment, replace `localhost` with your server IP:
```
http://YOUR_SERVER_IP:8080
```

---

## 📊 Signal Formats

EvoBot can parse various signal formats:

### Basic Signal
```
XAUUSD BUY
Entry: 2050.00
SL: 2045.00
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00
```

### Signal with Entry Zone
```
🟢 GOLD BUY
Entry Zone: 2050.00 - 2052.00
Stop Loss: 2045.00
Take Profit 1: 2055.00
Take Profit 2: 2060.00
Take Profit 3: 2065.00
Lot: 0.02
```

### Signal with Emojis
```
📈 GBPUSD LONG
@ 1.2500
SL: 1.2450
🎯 TP1: 1.2550
🎯 TP2: 1.2600
🎯 TP3: 1.2650
```

### Update Signals
```
✅ XAUUSD TP1 HIT
🔒 Move SL to Breakeven
❌ GBPUSD SL HIT
🏆 EURUSD TP3 REACHED
Close USDJPY
```

### Supported Symbols & Aliases

| Symbol | Aliases |
|--------|---------|
| XAUUSD | GOLD |
| GBPUSD | CABLE |
| EURUSD | FIBER |
| USDJPY | GOPHER |
| AUDUSD | AUSSIE |
| USDCAD | LOONIE |

---

## 📁 Project Structure

```
evobot/
├── broker/                 # MT5 broker integration
│   ├── __init__.py
│   ├── mt5_client.py       # MT5 API client
│   └── metaapi_client.py   # MetaAPI client (alternative)
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py         # Settings and config classes
├── core/                   # Core business logic
│   ├── __init__.py
│   ├── auth.py             # Authentication
│   ├── firebase_auth.py    # Firebase authentication
│   ├── firebase_service.py # Firebase realtime service
│   ├── firebase_settings.py# Firebase settings sync
│   ├── trade_manager.py    # Trade lifecycle management
│   ├── risk_manager.py     # Risk management system
│   ├── notifier.py         # Notification system
│   ├── security.py         # Security utilities
│   └── telegram_auth.py    # Telegram authentication
├── dashboard/              # Web dashboard
│   ├── app.py              # FastAPI application
│   ├── dependencies.py     # Dependency injection
│   ├── state.py            # Application state
│   ├── routes/             # API routes
│   ├── static/             # Static assets
│   └── templates/          # HTML templates
├── models/                 # Data models
│   ├── __init__.py
│   └── trade.py            # Trade, Signal, Account models
├── parsers/                # Signal parsing
│   ├── __init__.py
│   └── signal_parser.py    # Telegram message parser
├── telegram/               # Telegram integration
│   ├── __init__.py
│   └── listener.py         # Telethon-based listener
├── utils/                  # Utilities
│   ├── __init__.py
│   └── logging_utils.py    # Logging setup
├── assets/                 # Static assets
│   └── logos/              # Logo images
├── data/                   # Persisted data (runtime)
├── logs/                   # Log files (runtime)
├── main.py                 # Main application entry point
├── start_dashboard.py      # Dashboard launcher
├── requirements.txt        # Python dependencies
├── requirements_firebase.txt # Firebase dependencies
├── .env.example            # Example environment file
├── .env.firebase.example   # Firebase config example
├── .env.security.example   # Security config example
└── README.md               # This file
```

---

## ⚙️ Trading Configuration

Edit `config/settings.py` or use environment variables:

- `DEFAULT_LOT_SIZE`: Default lot size for trades (0.01)
- `MAX_SPREAD_PIPS`: Maximum allowed spread (5.0 pips)
- `MAX_DAILY_DRAWDOWN`: Daily drawdown limit (5.0%)
- `MAX_OPEN_TRADES`: Maximum concurrent trades (10)
- `tp1_close_percent`: Percentage to close at TP1 (50%)
- `tp2_close_percent`: Percentage to close at TP2 (30%)
- `tp3_close_percent`: Percentage to close at TP3 (20%)

### Risk Management

- `avoid_high_impact_news`: Skip trades during high-impact news
- `news_blackout_minutes_before`: Minutes before news to stop (30)
- `news_blackout_minutes_after`: Minutes after news to stop (15)
- `trading_start_hour`: Start of trading hours UTC (0)
- `trading_end_hour`: End of trading hours UTC (24)
- `max_risk_percent_per_trade`: Max risk per trade (2.0%)

### Breakeven Settings

- `move_sl_to_breakeven_at_tp1`: Auto-move SL when TP1 hit (True)
- `breakeven_offset_pips`: Buffer above entry for breakeven (1.0 pip)

---

## 🔍 Troubleshooting

### Telegram Connection Issues

```bash
# Delete session file and re-authenticate
rm evobot_session.session
python main.py
```

- Verify `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` are correct
- Check phone number includes country code (e.g., `+1234567890`)
- Ensure you're not logged in from too many devices

### MT5 Connection Issues

- Ensure MT5 terminal is running
- Verify `MT5_PATH` points to `terminal64.exe`
- Check `MT5_SERVER`, `MT5_LOGIN`, and `MT5_PASSWORD`
- Enable "Allow DLL imports" and "Allow automated trading" in MT5

### Signal Not Parsing

```bash
# Test signal parser
python test_parser.py
```

- Check `logs/system.log` for parse errors
- Verify signal format matches expected patterns

### Dashboard Not Loading

```bash
# Check if port is in use
lsof -i :8080

# Kill process using port
fuser -k 8080/tcp

# Restart dashboard
python start_dashboard.py
```

### Firebase Connection Issues

- Verify Firebase credentials in `.env`
- Check database URL is correct
- Ensure database rules allow read/write
- Check network connectivity

---

## 📈 Trade Lifecycle

1. **Signal Received** → Telegram message captured
2. **Signal Parsed** → Extract symbol, direction, entry, SL, TPs
3. **Risk Checks** → Spread, drawdown, news, trading hours
4. **Order Execution** → Market or pending order placed
5. **Position Monitoring** → Real-time price monitoring (1s intervals)
6. **TP1 Hit** → Partial close (50%) + Move SL to breakeven
7. **TP2 Hit** → Partial close (30%)
8. **TP3 Hit** → Close remaining (20%)
9. **Trade Closed** → Log results, update statistics

## 🔍 Monitoring

### Logs

Logs are stored in the `logs/` directory:

- `system.log`: General system logs (JSON format)
- `trades.log`: Trade-specific events (JSON format)
- `errors.log`: Error logs only

### Log Example

```json
{
  "timestamp": "2026-01-28T12:34:56.789012",
  "level": "INFO",
  "logger": "evobot.trades",
  "message": "Trade Event: OPENED",
  "trade_id": "abc123",
  "symbol": "XAUUSD",
  "data": {
    "event": "OPENED",
    "ticket": 123456789,
    "entry_price": 2050.00,
    "lot_size": 0.01
  }
}
```

### Trade Persistence

Trades are persisted to `data/trades.json` and automatically loaded on restart.

---

## 🚀 Production Deployment

### VPS Setup (Recommended)

1. **Choose a VPS** near your broker's servers (low latency)
2. **Install Python 3.8+** and required packages
3. **Install MT5** (Windows VPS or Wine on Linux)
4. **Configure firewall** to allow ports 8080 (dashboard) and MT5
5. **Set up systemd service** for auto-start

### Systemd Service

Create `/etc/systemd/system/evobot.service`:

```ini
[Unit]
Description=EvoBot Trading System
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/evobot
Environment="PATH=/path/to/evobot/venv/bin"
ExecStart=/path/to/evobot/venv/bin/python start_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable evobot
sudo systemctl start evobot
sudo systemctl status evobot
```

### Log Rotation

Create `/etc/logrotate.d/evobot`:

```
/path/to/evobot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 your_user your_user
}
```

---

## 🛡️ Safety Features

- **Dry-run mode**: Test signal parsing without executing trades (coming soon)
- **Max drawdown protection**: Stops trading if daily drawdown exceeds limit
- **Spread filtering**: Skips trades with excessive spread
- **News avoidance**: Skips trades during high-impact news events
- **Auto-reconnect**: Handles Telegram/MT5 disconnections
- **Trade persistence**: Survives system restarts
- **Error recovery**: Retries failed operations

---

## ⚠️ Disclaimer

**IMPORTANT**: Trading forex, gold, and other financial instruments involves substantial risk of loss and is not suitable for all investors. This bot is provided for educational purposes only. The authors are not responsible for any financial losses incurred through the use of this software.

- **Test thoroughly** on a demo account before using real money
- **Start with small lot sizes** to validate the system
- **Monitor the bot** regularly, especially during the first weeks
- **Understand the risks** of automated trading
- **Never risk more** than you can afford to lose

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Support

For questions, issues, or feature requests, please [open an issue](https://github.com/Hedayat-Farahi786/evobot/issues) on GitHub.

---

## 🙏 Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) for Telegram integration
- [MetaTrader5](https://www.mql5.com/en/docs/integration/python_metatrader5) Python package
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Firebase](https://firebase.google.com/) for real-time database
- [Vue.js](https://vuejs.org/) for the dashboard frontend

---

**Built with ❤️ for traders who want to automate their copy trading.**
