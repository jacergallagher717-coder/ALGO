#!/usr/bin/env python3
"""
Earnings Volatility Screener - Options Trading Algorithm
==========================================================

This algorithm implements the earnings volatility trading strategy that identifies
high-probability short calendar spread opportunities around earnings announcements.

Strategy Overview:
- Identify stocks with upcoming earnings where IV significantly exceeds RV
- Look for negative IV term structure (near-term IV > far-term IV)
- Execute short calendar spreads to profit from volatility crush post-earnings

Usage:
    python earnings_vol_screener.py --tickers NVDA AAPL MSFT META
    python earnings_vol_screener.py --auto-scan
    python earnings_vol_screener.py --backtest

Requirements:
    See requirements.txt for dependencies
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import logging
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Optional imports with fallbacks
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

try:
    import requests
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

try:
    from polygon import RESTClient
    POLYGON_AVAILABLE = True
except ImportError:
    POLYGON_AVAILABLE = False

# Configuration
CONFIG = {
    'IV_RV_THRESHOLD_RECOMMENDED': 1.25,
    'IV_RV_THRESHOLD_CONSIDER': 1.1,
    'SLOPE_THRESHOLD': -0.00406,
    'VOLUME_THRESHOLD_RECOMMENDED': 1_500_000,
    'VOLUME_THRESHOLD_CONSIDER': 1_000_000,
    'RV_WINDOW': 30,
    'POSITION_SIZE_KELLY_FRACTION': 0.25,
    'BACKTEST_STARTING_CAPITAL': 10_000,
    'MONTE_CARLO_SIMULATIONS': 1000,
    'MONTE_CARLO_TRADES': 252,  # One year of trading days
    'TELEGRAM_BOT_TOKEN': '',  # Set via config.ini or env var
    'TELEGRAM_CHAT_ID': '',     # Set via config.ini or env var
    'POLYGON_API_KEY': '',      # Set via config.ini or env var
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('earnings_vol_screener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataCollector:
    """
    Collects OHLC data, option chains, and earnings dates for specified tickers.
    """

    def __init__(self, use_polygon: bool = False, polygon_api_key: Optional[str] = None):
        """
        Initialize data collector.

        Args:
            use_polygon: Whether to use Polygon.io API (premium) or yfinance (free)
            polygon_api_key: API key for Polygon.io
        """
        self.use_polygon = use_polygon and POLYGON_AVAILABLE
        if self.use_polygon:
            if not polygon_api_key:
                logger.warning("Polygon API key not provided, falling back to yfinance")
                self.use_polygon = False
            else:
                self.polygon_client = RESTClient(polygon_api_key)

        logger.info(f"Data collector initialized with {'Polygon' if self.use_polygon else 'yfinance'}")

    def fetch_price_data(self, ticker: str, period: str = '3mo') -> pd.DataFrame:
        """
        Fetch historical OHLC data for a ticker.

        Args:
            ticker: Stock ticker symbol
            period: Time period (e.g., '3mo', '6mo', '1y')

        Returns:
            DataFrame with OHLC data
        """
        try:
            if self.use_polygon:
                # Polygon.io implementation
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)

                aggs = self.polygon_client.get_aggs(
                    ticker=ticker,
                    multiplier=1,
                    timespan="day",
                    from_=start_date.strftime('%Y-%m-%d'),
                    to=end_date.strftime('%Y-%m-%d')
                )

                df = pd.DataFrame([{
                    'Date': datetime.fromtimestamp(a.timestamp / 1000),
                    'Open': a.open,
                    'High': a.high,
                    'Low': a.low,
                    'Close': a.close,
                    'Volume': a.volume
                } for a in aggs])
                df.set_index('Date', inplace=True)
            else:
                # yfinance implementation
                stock = yf.Ticker(ticker)
                df = stock.history(period=period)

            logger.info(f"Fetched {len(df)} days of price data for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Error fetching price data for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_option_chain(self, ticker: str) -> Dict:
        """
        Fetch option chain data for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with option chain data by expiration
        """
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options

            if not expirations or len(expirations) < 2:
                logger.warning(f"Insufficient option expirations for {ticker}")
                return {}

            option_data = {}
            for exp in expirations[:3]:  # Get first 3 expirations
                try:
                    opt = stock.option_chain(exp)
                    option_data[exp] = {
                        'calls': opt.calls,
                        'puts': opt.puts,
                        'expiration': pd.to_datetime(exp)
                    }
                except Exception as e:
                    logger.warning(f"Error fetching options for {ticker} exp {exp}: {e}")
                    continue

            logger.info(f"Fetched option chain for {ticker} with {len(option_data)} expirations")
            return option_data

        except Exception as e:
            logger.error(f"Error fetching option chain for {ticker}: {e}")
            return {}

    def get_earnings_dates(self, tickers: List[str]) -> Dict[str, datetime]:
        """
        Get upcoming earnings dates for tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping ticker to earnings date
        """
        earnings_dates = {}

        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                calendar = stock.calendar

                if calendar is not None and 'Earnings Date' in calendar:
                    earnings_date = calendar['Earnings Date']
                    if isinstance(earnings_date, list):
                        earnings_date = earnings_date[0]
                    earnings_dates[ticker] = pd.to_datetime(earnings_date)
                    logger.info(f"{ticker} earnings date: {earnings_date}")
                else:
                    logger.warning(f"No earnings date found for {ticker}")

            except Exception as e:
                logger.warning(f"Error fetching earnings date for {ticker}: {e}")
                continue

        return earnings_dates


class VolatilityCalculator:
    """
    Calculates realized volatility (RV), implied volatility (IV), and term structure metrics.
    """

    @staticmethod
    def calculate_realized_volatility(prices: pd.Series, window: int = 30) -> float:
        """
        Calculate realized volatility using log returns.

        Args:
            prices: Series of closing prices
            window: Lookback window in days

        Returns:
            Annualized realized volatility
        """
        if len(prices) < window:
            return np.nan

        log_returns = np.log(prices / prices.shift(1))
        rv = log_returns.tail(window).std() * np.sqrt(252)

        return rv

    @staticmethod
    def extract_atm_iv(option_data: Dict, current_price: float) -> Tuple[float, str]:
        """
        Extract ATM implied volatility from option chain.

        Args:
            option_data: Option chain data for an expiration
            current_price: Current stock price

        Returns:
            Tuple of (ATM IV, expiration date)
        """
        try:
            calls = option_data['calls']
            puts = option_data['puts']

            # Find ATM strike (closest to current price)
            calls['distance'] = abs(calls['strike'] - current_price)
            atm_call = calls.loc[calls['distance'].idxmin()]

            puts['distance'] = abs(puts['strike'] - current_price)
            atm_put = puts.loc[puts['distance'].idxmin()]

            # Average call and put IV
            call_iv = atm_call.get('impliedVolatility', np.nan)
            put_iv = atm_put.get('impliedVolatility', np.nan)

            if pd.isna(call_iv) and pd.isna(put_iv):
                return np.nan, option_data['expiration']
            elif pd.isna(call_iv):
                return put_iv, option_data['expiration']
            elif pd.isna(put_iv):
                return call_iv, option_data['expiration']
            else:
                return (call_iv + put_iv) / 2, option_data['expiration']

        except Exception as e:
            logger.error(f"Error extracting ATM IV: {e}")
            return np.nan, option_data.get('expiration', '')

    @staticmethod
    def calculate_iv30(option_chain: Dict, current_price: float) -> Tuple[float, float, float, int, int]:
        """
        Calculate 30-day interpolated IV and term structure slope.

        Args:
            option_chain: Complete option chain data
            current_price: Current stock price

        Returns:
            Tuple of (IV30, near_term_IV, far_term_IV, near_dte, far_dte)
        """
        if len(option_chain) < 2:
            return np.nan, np.nan, np.nan, 0, 0

        # Extract IVs and DTEs
        ivs = []
        dtes = []
        expirations = sorted(option_chain.keys())

        for exp in expirations[:3]:
            iv, exp_date = VolatilityCalculator.extract_atm_iv(option_chain[exp], current_price)
            if not pd.isna(iv):
                dte = (exp_date - datetime.now()).days
                if dte > 0:
                    ivs.append(iv)
                    dtes.append(dte)

        if len(ivs) < 2:
            return np.nan, np.nan, np.nan, 0, 0

        # Interpolate to 30 days
        iv30 = np.interp(30, dtes, ivs)

        # Get near and far term
        near_iv, far_iv = ivs[0], ivs[1]
        near_dte, far_dte = dtes[0], dtes[1]

        return iv30, near_iv, far_iv, near_dte, far_dte


class MetricsCalculator:
    """
    Calculates screening metrics including IV/RV ratio and term structure slope.
    """

    def __init__(self, config: Dict = None):
        self.config = config or CONFIG
        self.data_collector = DataCollector(
            use_polygon=bool(self.config.get('POLYGON_API_KEY')),
            polygon_api_key=self.config.get('POLYGON_API_KEY')
        )
        self.vol_calculator = VolatilityCalculator()

    def calculate_metrics_for_ticker(self, ticker: str) -> Dict:
        """
        Calculate all metrics for a single ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with all calculated metrics
        """
        logger.info(f"Processing {ticker}...")

        # Fetch price data
        price_data = self.data_collector.fetch_price_data(ticker)
        if price_data.empty:
            return self._empty_metrics(ticker)

        # Calculate RV30
        rv30 = self.vol_calculator.calculate_realized_volatility(
            price_data['Close'],
            window=self.config['RV_WINDOW']
        )

        if pd.isna(rv30):
            return self._empty_metrics(ticker)

        # Fetch option chain
        option_chain = self.data_collector.fetch_option_chain(ticker)
        if not option_chain:
            return self._empty_metrics(ticker)

        # Calculate IV metrics
        current_price = price_data['Close'].iloc[-1]
        iv30, near_iv, far_iv, near_dte, far_dte = self.vol_calculator.calculate_iv30(
            option_chain, current_price
        )

        if pd.isna(iv30) or pd.isna(near_iv) or pd.isna(far_iv):
            return self._empty_metrics(ticker)

        # Calculate IV/RV ratio
        iv_rv_ratio = iv30 / rv30 if rv30 > 0 else np.nan

        # Calculate term structure slope
        slope = (near_iv - far_iv) / (far_dte - near_dte) if far_dte > near_dte else np.nan

        # Get average volume
        avg_volume = price_data['Volume'].tail(20).mean()

        # Determine verdict
        verdict = self._determine_verdict(iv_rv_ratio, slope, avg_volume)

        return {
            'Ticker': ticker,
            'CurrentPrice': current_price,
            'RV30': rv30,
            'IV30': iv30,
            'IV_RV_Ratio': iv_rv_ratio,
            'NearIV': near_iv,
            'FarIV': far_iv,
            'NearDTE': near_dte,
            'FarDTE': far_dte,
            'Slope': slope,
            'AvgVolume': avg_volume,
            'Verdict': verdict
        }

    def _determine_verdict(self, iv_rv_ratio: float, slope: float, avg_volume: float) -> str:
        """Determine trading verdict based on metrics."""
        if pd.isna(iv_rv_ratio) or pd.isna(slope):
            return 'Insufficient Data'

        # Recommended criteria
        if (avg_volume >= self.config['VOLUME_THRESHOLD_RECOMMENDED'] and
            iv_rv_ratio >= self.config['IV_RV_THRESHOLD_RECOMMENDED'] and
            slope <= self.config['SLOPE_THRESHOLD']):
            return 'Recommended'

        # Consider criteria
        elif (avg_volume >= self.config['VOLUME_THRESHOLD_CONSIDER'] and
              iv_rv_ratio >= self.config['IV_RV_THRESHOLD_CONSIDER']):
            return 'Consider'

        return 'Not Recommended'

    @staticmethod
    def _empty_metrics(ticker: str) -> Dict:
        """Return empty metrics dict for ticker."""
        return {
            'Ticker': ticker,
            'CurrentPrice': np.nan,
            'RV30': np.nan,
            'IV30': np.nan,
            'IV_RV_Ratio': np.nan,
            'NearIV': np.nan,
            'FarIV': np.nan,
            'NearDTE': 0,
            'FarDTE': 0,
            'Slope': np.nan,
            'AvgVolume': np.nan,
            'Verdict': 'Insufficient Data'
        }

    def screen_tickers(self, tickers: List[str]) -> pd.DataFrame:
        """
        Screen multiple tickers and return results DataFrame.

        Args:
            tickers: List of ticker symbols

        Returns:
            DataFrame with metrics for all tickers
        """
        results = []

        for ticker in tickers:
            try:
                metrics = self.calculate_metrics_for_ticker(ticker)
                results.append(metrics)
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                results.append(self._empty_metrics(ticker))

        df = pd.DataFrame(results)
        return df


class TradeSimulator:
    """
    Simulates short calendar spread trades with Kelly criterion position sizing.
    """

    def __init__(self, starting_capital: float = 10_000, kelly_fraction: float = 0.25):
        self.starting_capital = starting_capital
        self.kelly_fraction = kelly_fraction
        self.trade_history = []

    def simulate_trade(self,
                      iv_rv_ratio: float,
                      near_iv: float,
                      far_iv: float,
                      current_price: float,
                      near_dte: int,
                      far_dte: int) -> Dict:
        """
        Simulate a single short calendar spread trade.

        Strategy:
        - Short near-term ATM straddle (collect premium)
        - Long far-term ATM straddle (protection)
        - Profit from near-term premium decay and vol crush

        Args:
            iv_rv_ratio: Implied to realized volatility ratio
            near_iv: Near-term implied volatility
            far_iv: Far-term implied volatility
            current_price: Current stock price
            near_dte: Days to expiration for near-term
            far_dte: Days to expiration for far-term

        Returns:
            Dictionary with trade results
        """
        # Estimate option premiums using Black-Scholes approximation
        # Simplified: premium ≈ 0.4 * stock_price * IV * sqrt(DTE/365)
        near_premium = 0.4 * current_price * near_iv * np.sqrt(near_dte / 365)
        far_premium = 0.4 * current_price * far_iv * np.sqrt(far_dte / 365)

        # Net credit = premium collected - premium paid
        net_credit = near_premium - far_premium

        # Estimate probability of profit based on IV crush
        # Higher IV/RV ratio suggests higher probability of vol crush
        prob_profit = min(0.5 + (iv_rv_ratio - 1) * 0.2, 0.85)

        # Expected value (edge)
        expected_decay = net_credit * prob_profit

        # Kelly criterion position size
        if expected_decay > 0 and net_credit > 0:
            kelly_size = (prob_profit * net_credit - (1 - prob_profit) * net_credit) / net_credit
            position_size = self.kelly_fraction * kelly_size
        else:
            position_size = 0

        # Simulate outcome (win or loss)
        outcome = np.random.random() < prob_profit

        if outcome:
            # Win: collect net credit
            pnl = net_credit * position_size
        else:
            # Loss: lose amount risked (simplified)
            max_loss = far_premium * position_size
            pnl = -max_loss

        return {
            'net_credit': net_credit,
            'prob_profit': prob_profit,
            'position_size': position_size,
            'pnl': pnl,
            'outcome': 'Win' if outcome else 'Loss'
        }

    def backtest(self, metrics_df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
        """
        Backtest the strategy on screened tickers.

        Args:
            metrics_df: DataFrame with screening metrics

        Returns:
            Tuple of (trade history DataFrame, final account value)
        """
        account_value = self.starting_capital
        trades = []

        # Filter to recommended trades only
        recommended = metrics_df[metrics_df['Verdict'] == 'Recommended'].copy()

        logger.info(f"Backtesting {len(recommended)} recommended trades")

        for idx, row in recommended.iterrows():
            if pd.isna(row['IV_RV_Ratio']):
                continue

            trade = self.simulate_trade(
                iv_rv_ratio=row['IV_RV_Ratio'],
                near_iv=row['NearIV'],
                far_iv=row['FarIV'],
                current_price=row['CurrentPrice'],
                near_dte=row['NearDTE'],
                far_dte=row['FarDTE']
            )

            # Update account
            account_value += trade['pnl']

            trades.append({
                'Ticker': row['Ticker'],
                'Entry_Date': datetime.now(),
                'Account_Value': account_value,
                'PnL': trade['pnl'],
                'Position_Size': trade['position_size'],
                'Outcome': trade['outcome']
            })

        trades_df = pd.DataFrame(trades)
        return trades_df, account_value

    def monte_carlo_simulation(self,
                              num_simulations: int = 1000,
                              num_trades: int = 252,
                              win_rate: float = 0.65,
                              avg_win: float = 500,
                              avg_loss: float = 300) -> pd.DataFrame:
        """
        Run Monte Carlo simulation to project account growth.

        Args:
            num_simulations: Number of simulation runs
            num_trades: Number of trades per simulation
            win_rate: Probability of winning trade
            avg_win: Average winning trade P&L
            avg_loss: Average losing trade P&L

        Returns:
            DataFrame with simulation results
        """
        logger.info(f"Running {num_simulations} Monte Carlo simulations...")

        simulations = []

        for sim in range(num_simulations):
            account_value = self.starting_capital
            equity_curve = [account_value]

            for trade in range(num_trades):
                # Simulate trade outcome
                if np.random.random() < win_rate:
                    pnl = np.random.normal(avg_win, avg_win * 0.3)
                else:
                    pnl = -np.random.normal(avg_loss, avg_loss * 0.3)

                account_value += pnl
                equity_curve.append(account_value)

            simulations.append({
                'simulation': sim,
                'final_value': account_value,
                'return_pct': (account_value - self.starting_capital) / self.starting_capital * 100,
                'equity_curve': equity_curve
            })

        return pd.DataFrame(simulations)


class OutputGenerator:
    """
    Generates outputs including CSV exports and visualizations.
    """

    @staticmethod
    def export_to_csv(df: pd.DataFrame, filename: str = 'screener_results.csv'):
        """Export screening results to CSV."""
        df.to_csv(filename, index=False)
        logger.info(f"Results exported to {filename}")

    @staticmethod
    def plot_backtest_results(trades_df: pd.DataFrame, mc_results: pd.DataFrame = None):
        """
        Plot backtest results and Monte Carlo simulations.

        Args:
            trades_df: Trade history DataFrame
            mc_results: Monte Carlo simulation results
        """
        if not PLOTTING_AVAILABLE:
            logger.warning("Matplotlib not available, skipping plots")
            return

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Plot 1: Cumulative returns
        if not trades_df.empty:
            ax = axes[0, 0]
            ax.plot(trades_df.index, trades_df['Account_Value'], linewidth=2)
            ax.set_title('Cumulative Account Value', fontsize=14, fontweight='bold')
            ax.set_xlabel('Trade Number')
            ax.set_ylabel('Account Value ($)')
            ax.grid(True, alpha=0.3)

        # Plot 2: Trade P&L distribution
        if not trades_df.empty:
            ax = axes[0, 1]
            ax.hist(trades_df['PnL'], bins=30, edgecolor='black', alpha=0.7)
            ax.set_title('P&L Distribution', fontsize=14, fontweight='bold')
            ax.set_xlabel('P&L ($)')
            ax.set_ylabel('Frequency')
            ax.grid(True, alpha=0.3)

        # Plot 3: Monte Carlo simulations
        if mc_results is not None and not mc_results.empty:
            ax = axes[1, 0]
            for idx, row in mc_results.head(100).iterrows():
                ax.plot(row['equity_curve'], alpha=0.1, color='blue')
            ax.set_title('Monte Carlo Simulations (100 paths)', fontsize=14, fontweight='bold')
            ax.set_xlabel('Trade Number')
            ax.set_ylabel('Account Value ($)')
            ax.grid(True, alpha=0.3)

        # Plot 4: Final returns distribution
        if mc_results is not None and not mc_results.empty:
            ax = axes[1, 1]
            ax.hist(mc_results['return_pct'], bins=50, edgecolor='black', alpha=0.7)
            ax.set_title('Monte Carlo Return Distribution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Return (%)')
            ax.set_ylabel('Frequency')
            ax.axvline(mc_results['return_pct'].median(), color='red', linestyle='--', label='Median')
            ax.legend()
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('backtest_results.png', dpi=300, bbox_inches='tight')
        logger.info("Charts saved to backtest_results.png")
        plt.close()


class TelegramBot:
    """
    Sends alerts to Telegram for recommended trades.
    """

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = TELEGRAM_AVAILABLE and bot_token and chat_id

        if not self.enabled:
            logger.warning("Telegram bot not configured or requests library not available")

    def send_alert(self, message: str):
        """Send alert message to Telegram."""
        if not self.enabled:
            return

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data)

            if response.status_code == 200:
                logger.info("Telegram alert sent successfully")
            else:
                logger.error(f"Telegram alert failed: {response.text}")

        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")

    def send_screening_results(self, df: pd.DataFrame):
        """Send screening results to Telegram."""
        recommended = df[df['Verdict'] == 'Recommended']

        if recommended.empty:
            message = "📊 *Earnings Vol Screener*\n\nNo recommended trades today."
        else:
            message = "🚀 *Earnings Vol Screener - RECOMMENDED TRADES*\n\n"

            for idx, row in recommended.iterrows():
                message += f"*{row['Ticker']}*\n"
                message += f"  • IV/RV Ratio: {row['IV_RV_Ratio']:.2f}\n"
                message += f"  • Slope: {row['Slope']:.5f}\n"
                message += f"  • Volume: {row['AvgVolume']:,.0f}\n"
                message += f"  • Price: ${row['CurrentPrice']:.2f}\n\n"

        self.send_alert(message)


def load_config():
    """Load configuration from config.ini or environment variables."""
    import configparser
    import os

    config = CONFIG.copy()

    # Try to load from config.ini
    config_file = 'config.ini'
    if os.path.exists(config_file):
        parser = configparser.ConfigParser()
        parser.read(config_file)

        if 'API' in parser:
            config['POLYGON_API_KEY'] = parser['API'].get('polygon_api_key', '')
            config['TELEGRAM_BOT_TOKEN'] = parser['API'].get('telegram_bot_token', '')
            config['TELEGRAM_CHAT_ID'] = parser['API'].get('telegram_chat_id', '')

    # Override with environment variables
    config['POLYGON_API_KEY'] = os.getenv('POLYGON_API_KEY', config['POLYGON_API_KEY'])
    config['TELEGRAM_BOT_TOKEN'] = os.getenv('TELEGRAM_BOT_TOKEN', config['TELEGRAM_BOT_TOKEN'])
    config['TELEGRAM_CHAT_ID'] = os.getenv('TELEGRAM_CHAT_ID', config['TELEGRAM_CHAT_ID'])

    return config


def get_default_tickers() -> List[str]:
    """Get default list of high-volume tickers with frequent earnings."""
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
        'AMD', 'NFLX', 'DIS', 'BABA', 'CRM', 'INTC', 'PYPL',
        'UBER', 'SQ', 'SNAP', 'SHOP', 'ZM', 'DOCU'
    ]


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Earnings Volatility Screener - Options Trading Algorithm'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='List of tickers to screen (e.g., NVDA AAPL MSFT)'
    )
    parser.add_argument(
        '--auto-scan',
        action='store_true',
        help='Automatically scan default ticker list'
    )
    parser.add_argument(
        '--backtest',
        action='store_true',
        help='Run backtest simulation'
    )
    parser.add_argument(
        '--monte-carlo',
        action='store_true',
        help='Run Monte Carlo simulations'
    )
    parser.add_argument(
        '--send-telegram',
        action='store_true',
        help='Send results to Telegram'
    )
    parser.add_argument(
        '--output',
        default='screener_results.csv',
        help='Output CSV filename'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Determine tickers to screen
    if args.tickers:
        tickers = args.tickers
    elif args.auto_scan:
        tickers = get_default_tickers()
    else:
        # Interactive mode
        print("Enter tickers separated by spaces (or press Enter for default list):")
        user_input = input().strip()
        if user_input:
            tickers = user_input.upper().split()
        else:
            tickers = get_default_tickers()

    logger.info(f"Screening {len(tickers)} tickers: {', '.join(tickers)}")

    # Initialize components
    metrics_calc = MetricsCalculator(config)

    # Screen tickers
    print("\n📊 Screening tickers...")
    results_df = metrics_calc.screen_tickers(tickers)

    # Display results
    print("\n" + "="*80)
    print("SCREENING RESULTS")
    print("="*80)
    print(results_df.to_string(index=False))
    print("\n")

    # Export to CSV
    OutputGenerator.export_to_csv(results_df, args.output)

    # Backtest if requested
    if args.backtest:
        print("\n📈 Running backtest simulation...")
        simulator = TradeSimulator(
            starting_capital=config['BACKTEST_STARTING_CAPITAL'],
            kelly_fraction=config['POSITION_SIZE_KELLY_FRACTION']
        )

        trades_df, final_value = simulator.backtest(results_df)

        if not trades_df.empty:
            print(f"\nBacktest Results:")
            print(f"  Starting Capital: ${config['BACKTEST_STARTING_CAPITAL']:,.2f}")
            print(f"  Final Value: ${final_value:,.2f}")
            print(f"  Total Return: {(final_value/config['BACKTEST_STARTING_CAPITAL']-1)*100:.2f}%")
            print(f"  Number of Trades: {len(trades_df)}")
            print(f"  Win Rate: {(trades_df['Outcome']=='Win').sum()/len(trades_df)*100:.1f}%")

            trades_df.to_csv('backtest_trades.csv', index=False)
            logger.info("Backtest trades saved to backtest_trades.csv")
        else:
            print("\nNo trades executed in backtest (no recommended setups)")

    # Monte Carlo simulation if requested
    mc_results = None
    if args.monte_carlo:
        print("\n🎲 Running Monte Carlo simulations...")
        simulator = TradeSimulator()
        mc_results = simulator.monte_carlo_simulation(
            num_simulations=config['MONTE_CARLO_SIMULATIONS'],
            num_trades=config['MONTE_CARLO_TRADES']
        )

        print(f"\nMonte Carlo Results ({config['MONTE_CARLO_SIMULATIONS']} simulations):")
        print(f"  Median Return: {mc_results['return_pct'].median():.2f}%")
        print(f"  Mean Return: {mc_results['return_pct'].mean():.2f}%")
        print(f"  Best Case (95th percentile): {mc_results['return_pct'].quantile(0.95):.2f}%")
        print(f"  Worst Case (5th percentile): {mc_results['return_pct'].quantile(0.05):.2f}%")

        mc_results.to_csv('monte_carlo_results.csv', index=False)

    # Generate plots
    if args.backtest or args.monte_carlo:
        print("\n📊 Generating charts...")
        trades_df = trades_df if args.backtest else pd.DataFrame()
        OutputGenerator.plot_backtest_results(trades_df, mc_results)

    # Send Telegram alert if requested
    if args.send_telegram:
        print("\n📱 Sending Telegram alert...")
        bot = TelegramBot(config['TELEGRAM_BOT_TOKEN'], config['TELEGRAM_CHAT_ID'])
        bot.send_screening_results(results_df)

    print("\n✅ Done!")


if __name__ == '__main__':
    main()
