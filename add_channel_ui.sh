#!/bin/bash

# Add channel card styles to dashboard.html
cat >> /tmp/channel_styles.css << 'EOF'

/* Channel Card Styles */
.channel-card-compact {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    transition: all 0.2s ease;
    margin-bottom: 8px;
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
EOF

echo "✅ Channel styles created"
echo ""
echo "📝 To integrate the nice channel UI:"
echo ""
echo "1. Add these data properties to your Vue app:"
echo "   telegramChannels: [],"
echo "   loadingChannels: false,"
echo ""
echo "2. Add these methods:"
echo ""
cat << 'METHODS'
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
    } catch (e) {
        console.error('Channels error:', e);
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
METHODS

echo ""
echo "3. Replace the 'Signal Channels' section in your sidebar with:"
echo ""
cat << 'HTML'
<!-- Channels with Profile Images -->
<div class="sidebar-section">
    <div class="sidebar-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"/><path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"/><circle cx="12" cy="12" r="2"/><path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"/><path d="M19.1 4.9C23 8.8 23 15.1 19.1 19"/></svg>
        Signal Channels
        <button class="btn btn-sm" @click="refreshChannels" :disabled="loadingChannels" style="margin-left: auto; padding: 4px 8px;">
            <svg v-if="loadingChannels" class="spinner" width="10" height="10"></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
        </button>
    </div>
    
    <!-- Loading -->
    <div v-if="loadingChannels && telegramChannels.length === 0" style="padding: 12px;">
        <div class="loading-skeleton" style="height: 60px; margin-bottom: 8px;" v-for="i in 2" :key="'skel-' + i"></div>
    </div>
    
    <!-- Channels List -->
    <div v-else-if="telegramChannels.length > 0" style="padding: 12px;">
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
    
    <button class="btn btn-secondary btn-sm" @click="navigateTo('settings')" style="margin: 0 12px 12px; width: calc(100% - 24px);">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
        Manage Channels
    </button>
</div>
HTML

echo ""
echo "4. Call refreshChannels() when bot starts successfully in your startBot() method"
echo ""
echo "✨ Done! Your channels will now show with profile images and nice UI!"
