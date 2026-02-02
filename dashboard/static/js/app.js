        const { createApp } = Vue;
        
        createApp({
            data() {
                return {
                    ws: null,
                    isDarkTheme: false,
                    showConfirmModal: false,
                    showLogoutModal: false,
                    showMT5LoginModal: false,
                    showMT5DisconnectModal: false,
                    showChannelSearchModal: false,
                    channelSearchQuery: '',
                    channelSearchResults: [],
                    selectedChannels: [],
                    loadingChannelSearch: false,
                    addingChannels: false,
                    channelSearchTimeout: null,
                    mt5Testing: false,
                    showMT5Password: false,
                    mt5Form: {
                        server: '',
                        login: '',
                        password: ''
                    },
                    mt5TestResult: null,
                    showMT5Dropdown: false,
                    filteredMT5Servers: [],
                    mt5ServerSearchTimeout: null,
                    loadingMT5Servers: false,
                    loggingOut: false,
                    showConnectionError: false,
                    connectionErrors: {
                        mt5: { status: 'pending', message: 'Waiting to connect...' },
                        telegram: { status: 'pending', message: 'Waiting to connect...' },
                        account: { status: 'pending', message: 'Waiting for MT5 connection...' }
                    },
                    showChannelDeleteModal: false,
                    channelToDelete: null,
                    confirmAction: 'start',
                    connectionSteps: {
                        mt5: 'pending',
                        telegram: 'pending',
                        account: 'pending'
                    },
                    expandedSections: {
                        telegram: false,
                        broker: false,
                        trading: true,
                        channels: false
                    },
                    editingField: null,
                    editValue: '',
                    newSignalChannel: '',
                    telegramFields: [
                        { key: 'api_id', label: 'API ID', masked: false, required: true },
                        { key: 'api_hash', label: 'API Hash', masked: true, required: true },
                        { key: 'phone_number', label: 'Phone', masked: false, required: true }
                    ],
                    brokerFields: [
                        { key: 'metaapi_token', label: 'Token', masked: true, required: true },
                        { key: 'metaapi_account_id', label: 'Account ID', masked: false, required: true }
                    ],
                    tradingFields: [
                        { key: 'default_lot_size', label: 'Lot Size', step: 0.01 },
                        { key: 'max_spread_pips', label: 'Max Spread', suffix: ' pips', step: 0.5 },
                        { key: 'max_open_trades', label: 'Max Trades', step: 1 },
                        { key: 'max_daily_drawdown_percent', label: 'Max Drawdown', suffix: '%', step: 0.5 }
                    ],
                    status: { 
                        bot_running: false, 
                        mt5_connected: false, 
                        telegram_connected: false,
                        uptime_seconds: 0
                    },
                    telegramSessionValid: false,
                    mt5SessionValid: false,
                    startingStep: 0,
                    telegramUser: {
                        id: null,
                        first_name: '',
                        last_name: '',
                        username: '',
                        phone: '',
                        photo_path: null,
                        premium: false,
                        api_id: null
                    },
                    account: { 
                        balance: 0, 
                        equity: 0, 
                        margin: 0, 
                        free_margin: 0, 
                        profit: 0,
                        currency: 'USD',
                        leverage: 0,
                        server: '',
                        login: 0,
                        name: ''
                    },
                    stats: { 
                        total_trades: 0, 
                        closed_trades: 0,
                        winning_trades: 0,
                        losing_trades: 0,
                        win_rate: 0, 
                        total_profit: 0, 
                        open_trades: 0,
                        last_updated: null
                    },
                    risk: { current_drawdown: 0 },
                    config: { 
                        default_lot_size: 0.01, 
                        max_spread_pips: 5.0, 
                        max_daily_drawdown_percent: 5.0, 
                        max_open_trades: 10 
                    },
                    settings: {
                        telegram: {
                            api_id: '',
                            api_hash: '',
                            phone_number: '',
                            session_name: 'evobot_session',
                            signal_channels: [],
                            signal_channels_str: '',
                            notification_channel: ''
                        },
                        broker: {
                            metaapi_token: '',
                            metaapi_account_id: '',
                            server: '',
                            login: '',
                            password: ''
                        },
                        trading: {
                            default_lot_size: 0.01,
                            max_spread_pips: 10,
                            max_open_trades: 10,
                            max_daily_drawdown_percent: 5,
                            entry_zone_tolerance: 20,
                            execute_immediately: true
                        },
                        risk: {
                            avoid_high_impact_news: true,
                            news_blackout_minutes_before: 30,
                            news_blackout_minutes_after: 15,
                            trading_start_hour: 0,
                            trading_end_hour: 24,
                            max_risk_percent_per_trade: 2
                        }
                    },
                    activeTrades: [],
                    mt5Positions: [],
                    groupedPositions: {},
                    groupPositionsView: localStorage.getItem('evobot-group-positions') !== 'false',
                    activities: [],
                    notifications: [],
                    loading: { 
                        start: false, 
                        stop: false, 
                        refresh: false,
                        positions: false,
                        settings: false,
                        trades: {},
                        initial: true,
                        reconnect: false
                    },
                    nextNotifId: 0,
                    priceCache: {},
                    startingPhase: null,
                    // Settings validation
                    settingsValidated: false,
                    settingsErrors: [],
                    showSetupWizard: false,
                    // Connection testing
                    testingTelegram: false,
                    testingBroker: false,
                    telegramTestResult: null,
                    brokerTestResult: null,
                    displayUptime: 0,
                    uptimeInterval: null,
                    // Navbar properties
                    navbarCollapsed: false,
                    activeNavItem: 'dashboard',
                    showUserMenu: false,
                    // Telegram channels
                    telegramChannels: [],
                    loadingChannels: false,
                    channelMetadata: {},
                    // Dummy signals data
                    dummySignals: [
                        { id: 1, channel: 'Premium Signals', symbol: 'XAUUSD', direction: 'BUY', entry: '2050.00', sl: '2045.00', tp1: '2055.00', tp2: '2060.00', tp3: '2065.00', status: 'TP3 Hit', profit: 150.50, time: '2 hours ago' },
                        { id: 2, channel: 'Forex Masters', symbol: 'EURUSD', direction: 'SELL', entry: '1.0850', sl: '1.0880', tp1: '1.0820', tp2: '1.0800', tp3: '1.0780', status: 'TP2 Hit', profit: 85.30, time: '4 hours ago' },
                        { id: 3, channel: 'Gold Traders', symbol: 'XAUUSD', direction: 'SELL', entry: '2048.50', sl: '2053.00', tp1: '2043.00', tp2: '2038.00', tp3: '2033.00', status: 'Active', profit: null, time: '1 hour ago' },
                        { id: 4, channel: 'Premium Signals', symbol: 'GBPUSD', direction: 'BUY', entry: '1.2650', sl: '1.2620', tp1: '1.2680', tp2: '1.2710', tp3: '1.2740', status: 'TP1 Hit', profit: 45.20, time: '3 hours ago' },
                        { id: 5, channel: 'Forex Masters', symbol: 'USDJPY', direction: 'BUY', entry: '148.50', sl: '148.00', tp1: '149.00', tp2: '149.50', tp3: '150.00', status: 'SL Hit', profit: -50.00, time: '5 hours ago' },
                        { id: 6, channel: 'Gold Traders', symbol: 'XAUUSD', direction: 'BUY', entry: '2052.00', sl: '2047.00', tp1: '2057.00', tp2: '2062.00', tp3: '2067.00', status: 'Active', profit: null, time: '30 mins ago' }
                    ],
                    selectedChannel: '',
                    // Signal messages data
                    signalMessages: [],
                    filteredSignalMessages: [],
                    signalChannelFilter: '',
                    signalStatusFilter: '',
                    signalDateFilter: 'all',
                    signalStartDate: '',
                    signalEndDate: '',
                    loadingSignals: false,
                    signalAnalytics: {},
                    expandedSignals: {},
                    showChannelDropdown: false,
                    showDateDropdown: false,
                    showSignalChart: false
                };
            },
            watch: {
                'status.bot_running'(newValue) {
                    if (newValue) {
                        document.documentElement.classList.add('bot-running');
                    } else {
                        document.documentElement.classList.remove('bot-running');
                    }
                },
                'account.balance'() { this.triggerNumberAnimation(); },
                'account.equity'() { this.triggerNumberAnimation(); },
                'account.free_margin'() { this.triggerNumberAnimation(); },
                'account.profit'() { this.triggerNumberAnimation(); },
                'stats.win_rate'() { this.triggerNumberAnimation(); },
                'mt5Positions.length'() { this.triggerNumberAnimation(); }
            },
            computed: {
                currencySymbol() {
                    const symbols = {
                        'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CHF': 'Fr',
                        'AUD': 'A$', 'CAD': 'C$', 'NZD': 'NZ$', 'SGD': 'S$', 'HKD': 'HK$',
                        'ZAR': 'R', 'INR': '₹', 'CNY': '¥', 'KRW': '₩', 'BRL': 'R$',
                        'MXN': 'Mex$', 'PLN': 'zł', 'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr',
                        'RUB': '₽', 'TRY': '₺', 'THB': '฿', 'MYR': 'RM', 'IDR': 'Rp'
                    };
                    return symbols[this.account.currency] || this.account.currency || '$';
                },
                totalPnL() {
                    return this.mt5Positions.reduce((sum, pos) => sum + (pos.profit || 0), 0);
                },
                
                filteredSignals() {
                    if (!this.selectedChannel) return this.dummySignals;
                    return this.dummySignals.filter(s => s.channel === this.selectedChannel);
                },
                
                channelStats() {
                    const signals = this.filteredSignals;
                    const closed = signals.filter(s => s.status !== 'Active');
                    const wins = closed.filter(s => s.profit && s.profit > 0);
                    const tp3Hits = signals.filter(s => s.status === 'TP3 Hit');
                    const totalProfit = closed.reduce((sum, s) => sum + (s.profit || 0), 0);
                    
                    return {
                        total: signals.length,
                        closed: closed.length,
                        wins: wins.length,
                        winRate: closed.length > 0 ? Math.round((wins.length / closed.length) * 100) : 0,
                        profit: totalProfit,
                        avgProfit: closed.length > 0 ? totalProfit / closed.length : 0,
                        tp3Count: tp3Hits.length,
                        tp3Rate: signals.length > 0 ? Math.round((tp3Hits.length / signals.length) * 100) : 0
                    };
                },
                hasRequiredSettings() {
                    // Check if minimum required settings are configured
                    const hasTelegram = this.settings.telegram.api_id && 
                                       this.settings.telegram.api_hash && 
                                       this.settings.telegram.phone_number &&
                                       (this.settings.telegram.signal_channels && this.settings.telegram.signal_channels.length > 0);
                    const hasBroker = this.settings.broker.metaapi_token && 
                                     this.settings.broker.metaapi_account_id;
                    return hasTelegram && hasBroker;
                },
                getMT5StatusText() {
                    if (this.status.mt5_connected) return 'Connected';
                    if (this.mt5SessionValid && !this.status.bot_running) return 'Logged In';
                    if (this.loading.reconnect) return 'Reconnecting...';
                    if (this.connectionSteps.mt5 === 'loading') return 'Connecting...';
                    if (this.connectionSteps.mt5 === 'failed') return 'Failed to Connect';
                    if (this.status.bot_running) return 'Failed to Connect';
                    return 'Not Connected';
                },
                getTelegramStatusText() {
                    if (this.status.telegram_connected) return 'Connected';
                    if (this.telegramSessionValid && !this.status.bot_running) return 'Logged In';
                    if (this.loading.reconnect) return 'Reconnecting...';
                    if (this.connectionSteps.telegram === 'loading') return 'Connecting...';
                    if (this.connectionSteps.telegram === 'failed') return 'Failed to Connect';
                    if (this.status.bot_running) return 'Failed to Connect';
                    return 'Not Connected';
                },
                getAccountStatusText() {
                    if (this.account.login > 0) return this.account.name || ('Account #' + this.account.login);
                    if (this.connectionSteps.account === 'loading') return 'Loading...';
                    if (this.status.bot_running) return 'No Account Data';
                    return 'Not Loaded';
                },
                getPageTitle() {
                    const titles = {
                        'dashboard': 'Dashboard Overview',
                        'trades': 'Open Positions',
                        'history': 'Trade History',
                        'stats': 'Statistics',
                        'settings': 'Settings',
                        'logs': 'System Logs'
                    };
                    return titles[this.activeNavItem] || 'Dashboard';
                }
            },
            methods: {
                // Theme toggle method
                toggleTheme() {
                    this.isDarkTheme = !this.isDarkTheme;
                    if (this.isDarkTheme) {
                        document.documentElement.classList.remove('light-theme');
                    } else {
                        document.documentElement.classList.add('light-theme');
                    }
                    localStorage.setItem('evobot-theme', this.isDarkTheme ? 'dark' : 'light');
                },
                
                // Format channel ID for display
                formatChannelId(channelId) {
                    const id = String(channelId);
                    if (id.startsWith('-100')) {
                        return 'ID: ' + id;
                    } else if (id.startsWith('-')) {
                        return 'ID: ' + id;
                    } else if (id.startsWith('@')) {
                        return id;
                    }
                    return 'ID: ' + id;
                },
                
                // Icon initialization methods
                initIcons() {
                    // Use requestAnimationFrame to ensure DOM is ready
                    requestAnimationFrame(() => {
                        try {
                            lucide.createIcons();
                        } catch (e) {
                            // Ignore errors from icon initialization
                        }
                    });
                },
                triggerNumberAnimation() {
                    this.$nextTick(() => {
                        document.querySelectorAll('.animated-number').forEach(el => {
                            const newValue = parseFloat(el.getAttribute('data-value'));
                            const oldValue = parseFloat(el.getAttribute('data-old-value') || newValue);
                            
                            if (newValue !== oldValue && !isNaN(newValue) && !isNaN(oldValue)) {
                                el.classList.remove('number-increase', 'number-decrease');
                                void el.offsetWidth;
                                
                                if (newValue > oldValue) {
                                    el.classList.add('number-increase');
                                } else if (newValue < oldValue) {
                                    el.classList.add('number-decrease');
                                }
                                
                                el.setAttribute('data-old-value', newValue);
                            }
                        });
                    });
                },
                debouncedInitIcons() {
                    if (this._iconTimeout) {
                        clearTimeout(this._iconTimeout);
                    }
                    this._iconTimeout = setTimeout(() => {
                        this.initIcons();
                    }, 100);
                },
                formatNumber(value) {
                    if (value === null || value === undefined) return '0.00';
                    return Number(value).toLocaleString('en-US', { 
                        minimumFractionDigits: 2, 
                        maximumFractionDigits: 2 
                    });
                },
                getInitials(name) {
                    if (!name) return '?';
                    return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
                },
                getChannelInfo(channelId) {
                    if (!channelId) return null;
                    const sid = String(channelId);
                    const nid = sid.startsWith('-100') ? sid : (sid.startsWith('-') ? sid.replace('-', '-100') : '-100' + sid);
                    const cleanId = sid.replace('-100', '').replace('-', '');
                    
                    // Priority 1: Check rich metadata cache (Firebase backed)
                    if (this.channelMetadata) {
                        const info = this.channelMetadata[sid] || this.channelMetadata[nid] || this.channelMetadata[cleanId];
                        if (info) return info;
                    }
                    
                    // Priority 2: Check standard channels list (Telethon cache)
                    if (this.telegramChannels && this.telegramChannels.length > 0) {
                        const found = this.telegramChannels.find(ch => {
                            const cid = String(ch.id);
                            return cid === sid || cid === nid || cid === cleanId || cid.endsWith(cleanId);
                        });
                        if (found) return found;
                    }

                    // Priority 3: Check search results if in modal
                    if (this.channelSearchResults && this.channelSearchResults.length > 0) {
                        const found = this.channelSearchResults.find(ch => {
                            const cid = String(ch.id);
                            return cid === sid || cid === nid || cid === cleanId || cid.endsWith(cleanId);
                        });
                        if (found) return found;
                    }

                    return null;
                },
                getChannelName(channelId, index) {
                    const info = this.getChannelInfo(channelId);
                    return info?.title || (String(channelId).startsWith('-') ? `Channel ${String(channelId).replace(/^-100/, '')}` : channelId);
                },
                getChannelInitials(channelId, index) {
                    const info = this.getChannelInfo(channelId);
                    if (info?.title) {
                        return info.title.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
                    }
                    return 'CH';
                },
                hasChannelPhoto(channelId) {
                    const info = this.getChannelInfo(channelId);
                    return info?.photo_path || info?.has_photo;
                },
                getChannelPhoto(channelId) {
                    const info = this.getChannelInfo(channelId);
                    if (info?.photo_path || info?.has_photo) {
                        const id = info.id || channelId;
                        return { backgroundImage: `url(/api/telegram/channel/${id}/photo)` };
                    }
                    return {};
                },
                getChannelDisplayId(channelId) {
                    const info = this.getChannelInfo(channelId);
                    const id = info?.username || info?.id || channelId;
                    if (String(id).startsWith('@')) return id;
                    if (String(id).startsWith('-100')) return '@' + String(id).replace('-100', '');
                    if (String(id).startsWith('-')) return id;
                    return '@' + id;
                },
                formatNumberCompact(num) {
                    if (!num || isNaN(num)) return '0';
                    if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
                    if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
                    return num.toString();
                },
                isChannelVerified(channelId) {
                    const info = this.getChannelInfo(channelId);
                    return info?.verified === true;
                },
                async fetchTelegramUser() {
                    try {
                        const res = await fetch('/api/telegram/user');
                        if (res.ok) {
                            const data = await res.json();
                            if (data.user) {
                                this.telegramUser = {
                                    ...this.telegramUser,
                                    ...data.user,
                                    api_id: data.api_id
                                };
                                // Mark Telegram session as valid if we got user data
                                this.telegramSessionValid = true;
                            }
                        }
                    } catch (e) {
                        console.error('Error fetching telegram user:', e);
                    }
                },
                formatPrice(value, symbol) {
                    if (!value) return '-';
                    const digits = symbol?.includes('JPY') ? 3 : (symbol?.includes('XAU') ? 2 : 5);
                    return Number(value).toFixed(digits);
                },
                formatUptime(seconds) {
                    if (!seconds) return '0s';
                    const hours = Math.floor(seconds / 3600);
                    const minutes = Math.floor((seconds % 3600) / 60);
                    const secs = Math.floor(seconds % 60);
                    if (hours > 0) return `${hours}h ${minutes}m`;
                    if (minutes > 0) return `${minutes}m ${secs}s`;
                    return `${secs}s`;
                },
                formatSignalTime(timestamp) {
                    if (!timestamp) return 'Unknown time';
                    const date = new Date(timestamp);
                    return date.toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                },
                // Confirmation modal methods
                confirmStart() {
                    if (!this.hasRequiredSettings) {
                        this.expandedSections.telegram = true;
                        this.expandedSections.broker = true;
                        this.notify('Please configure Telegram and MetaApi settings first', 'warning');
                        return;
                    }
                    this.confirmAction = 'start';
                    this.showConfirmModal = true;
                    
                },
                confirmStop() {
                    this.confirmAction = 'stop';
                    this.showConfirmModal = true;
                    
                },
                async executeConfirmedAction() {
                    // Close modal immediately before starting action
                    this.showConfirmModal = false;
                    
                    // Small delay to let modal close animation finish
                    await this.$nextTick();
                    
                    if (this.confirmAction === 'start') {
                        await this.startBot();
                    } else {
                        await this.stopBot();
                    }
                },
                // Inline edit methods
                toggleSection(section) {
                    this.expandedSections[section] = !this.expandedSections[section];
                },
                getFieldDisplay(section, field) {
                    const value = this.settings[section][field.key];
                    if (!value) return field.required ? '(not set)' : '-';
                    if (field.masked) return '••••••••';
                    if (String(value).length > 15) return String(value).substring(0, 12) + '...';
                    return value;
                },
                startEdit(section, key, value) {
                    this.editingField = `${section}.${key}`;
                    this.editValue = value || '';
                    this.$nextTick(() => {
                        const input = document.querySelector('.inline-edit-input input');
                        if (input) input.focus();
                    });
                },
                async saveEdit(section, key) {
                    const oldValue = this.settings[section][key];
                    this.settings[section][key] = this.editValue;
                    this.editingField = null;
                    
                    // Auto-save to server
                    try {
                        const payload = {
                            telegram: {
                                ...this.settings.telegram
                            },
                            broker: this.settings.broker,
                            trading: this.settings.trading,
                            risk: this.settings.risk
                        };
                        
                        const res = await fetch('/api/settings', {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        
                        if (res.ok) {
                            this.notify('Setting saved', 'success');
                        } else {
                            this.settings[section][key] = oldValue;
                            this.notify('Failed to save setting', 'error');
                        }
                    } catch (e) {
                        this.settings[section][key] = oldValue;
                        this.notify('Failed to save setting', 'error');
                    }
                    
                },
                cancelEdit() {
                    this.editingField = null;
                    
                },
                // Channel management methods
                async addSignalChannel() {
                    const channel = this.newSignalChannel.trim();
                    if (!channel) return;
                    
                    // Parse as number if it looks like a channel ID
                    const channelValue = /^-?\d+$/.test(channel) ? parseInt(channel) : channel;
                    
                    if (this.settings.telegram.signal_channels.includes(channelValue)) {
                        this.notify('Channel already exists', 'warning');
                        return;
                    }
                    
                    this.settings.telegram.signal_channels.push(channelValue);
                    this.newSignalChannel = '';
                    
                    // Save to server
                    try {
                        const res = await fetch('/api/settings/telegram/channels', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                signal_channels: this.settings.telegram.signal_channels,
                                notification_channel: this.settings.telegram.notification_channel
                            })
                        });
                        
                        if (res.ok) {
                            this.notify('Signal channel added', 'success');
                        } else {
                            this.settings.telegram.signal_channels.pop();
                            this.notify('Failed to add channel', 'error');
                        }
                    } catch (e) {
                        this.settings.telegram.signal_channels.pop();
                        this.notify('Failed to add channel', 'error');
                    }
                },
                async removeSignalChannel(index) {
                    const removed = this.settings.telegram.signal_channels[index];
                    const info = this.getChannelInfo(removed);
                    
                    // Show custom delete confirmation modal
                    this.channelToDelete = {
                        id: removed,
                        name: info?.title || this.getChannelName(removed, index),
                        displayId: this.getChannelDisplayId(removed),
                        index: index
                    };
                    this.showChannelDeleteModal = true;
                },
                async confirmChannelDelete() {
                    if (!this.channelToDelete) return;
                    
                    const index = this.channelToDelete.index;
                    const removed = this.settings.telegram.signal_channels[index];
                    
                    // Close modal immediately
                    this.showChannelDeleteModal = false;
                    
                    this.settings.telegram.signal_channels.splice(index, 1);
                    
                    try {
                        const token = localStorage.getItem('token');
                        const res = await fetch('/api/telegram/channels/remove', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + token
                            },
                            body: JSON.stringify({
                                channel_id: String(removed)
                            })
                        });
                        
                        if (res.ok) {
                            const data = await res.json();
                            this.settings.telegram.signal_channels = data.channels || [];
                            this.notify('Channel removed', 'success');
                            this.addActivity(`Removed source ${removed}`, 'danger', 'trash-2');
                        } else {
                            const error = await res.json();
                            this.settings.telegram.signal_channels.splice(index, 0, removed);
                            this.notify(error.detail || 'Failed to remove channel', 'error');
                        }
                    } catch (e) {
                        this.settings.telegram.signal_channels.splice(index, 0, removed);
                        this.notify('Failed to remove channel', 'error');
                    }
                },
                async removeSignalChannelById(channelId) {
                    const index = this.settings.telegram.signal_channels.indexOf(channelId);
                    if (index !== -1) {
                        await this.removeSignalChannel(index);
                    } else {
                        // Try matching normalized ID
                        const sid = String(channelId);
                        const nid = sid.startsWith('-100') ? sid : (sid.startsWith('-') ? sid.replace('-', '-100') : '-100' + sid);
                        const cleanId = sid.replace('-100', '').replace('-', '');
                        
                        const altIndex = this.settings.telegram.signal_channels.findIndex(id => {
                            const cid = String(id);
                            return cid === sid || cid === nid || cid === cleanId;
                        });
                        
                        if (altIndex !== -1) {
                            await this.removeSignalChannel(altIndex);
                        }
                    }
                },
                async saveNotificationChannel() {
                    const oldValue = this.settings.telegram.notification_channel;
                    const newValue = this.editValue.trim();
                    
                    // Parse as number if it looks like a channel ID
                    this.settings.telegram.notification_channel = /^-?\d+$/.test(newValue) ? parseInt(newValue) : newValue;
                    this.editingField = null;
                    
                    try {
                        const res = await fetch('/api/settings/telegram/channels', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                signal_channels: this.settings.telegram.signal_channels,
                                notification_channel: this.settings.telegram.notification_channel
                            })
                        });
                        
                        if (res.ok) {
                            this.notify('Notification channel updated', 'success');
                        } else {
                            this.settings.telegram.notification_channel = oldValue;
                            this.notify('Failed to update channel', 'error');
                        }
                    } catch (e) {
                        this.settings.telegram.notification_channel = oldValue;
                        this.notify('Failed to update channel', 'error');
                    }
                    
                },
                getNotifIcon(type) {
                    const icons = {
                        success: 'check-circle',
                        error: 'alert-circle',
                        warning: 'alert-triangle',
                        info: 'info'
                    };
                    return icons[type] || 'info';
                },
                getNotifTitle(type) {
                    const titles = {
                        success: 'Success',
                        error: 'Error',
                        warning: 'Warning',
                        info: 'Info'
                    };
                    return titles[type] || 'Notification';
                },
                dismissNotification(id) {
                    const notif = this.notifications.find(n => n.id === id);
                    if (notif) {
                        notif.removing = true;
                        setTimeout(() => {
                            this.notifications = this.notifications.filter(n => n.id !== id);
                        }, 250);
                    }
                },
                async retryConnection() {
                    if (this.loading.reconnect) return;
                    
                    this.loading.reconnect = true;
                    this.addActivity('Retrying connections...', 'info', 'refresh-cw');
                    
                    try {
                        const res = await fetch('/api/bot/reconnect', { method: 'POST' });
                        if (!res.ok) {
                            const err = await res.json();
                            throw new Error(err.detail || 'Reconnect failed');
                        }
                        
                        const data = await res.json();
                        
                        // Update status based on results
                        this.status.mt5_connected = data.mt5_connected;
                        this.status.telegram_connected = data.telegram_connected;
                        
                        // Show results
                        if (data.mt5_connected && data.telegram_connected) {
                            this.showNotification('All services reconnected successfully!', 'success');
                            this.addActivity('All connections restored', 'success', 'check-circle');
                        } else {
                            const failed = [];
                            if (!data.mt5_connected) failed.push('MT5');
                            if (!data.telegram_connected) failed.push('Telegram');
                            this.showNotification(`Reconnect completed. Failed: ${failed.join(', ')}`, 'warning');
                            this.addActivity(`Reconnect partial: ${failed.join(', ')} still disconnected`, 'warning', 'alert-triangle');
                        }
                        
                        // Refresh all data
                        await this.refreshData();
                        
                    } catch (e) {
                        console.error('Reconnect error:', e);
                        this.showNotification(`Reconnect failed: ${e.message}`, 'error');
                        this.addActivity('Reconnect failed', 'error', 'x-circle');
                    } finally {
                        this.loading.reconnect = false;
                    }
                },
                async refreshData() {
                    this.loading.refresh = true;
                    try {
                        const res = await fetch('/api/status');
                        if (!res.ok) throw new Error('Failed to fetch status');
                        const data = await res.json();
                        
                        this.status = {
                            bot_running: data.bot_running,
                            mt5_connected: data.mt5_connected,
                            telegram_connected: data.telegram_connected,
                            uptime_seconds: data.uptime_seconds || 0
                        };
                        
                        if (data.account) {
                            this.account = {
                                balance: data.account.balance || 0,
                                equity: data.account.equity || 0,
                                margin: data.account.margin || 0,
                                free_margin: data.account.free_margin || 0,
                                profit: data.account.profit || 0,
                                currency: data.account.currency || 'USD',
                                leverage: data.account.leverage || 0,
                                server: data.account.server || '',
                                login: data.account.login || 0
                            };
                        }
                        
                        if (data.stats) {
                            this.stats = {
                                total_trades: data.stats.total_trades || 0,
                                closed_trades: data.stats.closed_trades || 0,
                                winning_trades: data.stats.winning_trades || 0,
                                losing_trades: data.stats.losing_trades || 0,
                                win_rate: data.stats.win_rate || 0,
                                total_profit: data.stats.total_profit || 0,
                                open_trades: data.stats.open_trades || 0,
                                last_updated: data.stats.last_updated || new Date().toISOString()
                            };
                        }
                        
                        if (data.risk) {
                            this.risk = data.risk;
                        }
                        
                        if (data.config) {
                            this.config = data.config;
                        }
                        
                        await this.refreshTrades();
                        
                        // Always try to load channel info (API returns cached metadata from Firebase)
                        await this.refreshChannelDetails();

                        // Fetch additional info if Telegram is connected
                        if (this.status.telegram_connected) {
                            await this.refreshChannels();
                        }
                        
                        this.loading.initial = false;
                    } catch (e) {
                        console.error('Refresh error:', e);
                        if (this.loading.initial) {
                            this.notify('Unable to connect to server. Please check if the bot is running.', 'error');
                        }
                    } finally {
                        this.loading.refresh = false;
                    }
                },
                async refreshTrades() {
                    try {
                        const res = await fetch('/api/trades?active_only=true');
                        if (!res.ok) throw new Error('Failed to fetch trades');
                        const data = await res.json();
                        this.activeTrades = data.trades || [];
                    } catch (e) {
                        console.error('Trades error:', e);
                    }
                },
                async refreshChannels(forceRefresh = false) {
                    // Refresh rich metadata first
                    await this.refreshChannelDetails(forceRefresh);
                    
                    // Fetch channels - API will auto-fetch from Telegram if cache is stale
                    this.loadingChannels = true;
                    try {
                        const token = localStorage.getItem('token');
                        const url = forceRefresh ? '/api/telegram/channels?refresh=true' : '/api/telegram/channels';
                        const res = await fetch(url, {
                            headers: { 'Authorization': 'Bearer ' + token }
                        });
                        if (!res.ok) throw new Error('Failed to fetch channels');
                        const data = await res.json();
                        this.telegramChannels = data.channels || [];
                        console.log('Channels loaded:', this.telegramChannels.length);
                    } catch (e) {
                        console.error('Channels error:', e);
                    } finally {
                        this.loadingChannels = false;
                    }
                },
                setPositionsView(grouped) {
                    this.groupPositionsView = grouped;
                    localStorage.setItem('evobot-group-positions', grouped ? 'true' : 'false');
                },
                async refreshPositions() {
                    this.loading.positions = true;
                    try {
                        const res = await fetch('/api/positions');
                        if (!res.ok) throw new Error('Failed to fetch positions');
                        const data = await res.json();
                        this.mt5Positions = data.positions || [];
                        this.groupedPositions = data.grouped || {};
                    } catch (e) {
                        console.error('Positions error:', e);
                    } finally {
                        this.loading.positions = false;
                    }
                },
                async closePosition(ticket) {
                    this.loading.trades[ticket] = true;
                    try {
                        const res = await fetch(`/api/positions/${ticket}/close`, { method: 'POST' });
                        if (res.ok) {
                            this.notify('Position closed successfully', 'success');
                            this.addActivity(`Closed #${ticket}`, 'danger', 'x');
                            await this.refreshPositions();
                        } else {
                            const data = await res.json();
                            this.notify(data.detail || 'Failed to close position', 'error');
                        }
                    } catch (e) {
                        this.notify('Connection error', 'error');
                    } finally {
                        delete this.loading.trades[ticket];
                    }
                },
                openModifyModal(position) {
                    // TODO: Implement modify SL/TP modal
                    this.notify('Modify SL/TP feature coming soon', 'info');
                },
                async startBot() {
                    // Check settings before starting
                    if (!this.hasRequiredSettings) {
                        this.expandedSections.telegram = true;
                        this.expandedSections.broker = true;
                        this.notify('Please configure required settings before starting the bot', 'warning');
                        
                        return;
                    }
                    
                    this.loading.start = true;
                    this.startingPhase = 'connecting';
                    this.startingStep = 0;
                    
                    // Reset connection steps to loading state
                    this.connectionSteps = {
                        mt5: 'loading',
                        telegram: 'pending',
                        account: 'pending'
                    };
                    
                    // Force Vue to update
                    await this.$nextTick();
                    
                    // Animate through steps
                    this.startingStep = 1;
                    await this.sleep(400);
                    this.startingStep = 2;
                    await this.sleep(500);
                    this.startingStep = 3;
                    
                    try {
                        const res = await fetch('/api/bot/start', { method: 'POST' });
                        const data = await res.json();
                        
                        this.startingStep = 4;
                        
                        if (!res.ok) {
                            this.notify(data.detail || 'Failed to start bot', 'error');
                            this.connectionSteps.mt5 = 'error';
                            this.startingPhase = null;
                            this.startingStep = 0;
                            this.status.bot_running = false;
                            return;
                        }
                        
                        // Check if startup failed (not all connections succeeded)
                        if (data.status === 'failed') {
                            // Update connection steps based on actual connection state
                            this.connectionSteps.mt5 = data.mt5_connected ? 'success' : 'failed';
                            this.connectionSteps.telegram = data.telegram_connected ? 'success' : 'failed';
                            this.connectionSteps.account = data.account_ok ? 'success' : 'failed';
                            
                            // Update connection error details for modal
                            this.connectionErrors = {
                                mt5: {
                                    status: data.mt5_connected ? 'success' : 'failed',
                                    message: data.mt5_connected ? 'Connected successfully' : (data.errors?.find(e => e.includes('MT5')) || 'Connection failed - check credentials')
                                },
                                telegram: {
                                    status: data.telegram_connected ? 'success' : 'failed',
                                    message: data.telegram_connected ? 'Connected successfully' : (data.errors?.find(e => e.includes('Telegram')) || 'Connection failed - check API credentials')
                                },
                                account: {
                                    status: data.account_ok ? 'success' : 'failed',
                                    message: data.account_ok ? 'Account loaded successfully' : (data.errors?.find(e => e.includes('Account')) || 'Unable to load account - MT5 not connected')
                                }
                            };
                            
                            // Show professional connection error modal
                            this.showConnectionError = true;
                            this.addActivity('Bot Startup Failed', 'danger', 'x-circle');
                            
                            this.startingPhase = null;
                            this.startingStep = 0;
                            this.status.bot_running = false;
                            return;
                        }
                        
                        // Bot started successfully - all connections are good
                        this.status.bot_running = true;
                        this.status.mt5_connected = data.mt5_connected;
                        this.status.telegram_connected = data.telegram_connected;
                        
                        // Update connection steps - all should be success
                        this.connectionSteps.mt5 = 'success';
                        this.connectionSteps.telegram = 'success';
                        this.connectionSteps.account = 'success';
                        
                        this.notify('Connected to MT5 broker ✓', 'success');
                        this.notify('Telegram listener active ✓', 'success');
                        this.notify('🚀 Bot is now live and monitoring signals!', 'success');
                        this.addActivity('Bot Started - All Connected', 'success', 'play');
                        
                        this.startingPhase = 'started';
                        
                        // Start uptime counter
                        this.startUptimeCounter();
                        
                        // Fetch positions immediately
                        this.refreshPositions();
                        
                        // Clear starting phase after a delay
                        await this.sleep(1500);
                        this.startingPhase = null;
                        
                    } catch (e) {
                        console.error('Start bot error:', e);
                        this.notify('Connection error. Please check your network.', 'error');
                        this.connectionSteps.mt5 = 'error';
                        this.startingPhase = null;
                        this.startingStep = 0;
                        this.status.bot_running = false;
                    } finally {
                        this.loading.start = false;
                        this.startingStep = 0;
                        await this.$nextTick();
                        
                        // Refresh data after a delay to let server state settle
                        setTimeout(() => {
                            this.refreshData();
                        }, 1000);
                    }
                },
                sleep(ms) {
                    return new Promise(resolve => setTimeout(resolve, ms));
                },
                async retryConnection() {
                    this.showConnectionError = false;
                    await this.$nextTick();
                    await this.startBot();
                },
                startUptimeCounter() {
                    // Clear any existing interval
                    if (this.uptimeInterval) {
                        clearInterval(this.uptimeInterval);
                    }
                    // Update uptime every second
                    this.uptimeInterval = setInterval(() => {
                        if (this.status.bot_running) {
                            this.displayUptime++;
                        }
                    }, 1000);
                },
                async stopBot() {
                    this.loading.stop = true;
                    
                    // Set bot stopped immediately so buttons update
                    this.status.bot_running = false;
                    
                    // Force Vue to update
                    await this.$nextTick();
                    
                    
                    try {
                        const res = await fetch('/api/bot/stop', { method: 'POST' });
                        if (!res.ok) {
                            const data = await res.json();
                            this.notify(data.detail || 'Failed to stop bot', 'error');
                            // Revert status on failure
                            this.status.bot_running = true;
                        } else {
                            // Stop uptime counter
                            if (this.uptimeInterval) {
                                clearInterval(this.uptimeInterval);
                                this.uptimeInterval = null;
                            }
                            this.displayUptime = 0;
                            
                            // Reset connection status
                            this.status.mt5_connected = false;
                            this.status.telegram_connected = false;
                            
                            // Reset connection steps
                            this.connectionSteps = {
                                mt5: 'pending',
                                telegram: 'pending',
                                signals: 'pending'
                            };
                            
                            this.notify('Trading bot stopped successfully', 'success');
                            this.addActivity('Bot Stopped', 'danger', 'square');
                        }
                    } catch (e) {
                        this.notify('Connection error. Please check your network.', 'error');
                        // Revert status on error
                        this.status.bot_running = true;
                    } finally {
                        this.loading.stop = false;
                        // Force UI update without calling refreshData (which would overwrite our status)
                        await this.$nextTick();
                        
                        
                        // Refresh other data after a delay to let server state settle
                        setTimeout(() => {
                            this.refreshData();
                        }, 1000);
                    }
                },
                async closeTrade(id) {
                    if (!confirm('Are you sure you want to close this trade?')) return;
                    this.loading.trades[id] = true;
                    try {
                        const res = await fetch(`/api/trades/${id}/close`, { method: 'POST' });
                        if (res.ok) {
                            this.notify('Trade closed successfully', 'success');
                            this.addActivity('Trade Closed', 'danger', 'x');
                            this.refreshData();
                        } else {
                            const data = await res.json();
                            this.notify(data.detail || 'Failed to close trade', 'error');
                        }
                    } catch (e) {
                        this.notify('Connection error. Please try again.', 'error');
                    } finally {
                        delete this.loading.trades[id];
                    }
                },
                connectWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws`;
                    console.log('Connecting to WebSocket:', wsUrl);
                    this.ws = new WebSocket(wsUrl);
                    
                    this.ws.onopen = () => {
                        console.log('WebSocket connected');
                    };
                    
                    this.ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        
                        // Handle real-time account updates
                        if (data.type === 'account_update') {
                            const acc = data.data;
                            this.account = {
                                balance: acc.balance || 0,
                                equity: acc.equity || 0,
                                margin: acc.margin || 0,
                                free_margin: acc.free_margin || 0,
                                profit: acc.profit || 0,
                                currency: acc.currency || 'USD',
                                leverage: acc.leverage || 0,
                                server: acc.server || '',
                                login: acc.login || 0
                            };
                        }
                        // Handle real-time positions updates
                        else if (data.type === 'positions_update') {
                            const newPositions = data.data.positions || [];
                            // Force complete array replacement to trigger Vue reactivity
                            this.mt5Positions = newPositions.map(pos => ({
                                id: pos.id || pos.position_ticket,
                                position_ticket: pos.position_ticket || pos.id,
                                symbol: pos.symbol,
                                direction: pos.direction,
                                lot_size: pos.lot_size || pos.volume,
                                entry_price: pos.entry_price || pos.open_price,
                                current_price: pos.current_price || pos.price_current || 0,
                                stop_loss: pos.stop_loss || pos.sl,
                                take_profit: pos.take_profit || pos.tp,
                                take_profit_1: pos.take_profit_1 || pos.tp1,
                                profit: pos.profit || 0,
                                swap: pos.swap || 0,
                                commission: pos.commission || 0,
                                time: pos.time
                            }));
                        }
                        // Handle real-time stats updates
                        else if (data.type === 'stats_update') {
                            const statsData = data.data;
                            this.stats = {
                                total_trades: statsData.total_trades || 0,
                                closed_trades: statsData.closed_trades || 0,
                                winning_trades: statsData.winning_trades || 0,
                                losing_trades: statsData.losing_trades || 0,
                                win_rate: statsData.win_rate || 0,
                                total_profit: statsData.total_profit || 0,
                                open_trades: statsData.open_trades || 0,
                                last_updated: statsData.last_updated || new Date().toISOString()
                            };
                        }
                        // Handle startup progress updates
                        else if (data.type === 'startup_progress') {
                            const { step, status, message, connected } = data.data;
                            
                            // Update connectionSteps for UI progress indicators
                            if (step === 'mt5') {
                                this.connectionSteps.mt5 = status;
                                // Update actual status based on connected flag
                                if (status === 'success') {
                                    this.status.mt5_connected = true;
                                } else if (status === 'failed' || status === 'error' || status === 'warning') {
                                    this.status.mt5_connected = connected === true;
                                }
                            } else if (step === 'telegram') {
                                this.connectionSteps.telegram = status;
                                if (status === 'success') {
                                    this.status.telegram_connected = true;
                                } else if (status === 'failed' || status === 'error' || status === 'warning') {
                                    this.status.telegram_connected = connected === true;
                                }
                            } else if (step === 'account') {
                                this.connectionSteps.account = status;
                            }
                            
                            if (step === 'error') {
                                this.connectionSteps.mt5 = 'error';
                                this.notify(message || 'Startup failed', 'error');
                            }
                        } else if (data.type === 'bot_started') {
                            // Don't override - use actual connection states from data
                            if (data.data.mt5_connected !== undefined) {
                                this.status.mt5_connected = data.data.mt5_connected;
                                this.connectionSteps.mt5 = data.data.mt5_connected ? 'success' : 'failed';
                            }
                            if (data.data.telegram_connected !== undefined) {
                                this.status.telegram_connected = data.data.telegram_connected;
                                this.connectionSteps.telegram = data.data.telegram_connected ? 'success' : 'failed';
                            }
                            this.connectionSteps.account = 'success';
                            this.status.bot_running = true;
                            this.addActivity('Bot Started', 'success', 'play');
                            this.refreshData();
                            this.refreshPositions();
                        } else if (data.type === 'reconnect_progress') {
                            const { service, status, message } = data.data;
                            if (service === 'mt5') {
                                if (status === 'connecting') {
                                    this.connectionSteps.mt5 = 'loading';
                                } else if (status === 'success') {
                                    this.status.mt5_connected = true;
                                    this.connectionSteps.mt5 = 'success';
                                } else {
                                    this.connectionSteps.mt5 = 'failed';
                                }
                            } else if (service === 'telegram') {
                                if (status === 'connecting') {
                                    this.connectionSteps.telegram = 'loading';
                                } else if (status === 'success') {
                                    this.status.telegram_connected = true;
                                    this.connectionSteps.telegram = 'success';
                                } else {
                                    this.connectionSteps.telegram = 'failed';
                                }
                            }
                        } else if (data.type === 'signal_received') {
                            this.addActivity(`Signal: ${data.data.symbol} ${data.data.direction}`, 'success', 'zap');
                            this.notify(`Signal: ${data.data.symbol} ${data.data.direction}`, 'info');
                        } else if (data.type === 'trade_created') {
                            this.addActivity(`Trade: ${data.data.trade?.symbol}`, 'success', 'trending-up');
                            this.notify(`Trade opened: ${data.data.trade?.symbol}`, 'success');
                        } else if (data.type === 'signal_rejected') {
                            this.addActivity(`Rejected: ${data.data.reason}`, 'danger', 'x-circle');
                        } else if (data.type === 'startup_failed') {
                            // Handle startup failure - update UI to show failed state
                            this.status.bot_running = false;
                            this.startingPhase = null;
                            
                            if (data.data.mt5_connected !== undefined) {
                                this.status.mt5_connected = data.data.mt5_connected;
                                this.connectionSteps.mt5 = data.data.mt5_connected ? 'success' : 'failed';
                            }
                            if (data.data.telegram_connected !== undefined) {
                                this.status.telegram_connected = data.data.telegram_connected;
                                this.connectionSteps.telegram = data.data.telegram_connected ? 'success' : 'failed';
                            }
                            if (data.data.account_ok !== undefined) {
                                this.connectionSteps.account = data.data.account_ok ? 'success' : 'failed';
                            }
                            
                            // Show error message
                            const msg = data.data.message || 'Startup failed';
                            this.notify(`❌ ${msg}`, 'error');
                            this.addActivity('Startup Failed', 'danger', 'x-circle');
                        }
                    };
                    
                    this.ws.onclose = () => {
                        console.log('WebSocket disconnected, reconnecting...');
                        setTimeout(() => this.connectWebSocket(), 3000);
                    };
                    
                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                    };
                },
                addActivity(title, type, icon) {
                    this.activities.unshift({
                        id: Date.now() + Math.random(),
                        title,
                        time: new Date().toLocaleTimeString(),
                        type,
                        icon
                    });
                    if (this.activities.length > 20) {
                        this.activities.pop();
                    }
                    
                },
                notify(message, type = 'info') {
                    const id = this.nextNotifId++;
                    this.notifications.push({ id, message, type, removing: false });
                    
                    // Auto-dismiss after timeout
                    const timeout = type === 'error' ? 8000 : type === 'warning' ? 6000 : 4000;
                    setTimeout(() => {
                        this.dismissNotification(id);
                    }, timeout);
                    
                    // Re-initialize icons for new notification
                    this.$nextTick(() => {
                        
                    });
                },
                async loadSettings() {
                    this.loading.settings = true;
                    try {
                        const res = await fetch('/api/settings');
                        if (res.ok) {
                            const data = await res.json();
                            if (data.telegram) {
                                this.settings.telegram = {
                                    ...this.settings.telegram,
                                    ...data.telegram,
                                    signal_channels: data.telegram.signal_channels || [],
                                    signal_channels_str: (data.telegram.signal_channels || []).join(', ')
                                };
                            }
                            if (data.broker) {
                                this.settings.broker = { ...this.settings.broker, ...data.broker };
                            }
                            if (data.trading) {
                                this.settings.trading = { ...this.settings.trading, ...data.trading };
                            }
                            if (data.risk) {
                                this.settings.risk = { ...this.settings.risk, ...data.risk };
                            }
                            this.notify('Settings loaded successfully', 'success');
                        } else {
                            this.notify('Failed to load settings', 'error');
                        }
                    } catch (e) {
                        console.error('Load settings error:', e);
                        this.notify('Failed to load settings', 'error');
                    } finally {
                        this.loading.settings = false;
                        
                    }
                },
                async saveSettings() {
                    // Validate before saving
                    if (!this.validateSettings()) {
                        this.notify('Please fill in all required fields', 'error');
                        return;
                    }
                    
                    this.loading.settings = true;
                    try {
                        // Parse signal channels from string
                        const signalChannels = this.settings.telegram.signal_channels_str
                            .split(',')
                            .map(s => s.trim())
                            .filter(s => s)
                            .map(s => parseInt(s) || s);
                        
                        const payload = {
                            telegram: {
                                ...this.settings.telegram,
                                signal_channels: signalChannels
                            },
                            broker: this.settings.broker,
                            trading: this.settings.trading,
                            risk: this.settings.risk
                        };
                        
                        const res = await fetch('/api/settings', {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        
                        if (res.ok) {
                            this.notify('Settings saved successfully! Restart bot to apply changes.', 'success');
                            this.addActivity('Settings Updated', 'success', 'settings');
                            this.settingsErrors = [];
                        } else {
                            const data = await res.json();
                            this.notify(data.detail || 'Failed to save settings', 'error');
                        }
                    } catch (e) {
                        console.error('Save settings error:', e);
                        this.notify('Failed to save settings', 'error');
                    } finally {
                        this.loading.settings = false;
                    }
                },
                validateSettings() {
                    this.settingsValidated = true;
                    this.settingsErrors = [];
                    
                    // Check Telegram credentials
                    if (!this.settings.telegram.api_id) {
                        this.settingsErrors.push('Telegram API ID is required');
                    }
                    if (!this.settings.telegram.api_hash) {
                        this.settingsErrors.push('Telegram API Hash is required');
                    }
                    if (!this.settings.telegram.phone_number) {
                        this.settingsErrors.push('Telegram Phone Number is required');
                    }
                    if (!this.settings.telegram.signal_channels_str) {
                        this.settingsErrors.push('At least one Signal Channel is required');
                    }
                    
                    // Check Broker credentials
                    if (!this.settings.broker.metaapi_token) {
                        this.settingsErrors.push('MetaApi Token is required');
                    }
                    if (!this.settings.broker.metaapi_account_id) {
                        this.settingsErrors.push('MetaApi Account ID is required');
                    }
                    
                    
                    return this.settingsErrors.length === 0;
                },
                async testTelegramConnection() {
                    this.testingTelegram = true;
                    this.telegramTestResult = null;
                    try {
                        const res = await fetch('/api/test/telegram', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                api_id: this.settings.telegram.api_id,
                                api_hash: this.settings.telegram.api_hash,
                                phone_number: this.settings.telegram.phone_number
                            })
                        });
                        const data = await res.json();
                        this.telegramTestResult = {
                            success: res.ok,
                            message: data.message || (res.ok ? 'Connection successful!' : 'Connection failed')
                        };
                    } catch (e) {
                        this.telegramTestResult = {
                            success: false,
                            message: 'Connection test failed: ' + e.message
                        };
                    } finally {
                        this.testingTelegram = false;
                        
                    }
                },
                async testBrokerConnection() {
                    this.testingBroker = true;
                    this.brokerTestResult = null;
                    try {
                        const res = await fetch('/api/test/broker', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                metaapi_token: this.settings.broker.metaapi_token,
                                metaapi_account_id: this.settings.broker.metaapi_account_id
                            })
                        });
                        const data = await res.json();
                        this.brokerTestResult = {
                            success: res.ok,
                            message: data.message || (res.ok ? 'Connection successful!' : 'Connection failed')
                        };
                    } catch (e) {
                        this.brokerTestResult = {
                            success: false,
                            message: 'Connection test failed: ' + e.message
                        };
                    } finally {
                        this.testingBroker = false;
                        
                    }
                },
                
                async loadSignalMessages() {
                    this.loadingSignals = true;
                    try {
                        let url = '/api/signals/messages?limit=200';
                        
                        if (this.signalChannelFilter) {
                            url += `&channel_id=${this.signalChannelFilter}`;
                        }
                        
                        if (this.signalStartDate) {
                            url += `&start_date=${this.signalStartDate}T00:00:00`;
                        }
                        
                        if (this.signalEndDate) {
                            url += `&end_date=${this.signalEndDate}T23:59:59`;
                        }
                        
                        const response = await fetch(url);
                        const data = await response.json();
                        
                        if (data.success) {
                            this.signalMessages = data.messages || [];
                            this.filterSignalMessages();
                            
                            // Load analytics if channel filter is set
                            if (this.signalChannelFilter) {
                                await this.loadChannelAnalytics(this.signalChannelFilter);
                            }
                        }
                    } catch (error) {
                        console.error('Failed to load signal messages:', error);
                        this.notify('Failed to load signals', 'error');
                    } finally {
                        this.loadingSignals = false;
                    }
                },
                
                filterSignalMessages() {
                    let filtered = this.signalMessages;
                    
                    // Apply status filter
                    if (this.signalStatusFilter) {
                        filtered = filtered.filter(sig => {
                            if (this.signalStatusFilter === 'executed') return sig.executed;
                            if (this.signalStatusFilter === 'pending') return !sig.executed;
                            if (this.signalStatusFilter === 'active') return sig.status === 'active';
                            if (this.signalStatusFilter === 'closed') return ['tp3_hit', 'sl_hit', 'closed'].includes(sig.status);
                            return true;
                        });
                    }
                    
                    this.filteredSignalMessages = filtered;
                },
                
                clearDateFilters() {
                    this.signalStartDate = '';
                    this.signalEndDate = '';
                    this.loadSignalMessages();
                },
                
                // Date preset methods
                setDatePreset(preset) {
                    const today = new Date();
                    const formatDate = (date) => date.toISOString().split('T')[0];
                    
                    if (preset === 'today') {
                        this.signalStartDate = formatDate(today);
                        this.signalEndDate = formatDate(today);
                    } else if (preset === 'week') {
                        const weekAgo = new Date(today);
                        weekAgo.setDate(today.getDate() - 7);
                        this.signalStartDate = formatDate(weekAgo);
                        this.signalEndDate = formatDate(today);
                    } else if (preset === 'month') {
                        const monthAgo = new Date(today);
                        monthAgo.setMonth(today.getMonth() - 1);
                        this.signalStartDate = formatDate(monthAgo);
                        this.signalEndDate = formatDate(today);
                    } else if (preset === 'year') {
                        const yearAgo = new Date(today);
                        yearAgo.setFullYear(today.getFullYear() - 1);
                        this.signalStartDate = formatDate(yearAgo);
                        this.signalEndDate = formatDate(today);
                    }
                    
                    this.loadSignalMessages();
                },
                
                isDatePresetActive(preset) {
                    if (!this.signalStartDate || !this.signalEndDate) return false;
                    
                    const today = new Date();
                    const formatDate = (date) => date.toISOString().split('T')[0];
                    
                    if (preset === 'today') {
                        return this.signalStartDate === formatDate(today) && this.signalEndDate === formatDate(today);
                    } else if (preset === 'week') {
                        const weekAgo = new Date(today);
                        weekAgo.setDate(today.getDate() - 7);
                        return this.signalStartDate === formatDate(weekAgo) && this.signalEndDate === formatDate(today);
                    } else if (preset === 'month') {
                        const monthAgo = new Date(today);
                        monthAgo.setMonth(today.getMonth() - 1);
                        return this.signalStartDate === formatDate(monthAgo) && this.signalEndDate === formatDate(today);
                    } else if (preset === 'year') {
                        const yearAgo = new Date(today);
                        yearAgo.setFullYear(today.getFullYear() - 1);
                        return this.signalStartDate === formatDate(yearAgo) && this.signalEndDate === formatDate(today);
                    }
                    
                    return false;
                },
                
                getDateRangeLabel() {
                    if (this.isDatePresetActive('week')) return 'This Week';
                    if (this.isDatePresetActive('month')) return 'This Month';
                    if (this.isDatePresetActive('year')) return 'This Year';
                    if (this.signalStartDate && this.signalEndDate) {
                        return `${this.signalStartDate} - ${this.signalEndDate}`;
                    }
                    return 'Select Date Range';
                },
                
                clearAllFilters() {
                    this.signalStartDate = '';
                    this.signalEndDate = '';
                    this.signalStatusFilter = '';
                    this.signalChannelFilter = '';
                    this.showDateDropdown = false;
                    this.loadSignalMessages();
                },
                
                // Status filter methods
                setStatusFilter(status) {
                    this.signalStatusFilter = status;
                    this.filterSignalMessages();
                },
                
                getStatusCount(status) {
                    if (!this.signalMessages || this.signalMessages.length === 0) return 0;
                    
                    if (status === 'executed') {
                        return this.signalMessages.filter(sig => sig.executed).length;
                    } else if (status === 'pending') {
                        return this.signalMessages.filter(sig => !sig.executed).length;
                    } else if (status === 'active') {
                        return this.signalMessages.filter(sig => sig.status === 'active').length;
                    } else if (status === 'closed') {
                        return this.signalMessages.filter(sig => ['tp3_hit', 'sl_hit', 'closed'].includes(sig.status)).length;
                    }
                    
                    return 0;
                },
                
                // Channel dropdown methods
                selectChannel(channelId) {
                    this.signalChannelFilter = channelId;
                    this.showChannelDropdown = false;
                    this.loadSignalMessages();
                },
                
                getChannelSignalCount(channelId) {
                    if (!this.signalMessages || this.signalMessages.length === 0) return 0;
                    return this.signalMessages.filter(sig => String(sig.channel_id) === String(channelId)).length;
                },
                
                toggleSignalMessage(signalId) {
                    this.expandedSignals[signalId] = !this.expandedSignals[signalId];
                },
                
                async loadChannelAnalytics(channelId) {
                    try {
                        const response = await fetch(`/api/signals/channel/${channelId}/analytics`);
                        const data = await response.json();
                        
                        if (data.success) {
                            this.signalAnalytics = data.analytics || {};
                        }
                    } catch (error) {
                        console.error('Failed to load channel analytics:', error);
                    }
                },
                
                // Navbar methods
                logout() {
                    // Close user menu first
                    this.showUserMenu = false;
                    // Show logout confirmation modal
                    this.showLogoutModal = true;
                },
                async confirmLogout() {
                    this.loggingOut = true;
                    try {
                        // Clear local storage first
                        localStorage.removeItem('token');
                        localStorage.removeItem('refresh_token');
                        localStorage.removeItem('user');
                        
                        // Call logout API
                        await fetch('/api/auth/telegram/logout', { method: 'POST' }).catch(() => {});
                        await fetch('/api/logout', { method: 'POST' }).catch(() => {});
                        
                        // Redirect to login
                        window.location.href = '/login';
                    } catch (err) {
                        console.error('Logout error:', err);
                        // Still redirect even on error since we cleared local storage
                        window.location.href = '/login';
                    }
                },
                toggleNavbar() {
                    this.navbarCollapsed = !this.navbarCollapsed;
                    // Save preference to localStorage
                    localStorage.setItem('navbarCollapsed', this.navbarCollapsed);
                },
                navigateTo(item) {
                    this.activeNavItem = item;
                    localStorage.setItem('evobot-active-nav', item);
                    console.log('Navigated to:', item, '- Saved to localStorage');
                    this.showUserMenu = false;
                    
                    // Load signals when navigating to signals page
                    if (item === 'signals') {
                        this.loadSignalMessages();
                    }
                    
                    // Scroll to top of content
                    const content = document.querySelector('.content');
                    if (content) content.scrollTo(0, 0);
                },
                clearLogs() {
                    if (confirm('Are you sure you want to clear all activity logs?')) {
                        this.activities = [];
                        this.notify('Logs cleared', 'success');
                    }
                },
                async saveAllSettings() {
                    this.loading.settings = true;
                    try {
                        const payload = {
                            telegram: {
                                ...this.settings.telegram
                            },
                            broker: this.settings.broker,
                            trading: this.settings.trading,
                            risk: this.settings.risk
                        };
                        
                        const res = await fetch('/api/settings', {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        
                        if (res.ok) {
                            this.notify('All settings saved successfully!', 'success');
                            this.addActivity('Settings Updated', 'success', 'settings');
                        } else {
                            const data = await res.json();
                            this.notify(data.detail || 'Failed to save settings', 'error');
                        }
                    } catch (e) {
                        console.error('Save settings error:', e);
                        this.notify('Failed to save settings', 'error');
                    } finally {
                        this.loading.settings = false;
                    }
                },
                closeMT5Modal() {
                    this.showMT5LoginModal = false;
                    this.mt5TestResult = null;
                    this.mt5Form = { server: '', login: '', password: '' };
                    this.showMT5Dropdown = false;
                    this.filteredMT5Servers = [];
                },
                async filterMT5Servers() {
                    clearTimeout(this.mt5ServerSearchTimeout);
                    this.mt5ServerSearchTimeout = setTimeout(async () => {
                        this.loadingMT5Servers = true;
                        try {
                            const query = this.mt5Form.server.trim();
                            const res = await fetch(`/api/mt5/servers?query=${encodeURIComponent(query)}`);
                            if (res.ok) {
                                const data = await res.json();
                                this.filteredMT5Servers = data.servers || [];
                                this.showMT5Dropdown = this.filteredMT5Servers.length > 0;
                            }
                        } catch (e) {
                            console.error('Error fetching MT5 servers:', e);
                        } finally {
                            this.loadingMT5Servers = false;
                        }
                    }, 300);
                },
                selectMT5Server(server) {
                    this.mt5Form.server = server;
                    this.showMT5Dropdown = false;
                },
                hideMT5Dropdown() {
                    setTimeout(() => {
                        this.showMT5Dropdown = false;
                    }, 200);
                },
                async showMT5ServerDropdown() {
                    if (this.filteredMT5Servers.length === 0) {
                        await this.filterMT5Servers();
                    }
                    this.showMT5Dropdown = true;
                },
                async connectMT5() {
                    // Validate form before submitting
                    if (!this.mt5Form.server || !this.mt5Form.login || !this.mt5Form.password) {
                        this.mt5TestResult = { success: false, message: 'Please fill all fields' };
                        return;
                    }
                    
                    this.mt5Testing = true;
                    this.mt5TestResult = null;
                    
                    try {
                        const token = localStorage.getItem('token');
                        const res = await fetch('/api/mt5/test', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + token
                            },
                            body: JSON.stringify(this.mt5Form)
                        });
                        
                        const data = await res.json();
                        
                        if (res.ok && data.success) {
                            this.mt5TestResult = { success: true, message: data.message };
                            this.account = data.account;
                            this.mt5SessionValid = true;
                            this.notify('MT5 connected successfully!', 'success');
                            setTimeout(() => {
                                this.closeMT5Modal();
                            }, 1500);
                        } else {
                            this.mt5TestResult = { success: false, message: data.message || 'Connection failed' };
                        }
                    } catch (e) {
                        this.mt5TestResult = { success: false, message: 'Connection error: ' + e.message };
                    } finally {
                        this.mt5Testing = false;
                    }
                },
                showMT5AccountInfo() {
                    this.showMT5LoginModal = true;
                    if (this.account.server && this.account.login) {
                        this.mt5Form.server = this.account.server;
                        this.mt5Form.login = String(this.account.login);
                    }
                },
                confirmMT5Disconnect() {
                    this.showMT5DisconnectModal = true;
                },
                async logoutMT5() {
                    this.showMT5DisconnectModal = false;
                    try {
                        const token = localStorage.getItem('token');
                        await fetch('/api/mt5/logout', {
                            method: 'POST',
                            headers: { 'Authorization': 'Bearer ' + token }
                        });
                        this.account = { balance: 0, equity: 0, margin: 0, free_margin: 0, profit: 0, currency: 'USD', leverage: 0, server: '', login: 0, name: '' };
                        this.mt5SessionValid = false;
                        this.closeMT5Modal();
                        this.notify('Signed out from MT5', 'success');
                    } catch (e) {
                        this.notify('Failed to sign out', 'error');
                    }
                },
                // Channel Search Modal Methods
                openChannelSearchModal() {
                    this.showChannelSearchModal = true;
                    this.channelSearchQuery = '';
                    this.channelSearchResults = [];
                    this.selectedChannels = [];
                    // Load channels immediately without debounce
                    this.loadingChannelSearch = true;
                    this.$nextTick(async () => {
                        const input = this.$refs.channelSearchInput;
                        if (input) input.focus();
                        // Load all channels immediately
                        try {
                            const token = localStorage.getItem('token');
                            const res = await fetch('/api/telegram/search-channels?query=', {
                                headers: { 'Authorization': 'Bearer ' + token }
                            });
                            if (res.ok) {
                                const data = await res.json();
                                this.channelSearchResults = data.channels || [];
                                console.log('Modal opened - loaded channels:', this.channelSearchResults.length);
                            } else {
                                console.error('Failed to load channels:', res.status);
                                this.notify('Failed to load channels', 'error');
                            }
                        } catch (e) {
                            console.error('Channel load error:', e);
                            this.notify('Failed to load channels: ' + e.message, 'error');
                        } finally {
                            this.loadingChannelSearch = false;
                        }
                    });
                },
                closeChannelSearchModal() {
                    this.showChannelSearchModal = false;
                    this.channelSearchQuery = '';
                    this.channelSearchResults = [];
                    this.selectedChannels = [];
                },
                async loadAllChannels() {
                    this.loadingChannelSearch = true;
                    try {
                        const token = localStorage.getItem('token');
                        const res = await fetch('/api/telegram/search-channels?query=', {
                            headers: { 'Authorization': 'Bearer ' + token }
                        });
                        if (res.ok) {
                            const data = await res.json();
                            this.channelSearchResults = data.channels || [];
                        } else {
                            this.notify('Failed to load channels', 'error');
                        }
                    } catch (e) {
                        console.error('Channel load error:', e);
                        this.notify('Failed to load channels: ' + e.message, 'error');
                    } finally {
                        this.loadingChannelSearch = false;
                    }
                },
                async searchChannels() {
                    clearTimeout(this.channelSearchTimeout);
                    this.channelSearchTimeout = setTimeout(async () => {
                        this.loadingChannelSearch = true;
                        try {
                            const query = this.channelSearchQuery.trim();
                            const token = localStorage.getItem('token');
                            const res = await fetch(`/api/telegram/search-channels?query=${encodeURIComponent(query)}`, {
                                headers: { 'Authorization': 'Bearer ' + token }
                            });
                            if (res.ok) {
                                const data = await res.json();
                                this.channelSearchResults = data.channels || [];
                            } else {
                                this.notify('Failed to search channels', 'error');
                            }
                        } catch (e) {
                            console.error('Channel search error:', e);
                            this.notify('Search failed: ' + e.message, 'error');
                        } finally {
                            this.loadingChannelSearch = false;
                        }
                    }, 300);
                },
                toggleChannelSelection(channel) {
                    const channelId = channel.id;
                    const index = this.selectedChannels.indexOf(channelId);
                    if (index > -1) {
                        this.selectedChannels.splice(index, 1);
                    } else {
                        this.selectedChannels.push(channelId);
                    }
                },
                isChannelSelected(channelId) {
                    return this.selectedChannels.includes(channelId);
                },
                isChannelAlreadyAdded(channelId) {
                    // Check if channel is already in the signal_channels list
                    return this.settings.telegram.signal_channels.includes(channelId);
                },
                getAlreadyAddedChannels() {
                    return this.settings.telegram.signal_channels || [];
                },
                removeSignalChannelById(channelId) {
                    const index = this.settings.telegram.signal_channels.indexOf(channelId);
                    if (index > -1) {
                        this.removeSignalChannel(index);
                    }
                },
                getChannelTitleById(channelId) {
                    const channel = this.channelSearchResults.find(c => c.id === channelId);
                    return channel ? channel.title : channelId;
                },
                removeFromSelection(channelId) {
                    const index = this.selectedChannels.indexOf(channelId);
                    if (index > -1) {
                        this.selectedChannels.splice(index, 1);
                    }
                },
                async refreshChannelDetails(forceRefresh = false) {
                    try {
                        const token = localStorage.getItem('token');
                        const url = forceRefresh ? '/api/telegram/channels?refresh=true' : '/api/telegram/channels';
                        const res = await fetch(url, {
                            headers: { 'Authorization': 'Bearer ' + token }
                        });
                        if (res.ok) {
                            const data = await res.json();
                            console.log(`[ChannelMeta] API response:`, data);
                            if (data.channels) {
                                console.log(`[ChannelMeta] Mapping ${data.channels.length} items`);
                                const newMeta = (data.channels || []).reduce((acc, c) => {
                                    acc[String(c.id)] = c;
                                    // Also index by clean ID for easier matching
                                    const clean = String(c.id).replace('-100', '').replace('-', '');
                                    acc[clean] = c;
                                    return acc;
                                }, {});
                                this.channelMetadata = newMeta;
                                console.log(`[ChannelMeta] Current keys:`, Object.keys(this.channelMetadata));
                            }
                        } else {
                            console.error(`[ChannelMeta] API error: ${res.status}`);
                        }
                    } catch (e) {
                        console.error('Failed to fetch channel details:', e);
                    }
                },
                async addChannel(channel) {
                    if (!channel || this.addingChannels) return;
                    
                    this.addingChannels = true;
                    const channelId = channel.id;
                    
                    try {
                        const token = localStorage.getItem('token');
                        const res = await fetch('/api/telegram/channels/add', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + token
                            },
                            body: JSON.stringify({
                                channels: [channel],
                                channel_ids: [channelId]
                            })
                        });
                        
                        if (res.ok) {
                            const data = await res.json();
                            // Update local settings with new channel list
                            this.settings.telegram.signal_channels = data.channels || [];
                            this.notify(`Added "${channel.title}" successfully!`, 'success');
                            
                            // Refresh metadata to show the new channel
                            await this.refreshChannels(true);
                        } else {
                            const error = await res.json();
                            this.notify(error.detail || 'Failed to add channel', 'error');
                        }
                    } catch (e) {
                        console.error('Add channel error:', e);
                        this.notify('Failed to add channel: ' + e.message, 'error');
                    } finally {
                        this.addingChannels = false;
                    }
                },
                async addSelectedChannels() {
                    // Keeping this for compatibility with any existing calls, 
                    // though we should use addChannel now.
                    if (this.selectedChannels.length === 0) return;
                    
                    this.addingChannels = true;
                    try {
                        const token = localStorage.getItem('token');
                        const res = await fetch('/api/telegram/channels/add', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + token
                            },
                            body: JSON.stringify({
                                channels: this.selectedChannels.map(id => {
                                    const channel = this.channelSearchResults.find(c => String(c.id) === String(id));
                                    return channel || { id };
                                }),
                                channel_ids: this.selectedChannels
                            })
                        });
                        
                        if (res.ok) {
                            const data = await res.json();
                            this.settings.telegram.signal_channels = data.channels || [];
                            this.notify(`Added ${this.selectedChannels.length} channel(s) successfully!`, 'success');
                            this.selectedChannels = [];
                            await this.refreshChannels(true);
                        } else {
                            const error = await res.json();
                            this.notify(error.detail || 'Failed to add channels', 'error');
                        }
                    } catch (e) {
                        console.error('Add channels error:', e);
                        this.notify('Failed to add channels: ' + e.message, 'error');
                    } finally {
                        this.addingChannels = false;
                    }
                }
            },
            async mounted() {
                // Check authentication
                const token = localStorage.getItem('token');
                if (!token) {
                    window.location.href = '/login';
                    return;
                }
                
                // Restore active navigation from localStorage FIRST
                const savedNav = localStorage.getItem('evobot-active-nav');
                console.log('localStorage check:', savedNav);
                if (savedNav) {
                    this.activeNavItem = savedNav;
                    console.log('Restored navigation to:', savedNav);
                    // Load signals if that's the saved page
                    if (savedNav === 'signals') {
                        this.loadSignalMessages();
                    }
                } else {
                    this.activeNavItem = 'dashboard';
                    console.log('No saved navigation found, defaulting to dashboard');
                }
                
                // Verify token is valid
                try {
                    const res = await fetch('/api/auth/telegram/me', {
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    if (!res.ok) {
                        localStorage.removeItem('token');
                        localStorage.removeItem('refresh_token');
                        localStorage.removeItem('user');
                        window.location.href = '/login';
                        return;
                    }
                } catch (e) {
                    console.error('Auth check failed:', e);
                }
                
                // Check for stored MT5 credentials and auto-login
                try {
                    const mt5Res = await fetch('/api/mt5/credentials', {
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    if (mt5Res.ok) {
                        const mt5Data = await mt5Res.json();
                        if (mt5Data.has_credentials) {
                            const accRes = await fetch('/api/mt5/account', {
                                headers: { 'Authorization': 'Bearer ' + token }
                            });
                            if (accRes.ok) {
                                const accData = await accRes.json();
                                this.account = { ...this.account, ...accData };
                                this.mt5SessionValid = true;
                            }
                        }
                    }
                } catch (e) {
                    console.error('MT5 auto-login failed:', e);
                }
                
                // Initialize theme from localStorage (default to light theme)
                const savedTheme = localStorage.getItem('evobot-theme');
                if (savedTheme === 'dark') {
                    this.isDarkTheme = true;
                } else {
                    // Default to light theme
                    this.isDarkTheme = false;
                    document.documentElement.classList.add('light-theme');
                }
                
                this.connectWebSocket();
                
                // Load settings first to check if setup is needed
                try {
                    const settingsRes = await fetch('/api/settings');
                    if (settingsRes.ok) {
                        const settingsData = await settingsRes.json();
                        console.log('Loaded settings:', settingsData);
                        if (settingsData.telegram) {
                            this.settings.telegram = {
                                ...this.settings.telegram,
                                ...settingsData.telegram,
                                signal_channels: settingsData.telegram.signal_channels || [],
                                signal_channels_str: (settingsData.telegram.signal_channels || []).join(', ')
                            };
                        }
                        if (settingsData.broker) {
                            this.settings.broker = { ...this.settings.broker, ...settingsData.broker };
                        }
                        if (settingsData.trading) {
                            this.settings.trading = { ...this.settings.trading, ...settingsData.trading };
                        }
                        if (settingsData.risk) {
                            this.settings.risk = { ...this.settings.risk, ...settingsData.risk };
                        }
                    }
                } catch (e) {
                    console.error('Failed to load settings:', e);
                }
                
                // Initialize Lucide icons after settings load
                
                
                // Check if bot is already running
                try {
                    const res = await fetch('/api/status');
                    const data = await res.json();
                    
                    // Always update status
                    this.status = {
                        bot_running: data.bot_running || false,
                        mt5_connected: data.mt5_connected || false,
                        telegram_connected: data.telegram_connected || false,
                        uptime_seconds: data.uptime_seconds || 0
                    };
                    
                    if (data.account) {
                        this.account = {
                            balance: data.account.balance || 0,
                            equity: data.account.equity || 0,
                            margin: data.account.margin || 0,
                            free_margin: data.account.free_margin || 0,
                            profit: data.account.profit || 0,
                            currency: data.account.currency || 'USD',
                            leverage: data.account.leverage || 0,
                            server: data.account.server || '',
                            login: data.account.login || 0,
                            name: data.account.name || ''
                        };
                        // Mark MT5 session as valid if we have account data with a login
                        if (data.account.login) {
                            this.mt5SessionValid = true;
                        }
                    }
                    
                    if (data.stats) {
                        this.stats = {
                            total_trades: data.stats.total_trades || 0,
                            closed_trades: data.stats.closed_trades || 0,
                            winning_trades: data.stats.winning_trades || 0,
                            losing_trades: data.stats.losing_trades || 0,
                            win_rate: data.stats.win_rate || 0,
                            total_profit: data.stats.total_profit || 0,
                            open_trades: data.stats.open_trades || 0,
                            last_updated: data.stats.last_updated || new Date().toISOString()
                        };
                    }
                    if (data.risk) this.risk = data.risk;
                    if (data.config) this.config = data.config;
                    
                    this.displayUptime = data.uptime_seconds || 0;
                    
                    // Use nextTick to ensure DOM is ready
                    await this.$nextTick();
                    
                    // Start uptime counter if bot is running
                    if (data.bot_running) {
                        this.startUptimeCounter();
                    }
                    
                    // Always add dashboard loaded activity
                    this.addActivity('Dashboard loaded', 'success', 'check');
                    
                    await this.refreshPositions();
                    await this.refreshChannels();
                    await this.fetchTelegramUser();
                } catch (e) {
                    console.error('Initial status check failed:', e);
                    this.addActivity('Dashboard loaded', 'warning', 'alert-circle');
                }
                
                // Firebase real-time listeners
                if (window.firebaseDB) {
                    const statusRef = window.firebaseRef(window.firebaseDB, 'status');
                    window.firebaseOnValue(statusRef, (snapshot) => {
                        const data = snapshot.val();
                        if (data) {
                            this.status = {
                                ...this.status,
                                bot_running: data.bot_running,
                                mt5_connected: data.mt5_connected,
                                telegram_connected: data.telegram_connected,
                                uptime_seconds: data.uptime_seconds || 0
                            };
                        }
                    });
                    
                    const accountRef = window.firebaseRef(window.firebaseDB, 'account');
                    window.firebaseOnValue(accountRef, (snapshot) => {
                        const data = snapshot.val();
                        if (data) {
                            this.account = {
                                balance: data.balance || 0,
                                equity: data.equity || 0,
                                margin: data.margin || 0,
                                free_margin: data.free_margin || 0,
                                profit: data.profit || 0,
                                currency: data.currency || 'USD',
                                leverage: data.leverage || 0,
                                server: data.server || '',
                                login: data.login || 0
                            };
                        }
                    });
                    
                    const tradesRef = window.firebaseRef(window.firebaseDB, 'trades');
                    window.firebaseOnValue(tradesRef, (snapshot) => {
                        const data = snapshot.val();
                        if (data) {
                            this.activeTrades = Object.values(data).filter(t => 
                                t.status === 'active' || t.status === 'pending'
                            );
                        }
                    });
                    
                    const statsRef = window.firebaseRef(window.firebaseDB, 'stats');
                    window.firebaseOnValue(statsRef, (snapshot) => {
                        const data = snapshot.val();
                        if (data) {
                            // Only update from Firebase if it's newer than current stats
                            const firebaseTimestamp = data.timestamp || data.last_updated;
                            const currentTimestamp = this.stats.last_updated;
                            
                            // If Firebase data is newer or we have no current timestamp, update
                            if (!currentTimestamp || (firebaseTimestamp && new Date(firebaseTimestamp) >= new Date(currentTimestamp))) {
                                this.stats = {
                                    total_trades: data.total_trades || 0,
                                    winning_trades: data.winning_trades || 0,
                                    losing_trades: data.losing_trades || 0,
                                    win_rate: data.win_rate || 0,
                                    total_profit: data.total_profit || 0,
                                    open_trades: data.open_trades || 0,
                                    last_updated: firebaseTimestamp || new Date().toISOString()
                                };
                            }
                        }
                    });
                    
                    // Listen for settings changes
                    const settingsRef = window.firebaseRef(window.firebaseDB, 'settings');
                    window.firebaseOnValue(settingsRef, (snapshot) => {
                        const data = snapshot.val();
                        if (data) {
                            // Only update if not currently editing
                            if (!this.editingField) {
                                if (data.telegram) {
                                    this.settings.telegram = {
                                        ...this.settings.telegram,
                                        ...data.telegram,
                                        signal_channels: data.telegram.signal_channels || []
                                    };
                                }
                                if (data.broker) {
                                    this.settings.broker = { ...this.settings.broker, ...data.broker };
                                }
                                if (data.trading) {
                                    this.settings.trading = { ...this.settings.trading, ...data.trading };
                                }
                                if (data.risk) {
                                    this.settings.risk = { ...this.settings.risk, ...data.risk };
                                }
                            }
                        }
                    });
                }
                
                // Initialize Lucide icons once on mount
                this.initIcons();
                
                // Close dropdown when clicking outside
                document.addEventListener('click', (e) => {
                    if (!e.target.closest('.filter-dropdown-compact')) {
                        this.showChannelDropdown = false;
                    }
                    if (!e.target.closest('.date-range-btn') && !e.target.closest('.date-range-dropdown')) {
                        this.showDateDropdown = false;
                    }
                });
            },
            updated() {
                // Trigger animations for changed numbers
                this.$nextTick(() => {
                    document.querySelectorAll('.animated-number').forEach(el => {
                        const newValue = parseFloat(el.getAttribute('data-value'));
                        const oldValue = parseFloat(el.getAttribute('data-old-value') || newValue);
                        
                        if (newValue !== oldValue && !isNaN(newValue) && !isNaN(oldValue)) {
                            // Remove existing animation classes
                            el.classList.remove('number-increase', 'number-decrease');
                            
                            // Trigger reflow to restart animation
                            void el.offsetWidth;
                            
                            // Add appropriate animation class
                            if (newValue > oldValue) {
                                el.classList.add('number-increase');
                            } else if (newValue < oldValue) {
                                el.classList.add('number-decrease');
                            }
                            
                            // Store current value as old value for next comparison
                            el.setAttribute('data-old-value', newValue);
                        }
                    });
                });
            }
        }).mount('#app');
