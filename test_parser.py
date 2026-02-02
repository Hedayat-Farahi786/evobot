"""
Test signal parser with weird/creative formats
"""
import asyncio
import sys
from parsers.signal_parser import signal_parser

# Test signals with creative formats
TEST_SIGNALS = [
    # 1. Real format - Gold buy now
    """Gold buy now 5094 - 5091

SL: 5088

TP: 5096
TP: 5098
TP: 5100
TP: open""",

    # 2. Real format - XAUUSD SELL NOW
    """XAUUSD   SELL  NOW

🎯4470-- 4471🎯

SL 4490
TP1: 4467
TP2: 4465
TP3: 4463""",

    # 3. Real format - NEW SIGNAL
    """🔔🔔🔔 NEW SIGNAL 🔔🔔🔔

GBPUSD BUY

Entry Zone: 1.3834-1.3840
Stop loss: 1.3720
Take Profit 1: 1.3860
Take Profit 2: 1.3880
Take Profit 3: 1.3900

⚠️ Please use 0.01 lot size for each 200 balance
⚠️ Place the signal only in entry zone

TP1,2,3 - Trade Closed ✅""",

    # 4. Real format - XAUUSD SEEL (typo)
    """XAUUSD SEEL 4654

TP 4652
TP 4650
TP 4648
TP 4646
TP 4644

SL 4664""",

    # 5. Cosmic theme
    """🛸 COSMIC LONG ENGAGED! 🛸
Pair: EURUSD
Entry Wormhole: 🌌 1.18035 → 1.18045 🌌
⚡ Blackhole SL: 1.18005 ⚡
🎯 Stellar Gains:
🚀 TP1 → 1.18090
🌟 TP2 → 1.18140
☄️ TP3 → 1.18190""",

    # 6. Ocean theme
    """🌊💎 RAISE THE BULL FLAG! 💎🌊
Pair: EURUSD
Entry Portal: 🌀 1.18035 ➡️ 1.18045 🌀
💀 Stop-Loss Abyss: 1.18005 💀
💥 Takeoff Targets:
🚀 TP1 → 1.18090
🌟 TP2 → 1.18140
☄️ TP3 → 1.18190""",

    # 7. Space theme
    """🌌🪐 LONG HYPERDRIVE ENGAGED! 🪐🌌
Pair: EURUSD
Entry Vortex: 🔮 1.18045 → 1.18065 🔮
⚡ SL Danger Zone: 1.18020 ⚡
💫 Profit Constellation:
🌟 TP1 → 1.18110
☄️ TP2 → 1.18160
✨ TP3 → 1.18210""",

    # 8. Dragon theme
    """🐉 DRAGON AWAKENS - SHORT 🐉
Symbol: XAUUSD
Attack Zone: 2650 ⟶ 2655
🛡️ Shield: 2665
💰 Treasure Chests:
💎 Chest 1: 2640
💎 Chest 2: 2630
💎 Chest 3: 2620""",

    # 9. Ninja theme
    """🥷 NINJA STRIKE - BUY 🥷
Pair: USDJPY
Stealth Entry: 145.50 → 145.60
⚔️ Retreat Point: 145.30
🎯 Targets:
🎯 Target Alpha: 145.90
🎯 Target Beta: 146.20
🎯 Target Gamma: 146.50""",

    # 10. Wizard theme
    """🧙♂️ WIZARD SPELL - SELL 🧙♂️
Magic Pair: XAUUSD
Casting Zone: 2700 ~ 2705
🔮 Protection: 2715
✨ Enchantments:
⚡ Spell 1: 2690
⚡ Spell 2: 2680
⚡ Spell 3: 2670""",
]


async def test_signal(idx, signal_text):
    """Test a single signal"""
    print(f"\n{'='*80}")
    print(f"TEST {idx + 1}")
    print(f"{'='*80}")
    # Skip printing signal text with emojis to avoid encoding issues
    print(f"Testing signal {idx + 1}...")
    
    # Parse signal
    result = await signal_parser.parse_async(signal_text)
    
    # Display results
    status = "PASS" if result.parsed_successfully else "FAIL"
    print(f"\n[{status}] Parsed: {result.parsed_successfully}")
    if result.parsed_successfully:
        print(f"Symbol: {result.symbol}")
        print(f"Direction: {result.direction}")
        print(f"Entry: {result.entry_min} - {result.entry_max}")
        print(f"SL: {result.stop_loss}")
        print(f"TP1: {result.take_profit_1}")
        print(f"TP2: {result.take_profit_2}")
        print(f"TP3: {result.take_profit_3}")
    else:
        print(f"Errors: {result.parse_errors}")
    
    return result.parsed_successfully


async def main():
    """Run all tests"""
    print("="*80)
    print("SIGNAL PARSER TEST SUITE")
    print("="*80)
    
    results = []
    for idx, signal in enumerate(TEST_SIGNALS):
        success = await test_signal(idx, signal)
        results.append(success)
        await asyncio.sleep(0.5)  # Small delay between tests
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("[SUCCESS] ALL TESTS PASSED!")
    else:
        print(f"[FAILED] {total - passed} tests failed")
        for idx, success in enumerate(results):
            if not success:
                print(f"  - Test {idx + 1} failed")


if __name__ == "__main__":
    asyncio.run(main())
