// Enhanced Firebase listeners for real-time updates
// Add this to the mounted() hook in app.js

// Positions listener with proper data handling
const positionsRef = window.firebaseRef(window.firebaseDB, 'positions');
window.firebaseOnValue(positionsRef, (snapshot) => {
    const data = snapshot.val();
    if (data) {
        if (Array.isArray(data)) {
            this.mt5Positions = data;
        } else if (data.data && Array.isArray(data.data)) {
            this.mt5Positions = data.data;
        }
        // Trigger grouping
        this.groupPositionsBySignal();
    }
});

// Account listener with change detection
const accountRef = window.firebaseRef(window.firebaseDB, 'account');
let lastAccountUpdate = Date.now();
window.firebaseOnValue(accountRef, (snapshot) => {
    const data = snapshot.val();
    if (data && Date.now() - lastAccountUpdate > 100) {
        this.account = {
            balance: data.balance || 0,
            equity: data.equity || 0,
            margin: data.margin || 0,
            free_margin: data.free_margin || 0,
            profit: data.profit || 0,
            currency: data.currency || 'USD',
            leverage: data.leverage || 0,
            server: data.server || '',
            login: data.login || 0,
            name: data.name || ''
        };
        lastAccountUpdate = Date.now();
        this.triggerNumberAnimation();
    }
});

// Stats listener
const statsRef = window.firebaseRef(window.firebaseDB, 'stats');
window.firebaseOnValue(statsRef, (snapshot) => {
    const data = snapshot.val();
    if (data) {
        this.stats = {
            total_trades: data.total_trades || 0,
            closed_trades: data.closed_trades || 0,
            winning_trades: data.winning_trades || 0,
            losing_trades: data.losing_trades || 0,
            win_rate: data.win_rate || 0,
            total_profit: data.total_profit || 0,
            open_trades: data.open_trades || 0,
            last_updated: data.last_updated || new Date().toISOString()
        };
    }
});

// Status listener
const statusRef = window.firebaseRef(window.firebaseDB, 'status');
window.firebaseOnValue(statusRef, (snapshot) => {
    const data = snapshot.val();
    if (data) {
        this.status = {
            bot_running: data.bot_running || false,
            mt5_connected: data.mt5_connected || false,
            telegram_connected: data.telegram_connected || false,
            uptime_seconds: data.uptime_seconds || 0
        };
    }
});
