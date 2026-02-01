# Channel Management Utilities

## Reset Channels from .env

If your signal channels are not loading in the dashboard, you can reset them from your `.env` file:

```bash
python reset_channels.py
```

This script will:
1. Read the `SIGNAL_CHANNELS` from your `.env` file
2. Update Firebase settings with the channels
3. Update the local cache file
4. Display the loaded channels for verification

After running this script, restart the dashboard:

```bash
python start_dashboard.py
```

## Troubleshooting

### Channels not showing in dashboard
- Run `python reset_channels.py` to reload from .env
- Check that `SIGNAL_CHANNELS` in `.env` is properly formatted (comma-separated)
- Verify Firebase is initialized (check logs)

### Mixed channel ID formats
The system automatically normalizes channel IDs:
- `-1001234567890` (Telegram supergroup format)
- `1234567890` (raw ID)
- Both formats are supported and will be normalized

### Channel photos not loading
Channel photos are cached in `data/channel_photos/`. If a photo is missing:
1. The dashboard will fetch it automatically when you view the channels
2. Or manually delete the cache and refresh the dashboard
