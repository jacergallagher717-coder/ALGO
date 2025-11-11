# 🔧 Setup Guide - Where to Plug In Your API Keys

## 📋 What You Need

### Required (FREE)
- ✅ **Python 3.8+** - Already have it
- ✅ **yfinance** - Free stock/options data (no API key needed)

### Optional (for better features)
- 🔑 **Polygon.io API** - More reliable option data (free tier available)
- 📱 **Telegram Bot** - Get alerts on your phone (completely free)

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies

```bash
# Run the setup script
bash setup.sh

# Or manually:
pip install -r requirements.txt
```

### Step 2: Test Installation

```bash
python test_installation.py
```

You should see:
```
✅ All tests passed! You're ready to run the screener.
```

### Step 3: Run Your First Scan

```bash
# Works immediately - no API keys needed!
python earnings_vol_screener.py --tickers NVDA AAPL MSFT
```

**That's it! The screener is fully functional.**

---

## 🔑 Optional: Add API Keys for Extra Features

### Polygon.io (Better Option Data)

**Why add this?**
- More reliable option chain data
- Higher rate limits
- Better historical data

**How to set up:**

1. **Get API Key:**
   - Go to https://polygon.io/
   - Sign up for free account
   - Copy your API key from dashboard

2. **Add to Config:**
   ```bash
   cp config.ini.template config.ini
   nano config.ini  # or use any text editor
   ```

3. **Edit config.ini:**
   ```ini
   [API]
   polygon_api_key = YOUR_API_KEY_HERE
   ```

4. **Test:**
   ```bash
   python earnings_vol_screener.py --tickers AAPL
   # Check logs - should say "Data collector initialized with Polygon"
   ```

---

### Telegram Bot (Phone Alerts)

**Why add this?**
- Get notified instantly when recommended trades appear
- Daily automated alerts
- Never miss a good setup

**How to set up (2 minutes):**

1. **Create Bot:**
   - Open Telegram app
   - Search for @BotFather
   - Send message: `/newbot`
   - Follow instructions to name your bot
   - **Copy the bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get Your Chat ID:**
   - Search for @userinfobot
   - Send any message
   - **Copy your ID** (numeric, like: `123456789`)

3. **Add to Config:**
   Edit `config.ini`:
   ```ini
   [API]
   telegram_bot_token = 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   telegram_chat_id = 123456789
   ```

4. **Important: Message Your Bot First**
   - Find your bot in Telegram (search for the name you gave it)
   - Send it any message like "Hi"
   - This activates the chat

5. **Test:**
   ```bash
   python earnings_vol_screener.py --tickers NVDA --send-telegram
   ```

   You should get a message on Telegram! 🎉

---

## 🌍 Alternative: Use Environment Variables

Instead of `config.ini`, you can use environment variables:

### Linux/Mac:
```bash
# Add to ~/.bashrc or ~/.zshrc
export POLYGON_API_KEY="your_key_here"
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### Windows:
```cmd
# PowerShell
$env:POLYGON_API_KEY="your_key_here"
$env:TELEGRAM_BOT_TOKEN="your_token_here"
$env:TELEGRAM_CHAT_ID="your_chat_id_here"
```

### Python (.env file):
```bash
# Create .env file
echo 'POLYGON_API_KEY=your_key_here' > .env
echo 'TELEGRAM_BOT_TOKEN=your_token_here' >> .env
echo 'TELEGRAM_CHAT_ID=your_chat_id_here' >> .env
```

---

## 📁 File Structure Reference

```
ALGO/
├── earnings_vol_screener.py    # Main algorithm (CLI)
├── streamlit_app.py            # Web interface
├── scheduler.py                # Daily automation
├── requirements.txt            # Python dependencies
├── config.ini.template         # Config template
├── config.ini                  # Your config (create from template)
├── setup.sh                    # Quick setup script
├── test_installation.py        # Test script
├── README.md                   # Full documentation
├── QUICK_START.md             # Quick reference
├── SETUP_GUIDE.md             # This file
└── tickers_example.txt        # Example ticker list
```

---

## ✅ Verification Checklist

- [ ] Python 3.8+ installed: `python --version`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Test passed: `python test_installation.py`
- [ ] First scan works: `python earnings_vol_screener.py --tickers AAPL`
- [ ] (Optional) Polygon API key added to config.ini
- [ ] (Optional) Telegram bot token added to config.ini
- [ ] (Optional) Sent test Telegram message

---

## 🎯 Common Use Cases

### Just Want to Screen Stocks
**No API keys needed!**
```bash
python earnings_vol_screener.py --auto-scan
```

### Want Telegram Alerts
**Need: Telegram bot (free)**
```bash
# Setup bot (see above), then:
python scheduler.py
# Runs daily at 3:30 PM, sends alerts
```

### Want Best Data Quality
**Need: Polygon API (free tier)**
```bash
# Add API key to config.ini, then run normally:
python earnings_vol_screener.py --auto-scan
```

### Want Web Interface
**No API keys needed!**
```bash
streamlit run streamlit_app.py
```

---

## 🆘 Troubleshooting

### "No module named 'xyz'"
```bash
pip install -r requirements.txt
```

### Can't create config.ini
```bash
cp config.ini.template config.ini
chmod 644 config.ini
```

### Telegram not working
- Did you message your bot first?
- Is the token correct? (Should have a `:` in the middle)
- Is chat ID numeric?
- Check logs: `tail -f earnings_vol_screener.log`

### Permission denied
```bash
chmod +x earnings_vol_screener.py
chmod +x setup.sh
```

---

## 📞 Where to Get Help

1. **Check logs:**
   ```bash
   tail -f earnings_vol_screener.log
   ```

2. **Run test script:**
   ```bash
   python test_installation.py
   ```

3. **Read full docs:**
   - `README.md` - Complete documentation
   - `QUICK_START.md` - Common commands
   - This file - Setup details

---

## 🎓 Next Steps

1. ✅ Setup complete? → See `QUICK_START.md` for usage examples
2. 📊 Want automation? → Run `python scheduler.py`
3. 🎨 Want web UI? → Run `streamlit run streamlit_app.py`
4. 📈 Want to backtest? → Add `--backtest --monte-carlo` flags

---

**You're all set! Happy trading! 📈**

*Remember: This is for educational purposes. Always paper trade first.*
