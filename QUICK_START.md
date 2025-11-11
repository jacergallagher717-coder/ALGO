# ⚡ Quick Start Guide

## 🏃 Get Running in 5 Minutes

### 1. Install
```bash
bash setup.sh
```

### 2. Run Your First Scan
```bash
source venv/bin/activate
python earnings_vol_screener.py --auto-scan
```

### 3. View Results
Check `screener_results.csv` - look for "Recommended" trades!

## 🎯 Common Commands

### Basic Screening
```bash
# Screen specific tickers
python earnings_vol_screener.py --tickers NVDA AAPL MSFT

# Auto-scan default list
python earnings_vol_screener.py --auto-scan

# Screen custom list from file
python earnings_vol_screener.py --tickers $(cat my_tickers.txt)
```

### With Backtest
```bash
python earnings_vol_screener.py --auto-scan --backtest --monte-carlo
```

### Launch Web Interface
```bash
streamlit run streamlit_app.py
```

### Daily Automation
```bash
python scheduler.py
```

## 📊 Understanding Results

### What to Look For
- **Verdict: "Recommended"** = Strong setup, all criteria met
- **IV/RV Ratio > 1.25** = Options are expensive vs. historical vol
- **Slope < -0.00406** = Near-term IV higher than far-term (good for calendar spreads)
- **Volume > 1.5M** = Liquid market

### Example Good Setup
```
Ticker: NVDA
IV/RV Ratio: 1.45
Slope: -0.0052
Volume: 45M
Verdict: Recommended
```

This means: NVDA options are expensive (1.45x historical vol), term structure is inverted (steep negative slope), and there's plenty of liquidity.

## 🔑 Optional: Add API Keys

### Why?
- **Polygon.io**: More reliable option data (free tier available)
- **Telegram**: Get alerts on your phone for recommended trades

### How?
1. Copy template: `cp config.ini.template config.ini`
2. Edit `config.ini` with your keys
3. See README.md for detailed setup instructions

## 🚀 Automation Setup

### Option 1: Built-in Scheduler
```bash
python scheduler.py
# Runs daily at 3:30 PM, sends Telegram alerts
```

### Option 2: Cron (Linux/Mac)
```bash
crontab -e
# Add: 30 15 * * 1-5 cd /path/to/ALGO && python earnings_vol_screener.py --auto-scan
```

### Option 3: Windows Task Scheduler
1. Open Task Scheduler
2. Create task: Daily at 3:30 PM
3. Action: Run `python earnings_vol_screener.py --auto-scan`

## 📱 Telegram Setup (2 Minutes)

1. Message @BotFather on Telegram → `/newbot`
2. Copy bot token
3. Message @userinfobot → copy your chat ID
4. Add both to `config.ini`
5. Test: `python earnings_vol_screener.py --auto-scan --send-telegram`

## 🎨 Streamlit Interface

```bash
streamlit run streamlit_app.py
```

Then open http://localhost:8501

Features:
- Adjust thresholds with sliders
- Run backtests interactively
- Download results as CSV
- View Monte Carlo simulations

## 🆘 Quick Troubleshooting

### "No module named 'yfinance'"
```bash
pip install -r requirements.txt
```

### "No options data available"
- Try high-volume stocks: AAPL, NVDA, TSLA, MSFT
- Make sure markets are open (9:30 AM - 4:00 PM EST)

### Telegram not working
- Did you message your bot first?
- Check token and chat ID in config.ini
- Look at logs: `tail -f earnings_vol_screener.log`

## 💡 Pro Tips

1. **Run before earnings season** - More opportunities when many companies report
2. **Focus on high volume stocks** - Better fills, tighter spreads
3. **Paper trade first** - Validate the strategy before using real money
4. **Monitor IV rank** - Best setups are when IV rank > 50%
5. **Use the backtest** - Understand expected win rate and returns

## 📈 What's Next?

- [ ] Run your first scan
- [ ] Set up Telegram alerts (optional)
- [ ] Run a backtest simulation
- [ ] Schedule daily automation
- [ ] Paper trade recommended setups
- [ ] Track results in a journal

---

**Ready to go? Run:**
```bash
python earnings_vol_screener.py --auto-scan --backtest
```

Good luck! 🚀
