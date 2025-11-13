#!/usr/bin/env python3
"""
Earnings Calendar Module - Alpha Vantage Integration
=====================================================

Fetches upcoming earnings dates and filters stocks with earnings announcements.
Uses Alpha Vantage free API (500 calls/day limit).

API Key Setup:
- Get free key at: https://www.alphavantage.co/support/#api-key
- Add to config.ini: alpha_vantage_api_key = YOUR_KEY
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import time

logger = logging.getLogger(__name__)


class EarningsCalendar:
    """
    Manages earnings calendar data from multiple sources.
    """

    def __init__(self, alpha_vantage_key: Optional[str] = None, fmp_key: Optional[str] = None):
        """
        Initialize earnings calendar with API keys.

        Args:
            alpha_vantage_key: Alpha Vantage API key (free)
            fmp_key: Financial Modeling Prep API key (paid)
        """
        self.av_key = alpha_vantage_key
        self.fmp_key = fmp_key
        self.cache = {}
        self.cache_timestamp = None
        self.cache_duration = 3600  # 1 hour cache

    def get_upcoming_earnings(
        self,
        days_ahead: int = 14,
        use_fmp: bool = False
    ) -> pd.DataFrame:
        """
        Get tickers with upcoming earnings in next N days.

        Args:
            days_ahead: Number of days to look ahead
            use_fmp: Use FMP API instead of Alpha Vantage (requires paid key)

        Returns:
            DataFrame with columns: [Ticker, EarningsDate, TimeOfDay, EPS_Estimate]
        """
        # Check cache
        if self._is_cache_valid():
            logger.info("Using cached earnings calendar data")
            return self._filter_by_date(self.cache['data'], days_ahead)

        # Fetch new data
        if use_fmp and self.fmp_key:
            earnings_df = self._fetch_from_fmp(days_ahead)
        elif self.av_key:
            earnings_df = self._fetch_from_alpha_vantage(days_ahead)
        else:
            logger.warning("No API keys configured, using fallback method")
            earnings_df = self._fetch_from_yfinance_fallback()

        # Update cache
        self.cache = {'data': earnings_df, 'timestamp': datetime.now()}

        return earnings_df

    def _fetch_from_alpha_vantage(self, days_ahead: int) -> pd.DataFrame:
        """
        Fetch earnings calendar from Alpha Vantage (free tier).

        API Docs: https://www.alphavantage.co/documentation/#earnings-calendar
        Limit: 500 calls/day
        """
        logger.info("Fetching earnings calendar from Alpha Vantage...")

        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'EARNINGS_CALENDAR',
            'horizon': '3month',
            'apikey': self.av_key
        }

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(f"Alpha Vantage API error: {response.status_code}")
                return pd.DataFrame()

            # Alpha Vantage returns CSV format
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))

            # Rename columns to standard format
            df = df.rename(columns={
                'symbol': 'Ticker',
                'reportDate': 'EarningsDate',
                'estimate': 'EPS_Estimate'
            })

            # Convert date
            df['EarningsDate'] = pd.to_datetime(df['EarningsDate'])

            # Filter to next N days
            today = datetime.now()
            cutoff = today + timedelta(days=days_ahead)
            df = df[(df['EarningsDate'] >= today) & (df['EarningsDate'] <= cutoff)]

            # Add time of day (Alpha Vantage doesn't provide this)
            df['TimeOfDay'] = 'Unknown'

            logger.info(f"Found {len(df)} stocks with earnings in next {days_ahead} days")

            return df[['Ticker', 'EarningsDate', 'TimeOfDay', 'EPS_Estimate']]

        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {e}")
            return pd.DataFrame()

    def _fetch_from_fmp(self, days_ahead: int) -> pd.DataFrame:
        """
        Fetch earnings calendar from Financial Modeling Prep (paid tier).

        API Docs: https://site.financialmodelingprep.com/developer/docs
        Better data quality than Alpha Vantage.
        """
        logger.info("Fetching earnings calendar from FMP...")

        today = datetime.now()
        end_date = today + timedelta(days=days_ahead)

        url = f"https://financialmodelingprep.com/api/v3/earning_calendar"
        params = {
            'from': today.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'apikey': self.fmp_key
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if not data or isinstance(data, dict) and 'Error Message' in data:
                logger.error(f"FMP API error: {data}")
                return pd.DataFrame()

            df = pd.DataFrame(data)

            # Rename to standard format
            df = df.rename(columns={
                'symbol': 'Ticker',
                'date': 'EarningsDate',
                'time': 'TimeOfDay',
                'epsEstimated': 'EPS_Estimate'
            })

            df['EarningsDate'] = pd.to_datetime(df['EarningsDate'])

            logger.info(f"Found {len(df)} stocks with earnings in next {days_ahead} days")

            return df[['Ticker', 'EarningsDate', 'TimeOfDay', 'EPS_Estimate']]

        except Exception as e:
            logger.error(f"Error fetching from FMP: {e}")
            return pd.DataFrame()

    def _fetch_from_yfinance_fallback(self) -> pd.DataFrame:
        """
        Fallback method using yfinance (less reliable, no bulk calendar).
        Only use if no API keys configured.
        """
        logger.warning("Using yfinance fallback - limited functionality")

        # Common high-volume tickers that often report earnings
        common_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
            'AMD', 'NFLX', 'DIS', 'CRM', 'INTC', 'PYPL', 'SQ',
            'UBER', 'SNAP', 'SHOP', 'ZM', 'DOCU', 'ROKU'
        ]

        import yfinance as yf

        earnings_data = []

        for ticker in common_tickers:
            try:
                stock = yf.Ticker(ticker)
                calendar = stock.calendar

                if calendar is not None and 'Earnings Date' in calendar:
                    earnings_date = calendar['Earnings Date']
                    if isinstance(earnings_date, list):
                        earnings_date = earnings_date[0]

                    earnings_data.append({
                        'Ticker': ticker,
                        'EarningsDate': pd.to_datetime(earnings_date),
                        'TimeOfDay': 'Unknown',
                        'EPS_Estimate': None
                    })

                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                logger.debug(f"Could not fetch earnings for {ticker}: {e}")
                continue

        df = pd.DataFrame(earnings_data)

        if not df.empty:
            today = datetime.now()
            df = df[df['EarningsDate'] >= today]
            logger.info(f"Found {len(df)} stocks with upcoming earnings (fallback method)")

        return df

    def _filter_by_date(self, df: pd.DataFrame, days_ahead: int) -> pd.DataFrame:
        """Filter dataframe to only include earnings in next N days."""
        if df.empty:
            return df

        today = datetime.now()
        cutoff = today + timedelta(days=days_ahead)

        return df[(df['EarningsDate'] >= today) & (df['EarningsDate'] <= cutoff)]

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self.cache or 'timestamp' not in self.cache:
            return False

        age = (datetime.now() - self.cache['timestamp']).total_seconds()
        return age < self.cache_duration

    def get_earnings_date(self, ticker: str) -> Optional[datetime]:
        """
        Get earnings date for a specific ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Earnings date or None if not found
        """
        # Try to get from cache first
        if self._is_cache_valid() and 'data' in self.cache:
            df = self.cache['data']
            matches = df[df['Ticker'] == ticker]
            if not matches.empty:
                return matches.iloc[0]['EarningsDate']

        # Fallback to yfinance for single ticker
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            calendar = stock.calendar

            if calendar is not None and 'Earnings Date' in calendar:
                earnings_date = calendar['Earnings Date']
                if isinstance(earnings_date, list):
                    earnings_date = earnings_date[0]
                return pd.to_datetime(earnings_date)

        except Exception as e:
            logger.debug(f"Could not fetch earnings date for {ticker}: {e}")

        return None

    def filter_high_volume_earnings(
        self,
        earnings_df: pd.DataFrame,
        min_volume: int = 1_000_000
    ) -> pd.DataFrame:
        """
        Filter earnings calendar to only high-volume stocks.

        Args:
            earnings_df: Earnings calendar DataFrame
            min_volume: Minimum average daily volume

        Returns:
            Filtered DataFrame
        """
        import yfinance as yf

        filtered = []

        for idx, row in earnings_df.iterrows():
            ticker = row['Ticker']

            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='1mo')

                if not hist.empty:
                    avg_volume = hist['Volume'].mean()

                    if avg_volume >= min_volume:
                        filtered.append(row)

                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                logger.debug(f"Could not check volume for {ticker}: {e}")
                continue

        return pd.DataFrame(filtered)


# Helper function for easy import
def get_earnings_calendar(
    alpha_vantage_key: Optional[str] = None,
    fmp_key: Optional[str] = None,
    days_ahead: int = 14,
    min_volume: int = 1_500_000
) -> List[str]:
    """
    Get list of tickers with upcoming earnings (high-volume only).

    Args:
        alpha_vantage_key: Alpha Vantage API key
        fmp_key: FMP API key (optional, paid)
        days_ahead: Look ahead N days
        min_volume: Minimum average daily volume

    Returns:
        List of ticker symbols
    """
    calendar = EarningsCalendar(alpha_vantage_key, fmp_key)

    # Get earnings calendar
    use_fmp = bool(fmp_key)
    earnings_df = calendar.get_upcoming_earnings(days_ahead, use_fmp)

    if earnings_df.empty:
        logger.warning("No earnings data found")
        return []

    # Filter by volume
    filtered_df = calendar.filter_high_volume_earnings(earnings_df, min_volume)

    # Return ticker list
    tickers = filtered_df['Ticker'].unique().tolist()

    logger.info(f"Found {len(tickers)} high-volume stocks with earnings in next {days_ahead} days")

    return tickers


if __name__ == '__main__':
    # Test the module
    import sys

    logging.basicConfig(level=logging.INFO)

    print("Testing Earnings Calendar Module")
    print("=" * 50)

    # You can test with your Alpha Vantage key
    # Get free key at: https://www.alphavantage.co/support/#api-key
    av_key = input("Enter Alpha Vantage API key (or press Enter to skip): ").strip()

    if av_key:
        tickers = get_earnings_calendar(
            alpha_vantage_key=av_key,
            days_ahead=14,
            min_volume=1_500_000
        )

        print(f"\nFound {len(tickers)} tickers with upcoming earnings:")
        print(tickers)
    else:
        print("\nNo API key provided, using fallback method...")
        calendar = EarningsCalendar()
        df = calendar.get_upcoming_earnings(days_ahead=14)
        print(df)
