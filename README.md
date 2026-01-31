# EvoBot - Advanced Telegram-to-Broker Copy Trading Bot

EvoBot is a professional-grade, high-frequency copy trading bot that listens to Telegram trading signals and automatically executes them on MetaTrader 5 (MT5). Built for scalping and high-frequency trading with support for partial closes, breakeven management, and comprehensive risk controls.

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

## 📋 Requirements

- Python 3.8+
- MetaTrader 5 terminal (Windows or Wine on Linux)
- Telegram API credentials
- MT5 broker account

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
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
```

### 4. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Telegram Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
SIGNAL_CHANNELS=channel1,channel2
NOTIFICATION_CHANNEL=your_notification_channel

# MT5 Configuration
MT5_SERVER=YourBroker-Server
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# Trading Configuration
DEFAULT_LOT_SIZE=0.01
MAX_SPREAD_PIPS=5.0
MAX_DAILY_DRAWDOWN=5.0
MAX_OPEN_TRADES=10
```

### 5. Get Telegram API Credentials

1. Visit https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Copy `api_id` and `api_hash`

## 🚀 Usage

### Start the Bot

```bash
python main.py
```

On first run, you'll be prompted to authenticate with Telegram (enter the code sent to your phone).

### Directory Structure

```
evobot/
├── broker/              # MT5 broker integration
│   ├── __init__.py
│   └── mt5_client.py    # MT5 API client
├── config/              # Configuration management
│   ├── __init__.py
│   └── settings.py      # Settings and config classes
├── core/                # Core business logic
│   ├── __init__.py
│   ├── trade_manager.py # Trade lifecycle management
│   ├── risk_manager.py  # Risk management system
│   └── notifier.py      # Notification system
├── models/              # Data models
│   ├── __init__.py
│   └── trade.py         # Trade, Signal, Account models
├── parsers/             # Signal parsing
│   ├── __init__.py
│   └── signal_parser.py # Telegram message parser
├── telegram/            # Telegram integration
│   ├── __init__.py
│   └── listener.py      # Telethon-based listener
├── utils/               # Utilities
│   ├── __init__.py
│   └── logging_utils.py # Logging setup
├── data/                # Persisted data (created at runtime)
├── logs/                # Log files (created at runtime)
├── main.py              # Main application entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment file
└── README.md            # This file
```

## 📊 Signal Format Examples

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
```

## ⚙️ Configuration

### Trading Configuration

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

## 🛡️ Safety Features

- **Dry-run mode**: Test signal parsing without executing trades (coming soon)
- **Max drawdown protection**: Stops trading if daily drawdown exceeds limit
- **Spread filtering**: Skips trades with excessive spread
- **News avoidance**: Skips trades during high-impact news events
- **Auto-reconnect**: Handles Telegram/MT5 disconnections
- **Trade persistence**: Survives system restarts
- **Error recovery**: Retries failed operations

## 🔧 Troubleshooting

### Telegram Connection Issues

- Verify `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` are correct
- Check that your phone number includes country code (e.g., +1234567890)
- Delete the session file and re-authenticate if needed

### MT5 Connection Issues

- Ensure MT5 terminal is running
- Verify `MT5_PATH` points to `terminal64.exe`
- Check `MT5_SERVER`, `MT5_LOGIN`, and `MT5_PASSWORD` are correct
- Enable "Allow DLL imports" and "Allow automated trading" in MT5

### Signal Not Parsing

- Check `logs/system.log` for parse errors
- Verify signal format matches expected patterns
- Add custom regex patterns in `parsers/signal_parser.py` if needed

### Trades Not Executing

- Check spread is within `MAX_SPREAD_PIPS`
- Verify daily drawdown hasn't exceeded `MAX_DAILY_DRAWDOWN`
- Check if trading hours restrictions apply
- Look for risk alerts in notifications

## 📝 Development

### Adding New Symbols

Edit `config/settings.py` and add to the `symbols` list:

```python
symbols: List[str] = field(default_factory=lambda: [
    "XAUUSD", "GBPUSD", "EURUSD", "YOUR_SYMBOL"
])
```

Add aliases in `parsers/signal_parser.py`:

```python
SYMBOL_ALIASES = {
    "YOUR_ALIAS": "YOUR_SYMBOL",
    ...
}
```

### Custom Signal Formats

Add regex patterns in `parsers/signal_parser.py`:

```python
PATTERNS = {
    "your_pattern": re.compile(r"YOUR_REGEX", re.IGNORECASE),
    ...
}
```

### Extending Risk Checks

Add custom risk checks in `core/risk_manager.py`:

```python
async def can_trade(self, signal: Signal) -> Tuple[bool, str]:
    # Add your custom checks here
    ...
```

## 🚀 Production Deployment

### VPS Setup (Recommended)

1. **Choose a VPS** near your broker's servers (low latency)
2. **Install Python 3.8+** and required packages
3. **Install MT5** (Windows VPS or Wine on Linux)
4. **Set up systemd service** (Linux) or Task Scheduler (Windows)
5. **Configure firewall** to allow MT5 and Telegram connections
6. **Set up log rotation** to manage disk space

### Systemd Service Example (Linux)

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
ExecStart=/path/to/evobot/venv/bin/python main.py
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

### Monitoring

- Set up **Telegram notifications** for trade events
- Monitor **log files** regularly
- Track **account balance** and drawdown
- Review **trade statistics** daily

## ⚠️ Disclaimer

**IMPORTANT**: Trading forex, gold, and other financial instruments involves substantial risk of loss and is not suitable for all investors. This bot is provided for educational purposes only. The authors are not responsible for any financial losses incurred through the use of this software.

- **Test thoroughly** on a demo account before using real money
- **Start with small lot sizes** to validate the system
- **Monitor the bot** regularly, especially during the first weeks
- **Understand the risks** of automated trading
- **Never risk more** than you can afford to lose

## 📄 License

[Specify your license here]

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📧 Support

For questions, issues, or feature requests, please open an issue on GitHub.

## 🙏 Acknowledgments

- Telethon for Telegram integration
- MetaTrader5 Python package
- The trading community for signal format insights

---

**Built with ❤️ for traders who want to automate their copy trading.**
