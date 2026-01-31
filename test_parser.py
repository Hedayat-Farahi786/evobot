"""
Test script to verify signal parsing functionality.
Run this to test the parser without connecting to Telegram or MT5.
"""
from parsers.signal_parser import signal_parser


def test_basic_signals():
    """Test basic signal parsing"""
    
    print("=" * 60)
    print("TESTING SIGNAL PARSER")
    print("=" * 60)
    
    # Test 1: Basic XAUUSD BUY signal
    test_signals = [
        """
        XAUUSD BUY
        Entry: 2050.00
        SL: 2045.00
        TP1: 2055.00
        TP2: 2060.00
        TP3: 2065.00
        """,
        
        """
        🟢 GOLD LONG
        Entry Zone: 2050.00 - 2052.00
        Stop Loss: 2045.00
        Take Profit 1: 2055.00
        Take Profit 2: 2060.00
        Take Profit 3: 2065.00
        Lot: 0.02
        """,
        
        """
        📉 GBPUSD SELL
        @ 1.2500
        SL: 1.2550
        🎯 TP1: 1.2450
        🎯 TP2: 1.2400
        🎯 TP3: 1.2350
        """,
        
        """
        ✅ XAUUSD TP1 HIT
        """,
        
        """
        🔒 Move GOLD to Breakeven
        """,
        
        """
        ❌ GBPUSD SL HIT
        """
    ]
    
    for i, message in enumerate(test_signals, 1):
        print(f"\n{'─' * 60}")
        print(f"Test #{i}")
        print(f"{'─' * 60}")
        print(f"Input:\n{message.strip()}")
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
        print(f"  Parsed Successfully: {signal.parsed_successfully}")
        
        if signal.parse_errors:
            print(f"  Parse Errors: {', '.join(signal.parse_errors)}")
        
        print()
    
    print("=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_signals()
