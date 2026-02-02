# Signal Messages Feature

## Overview
A new feature has been added to store and display all Telegram signal messages in a beautiful, Telegram-like interface.

## Files Created

### 1. `models/signal_message.py`
- Data model for storing raw Telegram messages
- Fields: id, channel_id, channel_name, message_id, text, timestamp, sender_name

### 2. `core/signal_storage.py`
- Service to manage signal message storage
- Stores messages in memory (last 500) and Firebase
- Methods:
  - `add_message()` - Add new message
  - `get_messages()` - Get recent messages
  - `get_messages_by_channel()` - Filter by channel

### 3. `dashboard/routers/signals.py`
- API endpoint: `GET /api/signals/messages`
- Query parameters:
  - `limit` (default: 100, max: 500)
  - `channel_id` (optional filter)

### 4. `dashboard/templates/signals.html`
- Beautiful Telegram-like message display
- Features:
  - Channel avatars with initials
  - Message cards with timestamps
  - Channel filter dropdown
  - Auto-refresh every 10 seconds
  - Responsive design

## Files Modified

### 1. `telegram/listener.py`
- Added code to save every message to storage
- Extracts channel name and message details
- Stores in both memory and Firebase

### 2. `main.py`
- Initialize Firebase connection
- Connect signal_storage to Firebase database

### 3. `dashboard/app.py`
- Import and register signals router

### 4. `dashboard/routers/views.py`
- Added `/signals` route to serve the signals page

### 5. `dashboard/templates/dashboard.html`
- Added "Signal Messages" navigation link in sidebar

## Usage

1. **Access the page**: Navigate to `http://localhost:8080/signals`

2. **View messages**: All Telegram messages from monitored channels are displayed

3. **Filter by channel**: Use the dropdown to filter messages by specific channel

4. **Auto-refresh**: Page automatically refreshes every 10 seconds

## Features

- ✅ Stores all Telegram messages in database
- ✅ Beautiful Telegram-like UI with channel avatars
- ✅ Filter messages by channel
- ✅ Real-time updates (10s refresh)
- ✅ Responsive design for mobile/desktop
- ✅ Firebase integration for persistence
- ✅ Shows channel name, timestamp, and full message text
- ✅ Smooth animations and transitions

## API Endpoints

### Get Signal Messages
```
GET /api/signals/messages?limit=100&channel_id=123456
```

Response:
```json
{
  "success": true,
  "count": 10,
  "messages": [
    {
      "id": "uuid",
      "channel_id": "123456",
      "channel_name": "Trading Signals",
      "message_id": 789,
      "text": "XAUUSD BUY...",
      "timestamp": "2024-01-28T12:00:00",
      "sender_name": null
    }
  ]
}
```

## Future Enhancements

- Add search functionality
- Export messages to CSV/JSON
- Message analytics (most active channels, signal types)
- Parse and highlight trading signals
- Add pagination for large datasets
