"""
Main application file for the EvoBot Trading System.
Initializes and runs all components of the copy-trading bot.
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.append(project_root)

from config.settings import config
from utils.logging_utils import setup_logging
from telegram.listener import telegram_listener
from broker import broker_client
from core.trade_manager import trade_manager
from core.risk_manager import risk_manager
from core.notifier import notifier

logger = setup_logging("evobot.main")


async def main():
    """Main function to start and run the bot"""
    logger.info("EvoBot Trading System starting...")
    
    # Initialize and connect broker
    logger.info("Connecting to MetaTrader 5...")
    if not await broker_client.connect():
        logger.critical("Failed to connect to MT5. Exiting.")
        sys.exit(1)
    
    # Initialize core components
    await risk_manager.start()
    await trade_manager.start()
    
    # Register notifier with telegram listener and trade manager
    notifier.set_telegram_client(telegram_listener)
    trade_manager.add_trade_listener(notifier.handle_trade_event)
    
    # Register signal handler
    telegram_listener.on_signal(handle_signal)
    
    # Start Telegram listener
    logger.info("Starting Telegram listener...")
    try:
        # Initial connection for getting me and channel setup
        await telegram_listener.start()
        
        # Notify system status
        await notifier.notify_system_status("EvoBot Started", "Connected to Telegram and MT5")
        
        # Run listener forever in background
        telegram_task = asyncio.create_task(telegram_listener.run_forever())
        
        # Keep main loop running to allow other tasks
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour, or until tasks complete
            await _check_daily_summary() # Check for daily summary generation
            
    except Exception as e:
        logger.critical(f"Critical error in main loop: {e}", exc_info=True)
    finally:
        await shutdown()


async def handle_signal(signal):
    """
    Handle incoming signals from Telegram.
    Performs risk checks and passes to trade manager.
    """
    logger.info(f"Received signal: {signal.symbol} {signal.direction.value if signal.direction else 'N/A'} - {signal.signal_type.value}")
    
    await notifier.notify_signal_received(
        signal.symbol,
        signal.direction.value if signal.direction else 'N/A',
        f"{signal.entry_min}-{signal.entry_max}" if signal.entry_min else "Market"
    )
    
    # Perform risk checks
    can_trade, reason = await risk_manager.can_trade(signal)
    if not can_trade:
        logger.warning(f"Skipping signal {signal.id} due to risk: {reason}")
        await notifier.notify_risk_alert("Trade Skipped", reason)
        return
    
    # Process signal with trade manager
    trade = await trade_manager.process_signal(signal)
    
    if trade:
        logger.info(f"Signal {signal.id} processed. Trade ID: {trade.id}")
    else:
        logger.warning(f"Signal {signal.id} not resulting in a trade or an error occurred.")


async def _check_daily_summary():
    """
    Checks if it's time to send a daily summary.
    This is a simplified check, a more robust solution would track last sent date.
    """
    now = datetime.utcnow()
    if now.hour == 23 and now.minute >= 55: # Send summary near midnight UTC
        stats = trade_manager.get_trade_stats()
        await notifier.notify_daily_summary(stats)
        logger.info("Daily summary sent.")
        # To prevent sending multiple times, could add a flag or persist last sent time
        await asyncio.sleep(60 * 5) # Sleep 5 minutes to pass the boundary


async def shutdown():
    """Gracefully shut down all components"""
    logger.info("EvoBot Trading System shutting down...")
    
    await trade_manager.stop()
    await risk_manager.stop()
    await broker_client.disconnect()
    await telegram_listener.stop()
    
    logger.info("EvoBot Trading System shut down successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("EvoBot stopped by user (KeyboardInterrupt).")
        asyncio.run(shutdown())
    except Exception as e:
        logger.critical(f"Unhandled exception in main execution: {e}", exc_info=True)
        sys.exit(1)
