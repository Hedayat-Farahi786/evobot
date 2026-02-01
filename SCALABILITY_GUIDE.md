# Multi-User Scalability Architecture

## Current Issue
The current implementation uses **local MT5 terminal**, which:
- ❌ Only supports ONE user per server
- ❌ Requires MT5 installed on server
- ❌ Can't scale to millions of users
- ❌ No user isolation

## Solution: MetaAPI Cloud Integration

### Architecture for Millions of Users

```
User 1 (Telegram) → EvoBot Server → MetaAPI Cloud → User 1's MT5 Broker
User 2 (Telegram) → EvoBot Server → MetaAPI Cloud → User 2's MT5 Broker
User N (Telegram) → EvoBot Server → MetaAPI Cloud → User N's MT5 Broker
```

### Required Changes

#### 1. Use MetaAPI Instead of Local MT5

**Current (Single User)**:
```python
# Connects to local MT5 terminal
mt5.initialize(login=123, password="pass", server="Broker-Demo")
```

**Scalable (Multi-User)**:
```python
# Each user has their own MetaAPI connection
from metaapi_cloud_sdk import MetaApi

api = MetaApi(token='your-metaapi-token')
account = await api.metatrader_account_api.get_account(user_account_id)
connection = await account.connect()
```

#### 2. Per-User Bot Instances

Each user needs their own bot instance:

```python
class UserBotInstance:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.telegram_listener = TelegramListener(user_id)
        self.mt5_connection = MetaAPIConnection(user_id)
        self.trade_manager = TradeManager(user_id)
        self.risk_manager = RiskManager(user_id)
```

#### 3. Database Schema

**Users Table**:
```
users/
  {user_id}/
    telegram_id: "123456789"
    telegram_username: "@user"
    metaapi_account_id: "abc123"
    subscription_tier: "premium"
    created_at: "2024-01-01"
    
    mt5_credentials/
      server: "Broker-Demo"
      login: "12345"
      encrypted_password: "..."
    
    settings/
      default_lot_size: 0.01
      max_spread_pips: 5.0
      signal_channels: ["channel1", "channel2"]
    
    trades/
      {trade_id}/
        symbol: "XAUUSD"
        direction: "BUY"
        status: "OPEN"
        ...
```

#### 4. Bot Manager Service

```python
class BotManager:
    def __init__(self):
        self.active_bots: Dict[str, UserBotInstance] = {}
    
    async def start_bot_for_user(self, user_id: str):
        if user_id in self.active_bots:
            return  # Already running
        
        bot = UserBotInstance(user_id)
        await bot.start()
        self.active_bots[user_id] = bot
    
    async def stop_bot_for_user(self, user_id: str):
        if user_id in self.active_bots:
            await self.active_bots[user_id].stop()
            del self.active_bots[user_id]
```

### Implementation Steps

#### Step 1: Switch to MetaAPI

1. Sign up at https://metaapi.cloud
2. Get API token
3. Update broker client:

```python
# broker/metaapi_client.py
from metaapi_cloud_sdk import MetaApi

class MetaAPIClient:
    def __init__(self, token: str):
        self.api = MetaApi(token)
    
    async def connect_user(self, user_id: str, account_id: str):
        account = await self.api.metatrader_account_api.get_account(account_id)
        connection = await account.connect()
        return connection
```

#### Step 2: Update Credential Storage

```python
# Store per-user MetaAPI account IDs
class UserCredentials:
    user_id: str
    telegram_id: int
    metaapi_account_id: str  # Each user's MetaAPI account
    metaapi_token: str       # Optional: per-user token
```

#### Step 3: Isolate User Data

```python
# All data scoped by user_id
firebase_service.db_ref.child(f"users/{user_id}/trades")
firebase_service.db_ref.child(f"users/{user_id}/settings")
firebase_service.db_ref.child(f"users/{user_id}/account_info")
```

#### Step 4: Resource Management

```python
# Limit concurrent bots per server
MAX_BOTS_PER_SERVER = 1000

# Queue system for scaling
if len(active_bots) >= MAX_BOTS_PER_SERVER:
    # Spin up new server instance
    # Or queue the request
    pass
```

### Deployment Architecture

#### Single Server (Up to 1000 users)
```
[Load Balancer]
     ↓
[EvoBot Server]
     ↓
[Firebase] + [MetaAPI Cloud]
```

#### Multi-Server (Millions of users)
```
[Load Balancer]
     ↓
[EvoBot Server 1] [EvoBot Server 2] ... [EvoBot Server N]
     ↓                ↓                      ↓
[Firebase Realtime DB] + [MetaAPI Cloud]
     ↓
[User Sharding: users 1-10k] [users 10k-20k] ...
```

### Cost Considerations

**MetaAPI Pricing** (as of 2024):
- Free: 1 account, limited features
- Starter: $49/month - 5 accounts
- Professional: $199/month - 25 accounts
- Enterprise: Custom pricing for unlimited

**For 1 Million Users**:
- Need ~40,000 MetaAPI accounts (if 25 users per account)
- Cost: ~$8M/month for MetaAPI alone
- **Alternative**: Each user brings their own MetaAPI account

### Recommended Approach

**User-Provided MetaAPI Accounts**:
1. User signs up for MetaAPI (free tier)
2. User connects their MT5 broker to MetaAPI
3. User provides MetaAPI account ID to EvoBot
4. EvoBot connects using user's MetaAPI account

**Benefits**:
- ✅ Zero MetaAPI costs for you
- ✅ Unlimited scalability
- ✅ Users control their own accounts
- ✅ Better security (users own their credentials)

### Updated User Flow

1. **User Registration**:
   - Login with Telegram
   - Get MetaAPI account ID from https://metaapi.cloud
   - Connect MT5 broker to MetaAPI
   - Paste MetaAPI account ID in EvoBot

2. **Bot Operation**:
   - EvoBot connects to user's MetaAPI account
   - Listens to user's Telegram channels
   - Executes trades on user's MT5 via MetaAPI
   - All isolated per user

### Migration Path

**Phase 1: Add MetaAPI Support** (Keep local MT5)
- Add MetaAPI client alongside MT5 client
- Let users choose: Local MT5 or MetaAPI
- Test with small user base

**Phase 2: Multi-User Support**
- Implement per-user bot instances
- Add user isolation
- Deploy to production

**Phase 3: Scale**
- Remove local MT5 support
- Full MetaAPI integration
- Horizontal scaling with load balancers

### Code Changes Needed

1. **broker/__init__.py**: Add broker factory
2. **broker/metaapi_client.py**: Implement MetaAPI client
3. **core/bot_manager.py**: Manage multiple bot instances
4. **dashboard/lifecycle.py**: Start/stop per-user bots
5. **models/user.py**: Add user model with credentials
6. **config/settings.py**: Per-user settings

### Security Considerations

1. **Encrypt credentials** in database
2. **Rate limiting** per user
3. **Resource quotas** (max trades, max channels)
4. **Audit logging** for all user actions
5. **API key rotation** for MetaAPI tokens

### Monitoring & Scaling

```python
# Metrics to track
- Active users
- Bots per server
- Trades per second
- API calls to MetaAPI
- Database connections
- Memory per bot instance
- CPU usage per bot

# Auto-scaling triggers
if cpu_usage > 80%:
    scale_up()
if active_bots > 900:
    provision_new_server()
```

## Next Steps

1. **Immediate**: Document current single-user limitations
2. **Short-term**: Implement MetaAPI support
3. **Medium-term**: Add multi-user bot management
4. **Long-term**: Full horizontal scaling

## Conclusion

The current architecture is perfect for:
- ✅ Personal use (1 user)
- ✅ Small team (2-10 users on separate servers)
- ✅ Testing and development

For millions of users, you MUST:
- ❌ Remove local MT5 dependency
- ✅ Use MetaAPI cloud service
- ✅ Implement per-user bot instances
- ✅ Add proper user isolation
- ✅ Deploy with horizontal scaling
