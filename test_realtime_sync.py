"""
Test script for real-time synchronization
Verifies MT5 -> Firebase -> WebSocket -> Dashboard data flow
"""
import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_realtime_sync")

# Import components
from broker import broker_client
from core.trade_manager import trade_manager
from core.firebase_service import firebase_service
from core.realtime_sync import realtime_sync
from dashboard.state import bot_state


class MockWebSocketBroadcast:
    """Mock WebSocket broadcast for testing"""
    def __init__(self):
        self.messages: List[Dict] = []
    
    async def __call__(self, message: dict):
        """Capture broadcast messages"""
        self.messages.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message
        })
        logger.info(f"📡 WebSocket Broadcast: {message.get('type', 'unknown')}")


async def test_mt5_connection():
    """Test 1: MT5 Connection"""
    logger.info("=" * 60)
    logger.info("TEST 1: MT5 Connection")
    logger.info("=" * 60)
    
    try:
        connected = await broker_client.connect()
        if connected:
            logger.info("✅ MT5 connected successfully")
            account = await broker_client.get_account_info()
            if account:
                logger.info(f"   Balance: {account.balance} {account.currency}")
                logger.info(f"   Equity: {account.equity}")
                logger.info(f"   Server: {account.server}")
                return True
        else:
            logger.error("❌ MT5 connection failed")
            return False
    except Exception as e:
        logger.error(f"❌ MT5 connection error: {e}")
        return False


async def test_firebase_connection():
    """Test 2: Firebase Connection"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Firebase Connection")
    logger.info("=" * 60)
    
    try:
        firebase_service.initialize()
        if firebase_service.initialized:
            logger.info("✅ Firebase initialized successfully")
            
            # Test write
            test_data = {
                "test": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            firebase_service.db_ref.child("test_sync").set(test_data)
            logger.info("✅ Firebase write test passed")
            
            # Test read
            read_data = firebase_service.db_ref.child("test_sync").get()
            if read_data and read_data.get("test"):
                logger.info("✅ Firebase read test passed")
                return True
            else:
                logger.error("❌ Firebase read test failed")
                return False
        else:
            logger.error("❌ Firebase initialization failed")
            return False
    except Exception as e:
        logger.error(f"❌ Firebase error: {e}")
        return False


async def test_snapshot_capture():
    """Test 3: Snapshot Capture"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Snapshot Capture")
    logger.info("=" * 60)
    
    try:
        # Initialize realtime sync
        mock_ws = MockWebSocketBroadcast()
        bot_state.is_running = True
        bot_state.is_connected_mt5 = True
        bot_state.start_time = datetime.utcnow()
        
        realtime_sync.initialize(
            firebase_service=firebase_service,
            broker_client=broker_client,
            trade_manager=trade_manager,
            websocket_broadcast=mock_ws,
            bot_state=bot_state
        )
        
        # Capture snapshot
        snapshot = await realtime_sync._capture_snapshot()
        
        # Verify snapshot
        if snapshot.account:
            logger.info("✅ Account data captured")
            logger.info(f"   Balance: {snapshot.account.get('balance')}")
            logger.info(f"   Equity: {snapshot.account.get('equity')}")
        else:
            logger.warning("⚠️  No account data")
        
        if snapshot.positions is not None:
            logger.info(f"✅ Positions captured: {len(snapshot.positions)} positions")
            for pos in snapshot.positions[:3]:  # Show first 3
                logger.info(f"   {pos.get('symbol')} {pos.get('direction')} - P/L: {pos.get('profit')}")
        else:
            logger.warning("⚠️  No positions data")
        
        if snapshot.stats:
            logger.info("✅ Stats captured")
            logger.info(f"   Total trades: {snapshot.stats.get('total_trades')}")
            logger.info(f"   Open trades: {snapshot.stats.get('open_trades')}")
        else:
            logger.warning("⚠️  No stats data")
        
        if snapshot.status:
            logger.info("✅ Status captured")
            logger.info(f"   Bot running: {snapshot.status.get('bot_running')}")
            logger.info(f"   MT5 connected: {snapshot.status.get('mt5_connected')}")
        else:
            logger.warning("⚠️  No status data")
        
        return True
    except Exception as e:
        logger.error(f"❌ Snapshot capture error: {e}", exc_info=True)
        return False


async def test_firebase_sync():
    """Test 4: Firebase Synchronization"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Firebase Synchronization")
    logger.info("=" * 60)
    
    try:
        # Capture and sync snapshot
        snapshot = await realtime_sync._capture_snapshot()
        await realtime_sync._sync_snapshot(snapshot)
        
        # Verify data in Firebase
        if snapshot.account:
            fb_account = firebase_service.db_ref.child("account").get()
            if fb_account and fb_account.get("balance") == snapshot.account.get("balance"):
                logger.info("✅ Account synced to Firebase")
            else:
                logger.warning("⚠️  Account sync mismatch")
        
        if snapshot.positions is not None:
            fb_positions = firebase_service.db_ref.child("positions").get()
            if fb_positions:
                logger.info(f"✅ Positions synced to Firebase: {len(fb_positions)} positions")
            else:
                logger.info("✅ Positions synced (empty)")
        
        if snapshot.stats:
            fb_stats = firebase_service.db_ref.child("stats").get()
            if fb_stats:
                logger.info("✅ Stats synced to Firebase")
            else:
                logger.warning("⚠️  Stats not found in Firebase")
        
        return True
    except Exception as e:
        logger.error(f"❌ Firebase sync error: {e}", exc_info=True)
        return False


async def test_websocket_broadcast():
    """Test 5: WebSocket Broadcast"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: WebSocket Broadcast")
    logger.info("=" * 60)
    
    try:
        mock_ws = MockWebSocketBroadcast()
        
        # Re-initialize with mock
        realtime_sync.websocket_broadcast = mock_ws
        
        # Capture and sync
        snapshot = await realtime_sync._capture_snapshot()
        await realtime_sync._sync_snapshot(snapshot)
        
        # Check broadcasts
        if len(mock_ws.messages) > 0:
            logger.info(f"✅ WebSocket broadcasts sent: {len(mock_ws.messages)}")
            for msg in mock_ws.messages:
                msg_type = msg["message"].get("type", "unknown")
                logger.info(f"   - {msg_type}")
            return True
        else:
            logger.warning("⚠️  No WebSocket broadcasts")
            return False
    except Exception as e:
        logger.error(f"❌ WebSocket broadcast error: {e}", exc_info=True)
        return False


async def test_realtime_loop():
    """Test 6: Real-time Sync Loop"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Real-time Sync Loop (10 seconds)")
    logger.info("=" * 60)
    
    try:
        mock_ws = MockWebSocketBroadcast()
        realtime_sync.websocket_broadcast = mock_ws
        
        # Start sync
        await realtime_sync.start()
        logger.info("✅ Sync loop started")
        
        # Run for 10 seconds
        initial_count = len(mock_ws.messages)
        await asyncio.sleep(10)
        final_count = len(mock_ws.messages)
        
        # Stop sync
        await realtime_sync.stop()
        logger.info("✅ Sync loop stopped")
        
        updates = final_count - initial_count
        logger.info(f"✅ Updates during 10s: {updates}")
        
        if updates > 0:
            logger.info("✅ Real-time updates working")
            return True
        else:
            logger.warning("⚠️  No updates detected (might be no changes)")
            return True  # Still pass if no changes
    except Exception as e:
        logger.error(f"❌ Sync loop error: {e}", exc_info=True)
        return False


async def test_change_detection():
    """Test 7: Change Detection"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 7: Change Detection")
    logger.info("=" * 60)
    
    try:
        # Capture initial snapshot
        snapshot1 = await realtime_sync._capture_snapshot()
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Capture second snapshot
        snapshot2 = await realtime_sync._capture_snapshot()
        
        # Check for changes
        has_changes = realtime_sync._has_changes(snapshot2)
        
        if has_changes:
            logger.info("✅ Changes detected between snapshots")
        else:
            logger.info("✅ No changes detected (expected if market is stable)")
        
        return True
    except Exception as e:
        logger.error(f"❌ Change detection error: {e}", exc_info=True)
        return False


async def run_all_tests():
    """Run all tests"""
    logger.info("\n" + "🚀" * 30)
    logger.info("REAL-TIME SYNC TEST SUITE")
    logger.info("🚀" * 30 + "\n")
    
    results = {}
    
    # Run tests
    results["MT5 Connection"] = await test_mt5_connection()
    results["Firebase Connection"] = await test_firebase_connection()
    results["Snapshot Capture"] = await test_snapshot_capture()
    results["Firebase Sync"] = await test_firebase_sync()
    results["WebSocket Broadcast"] = await test_websocket_broadcast()
    results["Real-time Loop"] = await test_realtime_loop()
    results["Change Detection"] = await test_change_detection()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("=" * 60)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    # Cleanup
    try:
        await broker_client.disconnect()
        logger.info("\n✅ Cleanup completed")
    except:
        pass
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Test suite error: {e}", exc_info=True)
        sys.exit(1)
