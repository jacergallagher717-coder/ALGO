#!/usr/bin/env python3
"""
Liquidity Filters for Options Quality
======================================

Filters options based on liquidity metrics:
- Bid-Ask Spread (should be < 5-10% of mid price)
- Option Volume (should be > 100 contracts/day)
- Open Interest (should be > 500)
- Market Depth

These filters prevent trading illiquid options with poor fills.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class LiquidityFilter:
    """
    Filters options based on liquidity metrics.
    """

    def __init__(
        self,
        max_spread_pct: float = 0.05,  # 5% max spread
        min_volume: int = 100,          # 100 contracts/day
        min_open_interest: int = 500    # 500 OI
    ):
        """
        Initialize liquidity filter with thresholds.

        Args:
            max_spread_pct: Maximum bid-ask spread as % of mid price (0.05 = 5%)
            min_volume: Minimum daily option volume
            min_open_interest: Minimum open interest
        """
        self.max_spread_pct = max_spread_pct
        self.min_volume = min_volume
        self.min_open_interest = min_open_interest

    def check_option_liquidity(
        self,
        option_data: pd.DataFrame,
        option_type: str = 'call'
    ) -> Dict:
        """
        Check if option passes liquidity filters.

        Args:
            option_data: DataFrame with option chain data
            option_type: 'call' or 'put'

        Returns:
            Dict with liquidity metrics and pass/fail status
        """
        try:
            if option_data.empty:
                return {'pass': False, 'reason': 'No option data'}

            # Extract metrics
            bid = option_data.get('bid', 0)
            ask = option_data.get('ask', 0)
            volume = option_data.get('volume', 0)
            open_interest = option_data.get('openInterest', 0)

            # Calculate mid price and spread
            mid_price = (bid + ask) / 2

            if mid_price == 0:
                return {'pass': False, 'reason': 'Zero mid price'}

            spread = ask - bid
            spread_pct = (spread / mid_price) if mid_price > 0 else 1.0

            # Check each criterion
            checks = {
                'spread_ok': spread_pct <= self.max_spread_pct,
                'volume_ok': volume >= self.min_volume,
                'oi_ok': open_interest >= self.min_open_interest,
                'bid_ask_valid': bid > 0 and ask > 0 and ask > bid
            }

            all_pass = all(checks.values())

            result = {
                'pass': all_pass,
                'bid': bid,
                'ask': ask,
                'mid_price': mid_price,
                'spread': spread,
                'spread_pct': spread_pct,
                'volume': volume,
                'open_interest': open_interest,
                'checks': checks
            }

            if not all_pass:
                failed_checks = [k for k, v in checks.items() if not v]
                result['reason'] = f"Failed: {', '.join(failed_checks)}"

            return result

        except Exception as e:
            logger.error(f"Error checking option liquidity: {e}")
            return {'pass': False, 'reason': str(e)}

    def filter_option_chain(
        self,
        option_chain: pd.DataFrame,
        current_price: float,
        strike_range_pct: float = 0.10
    ) -> pd.DataFrame:
        """
        Filter option chain to only liquid options near ATM.

        Args:
            option_chain: Full option chain DataFrame
            current_price: Current stock price
            strike_range_pct: % range around current price to include (0.10 = ±10%)

        Returns:
            Filtered DataFrame with only liquid options
        """
        if option_chain.empty:
            return option_chain

        try:
            # Filter by strike price (near ATM only)
            lower_strike = current_price * (1 - strike_range_pct)
            upper_strike = current_price * (1 + strike_range_pct)

            filtered = option_chain[
                (option_chain['strike'] >= lower_strike) &
                (option_chain['strike'] <= upper_strike)
            ].copy()

            # Add liquidity check column
            filtered['liquid'] = filtered.apply(
                lambda row: self._row_is_liquid(row),
                axis=1
            )

            # Keep only liquid options
            liquid_options = filtered[filtered['liquid']].copy()

            logger.info(f"Filtered {len(option_chain)} options → {len(liquid_options)} liquid options")

            return liquid_options

        except Exception as e:
            logger.error(f"Error filtering option chain: {e}")
            return pd.DataFrame()

    def _row_is_liquid(self, row: pd.Series) -> bool:
        """Check if a single option row passes liquidity filters."""
        try:
            bid = row.get('bid', 0)
            ask = row.get('ask', 0)
            volume = row.get('volume', 0)
            oi = row.get('openInterest', 0)

            # Basic validation
            if bid <= 0 or ask <= 0 or ask <= bid:
                return False

            # Spread check
            mid = (bid + ask) / 2
            spread_pct = (ask - bid) / mid if mid > 0 else 1.0

            if spread_pct > self.max_spread_pct:
                return False

            # Volume and OI checks
            if volume < self.min_volume:
                return False

            if oi < self.min_open_interest:
                return False

            return True

        except:
            return False

    def get_atm_straddle_liquidity(
        self,
        calls: pd.DataFrame,
        puts: pd.DataFrame,
        current_price: float
    ) -> Dict:
        """
        Check liquidity of ATM straddle (call + put at same strike).

        Args:
            calls: Call options DataFrame
            puts: Put options DataFrame
            current_price: Current stock price

        Returns:
            Dict with straddle liquidity metrics
        """
        try:
            # Find ATM strike (closest to current price)
            if calls.empty or puts.empty:
                return {'pass': False, 'reason': 'Missing option data'}

            calls['distance'] = abs(calls['strike'] - current_price)
            puts['distance'] = abs(puts['strike'] - current_price)

            atm_call = calls.loc[calls['distance'].idxmin()]
            atm_put = puts.loc[puts['distance'].idxmin()]

            # Check if same strike
            if atm_call['strike'] != atm_put['strike']:
                logger.warning("ATM call and put have different strikes")

            # Check liquidity of both legs
            call_liq = self.check_option_liquidity(atm_call, 'call')
            put_liq = self.check_option_liquidity(atm_put, 'put')

            # Calculate straddle metrics
            straddle_price = call_liq.get('mid_price', 0) + put_liq.get('mid_price', 0)
            combined_volume = call_liq.get('volume', 0) + put_liq.get('volume', 0)
            combined_oi = call_liq.get('open_interest', 0) + put_liq.get('open_interest', 0)

            # Average spread
            avg_spread_pct = (
                call_liq.get('spread_pct', 1) + put_liq.get('spread_pct', 1)
            ) / 2

            both_pass = call_liq.get('pass', False) and put_liq.get('pass', False)

            return {
                'pass': both_pass,
                'strike': atm_call['strike'],
                'straddle_price': straddle_price,
                'call_mid': call_liq.get('mid_price', 0),
                'put_mid': put_liq.get('mid_price', 0),
                'combined_volume': combined_volume,
                'combined_oi': combined_oi,
                'avg_spread_pct': avg_spread_pct,
                'call_details': call_liq,
                'put_details': put_liq
            }

        except Exception as e:
            logger.error(f"Error checking straddle liquidity: {e}")
            return {'pass': False, 'reason': str(e)}


class MarketQualityChecker:
    """
    Additional market quality checks beyond basic liquidity.
    """

    @staticmethod
    def check_market_hours() -> bool:
        """Check if market is currently open (US Eastern Time)."""
        from datetime import datetime
        import pytz

        try:
            et = pytz.timezone('US/Eastern')
            now = datetime.now(et)

            # Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
            if now.weekday() >= 5:  # Saturday or Sunday
                return False

            market_open = now.replace(hour=9, minute=30, second=0)
            market_close = now.replace(hour=16, minute=0, second=0)

            return market_open <= now <= market_close

        except:
            # If can't determine, assume closed (safer)
            return False

    @staticmethod
    def check_data_freshness(timestamp, max_age_minutes: int = 15) -> bool:
        """
        Check if data is fresh (< N minutes old).

        Args:
            timestamp: Data timestamp
            max_age_minutes: Maximum acceptable age in minutes

        Returns:
            True if data is fresh
        """
        from datetime import datetime, timedelta

        try:
            if timestamp is None:
                return False

            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)

            age = datetime.now() - timestamp
            return age < timedelta(minutes=max_age_minutes)

        except:
            return False

    @staticmethod
    def estimate_slippage(
        bid: float,
        ask: float,
        volume: int,
        quantity: int = 1
    ) -> float:
        """
        Estimate likely slippage for an order.

        Args:
            bid: Bid price
            ask: Ask price
            volume: Daily volume
            quantity: Number of contracts to trade

        Returns:
            Estimated slippage in dollars per contract
        """
        spread = ask - bid
        mid = (bid + ask) / 2

        # Base slippage: half the spread for market orders
        base_slippage = spread / 2

        # Additional slippage if large order relative to volume
        if volume > 0:
            size_impact = (quantity / volume) * mid * 0.10  # 10% impact factor
        else:
            size_impact = spread  # High slippage if no volume data

        total_slippage = base_slippage + min(size_impact, spread)

        return total_slippage


def check_option_quality(
    ticker: str,
    option_chain_data: Dict,
    current_price: float,
    strict: bool = True
) -> Dict:
    """
    Comprehensive option quality check.

    Args:
        ticker: Stock ticker
        option_chain_data: Dict with 'calls' and 'puts' DataFrames
        current_price: Current stock price
        strict: Use strict filtering (recommended for real money)

    Returns:
        Dict with quality assessment and metrics
    """
    # Set thresholds based on strict mode
    if strict:
        max_spread = 0.05  # 5%
        min_vol = 100
        min_oi = 500
    else:
        max_spread = 0.10  # 10%
        min_vol = 50
        min_oi = 200

    liquidity_filter = LiquidityFilter(max_spread, min_vol, min_oi)

    try:
        calls = option_chain_data.get('calls', pd.DataFrame())
        puts = option_chain_data.get('puts', pd.DataFrame())

        if calls.empty or puts.empty:
            return {
                'pass': False,
                'ticker': ticker,
                'reason': 'Missing option data',
                'quality_score': 0
            }

        # Check ATM straddle liquidity
        straddle_liq = liquidity_filter.get_atm_straddle_liquidity(
            calls, puts, current_price
        )

        # Calculate quality score (0-100)
        score = 0

        if straddle_liq.get('pass', False):
            score += 40

        # Spread bonus (lower is better)
        spread_pct = straddle_liq.get('avg_spread_pct', 1)
        spread_score = max(0, 30 - (spread_pct * 500))  # 30 points max
        score += spread_score

        # Volume bonus
        volume = straddle_liq.get('combined_volume', 0)
        if volume >= 1000:
            score += 20
        elif volume >= 500:
            score += 15
        elif volume >= min_vol:
            score += 10

        # OI bonus
        oi = straddle_liq.get('combined_oi', 0)
        if oi >= 5000:
            score += 10
        elif oi >= 1000:
            score += 5

        # Pass/fail based on score
        pass_threshold = 70 if strict else 50
        passed = score >= pass_threshold

        return {
            'pass': passed,
            'ticker': ticker,
            'quality_score': score,
            'straddle_price': straddle_liq.get('straddle_price', 0),
            'avg_spread_pct': spread_pct,
            'combined_volume': volume,
            'combined_oi': oi,
            'strict_mode': strict,
            'details': straddle_liq
        }

    except Exception as e:
        logger.error(f"Error checking option quality for {ticker}: {e}")
        return {
            'pass': False,
            'ticker': ticker,
            'reason': str(e),
            'quality_score': 0
        }


if __name__ == '__main__':
    # Test the module
    import logging
    logging.basicConfig(level=logging.INFO)

    print("Testing Liquidity Filters")
    print("=" * 70)

    # Create sample option data
    sample_call = pd.Series({
        'strike': 180,
        'bid': 4.20,
        'ask': 4.40,
        'volume': 150,
        'openInterest': 800,
        'impliedVolatility': 0.25
    })

    sample_put = pd.Series({
        'strike': 180,
        'bid': 3.80,
        'ask': 4.00,
        'volume': 120,
        'openInterest': 650,
        'impliedVolatility': 0.26
    })

    filter = LiquidityFilter()

    print("\nCall Option:")
    call_liq = filter.check_option_liquidity(sample_call, 'call')
    print(f"  Pass: {call_liq['pass']}")
    print(f"  Mid Price: ${call_liq['mid_price']:.2f}")
    print(f"  Spread: {call_liq['spread_pct']:.2%}")
    print(f"  Volume: {call_liq['volume']}")
    print(f"  OI: {call_liq['open_interest']}")

    print("\nPut Option:")
    put_liq = filter.check_option_liquidity(sample_put, 'put')
    print(f"  Pass: {put_liq['pass']}")
    print(f"  Mid Price: ${put_liq['mid_price']:.2f}")
    print(f"  Spread: {put_liq['spread_pct']:.2%}")
    print(f"  Volume: {put_liq['volume']}")
    print(f"  OI: {put_liq['open_interest']}")

    print("\n" + "=" * 70)
