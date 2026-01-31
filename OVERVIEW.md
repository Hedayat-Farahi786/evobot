# 🤖 EvoBot - Complete Telegram Copy Trading Bot

## 📦 What You've Got

A **professional, production-ready** Telegram-to-MT5 copy trading bot with:

- ✅ **5,000+ lines** of production-grade Python code
- ✅ **Real-time Telegram** signal capture (Telethon)
- ✅ **Advanced signal parsing** (handles multiple formats)
- ✅ **MT5 integration** (market + pending orders)
- ✅ **Smart trade management** (partial closes, breakeven)
- ✅ **Risk management** (spread, drawdown, news filtering)
- ✅ **Telegram notifications** (all trade events)
- ✅ **Comprehensive logging** (structured JSON)
- ✅ **Trade persistence** (survives restarts)
- ✅ **Auto-recovery** (reconnects automatically)
- ✅ **Scalping-ready** (1-second monitoring)
- ✅ **Complete documentation** (README, guides, examples)

## 🚀 Quick Start (3 Steps)

```bash
# 1. Setup environment
./setup.sh

# 2. Configure credentials
nano .env  # Add Telegram + MT5 credentials

# 3. Run the bot
python main.py
```

## 📁 What's Included

```
evobot/
├── 📄 Main Application
│   └── main.py                    # Entry point, orchestrates everything
│
├── 🔌 Broker Integration
│   └── broker/mt5_client.py       # Complete MT5 API wrapper
│
├── 📡 Telegram Integration
│   └── telegram/listener.py       # Real-time message listener
│
├── 🧠 Core Logic
│   ├── core/trade_manager.py      # Trade lifecycle management
│   ├── core/risk_manager.py       # Risk checks and filtering
│   └── core/notifier.py           # Telegram notifications
│
├── 🔍 Signal Processing
│   └── parsers/signal_parser.py   # Robust signal parser
│
├── 📊 Data Models
│   └── models/trade.py            # Trade, Signal, Account models
│
├── ⚙️ Configuration
│   ├── config/settings.py         # All configuration classes
│   └── .env.example               # Configuration template
│
├── 🛠️ Utilities
│   ├── utils/logging_utils.py     # Logging setup
│   ├── test_parser.py             # Parser testing tool
│   └── verify_install.py          # Installation checker
│
├── 📚 Documentation
│   ├── README.md                  # Complete documentation (60+ pages)
│   ├── QUICKSTART.md              # Quick reference guide
│   └── PROJECT_SUMMARY.md         # This overview
│
└── 🚀 Deployment
    ├── setup.sh                   # Quick setup script
    ├── evobot.service             # Systemd service template
    ├── requirements.txt           # Python dependencies
    └── .gitignore                 # Git ignore rules
```

## 🎯 Key Features Explained

### 1. Signal Parser (parsers/signal_parser.py)
**Handles multiple formats:**
```
✅ XAUUSD BUY @ 2050.00 SL: 2045 TP1: 2055 TP2: 2060
✅ 🟢 GOLD LONG Entry: 2050-2052 Stop: 2045 Targets: 2055/2060/2065
✅ GBPUSD SELL NOW SL 1.2550 TP 1.2450
✅ ✅ XAUUSD TP1 HIT
✅ 🔒 Move GOLD to Breakeven
```

### 2. Trade Manager (core/trade_manager.py)
**Complete lifecycle:**
```
Signal → Risk Check → Execute → Monitor → TP1 (50% close + BE) 
→ TP2 (30% close) → TP3 (20% close) → Log Results
```

### 3. Risk Manager (core/risk_manager.py)
**Multiple safety layers:**
- ❌ Skip if spread > 5 pips
- ❌ Skip if daily drawdown > 5%
- ❌ Skip if max trades reached
- ❌ Skip during high-impact news
- ❌ Skip outside trading hours

### 4. MT5 Client (broker/mt5_client.py)
**Full broker control:**
- Place market orders
- Place pending orders
- Modify positions (SL/TP)
- Partial closes
- Real-time position tracking
- Spread checking
- Symbol info caching

### 5. Notifier (core/notifier.py)
**Stay informed:**
```
🟢 Trade Opened: XAUUSD BUY @ 2050.00
🎯 TP1 Hit! Closed 50%, moved to BE
🏆 TP3 Hit! Trade fully closed
📊 Daily Summary: 10 trades, 70% win rate
```

## ⚙️ Configuration Overview

### .env File (Your Credentials)
```env
# Telegram
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abc123...
TELEGRAM_PHONE=+1234567890
SIGNAL_CHANNELS=channel1,channel2

# MT5
MT5_SERVER=YourBroker-Server
MT5_LOGIN=12345678
MT5_PASSWORD=yourpassword
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# Trading
DEFAULT_LOT_SIZE=0.01
MAX_SPREAD_PIPS=5.0
MAX_DAILY_DRAWDOWN=5.0
```

### config/settings.py (Behavior)
```python
# Partial close percentages
tp1_close_percent = 0.5  # 50% at TP1
tp2_close_percent = 0.3  # 30% at TP2
tp3_close_percent = 0.2  # 20% at TP3

# Auto-breakeven
move_sl_to_breakeven_at_tp1 = True
breakeven_offset_pips = 1.0

# Risk limits
max_open_trades = 10
max_daily_drawdown_percent = 5.0
avoid_high_impact_news = True
```

## 🔄 How It Works (Step by Step)

1. **Bot starts** → Connects to Telegram and MT5
2. **Listens** → Monitors configured channels 24/7
3. **Signal received** → "XAUUSD BUY @ 2050 SL 2045 TP 2055"
4. **Parses** → Extracts symbol, direction, prices
5. **Risk checks** → Spread OK? Drawdown OK? News OK?
6. **Executes** → Places market order on MT5
7. **Monitors** → Checks price every second
8. **TP1 hit** → Closes 50%, moves SL to entry + 1 pip
9. **TP2 hit** → Closes 30% more
10. **TP3 hit** → Closes remaining 20%
11. **Notifies** → Sends Telegram alert at each step
12. **Logs** → Records everything to JSON files
13. **Persists** → Saves state (survives restarts)

## 📊 Example Trade Flow

```
[12:00:00] 📨 Signal received: XAUUSD BUY
[12:00:01] ✅ Risk checks passed
[12:00:02] 🟢 Order placed @ 2050.00 (ticket #123456)
[12:00:02] 📊 Monitoring position...
[12:05:30] 🎯 TP1 hit @ 2055.00
[12:05:31] ✅ Closed 0.005 lots (50%)
[12:05:32] 🔒 SL moved to breakeven @ 2050.01
[12:08:15] 🎯 TP2 hit @ 2060.00
[12:08:16] ✅ Closed 0.003 lots (30%)
[12:10:45] 🏆 TP3 hit @ 2065.00
[12:10:46] ✅ Closed 0.002 lots (20%)
[12:10:47] 💰 Trade closed. P&L: +$150.00
```

## 🛡️ Safety & Reliability

### Built-in Protections
- ✅ Max daily drawdown (stops trading if losses exceed limit)
- ✅ Spread filtering (skips trades with high spread)
- ✅ News avoidance (skips trades during high-impact events)
- ✅ Max open trades (prevents overexposure)
- ✅ Trading hours (only trade during specified hours)
- ✅ Auto-reconnect (handles Telegram/MT5 disconnections)
- ✅ Error recovery (retries failed operations)
- ✅ Trade persistence (state survives crashes/restarts)

### Logging & Monitoring
```bash
# Real-time logs
tail -f logs/system.log | python -m json.tool
tail -f logs/trades.log | python -m json.tool

# Check trade data
cat data/trades.json | python -m json.tool

# Telegram notifications
All events sent to your notification channel
```

## 🧪 Testing Before Live Trading

### 1. Test Signal Parser
```bash
python test_parser.py
```
**Tests parsing of various signal formats**

### 2. Verify Installation
```bash
python verify_install.py
```
**Checks all components are properly configured**

### 3. Demo Account Testing
**Always test on demo account first!**
1. Use demo MT5 account
2. Set small lot sizes (0.01)
3. Monitor for 1-2 weeks
4. Review logs and results
5. Adjust configuration as needed

## 📈 Performance Tuning

### For Scalping (High Frequency)
```python
# config/settings.py
entry_zone_tolerance = 2.0  # Tighter entry
max_spread_pips = 2.0       # Lower spread limit
# Position check: Already 1 second
```

### For Swing Trading
```python
# config/settings.py
entry_zone_tolerance = 10.0  # Wider entry
max_spread_pips = 10.0       # Higher spread OK
# Could increase check interval in trade_manager.py
```

### For Conservative Trading
```python
# .env
MAX_DAILY_DRAWDOWN=2.0      # Stricter limit
MAX_OPEN_TRADES=5           # Fewer concurrent trades
DEFAULT_LOT_SIZE=0.01       # Smaller positions
```

## 🚀 Production Deployment

### VPS Deployment (Recommended)
```bash
# 1. Choose VPS near broker (low latency)
# 2. Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv

# 3. Clone and setup
git clone <your-repo>
cd evobot
./setup.sh

# 4. Configure
nano .env

# 5. Install as service
sudo cp evobot.service /etc/systemd/system/
sudo systemctl enable evobot
sudo systemctl start evobot

# 6. Monitor
sudo systemctl status evobot
sudo journalctl -u evobot -f
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Complete documentation (60+ pages) |
| **QUICKSTART.md** | Quick reference guide |
| **PROJECT_SUMMARY.md** | This overview |
| **.env.example** | Configuration template |
| **evobot.service** | Systemd service template |

## 🎓 Learning Path

1. **Read QUICKSTART.md** - Get familiar with basics
2. **Run verify_install.py** - Check everything is ready
3. **Run test_parser.py** - Understand signal parsing
4. **Configure .env** - Add your credentials
5. **Read README.md** - Deep dive into features
6. **Test on demo** - Validate with demo account
7. **Monitor logs** - Understand what's happening
8. **Adjust config** - Tune for your needs
9. **Go live** - Start with small lots
10. **Optimize** - Refine based on results

## ⚠️ Important Reminders

1. **Test on demo first** - Never skip this step
2. **Start small** - Use 0.01 lots initially
3. **Monitor regularly** - Check logs and notifications
4. **Understand risks** - Trading involves substantial risk
5. **Keep backups** - Backup .env and data/trades.json
6. **Update regularly** - Keep dependencies updated
7. **Review logs** - Weekly log review recommended
8. **Adjust limits** - Tune risk parameters based on results

## 🆘 Getting Help

### Check These First
1. **Logs** - `logs/errors.log` and `logs/system.log`
2. **README.md** - Comprehensive troubleshooting section
3. **QUICKSTART.md** - Common issues and solutions

### Provide When Asking for Help
- Error logs (last 50 lines)
- Configuration (without passwords!)
- Signal example that failed
- Python version
- MT5 version
- Operating system

## 🎉 You're Ready!

You now have a **complete, professional copy trading bot** that:

✅ Listens to Telegram 24/7
✅ Parses signals intelligently
✅ Executes trades automatically
✅ Manages risk proactively
✅ Handles partial closes
✅ Moves to breakeven
✅ Notifies you of everything
✅ Logs everything
✅ Recovers from errors
✅ Runs reliably 24/7

## 🚀 Next Steps

```bash
# 1. Verify installation
python verify_install.py

# 2. Test parser
python test_parser.py

# 3. Configure
nano .env

# 4. Start bot
python main.py

# 5. Monitor
tail -f logs/system.log
```

## 💡 Pro Tips

1. **Start conservative** - Use small lots and tight risk limits
2. **Monitor first week** - Check logs daily
3. **Review weekly** - Analyze trade statistics
4. **Backup regularly** - Save configuration and trade data
5. **Test changes** - Use demo account for config changes
6. **Keep learning** - Review logs to understand bot behavior
7. **Stay informed** - Monitor Telegram notifications
8. **Optimize gradually** - Make small adjustments based on data

---

**Built for traders who demand reliability, performance, and professional-grade automation.**

**Good luck with your trading! 🚀📈💰**
