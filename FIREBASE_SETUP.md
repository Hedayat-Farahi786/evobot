# Firebase Realtime Database Integration

## Overview

EvoBot now uses Firebase Realtime Database for real-time data synchronization across all dashboard instances. This enables:

- **Real-time price updates** across all connected clients
- **Live trade monitoring** without polling
- **Instant notifications** for trade events
- **Multi-device support** - view dashboard from anywhere
- **Data persistence** in the cloud

## Setup Instructions

### 1. Install Dependencies

```bash
./setup_firebase.sh
```

Or manually:
```bash
pip install firebase-admin
```

### 2. Configure Firebase Project

1. **Go to Firebase Console**: https://console.firebase.google.com/
2. **Select Project**: `evobot-8`
3. **Enable Realtime Database**:
   - Navigate to **Build > Realtime Database**
   - Click **Create Database**
   - Choose location: `us-central1` (or closest to your VPS)
   - Start in **Test Mode** (we'll secure it later)

### 3. Get Service Account Credentials

1. Go to **Project Settings** (gear icon) > **Service Accounts**
2. Click **Generate New Private Key**
3. Download the JSON file
4. Extract these values from the JSON:
   - `private_key_id`
   - `private_key`
   - `client_email`
   - `client_id`

### 4. Update Environment Variables

Add to your `.env` file:

```env
# Firebase Configuration
FIREBASE_PRIVATE_KEY_ID=abc123def456...
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBg...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@evobot-8.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=123456789012345678901
```

**Important**: Keep the `\n` characters in the private key!

### 5. Configure Database Rules

For production, update your Firebase Realtime Database rules:

```json
{
  "rules": {
    ".read": "auth != null",
    ".write": "auth != null"
  }
}
```

For development/testing (less secure):
```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

## Data Structure

Firebase stores data in the following structure:

```
evobot-8/
├── status/
│   ├── bot_running: boolean
│   ├── mt5_connected: boolean
│   ├── telegram_connected: boolean
│   └── timestamp: string
├── account/
│   ├── balance: number
│   ├── equity: number
│   ├── margin: number
│   ├── profit: number
│   └── timestamp: string
├── prices/
│   ├── XAUUSD/
│   │   ├── bid: number
│   │   ├── ask: number
│   │   └── spread_pips: number
│   └── timestamp: string
├── trades/
│   └── {trade_id}/
│       ├── symbol: string
│       ├── direction: string
│       ├── entry_price: number
│       ├── profit: number
│       └── timestamp: string
├── stats/
│   ├── total_trades: number
│   ├── win_rate: number
│   ├── total_profit: number
│   └── timestamp: string
└── activities/
    └── {activity_id}/
        ├── type: string
        ├── title: string
        └── timestamp: string
```

## Features

### Real-time Updates

The dashboard automatically subscribes to Firebase changes:

```javascript
// Prices update in real-time
const pricesRef = ref(firebaseDB, 'prices');
onValue(pricesRef, (snapshot) => {
    // Update UI instantly
});
```

### Multi-Device Sync

- Open dashboard on multiple devices
- All devices see the same data in real-time
- No need to refresh or poll

### Offline Support

Firebase SDK handles offline scenarios:
- Caches data locally
- Syncs when connection restored
- Queues writes for later

## Testing

1. Start the dashboard:
```bash
cd dashboard
python app.py
```

2. Open browser: http://localhost:8080

3. Check Firebase Console > Realtime Database to see live data

4. Open dashboard on another device/browser - data syncs instantly!

## Troubleshooting

### "Permission Denied" Error

- Check database rules allow read/write
- Verify service account credentials are correct
- Ensure private key has `\n` characters preserved

### Data Not Syncing

- Check Firebase Console for connection status
- Verify `databaseURL` in config matches your project
- Check browser console for Firebase errors

### Slow Updates

- Choose Firebase region closest to your VPS
- Check network latency
- Consider upgrading Firebase plan for better performance

## Security Best Practices

1. **Never commit** service account JSON to git
2. **Use environment variables** for credentials
3. **Enable authentication** in production
4. **Set strict database rules**:
   ```json
   {
     "rules": {
       "status": { ".read": "auth != null", ".write": "auth != null" },
       "trades": { ".read": "auth != null", ".write": "auth != null" }
     }
   }
   ```
5. **Rotate keys** periodically
6. **Monitor usage** in Firebase Console

## Cost

Firebase Realtime Database pricing:
- **Spark Plan (Free)**:
  - 1 GB stored
  - 10 GB/month downloaded
  - 100 simultaneous connections
  
- **Blaze Plan (Pay as you go)**:
  - $5/GB stored
  - $1/GB downloaded
  - Unlimited connections

For EvoBot, the free tier is sufficient for most users.

## Support

For issues or questions:
1. Check Firebase Console logs
2. Review browser console errors
3. Check `logs/system.log` for backend errors
4. Open GitHub issue with error details

---

**Built with Firebase Realtime Database for instant, scalable data sync! 🔥**
