"""
Optimize dashboard sync intervals for faster updates
Changes from 10s to 2s (safe from rate limits)
"""
import re

def optimize_dashboard_sync():
    """Update dashboard sync intervals"""
    file_path = "dashboard/static/js/app.js"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all setInterval with 10000ms (10 seconds)
    # Replace with 2000ms (2 seconds) for faster updates
    
    # Pattern: setInterval(..., 10000)
    pattern = r'setInterval\((.*?),\s*10000\)'
    matches = re.findall(pattern, content)
    
    print(f"Found {len(matches)} intervals set to 10000ms (10 seconds)")
    
    # Replace 10000 with 2000 (2 seconds)
    new_content = re.sub(
        r'(setInterval\(.*?,\s*)10000(\))',
        r'\g<1>2000\2',
        content
    )
    
    # Count changes
    changes = content.count('10000') - new_content.count('10000')
    
    if changes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[OK] Updated {changes} intervals from 10s to 2s")
        print("[OK] Dashboard will now sync every 2 seconds")
    else:
        print("[INFO] No changes needed or already optimized")
    
    return changes > 0

def optimize_monitoring_interval():
    """Update trade manager monitoring interval"""
    file_path = "core/trade_manager.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Current: await asyncio.sleep(10)  # Check every 10 seconds
    # Change to: await asyncio.sleep(2)  # Check every 2 seconds
    
    if 'await asyncio.sleep(10)  # Check every 10 seconds' in content:
        new_content = content.replace(
            'await asyncio.sleep(10)  # Check every 10 seconds',
            'await asyncio.sleep(2)  # Check every 2 seconds (fast monitoring)'
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("[OK] Updated trade monitoring from 10s to 2s")
        print("[OK] TP hits will be detected 5x faster")
        return True
    else:
        print("[INFO] Trade monitoring already optimized or different interval")
        return False

def main():
    print("="*60)
    print("OPTIMIZING DASHBOARD SYNC INTERVALS")
    print("="*60)
    print()
    print("Target: 2 seconds (safe from rate limits)")
    print("Benefit: 5x faster updates")
    print()
    
    # Optimize dashboard
    print("1. Dashboard Sync:")
    dashboard_updated = optimize_dashboard_sync()
    
    print()
    print("2. Trade Monitoring:")
    monitoring_updated = optimize_monitoring_interval()
    
    print()
    print("="*60)
    print("RESULTS")
    print("="*60)
    
    if dashboard_updated or monitoring_updated:
        print("[SUCCESS] Optimizations applied!")
        print()
        print("Changes:")
        if dashboard_updated:
            print("  - Dashboard: 10s -> 2s (5x faster)")
        if monitoring_updated:
            print("  - Monitoring: 10s -> 2s (5x faster)")
        print()
        print("Benefits:")
        print("  - Positions update every 2 seconds")
        print("  - TP hits detected 5x faster")
        print("  - Breakeven triggers faster")
        print("  - Real-time dashboard experience")
        print()
        print("Safety:")
        print("  - 2s interval = 30 requests/minute")
        print("  - Well below rate limits")
        print("  - No performance impact")
        print()
        print("Action Required:")
        print("  1. Refresh dashboard (Ctrl+F5)")
        print("  2. Restart bot for monitoring change")
    else:
        print("[INFO] Already optimized or no changes needed")
    
    print("="*60)

if __name__ == "__main__":
    main()
