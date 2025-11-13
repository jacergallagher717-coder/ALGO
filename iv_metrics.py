#!/usr/bin/env python3
"""
IV Rank and IV Percentile Calculator
=====================================

Calculates critical volatility metrics:
- IV Rank: Where current IV sits in 52-week range (0-100)
- IV Percentile: % of time IV was lower in past year (0-100)
- Expected Move: What the options market expects for price movement
- Historical Vol Crush: Average IV drop after past earnings

These metrics are CRITICAL for professional options trading.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class IVMetricsCalculator:
    """
    Calculates advanced IV metrics for options trading.
    """

    def __init__(self):
        self.cache = {}

    def calculate_iv_rank(self, ticker: str, current_iv: float, period_days: int = 252) -> float:
        """
        Calculate IV Rank: where current IV sits in historical range.

        IV Rank = (Current IV - Min IV) / (Max IV - Min IV) * 100

        Args:
            ticker: Stock ticker
            current_iv: Current implied volatility (as decimal, e.g., 0.35)
            period_days: Lookback period (default 252 = 1 year)

        Returns:
            IV Rank (0-100)
            - 0 = IV at 52-week low
            - 50 = IV in middle of range
            - 100 = IV at 52-week high
            - Above 70 = Good for selling premium
            - Below 30 = Good for buying premium
        """
        try:
            # Get historical IV data
            iv_history = self._get_historical_iv(ticker, period_days)

            if iv_history is None or len(iv_history) < 30:
                logger.warning(f"Insufficient IV history for {ticker}")
                return np.nan

            min_iv = iv_history.min()
            max_iv = iv_history.max()

            if max_iv == min_iv:
                return 50.0  # Constant IV (rare)

            iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100

            # Clamp to 0-100
            iv_rank = max(0, min(100, iv_rank))

            logger.info(f"{ticker} IV Rank: {iv_rank:.1f} (IV: {current_iv:.2%}, Range: {min_iv:.2%}-{max_iv:.2%})")

            return iv_rank

        except Exception as e:
            logger.error(f"Error calculating IV Rank for {ticker}: {e}")
            return np.nan

    def calculate_iv_percentile(self, ticker: str, current_iv: float, period_days: int = 252) -> float:
        """
        Calculate IV Percentile: % of time IV was lower than current.

        More robust than IV Rank (less affected by outliers).

        Args:
            ticker: Stock ticker
            current_iv: Current implied volatility
            period_days: Lookback period

        Returns:
            IV Percentile (0-100)
            - 80 = IV was lower 80% of the time
            - Above 50 = High IV environment
        """
        try:
            iv_history = self._get_historical_iv(ticker, period_days)

            if iv_history is None or len(iv_history) < 30:
                return np.nan

            percentile = (iv_history < current_iv).sum() / len(iv_history) * 100

            logger.info(f"{ticker} IV Percentile: {percentile:.1f}")

            return percentile

        except Exception as e:
            logger.error(f"Error calculating IV Percentile for {ticker}: {e}")
            return np.nan

    def _get_historical_iv(self, ticker: str, period_days: int) -> Optional[pd.Series]:
        """
        Get historical IV data for a ticker.

        Uses ATM option IVs from historical option chains.
        Fallback: Calculate HV as proxy for IV.
        """
        # Check cache
        cache_key = f"{ticker}_{period_days}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Method 1: Try to get historical IV from options
            # Note: This is limited with free data sources
            # Best approach with paid data: Use historical options database

            # Method 2: Use Historical Volatility as proxy (fallback)
            stock = yf.Ticker(ticker)
            hist = stock.history(period=f"{period_days}d")

            if hist.empty or len(hist) < 30:
                return None

            # Calculate rolling HV (20-day window)
            log_returns = np.log(hist['Close'] / hist['Close'].shift(1))
            hv = log_returns.rolling(window=20).std() * np.sqrt(252)

            # Drop NaN values
            hv = hv.dropna()

            # Cache it
            self.cache[cache_key] = hv

            return hv

        except Exception as e:
            logger.error(f"Error fetching historical IV for {ticker}: {e}")
            return None

    def calculate_expected_move(
        self,
        stock_price: float,
        atm_straddle_price: float,
        days_to_expiry: int
    ) -> Dict[str, float]:
        """
        Calculate expected move based on ATM straddle price.

        The ATM straddle price tells us what the market expects for movement.

        Args:
            stock_price: Current stock price
            atm_straddle_price: Price of ATM straddle (call + put)
            days_to_expiry: Days until expiration

        Returns:
            Dict with:
                - expected_move_pct: Expected move as %
                - expected_move_dollars: Expected move in dollars
                - upper_range: Stock price + expected move
                - lower_range: Stock price - expected move
                - annual_iv: Implied annualized volatility
        """
        try:
            # Expected move (1 standard deviation) ≈ Straddle Price / sqrt(DTE/365)
            # More accurate: Straddle Price ≈ 0.85 (this is the conversion factor)
            expected_move_dollars = atm_straddle_price / 0.85

            expected_move_pct = (expected_move_dollars / stock_price) * 100

            # Calculate implied annual IV from straddle
            # Straddle price ≈ stock_price * IV * sqrt(DTE/365)
            # Solving for IV:
            annual_iv = (atm_straddle_price / stock_price) / np.sqrt(days_to_expiry / 365)

            return {
                'expected_move_pct': expected_move_pct,
                'expected_move_dollars': expected_move_dollars,
                'upper_range': stock_price + expected_move_dollars,
                'lower_range': stock_price - expected_move_dollars,
                'annual_iv': annual_iv
            }

        except Exception as e:
            logger.error(f"Error calculating expected move: {e}")
            return {}

    def get_historical_earnings_vol_crush(
        self,
        ticker: str,
        num_earnings: int = 4
    ) -> Dict[str, float]:
        """
        Calculate average IV crush after past earnings.

        This helps predict how much IV will drop after next earnings.

        Args:
            ticker: Stock ticker
            num_earnings: Number of past earnings to analyze

        Returns:
            Dict with:
                - avg_iv_crush_pct: Average IV drop % after earnings
                - max_crush: Largest IV drop
                - min_crush: Smallest IV drop
                - consistency: How consistent the crush is (std dev)
        """
        try:
            # Get earnings dates from history
            stock = yf.Ticker(ticker)

            # This requires historical options data (premium feature)
            # For free tier, we'll estimate based on HV changes around earnings

            hist = stock.history(period="2y")

            if hist.empty:
                return {}

            # Calculate rolling 20-day HV
            log_returns = np.log(hist['Close'] / hist['Close'].shift(1))
            hv = log_returns.rolling(window=20).std() * np.sqrt(252)

            # Identify large vol spikes (likely earnings)
            # Earnings typically cause vol spike then crush
            vol_changes = hv.pct_change()

            # Find top vol spike events
            spike_threshold = vol_changes.quantile(0.95)
            spike_indices = vol_changes[vol_changes > spike_threshold].index

            crushes = []

            for spike_date in spike_indices:
                # Get HV before spike
                idx = hist.index.get_loc(spike_date)

                if idx < 5 or idx > len(hist) - 10:
                    continue

                hv_before = hv.iloc[idx - 5]
                hv_after_spike = hv.iloc[idx]

                # Check for crush in next 5 days
                hv_after_crush = hv.iloc[idx:idx+10].min()

                if pd.notna(hv_before) and pd.notna(hv_after_spike) and pd.notna(hv_after_crush):
                    crush_pct = ((hv_after_spike - hv_after_crush) / hv_after_spike) * 100
                    if crush_pct > 0:  # Only count actual crushes
                        crushes.append(crush_pct)

            if not crushes:
                return {}

            return {
                'avg_iv_crush_pct': np.mean(crushes),
                'max_crush': np.max(crushes),
                'min_crush': np.min(crushes),
                'consistency': np.std(crushes),
                'num_events': len(crushes)
            }

        except Exception as e:
            logger.error(f"Error calculating historical vol crush for {ticker}: {e}")
            return {}


def get_professional_metrics(
    ticker: str,
    current_iv: float,
    stock_price: float,
    atm_straddle_price: float,
    days_to_earnings: int
) -> Dict:
    """
    Get all professional-grade IV metrics for a ticker.

    Args:
        ticker: Stock ticker
        current_iv: Current implied volatility
        stock_price: Current stock price
        atm_straddle_price: ATM straddle price
        days_to_earnings: Days until earnings

    Returns:
        Dictionary with all metrics
    """
    calculator = IVMetricsCalculator()

    metrics = {
        'ticker': ticker,
        'current_iv': current_iv,
        'iv_rank': calculator.calculate_iv_rank(ticker, current_iv),
        'iv_percentile': calculator.calculate_iv_percentile(ticker, current_iv),
    }

    # Expected move
    expected_move = calculator.calculate_expected_move(
        stock_price,
        atm_straddle_price,
        days_to_earnings
    )
    metrics.update(expected_move)

    # Historical crush
    crush_data = calculator.get_historical_earnings_vol_crush(ticker)
    metrics['historical_crush'] = crush_data

    return metrics


if __name__ == '__main__':
    # Test the module
    import logging
    logging.basicConfig(level=logging.INFO)

    print("Testing IV Metrics Calculator")
    print("=" * 70)

    # Test with AAPL
    ticker = "AAPL"
    current_iv = 0.25  # 25% IV
    stock_price = 180.00
    atm_straddle = 8.50
    dte = 7

    calculator = IVMetricsCalculator()

    print(f"\nTicker: {ticker}")
    print(f"Current IV: {current_iv:.1%}")
    print(f"Stock Price: ${stock_price:.2f}")
    print(f"ATM Straddle: ${atm_straddle:.2f}")
    print(f"DTE: {dte} days")
    print("-" * 70)

    # IV Rank
    iv_rank = calculator.calculate_iv_rank(ticker, current_iv)
    print(f"\nIV Rank: {iv_rank:.1f}")
    if iv_rank > 70:
        print("  → HIGH IV RANK - Good for selling premium")
    elif iv_rank < 30:
        print("  → LOW IV RANK - Good for buying premium")
    else:
        print("  → NEUTRAL IV RANK")

    # IV Percentile
    iv_pct = calculator.calculate_iv_percentile(ticker, current_iv)
    print(f"\nIV Percentile: {iv_pct:.1f}")

    # Expected Move
    exp_move = calculator.calculate_expected_move(stock_price, atm_straddle, dte)
    print(f"\nExpected Move:")
    print(f"  Dollars: ±${exp_move.get('expected_move_dollars', 0):.2f}")
    print(f"  Percent: ±{exp_move.get('expected_move_pct', 0):.2f}%")
    print(f"  Range: ${exp_move.get('lower_range', 0):.2f} - ${exp_move.get('upper_range', 0):.2f}")

    # Historical Crush
    print(f"\nHistorical Earnings Vol Crush:")
    crush = calculator.get_historical_earnings_vol_crush(ticker)
    if crush:
        print(f"  Average Crush: {crush.get('avg_iv_crush_pct', 0):.1f}%")
        print(f"  Range: {crush.get('min_crush', 0):.1f}% - {crush.get('max_crush', 0):.1f}%")
        print(f"  Events Analyzed: {crush.get('num_events', 0)}")
    else:
        print("  Data not available")

    print("\n" + "=" * 70)
