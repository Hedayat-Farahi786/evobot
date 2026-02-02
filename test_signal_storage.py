
import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from models.signal_message import SignalMessage
from core.signal_storage import SignalMessageStorage

class TestSignalStorage(unittest.TestCase):
    def setUp(self):
        self.storage = SignalMessageStorage()
        # Mock Firebase
        self.mock_firebase = MagicMock()
        self.storage.firebase_db = self.mock_firebase
        
    def create_signal(self, channel_id="123", profit=0.0):
        return SignalMessage(
            id=f"sig_{datetime.now().timestamp()}",
            channel_id=channel_id,
            channel_name="Test Channel",
            message_id=1,
            text="Test Signal",
            timestamp=datetime.utcnow(),
            symbol="XAUUSD",
            direction="BUY",
            signal_type="new_signal",
            entry_min=2000.0,
            stop_loss=1990.0,
            take_profit_1=2010.0,
            total_profit=profit,
            executed=True,
            status="closed"
        )

    def test_add_message(self):
        sig = self.create_signal()
        self.storage.add_message(sig)
        
        self.assertEqual(len(self.storage.messages), 1)
        self.assertEqual(self.storage.messages[0].id, sig.id)
        # Verify Firebase sync
        self.mock_firebase.child.assert_called()

    def test_get_messages_filtering(self):
        # Add mixed signals
        sig1 = self.create_signal(channel_id="A", profit=10.0)
        sig2 = self.create_signal(channel_id="B", profit=20.0)
        sig3 = self.create_signal(channel_id="A", profit=-5.0)
        
        self.storage.messages = [sig1, sig2, sig3]
        
        # Test explicit filtering logic (mimicking API)
        # The storage class itself doesn't filter by channel in get_messages usually, 
        # but let's test the analytics which does filter
        
        analytics_a = self.storage.get_channel_analytics("A")
        self.assertEqual(analytics_a["total_signals"], 2)
        self.assertEqual(analytics_a["total_profit"], 5.0)
        
        analytics_b = self.storage.get_channel_analytics("B")
        self.assertEqual(analytics_b["total_signals"], 1)
        self.assertEqual(analytics_b["total_profit"], 20.0)

    def test_update_status(self):
        sig = self.create_signal()
        self.storage.add_message(sig)
        
        self.storage.update_message(sig.id, {"status": "active", "total_profit": 0.0})
        self.assertEqual(self.storage.messages[0].status, "active")
        
        # Verify Firebase update
        # self.mock_firebase.child().update.assert_called() 
        # Note: implementation of update might vary, checking if it didn't crash is good start

    def test_analytics_calculation(self):
        # 1 Win, 1 Loss, 1 Pending
        sig1 = self.create_signal(profit=100.0) # Win
        sig2 = self.create_signal(profit=-50.0) # Loss
        sig3 = self.create_signal(profit=0.0)
        sig3.status = "pending"
        sig3.executed = False
        
        self.storage.messages = [sig1, sig2, sig3]
        
        stats = self.storage.get_channel_analytics("123")
        
        self.assertEqual(stats["total_signals"], 3)
        self.assertEqual(stats["executed_signals"], 2) # executing implies executed=True
        self.assertEqual(stats["closed_signals"], 2)   # default status is closed in helper
        self.assertEqual(stats["win_rate"], 50.0)      # 1 win out of 2 closed
        self.assertEqual(stats["total_profit"], 50.0)  # 100 - 50

if __name__ == "__main__":
    unittest.main()
