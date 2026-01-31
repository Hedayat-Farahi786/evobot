# EvoBot Quick Reference Guide

## 🚀 Quick Start

```bash
# 1. Setup
./setup.sh

# 2. Configure
nano .env  # Edit with your credentials

# 3. Run
source venv/bin/activate
python main.py
```

## 📝 Configuration Checklist

### Telegram Setup
- [ ] Get API credentials from https://my.telegram.org/apps
- [ ] Add `TELEGRAM_API_ID` to .env
- [ ] Add `TELEGRAM_API_HASH` to .env
- [ ] Add `TELEGRAM_PHONE` with country code (e.g., +1234567890)
- [ ] Add channel usernames to `SIGNAL_CHANNELS` (comma-separated)

### MT5 Setup
- [ ] Install MetaTrader 5
- [ ] Get server name from MT5 (Tools → Options → Server)
- [ ] Add `MT5_SERVER` to .env
- [ ] Add `MT5_LOGIN` (account number)
- [ ] Add `MT5_PASSWORD`
- [ ] Add `MT5_PATH` (path to terminal64.exe)
- [ ] Enable "Allow DLL imports" in MT5
- [ ] Enable "Allow automated trading" in MT5

### Trading Configuration
- [ ] Set `DEFAULT_LOT_SIZE` (start small, e.g., 0.01)
- [ ] Set `MAX_SPREAD_PIPS` (e.g., 5.0)
- [ ] Set `MAX_DAILY_DRAWDOWN` (e.g., 5.0%)
- [ ] Set `MAX_OPEN_TRADES` (e.g., 10)

## 📊 Signal Formats Supported

### New Trade Signal
```
XAUUSD BUY
Entry: 2050.00
SL: 2045.00
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00
```

### With Entry Zone
```
GOLD LONG
Entry Zone: 2050.00 - 2052.00
Stop Loss: 2045.00
TP1: 2055.00
TP2: 2060.00
TP3: 2065.00
Lot: 0.02
```

### Update Signals
```
✅ XAUUSD TP1 HIT
🔒 Move GOLD to Breakeven
❌ GBPUSD SL HIT
🏆 EURUSD TP3 REACHED
Close USDJPY
```

## 🔍 Monitoring Commands

### Check Logs
```bash
# Real-time system logs
tail -f logs/system.log | python -m json.tool

# Real-time trade logs
tail -f logs/trades.log | python -m json.tool

# Error logs
tail -f logs/errors.log | python -m json.tool
```

### Check Trade Data
```bash
# View persisted trades
cat data/trades.json | python -m json.tool
```

## 🛠️ Common Tasks

### Test Signal Parser
```bash
python test_parser.py
```

### Restart Bot
```bash
# Stop with Ctrl+C
# Then restart
python main.py
```

### Check MT5 Connection
```python
import MetaTrader5 as mt5
mt5.initialize()
print(mt5.account_info())
mt5.shutdown()
```

### Clear Session (Re-authenticate Telegram)
```bash
rm evobot_session.session
python main.py  # Will prompt for code again
```

## ⚙️ Key Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DEFAULT_LOT_SIZE` | 0.01 | Default lot size for trades |
| `MAX_SPREAD_PIPS` | 5.0 | Skip trades if spread exceeds this |
| `MAX_DAILY_DRAWDOWN` | 5.0 | Stop trading if drawdown exceeds % |
| `MAX_OPEN_TRADES` | 10 | Maximum concurrent trades |
| `tp1_close_percent` | 0.5 | Close 50% at TP1 |
| `tp2_close_percent` | 0.3 | Close 30% at TP2 |
| `tp3_close_percent` | 0.2 | Close 20% at TP3 |
| `move_sl_to_breakeven_at_tp1` | True | Auto-breakeven after TP1 |
| `breakeven_offset_pips` | 1.0 | Buffer above entry for BE |

## 🐛 Troubleshooting

### Bot Won't Start

**Check logs:**
```bash
cat logs/system.log | grep ERROR
```

**Common issues:**
- .env file missing or incomplete
- MT5 not running
- Wrong MT5 credentials
- Telegram API credentials invalid

### No Trades Executing

**Possible reasons:**
1. Spread too high → Check `MAX_SPREAD_PIPS`
2. Daily drawdown limit → Check account balance
3. Outside trading hours → Check `trading_start_hour`
4. Max trades reached → Check `MAX_OPEN_TRADES`
5. High-impact news → Check `avoid_high_impact_news`

**Check risk status:**
```python
# In Python console
from core.risk_manager import risk_manager
import asyncio
asyncio.run(risk_manager.start())
print(risk_manager.get_risk_status())
```

### Signals Not Parsing

**Test parser:**
```bash
python test_parser.py
```

**Check parse errors in logs:**
```bash
grep "parse_errors" logs/system.log
```

### Telegram Connection Lost

- Bot will auto-reconnect (exponential backoff)
- Check internet connection
- Verify Telegram isn't blocking the session
- Delete session file and re-authenticate if needed

## 📈 Performance Tips

### For High-Frequency Trading
- Run on VPS near broker servers (low latency)
- Use SSD for faster file I/O
- Increase `max_slippage` slightly (e.g., 50 points)
- Monitor position check interval (currently 1 second)

### For Scalping
- Set tight `MAX_SPREAD_PIPS` (e.g., 2.0)
- Use smaller lot sizes
- Enable `move_sl_to_breakeven_at_tp1`
- Monitor frequently

### For Swing Trading
- Increase `entry_zone_tolerance`
- Use larger `breakeven_offset_pips`
- Disable high-frequency position checks

## 🔐 Security Best Practices

1. **Never share your .env file**
2. **Use strong MT5 password**
3. **Enable 2FA on Telegram**
4. **Run on secure VPS only**
5. **Regularly backup `data/trades.json`**
6. **Monitor logs for suspicious activity**
7. **Start with demo account**

## 📞 Support Checklist

Before asking for help, provide:
- [ ] Error logs (`logs/errors.log`)
- [ ] Last 50 lines of system log
- [ ] Configuration (without passwords!)
- [ ] Signal example that failed
- [ ] MT5 version
- [ ] Python version
- [ ] Operating system

## 🎯 Best Practices

1. **Test thoroughly** on demo account (minimum 2 weeks)
2. **Start small** (0.01 lots)
3. **Monitor daily** for first month
4. **Review trade logs** weekly
5. **Adjust risk parameters** based on results
6. **Keep logs** for at least 3 months
7. **Backup configuration** regularly
8. **Update dependencies** monthly
9. **Review and optimize** signal parsing quarterly
10. **Never leave unattended** without proper risk limits

## 📚 Additional Resources

- **Telethon Docs**: https://docs.telethon.dev/
- **MT5 Python Docs**: https://www.mql5.com/en/docs/python_metatrader5
- **Trading Best Practices**: [Your preferred resource]

---

**Remember**: Always test on demo first! Never risk more than you can afford to lose.
