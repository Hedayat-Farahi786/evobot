"""
EXTREME STRESS TEST - 60+ Worst-Case Scenarios
Tests parser robustness against malformed, ambiguous, and edge cases
"""
import asyncio
from parsers.signal_parser import signal_parser

TEST_SIGNALS = [
    # === CATEGORY 1: REAL CHANNEL FORMATS (5) ===
    ("Gold buy now 5094 - 5091\n\nSL: 5088\n\nTP: 5096\nTP: 5098\nTP: 5100", "Real: Gold buy now"),
    ("XAUUSD SELL NOW\n\n🎯4470-- 4471🎯\n\nSL 4490\nTP1: 4467\nTP2: 4465\nTP3: 4463", "Real: XAUUSD SELL NOW"),
    ("🔔 NEW SIGNAL 🔔\nGBPUSD BUY\nEntry Zone: 1.3834-1.3840\nStop loss: 1.3720\nTP1: 1.3860\nTP2: 1.3880\nTP3: 1.3900", "Real: NEW SIGNAL"),
    ("XAUUSD SEEL 4654\nTP 4652\nTP 4650\nTP 4648\nSL 4664", "Real: SEEL typo"),
    ("Gold Long 2700-2705\nStop: 2690\nTargets: 2710, 2720, 2730", "Real: Targets comma"),
    
    # === CATEGORY 2: EXTREME MINIMAL (5) ===
    ("EURUSD BUY 1.18 SL 1.17 TP 1.19", "Minimal: Ultra compact"),
    ("XAUUSD\nSELL\n2700\n2720\n2680", "Minimal: Line breaks only"),
    ("Gold buy @ 2700 sl 2690 tp 2710 2720 2730", "Minimal: No punctuation"),
    ("GBPUSD LONG NOW SL:1.24 TP:1.26", "Minimal: NOW with colon"),
    ("EURUSD BUY Entry 1.18 Stop 1.17 Target 1.19", "Minimal: Full words short"),
    
    # === CATEGORY 3: MALFORMED ENTRIES (8) ===
    ("EURUSD BUY\nEntry: 1.1800 - 1.1790\nSL: 1.1780\nTP1: 1.1820", "Malformed: Entry reversed"),
    ("XAUUSD SELL\nEntry Zone: 2700\nSL: 2720\nTP1: 2680", "Malformed: Single entry SELL"),
    ("GBPUSD BUY\nEntry: 1.2500 to 1.2510\nSL: 1.2480\nTP1: 1.2550", "Malformed: 'to' separator"),
    ("EURUSD LONG\nEntry Range: 1.1800~1.1810\nSL: 1.1780\nTP1: 1.1850", "Malformed: Tilde separator"),
    ("XAUUSD BUY\nEntry 2700/2705\nSL 2690\nTP1 2720", "Malformed: Slash separator"),
    ("GBPUSD BUY\nEntry: 1.2500 | 1.2510\nSL: 1.2480\nTP1: 1.2550", "Malformed: Pipe separator"),
    ("EURUSD LONG\nEntry 1.1800 1.1810\nSL 1.1780\nTP1 1.1850", "Malformed: Space separator"),
    ("XAUUSD BUY\nEntry: 2700 ... 2705\nSL: 2690\nTP1: 2720", "Malformed: Dots separator"),
    
    # === CATEGORY 4: AMBIGUOUS SL/TP (8) ===
    ("EURUSD BUY 1.1800\nRisk: 1.1780\nReward: 1.1850", "Ambiguous: Risk/Reward"),
    ("XAUUSD SELL 2700\nCut Loss: 2720\nProfit: 2680", "Ambiguous: Cut Loss/Profit"),
    ("GBPUSD LONG 1.2500\nExit: 1.2480\nGoal: 1.2550", "Ambiguous: Exit/Goal"),
    ("EURUSD BUY 1.1800\nLimit: 1.1780\nObjective: 1.1850", "Ambiguous: Limit/Objective"),
    ("XAUUSD SELL 2700\nBarrier: 2720\nMilestone: 2680", "Ambiguous: Barrier/Milestone"),
    ("GBPUSD BUY 1.2500\nDefense: 1.2480\nVictory: 1.2550", "Ambiguous: Defense/Victory"),
    ("EURUSD LONG 1.1800\nGuard: 1.1780\nPrize: 1.1850", "Ambiguous: Guard/Prize"),
    ("XAUUSD BUY 2700\nSafety: 2680\nJackpot: 2720", "Ambiguous: Safety/Jackpot"),
    
    # === CATEGORY 5: MISSING COMPONENTS (6) ===
    ("EURUSD BUY\nEntry: 1.1800\nTP1: 1.1850", "Missing: No SL"),
    ("XAUUSD SELL\nEntry: 2700\nSL: 2720", "Missing: No TP"),
    ("GBPUSD\nEntry: 1.2500\nSL: 1.2480\nTP1: 1.2550", "Missing: No direction"),
    ("BUY\nEntry: 1.1800\nSL: 1.1780\nTP1: 1.1850", "Missing: No symbol"),
    ("EURUSD BUY\nSL: 1.1780\nTP1: 1.1850", "Missing: No entry"),
    ("XAUUSD SELL 2700\nTP1: 2680\nTP2: 2670", "Missing: No SL with TPs"),
    
    # === CATEGORY 6: EXTREME FORMATTING (8) ===
    ("E U R U S D   B U Y   1 . 1 8 0 0\nS L : 1 . 1 7 8 0\nT P 1 : 1 . 1 8 5 0", "Format: Spaced chars"),
    ("EURUSD BUY 1.1800\n\n\n\nSL: 1.1780\n\n\nTP1: 1.1850", "Format: Extra newlines"),
    ("***EURUSD***BUY***1.1800***SL:1.1780***TP1:1.1850***", "Format: Asterisk delim"),
    ("===XAUUSD===SELL===2700===SL:2720===TP1:2680===", "Format: Equals delim"),
    ("EURUSD BUY 1.1800 | SL: 1.1780 | TP1: 1.1850 | TP2: 1.1900", "Format: Pipe delim"),
    ("【GBPUSD】【BUY】【1.2500】【SL:1.2480】【TP1:1.2550】", "Format: Brackets"),
    ("EURUSD BUY 1.1800; SL: 1.1780; TP1: 1.1850; TP2: 1.1900", "Format: Semicolon"),
    ("XAUUSD SELL 2700 // SL: 2720 // TP1: 2680 // TP2: 2670", "Format: Double slash"),
    
    # === CATEGORY 7: UNICODE & SPECIAL CHARS (5) ===
    ("EURUSD BUY 1․1800\nSL: 1․1780\nTP1: 1․1850", "Unicode: Middle dot decimal"),
    ("XAUUSD SELL 2700\nSL： 2720\nTP1： 2680", "Unicode: Fullwidth colon"),
    ("GBPUSD BUY 1.2500\nSL：1.2480\nTP1：1.2550", "Unicode: Mixed colons"),
    ("EURUSD LONG 1.1800\nSL: 1.1780\nTP1: 1.1850", "Unicode: Zero-width spaces"),
    ("XAUUSD BUY 2700\nSL: 2690\nTP1: 2720", "Unicode: Right-to-left marks"),
    
    # === CATEGORY 8: TYPOS & MISSPELLINGS (8) ===
    ("EURUSD BYU 1.1800\nSL: 1.1780\nTP1: 1.1850", "Typo: BYU instead of BUY"),
    ("XAUUSD SEEL 2700\nSL: 2720\nTP1: 2680", "Typo: SEEL instead of SELL"),
    ("GBPUSD LONGG 1.2500\nSL: 1.2480\nTP1: 1.2550", "Typo: LONGG double G"),
    ("EURUSD BUY 1.1800\nSLL: 1.1780\nTP1: 1.1850", "Typo: SLL double L"),
    ("XAUUSD SELL 2700\nSL: 2720\nTTP1: 2680", "Typo: TTP1 double T"),
    ("GBPUSD BUY 1.2500\nStop Los: 1.2480\nTP1: 1.2550", "Typo: Los instead of Loss"),
    ("EURUSD LONG 1.1800\nSL: 1.1780\nTake Proffit: 1.1850", "Typo: Proffit double F"),
    ("XAUUSD BUY 2700\nStoop Loss: 2690\nTP1: 2720", "Typo: Stoop instead of Stop"),
    
    # === CATEGORY 9: MIXED CASE & CAPS (5) ===
    ("eurusd buy 1.1800\nsl: 1.1780\ntp1: 1.1850", "Case: All lowercase"),
    ("EURUSD BUY 1.1800\nSL: 1.1780\nTP1: 1.1850", "Case: All uppercase"),
    ("EuRuSd BuY 1.1800\nSl: 1.1780\nTp1: 1.1850", "Case: Mixed random"),
    ("eUrUsD bUy 1.1800\nsL: 1.1780\ntP1: 1.1850", "Case: Alternating"),
    ("EURUSD buy 1.1800\nSL: 1.1780\ntp1: 1.1850", "Case: Mixed sections"),
    
    # === CATEGORY 10: EXTREME CREATIVE THEMES (5) ===
    ("🌈🦄 UNICORN MAGIC - BUY 🦄🌈\nPair: EURUSD\nRainbow Entry: 1.1800-1.1810\n🌟 Sparkle Shield: 1.1780\n✨ Dream Targets:\n💫 Dream 1: 1.1850\n🌠 Dream 2: 1.1900\n⭐ Dream 3: 1.1950", "Theme: Unicorn"),
    ("🔥🐲 DRAGON FIRE - SELL 🐲🔥\nSymbol: XAUUSD\nInferno Zone: 2700-2705\n🛡️ Flame Shield: 2720\n💎 Loot:\n💰 Gold 1: 2680\n💰 Gold 2: 2670\n💰 Gold 3: 2660", "Theme: Dragon Fire"),
    ("⚡🌩️ THUNDER GOD - LONG ⚡🌩️\nPair: GBPUSD\nLightning Strike: 1.2500-1.2510\n🌪️ Storm Barrier: 1.2480\n⚡ Thunder Rewards:\n🌩️ Bolt 1: 1.2550\n⚡ Bolt 2: 1.2600\n🌩️ Bolt 3: 1.2650", "Theme: Thunder"),
    ("🌊🐋 WHALE DIVE - SHORT 🐋🌊\nAsset: EURUSD\nOcean Depth: 1.1800-1.1810\n🌊 Surface: 1.1830\n🐠 Treasures:\n🐟 Fish 1: 1.1780\n🐠 Fish 2: 1.1760\n🐟 Fish 3: 1.1740", "Theme: Whale"),
    ("🚀🌙 MOON MISSION - BUY 🌙🚀\nCurrency: XAUUSD\nLaunch Pad: 2700-2705\n🔴 Abort: 2680\n🌟 Orbit Levels:\n🛸 Moon 1: 2720\n🌙 Moon 2: 2740\n⭐ Moon 3: 2760", "Theme: Moon"),
    
    # === CATEGORY 11: NUMBERS EDGE CASES (5) ===
    ("EURUSD BUY 1.18000000\nSL: 1.17800000\nTP1: 1.18500000", "Numbers: Extra zeros"),
    ("XAUUSD SELL 2,700.00\nSL: 2,720.00\nTP1: 2,680.00", "Numbers: Comma thousands"),
    ("GBPUSD BUY 1.25\nSL: 1.24\nTP1: 1.26", "Numbers: No decimals"),
    ("EURUSD LONG 1.180\nSL: 1.178\nTP1: 1.185", "Numbers: Three decimals"),
    ("XAUUSD BUY 2700.5\nSL: 2690.5\nTP1: 2720.5", "Numbers: Half pips"),
    
    # === CATEGORY 12: SYMBOL VARIATIONS (5) ===
    ("XAU/USD SELL 2700\nSL: 2720\nTP1: 2680", "Symbol: Slash format"),
    ("EUR/USD BUY 1.1800\nSL: 1.1780\nTP1: 1.1850", "Symbol: Slash format"),
    ("GBP/USD LONG 1.2500\nSL: 1.2480\nTP1: 1.2550", "Symbol: Slash format"),
    ("GOLD BUY 2700\nSL: 2690\nTP1: 2720", "Symbol: Alias GOLD"),
    ("CABLE SELL 1.2500\nSL: 1.2520\nTP1: 1.2480", "Symbol: Alias CABLE"),
]


async def test_signal(idx, signal_text, description):
    """Test a single signal"""
    result = await signal_parser.parse_async(signal_text)
    
    status = "PASS" if result.parsed_successfully else "FAIL"
    symbol = result.symbol or "N/A"
    direction = result.direction.name if result.direction else "N/A"
    entry = f"{result.entry_min}-{result.entry_max}" if result.entry_min else "N/A"
    sl = str(result.stop_loss) if result.stop_loss else "N/A"
    tp1 = str(result.take_profit_1) if result.take_profit_1 else "N/A"
    
    print(f"{status} {idx+1:2d} | {description:35s} | {symbol:8s} {direction:5s} | E:{entry:15s} SL:{sl:8s} TP1:{tp1:8s}")
    
    return result.parsed_successfully


async def main():
    """Run extreme stress test"""
    print("="*140)
    print("EXTREME STRESS TEST - 60+ WORST-CASE SCENARIOS")
    print("="*140)
    print()
    
    results = []
    categories = {}
    
    for idx, (signal, desc) in enumerate(TEST_SIGNALS):
        success = await test_signal(idx, signal, desc)
        results.append((desc, success))
        
        # Track by category
        category = desc.split(":")[0]
        if category not in categories:
            categories[category] = {"passed": 0, "total": 0}
        categories[category]["total"] += 1
        if success:
            categories[category]["passed"] += 1
        
        await asyncio.sleep(0.05)
    
    # Summary
    print()
    print("="*140)
    print("CATEGORY BREAKDOWN")
    print("="*140)
    for cat, stats in sorted(categories.items()):
        pct = (stats["passed"]/stats["total"]*100) if stats["total"] > 0 else 0
        status = "PASS" if pct == 100 else "WARN" if pct >= 80 else "FAIL"
        print(f"{status} {cat:20s}: {stats['passed']:2d}/{stats['total']:2d} ({pct:5.1f}%)")
    
    print()
    print("="*140)
    print("OVERALL SUMMARY")
    print("="*140)
    passed = sum(1 for _, s in results if s)
    total = len(results)
    percentage = (passed/total*100) if total > 0 else 0
    
    print(f"Total Passed: {passed}/{total} ({percentage:.1f}%)")
    print()
    
    if passed == total:
        print("[PERFECT] Parser handles ALL worst-case scenarios!")
    elif percentage >= 95:
        print("[EXCELLENT] Parser is production-ready with 95%+ coverage!")
    elif percentage >= 90:
        print("[GOOD] Parser handles most edge cases effectively.")
    elif percentage >= 80:
        print("[ACCEPTABLE] Some edge cases need attention.")
    else:
        print("[NEEDS WORK] Multiple scenarios failing.")
    
    if passed < total:
        print()
        print("Failed scenarios:")
        for desc, success in results:
            if not success:
                print(f"  - {desc}")
    
    print()
    print("="*140)


if __name__ == "__main__":
    asyncio.run(main())
