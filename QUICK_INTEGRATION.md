# Quick Integration Guide - Telegram Channels with Profile Images

## Step 1: Add Data Properties

In your Vue app's `data()` section, add:

```javascript
data() {
    return {
        // ... existing properties
        telegramChannels: [],
        loadingChannels: false,
    }
}
```

## Step 2: Add Methods

In your Vue app's `methods` section, add:

```javascript
methods: {
    // ... existing methods
    
    async refreshChannels() {
        if (!this.status.telegram_connected) {
            this.notify('Telegram not connected', 'warning');
            return;
        }
        
        this.loadingChannels = true;
        try {
            const res = await fetch('/api/telegram/channels');
            if (!res.ok) throw new Error('Failed to fetch channels');
            const data = await res.json();
            this.telegramChannels = data.channels || [];
            
            // Optionally notify success
            if (data.channels.length > 0) {
                this.notify(`Loaded ${data.channels.length} channel(s)`, 'success');
            }
        } catch (e) {
            console.error('Channels error:', e);
            this.notify('Failed to load channel info', 'error');
        } finally {
            this.loadingChannels = false;
        }
    },
    
    getInitials(name) {
        if (!name) return '?';
        return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
    },
    
    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }
}
```

## Step 3: Add HTML Component

Replace your existing "Channels" section in the sidebar with this:

```html
<!-- Telegram Channels Section with Profile Images -->
<div class="sidebar-section">
    <div class="sidebar-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>
        Signal Channels
        <button class="btn btn-sm" @click="refreshChannels" :disabled="loadingChannels" style="margin-left: auto; padding: 4px 8px;">
            <svg v-if="loadingChannels" class="spinner" width="10" height="10"></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
        </button>
    </div>
    
    <!-- Loading State -->
    <div v-if="loadingChannels && telegramChannels.length === 0" style="padding: 12px;">
        <div class="loading-skeleton" style="height: 72px; margin-bottom: 8px;" v-for="i in 2" :key="'skel-' + i"></div>
    </div>
    
    <!-- Channels List -->
    <div v-else-if="telegramChannels.length > 0" style="padding: 12px; display: flex; flex-direction: column; gap: 10px;">
        <div class="channel-card-compact" v-for="channel in telegramChannels" :key="channel.id">
            <div class="channel-avatar-small">
                <img v-if="channel.photo_path" :src="`/api/telegram/channel/${channel.id}/photo`" :alt="channel.title" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">
                <span v-else>{{ getInitials(channel.title) }}</span>
            </div>
            <div class="channel-info-compact">
                <div class="channel-title-small">
                    {{ channel.title }}
                    <svg v-if="channel.verified" width="12" height="12" viewBox="0 0 24 24" fill="#3b82f6"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </div>
                <div class="channel-meta-small">
                    <span class="channel-id-small">{{ channel.id }}</span>
                    <span v-if="channel.participants_count" style="display: flex; align-items: center; gap: 3px;">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                        {{ formatNumber(channel.participants_count) }}
                    </span>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Empty State -->
    <div v-else class="empty-channels" style="margin: 12px;">
        No channels configured
    </div>
</div>

<!-- Add these styles to your <style> section -->
<style>
.channel-card-compact {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    transition: all 0.2s ease;
}

.channel-card-compact:hover {
    background: var(--bg-hover);
    border-color: var(--accent);
    transform: translateX(2px);
}

.channel-avatar-small {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 14px;
    flex-shrink: 0;
    overflow: hidden;
}

.channel-info-compact {
    flex: 1;
    min-width: 0;
}

.channel-title-small {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 3px;
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.channel-meta-small {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 10px;
    color: var(--text-secondary);
}

.channel-id-small {
    font-family: 'JetBrains Mono', monospace;
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 6px;
    border-radius: 3px;
}

.loading-skeleton {
    background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-hover) 50%, var(--bg-secondary) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
}

@keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
</style>
```

## Step 4: Call on Bot Start

In your `startBot()` method, after successful connection, add:

```javascript
async startBot() {
    // ... existing code
    
    if (data.status === 'success') {
        // ... existing success code
        
        // Load channel info
        setTimeout(() => {
            this.refreshChannels();
        }, 2000); // Wait 2 seconds for connections to stabilize
    }
}
```

## Step 5: Add to WebSocket Handler

In your WebSocket `onmessage` handler:

```javascript
this.ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // ... existing handlers
    
    if (data.type === 'bot_started') {
        // ... existing code
        
        // Refresh channels after bot starts
        setTimeout(() => {
            this.refreshChannels();
        }, 3000);
    }
};
```

## Step 6: Test It!

1. Start your bot
2. Make sure Telegram is connected
3. The channels section should show profile images and info
4. Click the refresh button to update

## Example Output

When working, you'll see:
- Channel profile photo (or gradient avatar with initials)
- Channel name with verified badge (if verified)
- Channel ID in monospace font
- Member count (formatted: 1.2K, 5.3M, etc.)
- Hover effects on cards

## Troubleshooting

**No images showing?**
- Check browser console for errors
- Verify `/api/telegram/channel/{id}/photo` endpoint works
- Check `data/channel_photos/` directory exists

**"Telegram not connected" error?**
- Make sure bot is running
- Verify Telegram connection status is true
- Check WebSocket is connected

**Empty list?**
- Verify signal_channels are configured in settings
- Check `/api/telegram/channels` returns data
- Look at server logs for errors

## That's It!

You now have a beautiful Telegram channels display with profile images! 🎉

The component will:
- ✅ Show actual channel profile photos
- ✅ Display channel metadata (name, ID, members)
- ✅ Show verified badges
- ✅ Have smooth hover effects
- ✅ Auto-refresh when bot starts
- ✅ Handle loading and empty states
