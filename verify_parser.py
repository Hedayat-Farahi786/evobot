"""
Quick verification that parser works in the actual app
"""
import asyncio
from parsers.signal_parser import signal_parser

# Test a few real-world signals
TEST_SIGNALS = [
    "Gold buy now 2700 - 2705\nSL: 2690\nTP: 2710, 2720, 2730",
    "XAUUSD SEEL 2700\nTP 2680\nSL 2720",
    "EURUSD BYU 1.18\nSL: 1.17\nTP1: 1.19",
    "GBPUSD LONGG 1.25\nStop Los: 1.24\nTake Proffit: 1.26",
]

async def main():
    print("="*60)
    print("PARSER VERIFICATION - Real App Integration")
    print("="*60)
    
    passed = 0
    for idx, signal_text in enumerate(TEST_SIGNALS, 1):
        print(f"\nTest {idx}: {signal_text[:40]}...")
        result = await signal_parser.parse_async(signal_text)
        
        if result.parsed_successfully:
            print(f"  [PASS] {result.symbol} {result.direction.name if result.direction else 'N/A'}")
            passed += 1
        else:
            print(f"  [FAIL] {result.parse_errors}")
    
    print(f"\n{'='*60}")
    print(f"Result: {passed}/{len(TEST_SIGNALS)} passed")
    print(f"Status: {'SUCCESS - Parser ready for production' if passed == len(TEST_SIGNALS) else 'NEEDS ATTENTION'}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
