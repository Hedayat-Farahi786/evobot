/**
 * WebSocket Connection Manager
 * Handles connection, reconnection, and message dispatching
 */

export class ConnectionManager {
    constructor(options = {}) {
        this.url = options.url || this._getDefaultUrl();
        this.handlers = options.handlers || {};
        this.onConnect = options.onConnect || (() => {});
        this.onDisconnect = options.onDisconnect || (() => {});
        this.ws = null;
        this.reconnectTimer = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.reconnectDelay = options.reconnectDelay || 1000;
    }

    /**
     * Get default WebSocket URL based on current location
     * @returns {string} WebSocket URL
     */
    _getDefaultUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws`;
    }

    /**
     * Establish WebSocket connection
     */
    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        if (this.ws) {
            this.ws.close();
        }

        console.log('Connecting to WebSocket:', this.url);
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.onConnect();
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const handler = this.handlers[data.type];
                if (handler) {
                    handler(data.data);
                } else {
                    // console.debug(`No handler for message type: ${data.type}`);
                }
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e, event.data);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected:', event.reason);
            this.onDisconnect();
            
            // Don't reconnect if closed normally (status 1000)
            if (event.code !== 1000) {
                this._handleReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    /**
     * Handle reconnection logic with exponential backoff
     */
    _handleReconnect() {
        if (this.reconnectTimer) return;

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts), 30000);
            console.log(`Reconnecting in ${Math.round(delay)}ms (Attempt ${this.reconnectAttempts})...`);
            
            this.reconnectTimer = setTimeout(() => {
                this.reconnectTimer = null;
                this.connect();
            }, delay);
        } else {
            console.error('Maximum WebSocket reconnection attempts reached');
        }
    }

    /**
     * Close the connection and stop reconnection attempts
     */
    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        if (this.ws) {
            // Remove onclose handler to prevent automatic reconnection
            this.ws.onclose = null;
            this.ws.close(1000, 'Intentional disconnect');
            this.ws = null;
        }
    }

    /**
     * Send message to the server
     * @param {string} type - Message type
     * @param {Object} data - Message payload
     */
    send(type, data = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, data }));
        } else {
            console.warn('Cannot send message: WebSocket not connected');
        }
    }
}
