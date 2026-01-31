# Firebase-Backed Settings Configuration

EvoBot now has a **completely Firebase-backed settings system** where all configuration values are editable from the dashboard without any hardcoded values or .env requirements.

## How It Works

### 1. **Settings Storage**
- All settings are stored in Firebase Realtime Database
- Local cache backup saved to `data/settings_cache.json`
- Falls back to defaults if Firebase is unavailable
- Environment variables override defaults on first run, then sync to Firebase

### 2. **Settings Sections**

#### Telegram Settings
```json
{
  "api_id": 0,
  "api_hash": "",
  "phone_number": "",
  "session_name": "evobot_session",
  "signal_channels": [],
  "notification_channel": "",
  "reconnect_delay": 5,
  "max_reconnect_attempts": 999
}
```

#### Broker Settings (MetaApi/MT5)
```json
{
  "broker_type": "metaapi",
  "metaapi_token": "",
  "metaapi_account_id": "",
  "server": "",
  "login": 0,
  "password": "",
  "timeout": 60000,
  "retry_attempts": 3,
  "retry_delay": 1.0
}
```

#### Trading Settings
```json
{
  "symbols": ["XAUUSD", "GBPUSD", ...],
  "default_lot_size": 0.01,
  "max_spread_pips": 10.0,
  "max_daily_drawdown_percent": 5.0,
  "max_open_trades": 10,
  "symbol_max_spreads": {
    "XAUUSD": 50.0,
    "XAGUSD": 30.0,
    "BTCUSD": 100.0
  },
  "execute_immediately": true,
  "entry_zone_tolerance": 5.0
}
```

#### Risk Settings
```json
{
  "avoid_high_impact_news": true,
  "news_blackout_minutes_before": 30,
  "news_blackout_minutes_after": 15,
  "trading_start_hour": 0,
  "trading_end_hour": 24,
  "max_risk_percent_per_trade": 2.0
}
```

## API Endpoints

### Get Settings
```bash
# Get all settings
GET /api/settings

# Get specific section
GET /api/settings/telegram
GET /api/settings/broker
GET /api/settings/trading
GET /api/settings/risk
```

### Update Settings
```bash
# Update all settings at once
PUT /api/settings
Body: { "section": { "key": "value" } }

# Update a section
PUT /api/settings/telegram
Body: { "api_id": 12345, "api_hash": "..." }

# Update single setting
PUT /api/settings/telegram/api_id
Body: { "value": 12345 }

# Update Telegram channels
POST /api/settings/telegram/channels
Body: {
  "signal_channels": ["-1001234567890", "-1009876543210"],
  "notification_channel": "-1001111111111"
}

# Update Telegram credentials
POST /api/settings/telegram/credentials
Body: {
  "api_id": 12345,
  "api_hash": "abcd1234...",
  "phone_number": "+1234567890"
}

# Update Broker credentials
POST /api/settings/broker/credentials
Body: {
  "metaapi_token": "...",
  "metaapi_account_id": "...",
  "server": "FusionMarkets-Demo",
  "login": 123456,
  "password": "..."
}

# Reload settings from Firebase
POST /api/settings/reload
```

## Configuration Priority

1. **Firebase Database** (highest priority - used at runtime)
2. **Environment Variables** (used on first run to populate Firebase)
3. **Default Values** (fallback if Firebase unavailable)

## Key Features

✅ **No Hardcoded Values** - Everything is configurable from the dashboard
✅ **Dynamic Reload** - Update settings and they take effect immediately
✅ **Secure** - Settings changes are audit-logged
✅ **Persistent** - All changes saved to Firebase
✅ **Fallback** - Local cache for offline operation
✅ **Type-Safe** - Properties return correct types

## Usage in Code

### Get Settings
```python
from config.settings import config

# Access settings via properties
api_id = config.telegram.api_id
lot_size = config.trading.default_lot_size
max_spread = config.trading.max_spread_pips

# Settings are automatically pulled from Firebase
# No need to manually reload
```

### Update Settings from Code
```python
from core.firebase_settings import firebase_settings

# Update single setting
firebase_settings.set("trading", "default_lot_size", 0.02)

# Update section
firebase_settings.set_section("trading", {
    "default_lot_size": 0.02,
    "max_spread_pips": 12.0
})

# Update all
firebase_settings.update_all({
    "trading": {...},
    "telegram": {...}
})
```

## Migration from .env

When you first start the bot:
1. It reads .env values
2. Syncs them to Firebase
3. Thereafter uses Firebase as the source of truth
4. You can safely remove .env values after first run

To migrate existing .env:
```bash
# On first startup, set all env vars:
export TELEGRAM_API_ID=12345
export TELEGRAM_API_HASH="..."
export METAAPI_TOKEN="..."
# etc...

# Then restart the bot - settings will be synced to Firebase
sudo systemctl restart evobot_dashboard
```

## Testing Settings API

```bash
# Get all settings (requires authentication)
curl -H "Authorization: Bearer TOKEN" http://localhost:8080/api/settings

# Update trading settings
curl -X PUT -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"default_lot_size": 0.02}' \
  http://localhost:8080/api/settings/trading/default_lot_size

# Update Telegram channels
curl -X POST -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"signal_channels": ["-1001234567890"], "notification_channel": "-1009876543210"}' \
  http://localhost:8080/api/settings/telegram/channels
```

## Next Steps

1. Log in to the dashboard: http://localhost:8080
2. Go to Settings tab
3. Update any values you need
4. All changes are immediately saved to Firebase
5. Restart bot if you change Telegram/Broker credentials

**No more editing .env files!** 🎉
