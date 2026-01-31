"""
Test script to verify signal parsing with actual channel signals.
"""
import sys
sys.path.insert(0, '.')

from parsers.signal_parser import signal_parser


def test_channel_signals():
    """Test parsing with actual signals from the channel"""
    
    print("=" * 60)
    print("TESTING SIGNAL PARSER WITH CHANNEL SIGNALS")
    print("=" * 60)
    
    # Actual signals from the channel
    test_signals = [
        # Signal 1: GBPUSD SELL with entry zone
        """🔔🔔🔔 NEW SIGNAL 🔔🔔🔔

GBPUSD SELL

Entry Zone: 1.3682-1.3674
Stop loss: 1.3782
Take Profit 1: 1.3662
Take Profit 2: 1.3622
Take Profit 3: 1.3552

⚠️ Please use 0.01 lot size for each 200 balance
⚠️ Place the signal only in entry zone""",

        # Signal 2: AUDUSD SELL
        """🔔🔔🔔 NEW SIGNAL 🔔🔔🔔

AUDUSD SELL

Entry Zone: 0.6927-0.6920
Stop loss: 0.6997
Take Profit 1: 0.6907
Take Profit 2: 0.6777
Take Profit 3: 0.6700

⚠️ Please use 0.01 lot size for each 200 balance
⚠️ Place the signal only in entry zone""",

        # Signal 3: XAUUSD SELL (Gold)
        """🔔🔔🔔 NEW SIGNAL 🔔🔔🔔

XAUUSD SELL

Entry Zone: 5035.00-5033.00
Stop loss: 5037.00
Take Profit 1: 5028.00
Take Profit 2: 5000.00
Take Profit 3: 4950.00

⚠️ Please use 0.01 lot size for each 200 balance
⚠️ Place the signal only in entry zone""",

        # Signal 4: USDCAD BUY
        """🔔🔔🔔 NEW SIGNAL 🔔🔔🔔

USDCAD BUY

Entry Zone: 1.3692-1.3699
Stop loss: 1.3622
Take Profit 1: 1.3712
Take Profit 2: 1.3742
Take Profit 3: 1.3792

⚠️ Please use 0.01 lot size for each 200 balance
⚠️ Place the signal only in entry zone""",

        # Update 1: TP 1 hit
        "TP 1 hit - Trade Closed ✅",
        
        # Update 2: TP 1,2 hit
        "TP 1,2 hit ✅",
        
        # Update 3: SL hit
        "SL ❌",
        
        # Update 4: Move to breakeven
        "TP 1 hit +20 Pips✅✅✅ Move SL to entry🚀🚀🚀",
        
        # Update 5: Closed
        "CLOSED",
        
        # EURUSD signal
        """🔔🔔🔔 NEW SIGNAL 🔔🔔🔔

EURUSD SELL

Entry Zone: 1.1890-1.1883
Stop loss: 1.1900
Take Profit 1: 1.1870
Take Profit 2: 1.1840
Take Profit 3: 1.1770

⚠️ Please use 0.01 lot size for each 200 balance
⚠️ Place the signal only in entry zone""",
    ]
    
    for i, message in enumerate(test_signals, 1):
        print(f"\n{'─' * 60}")
        print(f"Test #{i}")
        print(f"{'─' * 60}")
        
        # Show first 100 chars of input
        preview = message.strip()[:100].replace('\n', ' ')
        if len(message) > 100:
            preview += "..."
        print(f"Input: {preview}")
        print()
        
        signal = signal_parser.parse(message)
        
        print(f"Parsed Signal:")
        print(f"  Type: {signal.signal_type.value}")
        print(f"  Symbol: {signal.symbol}")
        print(f"  Direction: {signal.direction.value if signal.direction else 'N/A'}")
        print(f"  Entry Min: {signal.entry_min}")
        print(f"  Entry Max: {signal.entry_max}")
        print(f"  Stop Loss: {signal.stop_loss}")
        print(f"  TP1: {signal.take_profit_1}")
        print(f"  TP2: {signal.take_profit_2}")
        print(f"  TP3: {signal.take_profit_3}")
        print(f"  Lot Size: {signal.lot_size}")
        print(f"  ✅ Parsed Successfully: {signal.parsed_successfully}")
        
        if signal.parse_errors:
            print(f"  ⚠️ Parse Errors: {', '.join(signal.parse_errors)}")
        
        print()
    
    print("=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_channel_signals()
