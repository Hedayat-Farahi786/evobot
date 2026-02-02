/**
 * Formatters for use across the dashboard application
 */

/**
 * Formats a number with 2 decimal places and thousands separators
 * @param {number|string} value - The value to format
 * @returns {string} Formatted number
 */
export function formatNumber(value) {
    if (value === null || value === undefined) return '0.00';
    return Number(value).toLocaleString('en-US', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
    });
}

/**
 * Formats a price with symbol-specific decimal precision
 * @param {number|string} value - The price to format
 * @param {string} symbol - The trading symbol (e.g., 'EURUSD', 'XAUUSD', 'USDJPY')
 * @returns {string} Formatted price
 */
export function formatPrice(value, symbol) {
    if (!value) return '-';
    const digits = symbol?.includes('JPY') ? 3 : (symbol?.includes('XAU') ? 2 : 5);
    return Number(value).toFixed(digits);
}

/**
 * Formats uptime from seconds to a human-readable string
 * @param {number} seconds - Uptime in seconds
 * @returns {string} Formatted uptime
 */
export function formatUptime(seconds) {
    if (!seconds) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
}

/**
 * Formats an ISO timestamp for display in signals
 * @param {string|number} timestamp - The timestamp to format
 * @returns {string} Formatted date/time
 */
export function formatSignalTime(timestamp) {
    if (!timestamp) return 'Unknown time';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Formats a number for compact display (K, M)
 * @param {number} num - The number to format
 * @returns {string} Compact formatted number
 */
export function formatNumberCompact(num) {
    if (!num || isNaN(num)) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
    return num.toString();
}

/**
 * Formats channel numeric ID to display ID
 * @param {number|string} channelId 
 * @returns {string}
 */
export function getChannelDisplayId(channelId) {
    if (!channelId) return '';
    const id = String(channelId);
    if (id.startsWith('-100')) return id.substring(4);
    if (id.startsWith('-')) return id.substring(1);
    return id;
}
