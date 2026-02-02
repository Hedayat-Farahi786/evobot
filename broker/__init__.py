"""
Broker module for EvoBot Trading System
Auto-selects appropriate broker client based on platform and configuration.
NOTE: On Linux, always use MetaApiClient. Credentials are checked at connect() time,
not at import time, to allow Firebase settings to be initialized first.
"""
import sys
import os

# Force MT5 client usage only
def _get_broker_client():
    """Get MT5 broker client - MetaAPI is disabled"""
    try:
        import MetaTrader5
        from .mt5_client import MT5Client, mt5_client as _mt5_instance
        return _mt5_instance, MT5Client
    except ImportError:
        raise ImportError("MetaTrader5 package not installed. Install with: pip install MetaTrader5")

# Get the appropriate client
_client, _client_class = _get_broker_client()

# Export with standard names for compatibility
# Use 'broker_client' to avoid collision with broker/mt5_client.py module name
broker_client = _client
BrokerClient = _client_class

# Also export as mt5_client for backward compatibility (but prefer broker_client)
# Note: This may conflict with the mt5_client.py module in some import scenarios
mt5_client = _client
MT5Client = _client_class

__all__ = ['BrokerClient', 'broker_client', 'MT5Client', 'mt5_client']
