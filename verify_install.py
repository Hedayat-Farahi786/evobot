#!/usr/bin/env python3
"""
Installation verification script for EvoBot.
Checks that all components are properly configured.
"""
import sys
import os
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False

def check_env_file():
    """Check .env file"""
    if not Path(".env").exists():
        print("❌ .env file not found")
        print("   Run: cp .env.example .env")
        return False
    
    print("✅ .env file exists")
    
    # Check required variables
    required_vars = [
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH",
        "TELEGRAM_PHONE",
        "MT5_SERVER",
        "MT5_LOGIN",
        "MT5_PASSWORD"
    ]
    
    with open(".env") as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=your_" in content:
            missing.append(var)
    
    if missing:
        print(f"⚠️  Please configure these variables in .env:")
        for var in missing:
            print(f"   - {var}")
        return False
    
    print("✅ .env file configured")
    return True

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} is too old (need 3.8+)")
        return False

def check_dependencies():
    """Check if dependencies are installed"""
    try:
        import telethon
        print(f"✅ Telethon installed: {telethon.__version__}")
    except ImportError:
        print("❌ Telethon not installed")
        print("   Run: pip install -r requirements.txt")
        return False
    
    try:
        import MetaTrader5
        print(f"✅ MetaTrader5 installed")
    except ImportError:
        print("⚠️  MetaTrader5 not installed (required for live trading)")
        print("   Run: pip install MetaTrader5")
        print("   Note: Only works on Windows or with Wine on Linux")
    
    try:
        import dotenv
        print(f"✅ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not installed")
        return False
    
    try:
        import aiohttp
        print(f"✅ aiohttp installed")
    except ImportError:
        print("❌ aiohttp not installed")
        return False
    
    return True

def check_directory_structure():
    """Check directory structure"""
    required_dirs = [
        "broker",
        "config",
        "core",
        "models",
        "parsers",
        "telegram",
        "utils"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        if Path(dir_name).is_dir():
            print(f"✅ Directory exists: {dir_name}/")
        else:
            print(f"❌ Directory missing: {dir_name}/")
            all_exist = False
    
    return all_exist

def check_required_files():
    """Check required files"""
    required_files = [
        ("main.py", "Main entry point"),
        ("requirements.txt", "Dependencies"),
        ("README.md", "Documentation"),
        (".env.example", "Configuration template"),
        ("broker/mt5_client.py", "MT5 client"),
        ("parsers/signal_parser.py", "Signal parser"),
        ("telegram/listener.py", "Telegram listener"),
        ("core/trade_manager.py", "Trade manager"),
        ("core/risk_manager.py", "Risk manager")
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def main():
    """Main verification function"""
    print("=" * 60)
    print("EvoBot Installation Verification")
    print("=" * 60)
    print()
    
    checks = []
    
    print("Checking Python version...")
    checks.append(check_python_version())
    print()
    
    print("Checking directory structure...")
    checks.append(check_directory_structure())
    print()
    
    print("Checking required files...")
    checks.append(check_required_files())
    print()
    
    print("Checking dependencies...")
    checks.append(check_dependencies())
    print()
    
    print("Checking configuration...")
    checks.append(check_env_file())
    print()
    
    print("=" * 60)
    if all(checks):
        print("✅ All checks passed! EvoBot is ready to run.")
        print()
        print("Next steps:")
        print("1. Review and configure .env file")
        print("2. Test signal parser: python test_parser.py")
        print("3. Start bot: python main.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        print("For help, see:")
        print("- README.md for full documentation")
        print("- QUICKSTART.md for quick reference")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
