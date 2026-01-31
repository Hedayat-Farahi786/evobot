# 🐧 EvoBot on Linux - Installation Guide

## ⚠️ Important: MetaTrader5 Limitation

MetaTrader5 Python package is **only available on Windows**. On Linux, you have two options:

### Option 1: Dashboard Only (Testing/Monitoring)
Run the dashboard to test signal parsing and monitor the system without actual trading.

### Option 2: Use Wine + MT5 (Advanced)
Install MetaTrader5 terminal using Wine and connect remotely.

## 🚀 Quick Start (Linux)

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

This will install everything except MetaTrader5 (which is Windows-only).

### 2️⃣ Configure Settings

```bash
nano .env
```

Set your Telegram credentials:
```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
SIGNAL_CHANNELS=channel1,channel2
```

### 3️⃣ Start Dashboard

```bash
./run_dashboard.sh
```

Or:

```bash
python start_dashboard.py
```

### 4️⃣ Access Dashboard

Open browser: **http://localhost:8080**

## 🎯 What Works on Linux

✅ **Web Dashboard** - Full functionality
✅ **Telegram Integration** - Receive and parse signals
✅ **Signal Testing** - Test signal parsing
✅ **Configuration** - Manage settings
✅ **Monitoring** - View system status
✅ **API** - Full REST API access

❌ **MT5 Trading** - Requires Windows or Wine setup

## 🍷 Option: Using Wine (Advanced)

If you want actual trading on Linux:

### 1. Install Wine

```bash
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install wine64 wine32 winetricks
```

### 2. Install MT5 via Wine

```bash
# Download MT5 installer
wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe

# Install with Wine
wine mt5setup.exe
```

### 3. Install MetaTrader5 Python Package

```bash
pip install MetaTrader5==5.0.45
```

### 4. Configure MT5 Path in .env

```env
MT5_PATH=/home/ubuntu/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe
```

## 🖥️ Recommended: Use Windows VPS

For production trading, it's recommended to use:
- **Windows VPS** (Vultr, DigitalOcean, AWS EC2 Windows)
- **Windows Server** with MT5 installed
- Run the dashboard there for full functionality

## 🧪 Testing on Linux

You can still test everything on Linux:

1. **Start Dashboard**: `./run_dashboard.sh`
2. **Test Signal Parsing**: Use the "🧪 Test Signal" feature
3. **Monitor System**: View logs and status
4. **Configure Settings**: Adjust all parameters
5. **API Testing**: Use http://localhost:8080/docs

The bot will show "MT5: Disconnected" but everything else works!

## 🔄 Hybrid Setup

**Best approach for Linux users:**

1. **Development/Testing**: Use Linux for dashboard and testing
2. **Production Trading**: Deploy to Windows VPS for actual trading
3. **Remote Control**: Access Windows VPS dashboard from Linux

## 📦 Install Only What You Need

```bash
# Core dependencies (works on Linux)
pip install telethon python-dotenv aiohttp

# Dashboard dependencies
pip install fastapi uvicorn jinja2 python-multipart websockets

# Skip MetaTrader5 on Linux
```

## 🚀 Start Without MT5

The dashboard will start fine without MT5:

```bash
python start_dashboard.py
```

You'll see:
- ✅ Dashboard running
- ✅ Telegram can connect
- ⚠️ MT5 shows disconnected (expected on Linux)

## 💡 Pro Tips

- Use Linux for **development and testing**
- Use Windows VPS for **production trading**
- Test signal parsing on Linux before deploying
- Configure everything on Linux, then copy .env to Windows
- Use the dashboard API to integrate with other systems

## 🔗 Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Start dashboard: `./run_dashboard.sh`
3. Test signal parsing: Use dashboard test feature
4. When ready for trading: Deploy to Windows VPS
5. Copy your .env file to Windows
6. Install MT5 on Windows
7. Run dashboard on Windows with full trading

---

**For production trading, use Windows. For testing, Linux works great!** 🐧🚀
