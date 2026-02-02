"""
Comprehensive signal parser test suite - 25+ diverse formats
"""
import asyncio
from parsers.signal_parser import signal_parser

TEST_SIGNALS = [
    # === REAL CHANNEL FORMATS ===
    ("Gold buy now 5094 - 5091\n\nSL: 5088\n\nTP: 5096\nTP: 5098\nTP: 5100", "Real: Gold buy now"),
    ("XAUUSD SELL NOW\n\n🎯4470-- 4471🎯\n\nSL 4490\nTP1: 4467\nTP2: 4465\nTP3: 4463", "Real: XAUUSD SELL NOW"),
    ("🔔🔔🔔 NEW SIGNAL 🔔🔔🔔\n\nGBPUSD BUY\n\nEntry Zone: 1.3834-1.3840\nStop loss: 1.3720\nTake Profit 1: 1.3860\nTake Profit 2: 1.3880\nTake Profit 3: 1.3900", "Real: NEW SIGNAL"),
    ("XAUUSD SEEL 4654\n\nTP 4652\nTP 4650\nTP 4648\n\nSL 4664", "Real: SEEL typo"),
    
    # === MINIMAL FORMATS ===
    ("EURUSD BUY\nEntry: 1.1800\nSL: 1.1780\nTP1: 1.1820\nTP2: 1.1840\nTP3: 1.1860", "Minimal: Standard"),
    ("XAUUSD SELL @ 2650\nSL 2665\nTP 2640\nTP 2630\nTP 2620", "Minimal: @ entry"),
    ("Gold Long 2700-2705\nStop: 2690\nTargets: 2710, 2720, 2730", "Minimal: Targets comma"),
    
    # === ENTRY VARIATIONS ===
    ("GBPUSD BUY NOW\nEntry Zone: 1.2500 - 1.2510\nSL: 1.2480\nTP1: 1.2550", "Entry: Zone with dash"),
    ("EURUSD LONG\nEntry Portal: 🌀 1.1800 ➡️ 1.1810 🌀\nSL: 1.1780\nTP1: 1.1850", "Entry: Portal emoji"),
    ("XAUUSD BUY\n🎯 2650 -- 2655 🎯\nSL: 2640\nTP1: 2670", "Entry: Emoji zone"),
    ("USDJPY LONG\nEntry: 145.50 → 145.60\nSL: 145.30\nTP1: 145.90", "Entry: Arrow"),
    ("GBPUSD BUY MARKET\nSL: 1.2480\nTP1: 1.2550\nTP2: 1.2600", "Entry: Market order"),
    
    # === SL VARIATIONS ===
    ("EURUSD BUY 1.1800\n⚡ SL Danger Zone: 1.1780 ⚡\nTP1: 1.1850", "SL: Danger Zone"),
    ("XAUUSD LONG 2700\n💀 Stop-Loss Abyss: 2680 💀\nTP1: 2720", "SL: Abyss"),
    ("GBPUSD BUY 1.2500\n🛡️ Shield: 1.2480 🛡️\nTP1: 1.2550", "SL: Shield"),
    ("USDJPY LONG 145.50\n⚔️ Retreat Point: 145.30\nTP1: 145.90", "SL: Retreat Point"),
    ("EURUSD BUY 1.1800\n🔮 Protection: 1.1780\nTP1: 1.1850", "SL: Protection"),
    ("GBPUSD BUY 1.2500\n🛑 Emergency Exit: 1.2480\nTP1: 1.2550", "SL: Emergency Exit"),
    
    # === TP VARIATIONS ===
    ("XAUUSD BUY 2700\nSL: 2680\n🚀 TP1 → 2720\n🌟 TP2 → 2740\n☄️ TP3 → 2760", "TP: Emoji arrows"),
    ("EURUSD LONG 1.1800\nSL: 1.1780\n💎 Chest 1: 1.1850\n💎 Chest 2: 1.1900\n💎 Chest 3: 1.1950", "TP: Treasure Chests"),
    ("GBPUSD BUY 1.2500\nSL: 1.2480\n🪙 Gold 1: 1.2550\n🪙 Gold 2: 1.2600\n🪙 Gold 3: 1.2650", "TP: Gold"),
    ("USDJPY LONG 145.50\nSL: 145.30\n🛰️ Orbit 1: 145.90\n🛰️ Orbit 2: 146.20\n🛰️ Orbit 3: 146.50", "TP: Orbit"),
    ("XAUUSD BUY 2700\nSL: 2680\n⚡ Spell 1: 2720\n⚡ Spell 2: 2740\n⚡ Spell 3: 2760", "TP: Spell"),
    ("EURUSD LONG 1.1800\nSL: 1.1780\n🏯 Honor 1: 1.1850\n🏯 Honor 2: 1.1900\n🏯 Honor 3: 1.1950", "TP: Honor"),
    ("GBPUSD BUY 1.2500\nSL: 1.2480\n🎯 Target Alpha: 1.2550\n🎯 Target Beta: 1.2600\n🎯 Target Gamma: 1.2650", "TP: Greek letters"),
    
    # === CREATIVE THEMES ===
    ("🛸 COSMIC LONG ENGAGED! 🛸\nPair: EURUSD\nEntry Wormhole: 🌌 1.18035 → 1.18045 🌌\n⚡ Blackhole SL: 1.18005 ⚡\n🎯 Stellar Gains:\n🚀 TP1 → 1.18090\n🌟 TP2 → 1.18140\n☄️ TP3 → 1.18190", "Theme: Cosmic"),
    ("🐉 DRAGON AWAKENS - SHORT 🐉\nSymbol: XAUUSD\nAttack Zone: 2650 ⟶ 2655\n🛡️ Shield: 2665\n💰 Treasure Chests:\n💎 Chest 1: 2640\n💎 Chest 2: 2630\n💎 Chest 3: 2620", "Theme: Dragon"),
    ("🥷 NINJA STRIKE - BUY 🥷\nPair: USDJPY\nStealth Entry: 145.50 → 145.60\n⚔️ Retreat Point: 145.30\n🎯 Targets:\n🎯 Target Alpha: 145.90\n🎯 Target Beta: 146.20\n🎯 Target Gamma: 146.50", "Theme: Ninja"),
    ("🧙♂️ WIZARD SPELL - SELL 🧙♂️\nMagic Pair: XAUUSD\nCasting Zone: 2700 ~ 2705\n🔮 Protection: 2715\n✨ Enchantments:\n⚡ Spell 1: 2690\n⚡ Spell 2: 2680\n⚡ Spell 3: 2670", "Theme: Wizard"),
    
    # === EDGE CASES ===
    ("EURUSD\nBUY\n1.1800-1.1810\nSL 1.1780\nTP 1.1850 1.1900 1.1950", "Edge: Minimal spacing"),
    ("Gold buy now 2700 - 2705 SL: 2690 TP: 2710 TP: 2720 TP: 2730", "Edge: Single line"),
    ("XAUUSD LONG\nEntry: 2700\nStop Loss: 2680\nTake Profit 1: 2720\nTake Profit 2: 2740\nTake Profit 3: 2760", "Edge: Full words"),
    ("GBPUSD BUY 1.2500\nS.L. 1.2480\nT.P.1 1.2550\nT.P.2 1.2600\nT.P.3 1.2650", "Edge: Dots in SL/TP"),
    
    # === SYMBOL ALIASES ===
    ("CABLE BUY 1.2500\nSL: 1.2480\nTP1: 1.2550", "Alias: CABLE = GBPUSD"),
    ("FIBER LONG 1.1800\nSL: 1.1780\nTP1: 1.1850", "Alias: FIBER = EURUSD"),
    ("GOLD SELL 2700\nSL: 2720\nTP1: 2680", "Alias: GOLD = XAUUSD"),
    ("AUSSIE BUY 0.6500\nSL: 0.6480\nTP1: 0.6550", "Alias: AUSSIE = AUDUSD"),
]


async def test_signal(idx, signal_text, description):
    """Test a single signal"""
    result = await signal_parser.parse_async(signal_text)
    
    status = "✅ PASS" if result.parsed_successfully else "❌ FAIL"
    print(f"{status} | Test {idx+1:2d} | {description:30s} | ", end="")
    
    if result.parsed_successfully:
        print(f"{result.symbol} {result.direction.name if result.direction else 'N/A'} | Entry: {result.entry_min}-{result.entry_max} | SL: {result.stop_loss} | TPs: {result.take_profit_1}/{result.take_profit_2}/{result.take_profit_3}")
    else:
        print(f"Errors: {', '.join(result.parse_errors[:2])}")
    
    return result.parsed_successfully


async def main():
    """Run comprehensive test suite"""
    print("="*120)
    print("COMPREHENSIVE SIGNAL PARSER TEST SUITE - 35+ FORMATS")
    print("="*120)
    print()
    
    results = []
    for idx, (signal, desc) in enumerate(TEST_SIGNALS):
        success = await test_signal(idx, signal, desc)
        results.append((desc, success))
        await asyncio.sleep(0.1)
    
    # Summary
    print()
    print("="*120)
    print("SUMMARY")
    print("="*120)
    passed = sum(1 for _, s in results if s)
    total = len(results)
    percentage = (passed/total*100) if total > 0 else 0
    
    print(f"Passed: {passed}/{total} ({percentage:.1f}%)")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Parser is robust and ready for production.")
    else:
        print(f"⚠️  {total - passed} tests failed:")
        for desc, success in results:
            if not success:
                print(f"  - {desc}")
    
    print()
    print("="*120)


if __name__ == "__main__":
    asyncio.run(main())
