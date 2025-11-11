# 📊 Earnings Volatility Screener

A fully functional Python algorithm that identifies high-probability options trading opportunities around earnings announcements by analyzing volatility patterns. Based on the strategy of shorting calendar spreads when implied volatility significantly exceeds realized volatility.

## 🎯 Strategy Overview

This algorithm replicates the earnings volatility crush strategy that can turn small accounts into large gains through systematic options trading:

- **Goal**: Profit from volatility crush after earnings announcements
- **Method**: Short calendar spreads (short near-term straddle + long far-term straddle)
- **Edge**: Enter when IV/RV ratio is high and term structure is inverted
- **Risk Management**: Kelly criterion position sizing + defined risk spreads

## ✨ Features

- ✅ **Data Collection**: Fetch OHLC and option chain data using yfinance or Polygon.io
- ✅ **Volatility Analysis**: Calculate RV30, IV30, and IV term structure slope
- ✅ **Smart Filtering**: Automated screening with customizable thresholds
- ✅ **Trade Simulation**: Backtest with realistic calendar spread modeling
- ✅ **Monte Carlo**: Project account growth over thousands of simulations
- ✅ **CSV Export**: Export results for further analysis
- ✅ **Visualization**: Charts for cumulative returns and drawdowns
- ✅ **CLI Interface**: Command-line tool for automation
- ✅ **Telegram Alerts**: Automated notifications for recommended trades
- ✅ **Scheduling**: Daily automated screening before market close
- ✅ **Streamlit UI**: Interactive web interface with real-time filtering

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ALGO
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API keys (optional)**
```bash
cp config.ini.template config.ini
# Edit config.ini with your API keys
```

### Basic Usage

**Screen specific tickers:**
```bash
python earnings_vol_screener.py --tickers NVDA AAPL MSFT META
```

**Auto-scan default ticker list:**
```bash
python earnings_vol_screener.py --auto-scan
```

**Run backtest simulation:**
```bash
python earnings_vol_screener.py --auto-scan --backtest --monte-carlo
```

**Send results to Telegram:**
```bash
python earnings_vol_screener.py --auto-scan --send-telegram
```

### Streamlit Web Interface

Launch the interactive web interface:
```bash
streamlit run streamlit_app.py
```

Then open your browser to `http://localhost:8501`

## 📋 Configuration

### Option 1: Using config.ini

Copy the template and fill in your API keys:

```bash
cp config.ini.template config.ini
```

Edit `config.ini`:
```ini
[API]
polygon_api_key = YOUR_POLYGON_API_KEY
telegram_bot_token = YOUR_TELEGRAM_BOT_TOKEN
telegram_chat_id = YOUR_TELEGRAM_CHAT_ID

[STRATEGY]
iv_rv_threshold_recommended = 1.25
iv_rv_threshold_consider = 1.1
slope_threshold = -0.00406
volume_threshold_recommended = 1500000
volume_threshold_consider = 1000000
```

### Option 2: Using Environment Variables

Set environment variables (recommended for security):

```bash
export POLYGON_API_KEY="your_api_key"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

## 🔑 API Setup Instructions

### Polygon.io (Optional - Better Data Quality)

1. Go to https://polygon.io/
2. Sign up for a free account
3. Copy your API key from the dashboard
4. Add to `config.ini` or set as environment variable

**Note**: yfinance is used by default (free, no API key needed)

### Telegram Bot (Optional - For Alerts)

1. **Create a bot:**
   - Open Telegram and message [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow instructions
   - Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get your Chat ID:**
   - Message [@userinfobot](https://t.me/userinfobot)
   - Copy your Chat ID (numeric)

3. **Add to configuration:**
   ```ini
   telegram_bot_token = 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   telegram_chat_id = 123456789
   ```

4. **Test the bot:**
   - Send a message to your bot first
   - Run with `--send-telegram` flag

## 📊 Understanding the Metrics

### IV/RV Ratio
- **Formula**: `IV30 / RV30`
- **Meaning**: How expensive options are vs. historical volatility
- **Good Setup**: ≥ 1.25 (IV is 25% higher than RV)

### IV Slope
- **Formula**: `(Near_IV - Far_IV) / (Far_DTE - Near_DTE)`
- **Meaning**: Term structure showing near-term vs. far-term IV
- **Good Setup**: ≤ -0.00406 (steep negative slope)

### Verdict Labels
- **Recommended**: Meets all criteria (IV/RV ≥ 1.25, slope ≤ -0.00406, volume ≥ 1.5M)
- **Consider**: Meets some criteria (IV/RV ≥ 1.1, volume ≥ 1M)
- **Not Recommended**: Does not meet criteria
- **Insufficient Data**: Unable to calculate metrics

## 🎲 Backtesting & Monte Carlo

### Run Backtest

```bash
python earnings_vol_screener.py --auto-scan --backtest
```

This simulates trading all "Recommended" setups with:
- Kelly criterion position sizing (25% Kelly fraction)
- Realistic calendar spread pricing
- Win/loss outcomes based on probability models

Output:
- `backtest_trades.csv`: Trade-by-trade history
- `backtest_results.png`: Cumulative returns chart

### Run Monte Carlo Simulation

```bash
python earnings_vol_screener.py --auto-scan --monte-carlo
```

This projects account growth over 1,000 simulations of 252 trades (1 year):
- Shows median, mean, and percentile outcomes
- Accounts for randomness in trade outcomes
- Validates strategy edge over many scenarios

Output:
- `monte_carlo_results.csv`: All simulation results
- Charts showing return distribution

## ⏰ Automated Daily Screening

### Option 1: Using the Scheduler Script

Run the built-in scheduler (runs daily at 3:30 PM EST):

```bash
python scheduler.py
```

The scheduler will:
- Screen all default tickers daily before market close
- Export results with timestamp
- Send Telegram alerts for recommended trades
- Keep running indefinitely

### Option 2: Using Cron (Linux/Mac)

Add to your crontab:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 3:30 PM EST weekdays)
30 15 * * 1-5 cd /path/to/ALGO && /usr/bin/python3 earnings_vol_screener.py --auto-scan --send-telegram
```

### Option 3: Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 3:30 PM
4. Action: Start a Program
   - Program: `python.exe`
   - Arguments: `earnings_vol_screener.py --auto-scan --send-telegram`
   - Start in: `C:\path\to\ALGO`

## 📁 Output Files

| File | Description |
|------|-------------|
| `screener_results.csv` | Latest screening results |
| `screener_results_YYYYMMDD_HHMMSS.csv` | Timestamped results (scheduler) |
| `backtest_trades.csv` | Simulated trade history |
| `monte_carlo_results.csv` | Monte Carlo simulation data |
| `backtest_results.png` | Charts (equity curve, P&L distribution, etc.) |
| `earnings_vol_screener.log` | Application logs |
| `scheduler.log` | Scheduler logs |

## 🎨 Streamlit Interface Features

The web interface provides:

- **Interactive Filtering**: Adjust thresholds in real-time
- **Custom Ticker Lists**: Screen any tickers you want
- **Live Backtesting**: Run simulations with custom parameters
- **Monte Carlo Visualization**: Interactive return distributions
- **Trade Detail Cards**: Expandable detail for each recommendation
- **CSV Download**: Export results directly from the browser

## 🛠️ Customization

### Adjust Strategy Thresholds

Edit `config.ini` or use the Streamlit interface:

```ini
[STRATEGY]
# Higher = more conservative
iv_rv_threshold_recommended = 1.30

# More negative = steeper term structure required
slope_threshold = -0.005

# Higher = require more liquidity
volume_threshold_recommended = 2000000
```

### Modify Default Tickers

Edit `earnings_vol_screener.py`, function `get_default_tickers()`:

```python
def get_default_tickers() -> List[str]:
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
        # Add your favorite tickers here
    ]
```

### Change Position Sizing

Adjust Kelly fraction (default 0.25 = 25% of Kelly):

```python
CONFIG = {
    'POSITION_SIZE_KELLY_FRACTION': 0.25,  # Increase for more aggressive sizing
    # ...
}
```

## 📚 Advanced Usage

### Screen Tickers from a File

Create `tickers.txt`:
```
NVDA
AAPL
MSFT
META
TSLA
```

Then:
```bash
python earnings_vol_screener.py --tickers $(cat tickers.txt)
```

### Chain Multiple Commands

```bash
python earnings_vol_screener.py \
  --auto-scan \
  --backtest \
  --monte-carlo \
  --send-telegram \
  --output results_$(date +%Y%m%d).csv
```

### Run as Background Service (Linux)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/earnings-screener.service
```

Add:
```ini
[Unit]
Description=Earnings Volatility Screener
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/ALGO
ExecStart=/usr/bin/python3 scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable earnings-screener
sudo systemctl start earnings-screener
```

## ⚠️ Disclaimer

**IMPORTANT**: This software is for educational purposes only. Trading options involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results.

- This is not financial advice
- Always paper trade before using real money
- Understand the risks of options trading
- Consult a licensed financial advisor

The creators of this software are not responsible for any financial losses incurred through its use.

## 🐛 Troubleshooting

### "No option data available"
- **Cause**: Ticker may not have liquid options or upcoming earnings
- **Solution**: Try high-volume stocks with active options markets

### "Insufficient data" for all tickers
- **Cause**: API rate limiting or network issues
- **Solution**:
  - Wait a few minutes between runs
  - Consider using Polygon.io API (higher rate limits)
  - Check your internet connection

### Telegram alerts not working
- **Cause**: Bot token or chat ID incorrect
- **Solution**:
  - Verify bot token from @BotFather
  - Get chat ID from @userinfobot
  - Send a message to your bot first
  - Check `earnings_vol_screener.log` for errors

### Charts not generating
- **Cause**: matplotlib not installed
- **Solution**: `pip install matplotlib seaborn`

## 📞 Support

For issues, questions, or contributions:

1. Check the `earnings_vol_screener.log` file for errors
2. Review this README for configuration steps
3. Open an issue on GitHub with:
   - Python version
   - OS type
   - Error message
   - Steps to reproduce

## 🎓 Learning Resources

- **Options Trading**: Learn about straddles, calendars, and spreads
- **Implied Volatility**: Understand IV rank and IV percentile
- **Kelly Criterion**: Study optimal position sizing
- **Backtesting**: Learn about overfitting and walk-forward analysis

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Strategy inspired by Volatility Vibes' earnings vol crush strategy
- Built with yfinance, pandas, and the Python data science stack
- Community contributions welcome!

---

**Happy Trading! 📈**

*Remember: The best trade is the one you fully understand.*
